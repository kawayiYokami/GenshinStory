import { beforeEach, describe, expect, it } from 'vitest';
import scoutAgentService from './scoutAgentService';

describe('scoutAgentService', () => {
  beforeEach(() => {
    scoutAgentService.resetForTest();
  });

  it('enforces max 5 tasks per dispatch', () => {
    const result = scoutAgentService.dispatchTasks({
      tasks: ['1', '2', '3', '4', '5', '6'],
    });

    expect(result.ok).toBe(false);
    expect(result.code).toBe('SCOUT_TASK_LIMIT_EXCEEDED');
  });

  it('requires read_doc before report_findings', () => {
    const created = scoutAgentService.dispatchTasks({ tasks: ['collect facts'] });
    expect(created.ok).toBe(true);
    const scoutId = created.tasks![0].scoutId;

    const guard = scoutAgentService.beforeToolCall('report_findings', { scoutId });
    expect(guard.allow).toBe(false);
    expect(guard.code).toBe('TOOL_ORDER_VIOLATION');
  });

  it('returns recoverable limit error and forces report after maxToolCalls', () => {
    const created = scoutAgentService.dispatchTasks({
      tasks: ['collect facts'],
      maxToolCalls: 1,
    });
    expect(created.ok).toBe(true);
    const scoutId = created.tasks![0].scoutId;

    const first = scoutAgentService.beforeToolCall('search_docs', { scoutId });
    expect(first.allow).toBe(true);

    const second = scoutAgentService.beforeToolCall('read_doc', { scoutId });
    expect(second.allow).toBe(false);
    expect(second.code).toBe('TOOL_CALL_LIMIT_REACHED');
  });

  it('allows report after at least one successful read', () => {
    const created = scoutAgentService.dispatchTasks({ tasks: ['collect facts'] });
    expect(created.ok).toBe(true);
    const scoutId = created.tasks![0].scoutId;

    const readCall = scoutAgentService.beforeToolCall('read_doc', { scoutId });
    expect(readCall.allow).toBe(true);
    scoutAgentService.markReadSuccess(scoutId);

    const reportCall = scoutAgentService.beforeToolCall('report_findings', { scoutId });
    expect(reportCall.allow).toBe(true);
  });
});
