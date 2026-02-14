import { tool as createAiTool } from 'ai';
import { z } from 'zod';
import type { Tool } from '@/features/agent/tools/tool';
import type { ExploreEvidence, ExploreReport } from './contracts';

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

export function referencesFromEvidence(evidence: ExploreEvidence[]): string[] {
  return uniqueStrings(
    evidence
      .map(item => normalizeReference(item.source))
      .filter((item): item is string => Boolean(item))
  );
}

export function buildFallbackSummary(task: string, evidence: ExploreEvidence[], error?: string): string {
  if (error) {
    return `子会话未能完成标准汇报：${error}`;
  }
  if (evidence.length > 0) {
    return `已完成探索任务“${task}”，并提取到 ${evidence.length} 条证据。`;
  }
  return `探索任务“${task}”未获得有效证据。`;
}

export function buildFallbackAnswer(task: string, evidence: ExploreEvidence[], error?: string): string {
  if (error) {
    return `任务“${task}”未完成：${error}`;
  }
  if (evidence.length > 0) {
    return `基于已检索证据，任务“${task}”有初步结论，请结合引用行号继续复核。`;
  }
  return `未找到足够证据回答任务“${task}”。`;
}

export function pickConfidence(evidenceCount: number, hasError: boolean): number {
  if (hasError) return 0.2;
  if (evidenceCount >= 3) return 0.85;
  if (evidenceCount >= 1) return 0.65;
  return 0.35;
}

interface CreateChildToolsParams {
  task: string;
  maxToolCalls: number;
  searchTool: Tool;
  readTool: Tool;
}

interface ChildToolsRuntime {
  tools: Record<string, any>;
  getFinalReport: () => ExploreReport | null;
  getEvidence: () => ExploreEvidence[];
  getUsedCalls: () => number;
}

export function createChildTools(params: CreateChildToolsParams): ChildToolsRuntime {
  const { task, maxToolCalls, searchTool, readTool } = params;
  let nonReportCalls = 0;
  let successfulReadCount = 0;
  let forceReport = false;
  const evidence: ExploreEvidence[] = [];
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
    execute: async (toolInput: any) => {
      if (forceReport || nonReportCalls >= maxToolCalls) {
        forceReport = true;
        return '错误(TOOL_FORCE_REPORT): 已达到或接近预算上限，请立刻调用 report_findings。';
      }

      const beforeEvidenceCount = evidence.length;
      nonReportCalls += 1;
      if (nonReportCalls >= maxToolCalls) {
        forceReport = true;
      }
      const result = await searchTool.execute(toolInput);
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
    execute: async (toolInput: any) => {
      if (forceReport || nonReportCalls >= maxToolCalls) {
        forceReport = true;
        return '错误(TOOL_FORCE_REPORT): 已达到或接近预算上限，请立刻调用 report_findings。';
      }

      const beforeEvidenceCount = evidence.length;
      nonReportCalls += 1;
      if (nonReportCalls >= maxToolCalls) {
        forceReport = true;
      }
      const result = await readTool.execute(toolInput);
      if (!isErrorResult(result.result)) {
        successfulReadCount += 1;
        addEvidenceFromRead(result.result);
      }

      if (evidence.length === beforeEvidenceCount) {
        noNewEvidenceStreak += 1;
      } else {
        noNewEvidenceStreak = 0;
      }

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
    execute: async (toolInput: any) => {
      if (successfulReadCount < 1) {
        return '错误(TOOL_ORDER_VIOLATION): report_findings 前必须先成功调用 read_doc。请先使用 read_doc。';
      }

      const answer = String(toolInput.answer || '').trim();
      if (!answer) {
        return '错误(REPORT_MISSING_ANSWER): report_findings 必须提供 answer，并直接回答任务问题。';
      }

      const insights = Array.isArray(toolInput.insights)
        ? toolInput.insights.map((item: string) => String(item || '').trim()).filter(Boolean)
        : [];
      if (insights.length === 0) {
        return '错误(REPORT_MISSING_INSIGHTS): report_findings 必须提供 insights（2-5条见解）。';
      }

      const userReferences = Array.isArray(toolInput.references)
        ? toolInput.references
            .map((item: string) => normalizeReference(item))
            .filter((item: unknown): item is string => typeof item === 'string' && item.length > 0)
        : [];
      const autoReferences = referencesFromEvidence(evidence);
      const mergedReferences = uniqueStrings(userReferences.concat(autoReferences));
      if (mergedReferences.length === 0) {
        return '错误(REPORT_MISSING_LINE_REFERENCES): report_findings 必须提供精确行号引用，格式 path:line 或 path:start-end。';
      }

      const userEvidence = Array.isArray(toolInput.evidence)
        ? toolInput.evidence.map((item: string, index: number) => ({
            source: `llm_evidence_${index + 1}`,
            note: String(item),
          }))
        : [];
      const mergedEvidence = evidence.concat(userEvidence).slice(0, 8);
      const summary = String(toolInput.summary || '').trim() || `任务结论：${answer}`;
      const confidenceRaw = Number(toolInput.confidence ?? pickConfidence(mergedEvidence.length, false));
      const confidence = Number.isFinite(confidenceRaw)
        ? Math.max(0, Math.min(1, confidenceRaw))
        : 0.5;

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
