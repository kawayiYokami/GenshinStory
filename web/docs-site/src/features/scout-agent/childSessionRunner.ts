import { tool as createAiTool, type CoreMessage } from 'ai';
import { z } from 'zod';
import type { Config } from '@/features/app/stores/config';
import logger from '@/features/app/services/loggerService';
import llmProviderService from '@/lib/llm/llmProviderService';
import { paramsToRequestBody } from '@/features/app/utils/paramUtils';
import { toolRegistryService } from '@/features/agent/tools/registry/toolRegistryService';
import type { Tool } from '@/features/agent/tools/tool';

export interface ExploreReport {
  task: string;
  status: 'success' | 'partial' | 'failed' | 'timeout';
  answer: string;
  insights: string[];
  references: string[];
  summary: string;
  evidence: Array<{ source: string; note: string }>;
  confidence: number;
  usedCalls: number;
  maxToolCalls: number;
  error?: string;
}

interface RunChildSessionOptions {
  config: Config;
  task: string;
  maxToolCalls: number;
  timeoutMs?: number;
}

function isErrorResult(text: string): boolean {
  return String(text || '').trim().startsWith('错误');
}

function safeJsonParse(text: string): any {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function normalizeReference(raw: string): string | null {
  const text = String(raw || '').trim();
  if (!text) return null;
  const main = text.split('|')[0].trim();
  const preciseRefPattern = /.+:\d+(?:-\d+)?$/;
  if (!preciseRefPattern.test(main)) return null;
  return main;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.map(v => v.trim()).filter(Boolean)));
}

function referencesFromEvidence(evidence: Array<{ source: string; note: string }>): string[] {
  return uniqueStrings(
    evidence
      .map(item => normalizeReference(item.source))
      .filter((item): item is string => Boolean(item))
  );
}

function buildFallbackSummary(task: string, evidence: Array<{ source: string; note: string }>, error?: string): string {
  if (error) {
    return `子会话未能完成标准汇报：${error}`;
  }
  if (evidence.length > 0) {
    return `已完成探索任务“${task}”，并提取到 ${evidence.length} 条证据。`;
  }
  return `探索任务“${task}”未获得有效证据。`;
}

function buildFallbackAnswer(task: string, evidence: Array<{ source: string; note: string }>, error?: string): string {
  if (error) {
    return `任务“${task}”未完成：${error}`;
  }
  if (evidence.length > 0) {
    return `基于已检索证据，任务“${task}”有初步结论，请结合引用行号继续复核。`;
  }
  return `未找到足够证据回答任务“${task}”。`;
}

function pickConfidence(evidenceCount: number, hasError: boolean): number {
  if (hasError) return 0.2;
  if (evidenceCount >= 3) return 0.85;
  if (evidenceCount >= 1) return 0.65;
  return 0.35;
}

function buildChildSystemPrompt(maxToolCalls: number): string {
  return [
    '你是一个专业的信息搜索专家（探索子代理），会话与主会话完全隔离。',
    '你的唯一目标：高效完成当前任务，严禁过度发散、严禁无意义重复搜索。',
    '你只允许调用三个工具：search_docs、read_doc、report_findings。',
    '必须先至少成功调用一次 read_doc，再调用 report_findings。',
    `非 report 工具总调用次数上限为 ${maxToolCalls}。达到上限后必须立刻调用 report_findings。`,
    '执行策略（必须遵守）：先小范围 search，再精准 read，证据足够后立即 report。',
    '停止条件（必须立即汇报）：',
    '1) 已获得可直接回答任务的关键证据；',
    '2) 连续两次工具调用没有新增有效证据；',
    '3) 已出现重复检索/重复阅读趋势；',
    '4) 预算接近上限或无法进一步提升答案质量。',
    'report_findings 输出契约（必须遵守）：',
    '1) answer: 直接回答任务问题，先给结论；',
    '2) insights: 给出2-5条探索见解（方法、局限、风险、冲突点）；',
    '3) references: 给出精确文件行号，格式必须是 path:line 或 path:start-end；',
    '4) confidence: 0-1 的置信度；',
    '5) summary 可选，但建议包含最终一句话摘要。',
    '如果无法给出带行号的 references，不允许结束，必须继续 search/read 后再 report。',
    '禁止输出与任务无关内容。',
  ].join('\n');
}

