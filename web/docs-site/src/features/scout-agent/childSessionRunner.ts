import type { ModelMessage } from 'ai';
import type { Config } from '@/features/app/stores/config';
import logger from '@/features/app/services/loggerService';
import llmProviderService from '@/lib/llm/llmProviderService';
import { paramsToRequestBody } from '@/features/app/utils/paramUtils';
import { toolRegistryService } from '@/features/agent/tools/registry/toolRegistryService';
import {
  type ExploreReport,
  type RunChildSessionOptions,
  DEFAULT_CHILD_TIMEOUT_MS,
  MAX_CHILD_SESSION_CONCURRENCY,
} from './contracts';
import { buildChildSystemPrompt } from './prompt';
import {
  buildFallbackAnswer,
  buildFallbackSummary,
  createChildTools,
  pickConfidence,
  referencesFromEvidence,
} from './sessionTools';
import { markChildFinished, markChildRunning } from './exploreProgressStore';
import { registerChildSessionAbortController, unregisterChildSessionAbortController } from './childSessionAbortRegistry';

export type { ExploreReport } from './contracts';

export async function runChildSession(options: RunChildSessionOptions): Promise<ExploreReport> {
  const { config, task, maxToolCalls, progressSessionId } = options;
  const timeoutMs = options.timeoutMs ?? DEFAULT_CHILD_TIMEOUT_MS;
  markChildRunning(progressSessionId, task);

  await toolRegistryService.loadTools();
  const searchTool = toolRegistryService.getTool('search_docs');
  const readTool = toolRegistryService.getTool('read_doc');
  if (!searchTool || !readTool) {
    markChildFinished(progressSessionId, task, 'failed', 0);
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

  const child = createChildTools({
    task,
    maxToolCalls,
    searchTool,
    readTool,
    progressSessionId,
  });
  const controller = new AbortController();
  registerChildSessionAbortController(controller);
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const messages: ModelMessage[] = [
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
      markChildFinished(progressSessionId, task, finalReport.status, finalReport.usedCalls);
      return finalReport;
    }

    const fallbackEvidence = child.getEvidence();
    const fallbackStatus: ExploreReport['status'] = fallbackEvidence.length > 0 ? 'partial' : 'failed';
    const fallbackReport: ExploreReport = {
      task,
      status: fallbackStatus,
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
    markChildFinished(progressSessionId, task, fallbackReport.status, fallbackReport.usedCalls);
    return fallbackReport;
  } catch (error: any) {
    const isTimeout = error?.name === 'AbortError';
    const fallbackEvidence = child.getEvidence();
    const errMessage = isTimeout ? 'TIMEOUT' : (error?.message || String(error));
    logger.error('[ChildSessionRunner] 子会话执行失败', { task, error: errMessage });

    const failedStatus: ExploreReport['status'] = isTimeout ? 'timeout' : 'failed';
    const failedReport: ExploreReport = {
      task,
      status: failedStatus,
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
    markChildFinished(progressSessionId, task, failedReport.status, failedReport.usedCalls);
    return failedReport;
  } finally {
    clearTimeout(timeoutId);
    unregisterChildSessionAbortController(controller);
  }
}

export async function runChildSessionsInParallel(
  tasks: string[],
  config: Config,
  maxToolCalls: number,
  timeoutMs: number = DEFAULT_CHILD_TIMEOUT_MS,
  progressSessionId?: string,
): Promise<ExploreReport[]> {
  const concurrency = Math.min(MAX_CHILD_SESSION_CONCURRENCY, Math.max(1, tasks.length));
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
        progressSessionId,
      });
    }
  };

  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return results;
}
