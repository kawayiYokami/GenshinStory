import type { Tool, ToolExecutionResult } from './tool';
import { useConfigStore } from '@/features/app/stores/config';
import { runChildSessionsInParallel } from '@/features/scout-agent';
import { DEFAULT_CHILD_TIMEOUT_MS } from '@/features/scout-agent/contracts';
import { finishExploreProgress, startExploreProgress } from '@/features/scout-agent/exploreProgressStore';

interface ExploreParams {
  tasks?: string[];
  maxToolCalls?: number;
  timeoutMs?: number;
}

const exploreTool: Tool<ExploreParams> = {
  name: 'explore',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: ExploreParams): Promise<ToolExecutionResult> {
    const tasks = (params.tasks || []).map(t => String(t || '').trim()).filter(Boolean);
    if (tasks.length === 0) {
      return { result: '错误(INVALID_TASKS): tasks 不能为空。' };
    }
    if (tasks.length > 5) {
      return { result: '错误(EXPLORE_TASK_LIMIT_EXCEEDED): explore 一次最多 5 个探索任务。' };
    }

    const maxToolCalls = Math.min(100, Math.max(1, Math.floor(params.maxToolCalls ?? 100)));
    // 子代理整场会话默认 30 分钟，可按需调整（最小 10 秒）
    const timeoutMs = Math.max(10_000, Math.floor(params.timeoutMs ?? DEFAULT_CHILD_TIMEOUT_MS));
    const configStore = useConfigStore();
    const activeConfig = configStore.activeConfig;
    if (!activeConfig) {
      return { result: '错误(NO_ACTIVE_CONFIG): 当前没有可用的 AI 配置，无法执行 explore。' };
    }

    const progressSessionId = startExploreProgress(tasks);
    try {
      const reports = await runChildSessionsInParallel(tasks, activeConfig, maxToolCalls, timeoutMs, progressSessionId);
      const successCount = reports.filter(item => item.status === 'success' || item.status === 'partial').length;

      return {
        result: JSON.stringify({
          tool: 'explore',
          message: `已完成 ${reports.length} 个独立探索子会话（成功/部分成功 ${successCount} 个）。`,
          reports,
        }, null, 2),
      };
    } finally {
      finishExploreProgress(progressSessionId);
    }
  },
};

export default exploreTool;