function createChildTools(
  searchTool: Tool,
  readTool: Tool,
  maxToolCalls: number,
  task: string,
) {
  let nonReportCalls = 0;
  let successfulReadCount = 0;
  let forceReport = false;
  const evidence: Array<{ source: string; note: string }> = [];
  let noNewEvidenceStreak = 0;
  let finalReport: ExploreReport | null = null;
  const pushEvidence = (source: string, note: string) => {
    const normalized = source.trim();
    if (!normalized) return;
    const exists = evidence.some(item => item.source === normalized && item.note === note);
    if (!exists) {
      evidence.push({ source: normalized, note });
    }
  };

  const addEvidenceFromSearch = (raw: string) => {
    const parsed = safeJsonParse(raw);
    const results = Array.isArray(parsed?.results) ? parsed.results : [];
    const top = results[0];
    if (top?.path && Array.isArray(top?.hits) && top.hits.length > 0) {
      for (const hit of top.hits.slice(0, 3)) {
        const line = Number(hit?.line || 0);
        if (line > 0) {
          pushEvidence(
            `${String(top.path)}:${line}`,
            `search 命中，hitCount=${Number(top.hitCount || 0)}`
          );
        }
      }
      return;
    }
    if (top?.path && Number(top?.line || 0) > 0) {
      pushEvidence(
        `${String(top.path)}:${Number(top.line)}`,
        `search 命中，hitCount=${Number(top.hitCount || 0)}`
      );
    }
  };

  const addEvidenceFromRead = (raw: string) => {
    const parsed = safeJsonParse(raw);
    const firstDoc = Array.isArray(parsed?.docs) ? parsed.docs[0] : null;
    if (firstDoc?.path) {
      const lineRange = String(firstDoc.lineRange || '').trim();
      if (lineRange) {
        pushEvidence(
          `${String(firstDoc.path)}:${lineRange}`,
          `read 命中，lineRange=${lineRange}`
        );
      }
    }
  };

  const searchDocs = createAiTool({
    description: searchTool.description || '搜索文档',
    inputSchema: z.object({
      query: z.string().optional(),
      regex: z.string().optional(),
      path: z.string().optional(),
      maxResults: z.number().optional(),
    }),
    execute: async (params: any) => {
      if (forceReport || nonReportCalls >= maxToolCalls) {
        forceReport = true;
        return '错误(TOOL_FORCE_REPORT): 已达到或接近预算上限，请立刻调用 report_findings。';
      }
      const beforeEvidenceCount = evidence.length;
      nonReportCalls += 1;
      if (nonReportCalls >= maxToolCalls) {
        forceReport = true;
      }
      const result = await searchTool.execute(params);
      addEvidenceFromSearch(result.result);

      if (evidence.length === beforeEvidenceCount) {
        noNewEvidenceStreak += 1;
      } else {
        noNewEvidenceStreak = 0;
      }
      if (noNewEvidenceStreak >= 2) {
        forceReport = true;
      }
      return result.result;
    },
  });

  const readDoc = createAiTool({
    description: readTool.description || '读取文档',
    inputSchema: z.object({
      path: z.string().optional(),
      line_range: z.string().optional(),
    }),
    execute: async (params: any) => {
      if (forceReport || nonReportCalls >= maxToolCalls) {
        forceReport = true;
        return '错误(TOOL_FORCE_REPORT): 已达到或接近预算上限，请立刻调用 report_findings。';
      }
      const beforeEvidenceCount = evidence.length;
      nonReportCalls += 1;
      if (nonReportCalls >= maxToolCalls) {
        forceReport = true;
      }
      const result = await readTool.execute(params);
      if (!isErrorResult(result.result)) {
        successfulReadCount += 1;
        addEvidenceFromRead(result.result);
      }

      if (evidence.length === beforeEvidenceCount) {
        noNewEvidenceStreak += 1;
      } else {
        noNewEvidenceStreak = 0;
      }

      // 已经有读取证据后，优先收敛，避免过度发散
      if ((successfulReadCount >= 1 && evidence.length >= 2) || noNewEvidenceStreak >= 2) {
        forceReport = true;
      }
      return result.result;
    },
  });

  const reportFindings = createAiTool({
    description: '提交最终探索报告',
    inputSchema: z.object({
      answer: z.string().optional(),
      insights: z.array(z.string()).optional(),
      references: z.array(z.string()).optional(),
      summary: z.string().optional(),
      evidence: z.array(z.string()).optional(),
      confidence: z.number().optional(),
    }),
    execute: async (params: any) => {
      if (successfulReadCount < 1) {
        return '错误(TOOL_ORDER_VIOLATION): report_findings 前必须先成功调用 read_doc。请先使用 read_doc。';
      }

      const answer = String(params.answer || '').trim();
      if (!answer) {
        return '错误(REPORT_MISSING_ANSWER): report_findings 必须提供 answer，并直接回答任务问题。';
      }

      const insights = Array.isArray(params.insights)
        ? params.insights.map((item: string) => String(item || '').trim()).filter(Boolean)
        : [];
      if (insights.length === 0) {
        return '错误(REPORT_MISSING_INSIGHTS): report_findings 必须提供 insights（2-5条见解）。';
      }

      const userReferences = Array.isArray(params.references)
        ? params.references
            .map((item: string) => normalizeReference(item))
            .filter((item: unknown): item is string => typeof item === 'string' && item.length > 0)
        : [];
      const autoReferences = referencesFromEvidence(evidence);
      const mergedReferences = uniqueStrings(userReferences.concat(autoReferences));
      if (mergedReferences.length === 0) {
        return '错误(REPORT_MISSING_LINE_REFERENCES): report_findings 必须提供精确行号引用，格式 path:line 或 path:start-end。';
      }

      const userEvidence = Array.isArray(params.evidence)
        ? params.evidence.map((item: string, index: number) => ({ source: `llm_evidence_${index + 1}`, note: String(item) }))
        : [];
      const mergedEvidence = evidence.concat(userEvidence).slice(0, 8);
      const summary = String(params.summary || '').trim() || `任务结论：${answer}`;
      const confidenceRaw = Number(params.confidence ?? pickConfidence(mergedEvidence.length, false));
      const confidence = Number.isFinite(confidenceRaw) ? Math.max(0, Math.min(1, confidenceRaw)) : 0.5;

      finalReport = {
        task,
        status: 'success',
        answer,
        insights: insights.slice(0, 5),
        references: mergedReferences,
        summary,
        evidence: mergedEvidence,
        confidence,
        usedCalls: nonReportCalls,
        maxToolCalls,
      };

      return JSON.stringify(finalReport);
    },
  });

  return {
    tools: {
      search_docs: searchDocs,
      read_doc: readDoc,
      report_findings: reportFindings,
    },
    getFinalReport: () => finalReport,
    getEvidence: () => evidence,
    getUsedCalls: () => nonReportCalls,
  };
}

