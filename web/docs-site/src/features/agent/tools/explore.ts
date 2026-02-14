import type { Tool, ToolExecutionResult } from './tool';
import { useConfigStore } from '@/features/app/stores/config';
import { runChildSessionsInParallel } from '@/features/scout-agent';

interface ExploreParams {
  tasks?: string[];
  maxToolCalls?: number;
  timeoutMs?: number;
}

function isExplorationTask(task: string): boolean {
  const text = task.trim();
  if (!text) return false;
  const keywords = ['探索', '检索', '查找', '阅读', '核验', '调查', 'explore', 'search', 'investigate', 'read'];
  return keywords.some(k => text.toLowerCase().includes(k.toLowerCase()));
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

    const nonExploreTask = tasks.find(t => !isExplorationTask(t));
    if (nonExploreTask) {
      return {
        result: `错误(INVALID_EXPLORE_TASK): 仅允许探索类任务。非法任务: "${nonExploreTask}"。`,
      };
    }

    const maxToolCalls = Math.min(100, Math.max(1, Math.floor(params.maxToolCalls ?? 100)));
    const timeoutMs = Math.min(10 * 60 * 1000, Math.max(10_000, Math.floor(params.timeoutMs ?? 10 * 60 * 1000)));
    const configStore = useConfigStore();
    const activeConfig = configStore.activeConfig;
    if (!activeConfig) {
      return { result: '错误(NO_ACTIVE_CONFIG): 当前没有可用的 AI 配置，无法执行 explore。' };
    }

    const reports = await runChildSessionsInParallel(tasks, activeConfig, maxToolCalls, timeoutMs);
    const successCount = reports.filter(item => item.status === 'success' || item.status === 'partial').length;

    return {
      result: JSON.stringify({
        tool: 'explore',
        message: `已完成 ${reports.length} 个独立探索子会话（成功/部分成功 ${successCount} 个）。`,
        reports,
      }, null, 2),
    };
  },
};

export default exploreTool;
