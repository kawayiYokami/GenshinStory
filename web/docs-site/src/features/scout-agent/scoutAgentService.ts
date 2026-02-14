import { nanoid } from 'nanoid';
import type {
  DispatchScoutTasksParams,
  DispatchScoutTasksResult,
  ScoutAllowedTool,
  ScoutGuardDecision,
  ScoutTask,
} from './contracts';
import {
  DEFAULT_MAX_TOOL_CALLS,
  MAX_CONCURRENT_SCOUTS,
  SCOUT_ALLOWED_TOOLS,
} from './contracts';

function toRecoverableError(code: string, message: string): ScoutGuardDecision {
  return {
    allow: false,
    code,
    message: `错误(${code}): ${message}`,
  };
}

class ScoutAgentService {
  private tasks = new Map<string, ScoutTask>();

  dispatchTasks(params: DispatchScoutTasksParams): DispatchScoutTasksResult {
    const tasks = Array.isArray(params.tasks) ? params.tasks : [];
    const cleanedTasks = tasks.map(t => String(t || '').trim()).filter(Boolean);

    if (cleanedTasks.length === 0) {
      return {
        ok: false,
        code: 'INVALID_TASKS',
        message: '错误(INVALID_TASKS): tasks 不能为空。',
      };
    }

    if (cleanedTasks.length > MAX_CONCURRENT_SCOUTS) {
      return {
        ok: false,
        code: 'SCOUT_TASK_LIMIT_EXCEEDED',
        message: `错误(SCOUT_TASK_LIMIT_EXCEEDED): 单次最多下发 ${MAX_CONCURRENT_SCOUTS} 个子任务。`,
      };
    }

    const activeRunning = this.getRunningCount();
    if (activeRunning + cleanedTasks.length > MAX_CONCURRENT_SCOUTS) {
      return {
        ok: false,
        code: 'SCOUT_CONCURRENCY_LIMIT_REACHED',
        message: `错误(SCOUT_CONCURRENCY_LIMIT_REACHED): 当前运行中的子任务已接近上限(${MAX_CONCURRENT_SCOUTS})。`,
      };
    }

    const maxToolCalls = Math.max(1, Math.floor(params.maxToolCalls ?? DEFAULT_MAX_TOOL_CALLS));
    const createdAt = new Date().toISOString();

    const created = cleanedTasks.map(task => {
      const scoutId = `scout_${nanoid(10)}`;
      const record: ScoutTask = {
        scoutId,
        task,
        status: 'running',
        createdAt,
        updatedAt: createdAt,
        maxToolCalls,
        nonReportToolCalls: 0,
        successfulReadCount: 0,
        forceReportRequired: false,
      };
      this.tasks.set(scoutId, record);
      return { scoutId, task };
    });

    return {
      ok: true,
      message: `已创建 ${created.length} 个子任务。请对每个 scoutId 使用 search_docs/read_doc，完成后调用 report_findings。`,
      tasks: created,
    };
  }

  beforeToolCall(toolName: string, params: Record<string, unknown> | undefined): ScoutGuardDecision {
    const scoutId = String((params as any)?.scoutId || '').trim();

    if (toolName === 'explore') {
      return { allow: true };
    }

    if (toolName === 'report_findings' && !scoutId) {
      return toRecoverableError('MISSING_SCOUT_ID', "report_findings 必须提供 scoutId。");
    }

    if (!scoutId) {
      return { allow: true };
    }

    const task = this.tasks.get(scoutId);
    if (!task) {
      return toRecoverableError('SCOUT_NOT_FOUND', `未找到 scoutId=${scoutId} 的子任务。`);
    }

    if (task.status !== 'running') {
      return toRecoverableError('SCOUT_NOT_RUNNING', `scoutId=${scoutId} 已结束，不能继续调用工具。`);
    }

    if (!SCOUT_ALLOWED_TOOLS.includes(toolName as ScoutAllowedTool)) {
      return toRecoverableError('TOOL_NOT_ALLOWED', `子任务仅允许工具: ${SCOUT_ALLOWED_TOOLS.join(', ')}。`);
    }

    if (toolName === 'report_findings' && task.successfulReadCount < 1) {
      return toRecoverableError('TOOL_ORDER_VIOLATION', "请先成功调用 read_doc，再执行 report_findings。");
    }

    if (toolName !== 'report_findings' && task.forceReportRequired) {
      return toRecoverableError('TOOL_CALL_LIMIT_REACHED', "已达到最大工具调用次数，请立刻执行 report_findings。");
    }

    if (toolName !== 'report_findings' && task.nonReportToolCalls >= task.maxToolCalls) {
      task.forceReportRequired = true;
      task.updatedAt = new Date().toISOString();
      return toRecoverableError('TOOL_CALL_LIMIT_REACHED', "已达到最大工具调用次数，请立刻执行 report_findings。");
    }

    task.nonReportToolCalls += 1;
    if (task.nonReportToolCalls >= task.maxToolCalls) {
      task.forceReportRequired = true;
    }
    task.updatedAt = new Date().toISOString();
    return { allow: true };
  }

  markReadSuccess(scoutId: string): void {
    const task = this.tasks.get(scoutId);
    if (!task || task.status !== 'running') {
      return;
    }
    task.successfulReadCount += 1;
    task.updatedAt = new Date().toISOString();
  }

  completeWithReport(scoutId: string): ScoutTask | null {
    const task = this.tasks.get(scoutId);
    if (!task) {
      return null;
    }
    task.status = 'completed';
    task.updatedAt = new Date().toISOString();
    return task;
  }

  getTask(scoutId: string): ScoutTask | null {
    return this.tasks.get(scoutId) || null;
  }

  resetForTest(): void {
    this.tasks.clear();
  }

  private getRunningCount(): number {
    let count = 0;
    for (const task of this.tasks.values()) {
      if (task.status === 'running') {
        count += 1;
      }
    }
    return count;
  }
}

const scoutAgentService = new ScoutAgentService();
export default scoutAgentService;