export async function runChildSession(options: RunChildSessionOptions): Promise<ExploreReport> {
  const { config, task, maxToolCalls } = options;
  const timeoutMs = options.timeoutMs ?? 10 * 60 * 1000;

  await toolRegistryService.loadTools();
  const searchTool = toolRegistryService.getTool('search_docs');
  const readTool = toolRegistryService.getTool('read_doc');
  if (!searchTool || !readTool) {
    return {
      task,
      status: 'failed',
      answer: `任务“${task}”初始化失败。`,
      insights: ['缺少必要工具，无法开始探索。'],
      references: [],
      summary: '子会话初始化失败：缺少必要工具。',
      evidence: [],
      confidence: 0.1,
      usedCalls: 0,
      maxToolCalls,
      error: 'MISSING_REQUIRED_TOOLS',
    };
  }

  const child = createChildTools(searchTool, readTool, maxToolCalls, task);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const messages: CoreMessage[] = [
      { role: 'system', content: buildChildSystemPrompt(maxToolCalls) },
      { role: 'user', content: `探索任务：${task}` },
    ];

    const childConfig: Config = {
      ...config,
      stream: false,
      maxIterations: Math.max(4, maxToolCalls + 3),
    };
    const customParamsBody = paramsToRequestBody(config.customParams);

    await llmProviderService.createStructuredChatCompletion(
      messages,
      childConfig,
      controller.signal,
      child.tools,
      customParamsBody,
      childConfig.maxIterations
    );

    const finalReport = child.getFinalReport();
    if (finalReport) {
      return finalReport;
    }

    const fallbackEvidence = child.getEvidence();
    return {
      task,
      status: fallbackEvidence.length > 0 ? 'partial' : 'failed',
      answer: buildFallbackAnswer(task, fallbackEvidence, '未产生 report_findings'),
      insights: ['子会话未形成完整结构化报告，已返回可用证据。'],
      references: referencesFromEvidence(fallbackEvidence),
      summary: buildFallbackSummary(task, fallbackEvidence, '未产生 report_findings'),
      evidence: fallbackEvidence,
      confidence: pickConfidence(fallbackEvidence.length, fallbackEvidence.length === 0),
      usedCalls: child.getUsedCalls(),
      maxToolCalls,
      error: 'REPORT_NOT_PRODUCED',
    };
  } catch (error: any) {
    const isTimeout = error?.name === 'AbortError';
    const fallbackEvidence = child.getEvidence();
    const errMessage = isTimeout ? 'TIMEOUT' : (error?.message || String(error));
    logger.error('[ChildSessionRunner] 子会话执行失败', { task, error: errMessage });

    return {
      task,
      status: isTimeout ? 'timeout' : 'failed',
      answer: buildFallbackAnswer(task, fallbackEvidence, errMessage),
      insights: ['子会话执行中断，返回当前可用证据用于人工复核。'],
      references: referencesFromEvidence(fallbackEvidence),
      summary: buildFallbackSummary(task, fallbackEvidence, errMessage),
      evidence: fallbackEvidence,
      confidence: pickConfidence(fallbackEvidence.length, true),
      usedCalls: child.getUsedCalls(),
      maxToolCalls,
      error: errMessage,
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function runChildSessionsInParallel(
  tasks: string[],
  config: Config,
  maxToolCalls: number,
  timeoutMs: number = 10 * 60 * 1000,
): Promise<ExploreReport[]> {
  const concurrency = Math.min(5, Math.max(1, tasks.length));
  const results: ExploreReport[] = new Array(tasks.length);
  let cursor = 0;

  const worker = async () => {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= tasks.length) return;
      results[index] = await runChildSession({
        config,
        task: tasks[index],
        maxToolCalls,
        timeoutMs,
      });
    }
  };

  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return results;
}
