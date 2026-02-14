import type { Tool, ToolExecutionResult } from './tool';
import scoutAgentService from '@/features/scout-agent/scoutAgentService';

interface ReportFindingsParams {
  scoutId?: string;
  summary?: string;
  evidence?: string[];
  confidence?: number;
}

const reportFindingsTool: Tool<ReportFindingsParams> = {
  name: 'report_findings',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: ReportFindingsParams): Promise<ToolExecutionResult> {
    const scoutId = String(params.scoutId || '').trim();
    if (!scoutId) {
      return { result: '错误(MISSING_SCOUT_ID): report_findings 必须提供 scoutId。' };
    }

    const task = scoutAgentService.completeWithReport(scoutId);
    if (!task) {
      return { result: `错误(SCOUT_NOT_FOUND): 未找到 scoutId=${scoutId} 的子任务。` };
    }

    const summary = String(params.summary || '').trim() || '未提供总结';
    const evidence = Array.isArray(params.evidence) ? params.evidence : [];
    const confidenceRaw = Number(params.confidence ?? 0.5);
    const confidence = Number.isFinite(confidenceRaw)
      ? Math.max(0, Math.min(1, confidenceRaw))
      : 0.5;

    return {
      result: JSON.stringify({
        scoutId,
        status: 'completed',
        task: task.task,
        summary,
        evidence,
        confidence,
      }, null, 2),
    };
  },
};

export default reportFindingsTool;
