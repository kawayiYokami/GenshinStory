export const SCOUT_ALLOWED_TOOLS = ['search_docs', 'read_doc', 'report_findings'] as const;
export type ScoutAllowedTool = typeof SCOUT_ALLOWED_TOOLS[number];

export const MAX_CONCURRENT_SCOUTS = 5;
export const DEFAULT_MAX_TOOL_CALLS = 3;

export interface ScoutTask {
  scoutId: string;
  task: string;
  status: 'running' | 'completed';
  createdAt: string;
  updatedAt: string;
  maxToolCalls: number;
  nonReportToolCalls: number;
  successfulReadCount: number;
  forceReportRequired: boolean;
}

export interface DispatchScoutTasksParams {
  tasks: string[];
  maxToolCalls?: number;
}

export interface DispatchScoutTasksResult {
  ok: boolean;
  code?: string;
  message: string;
  tasks?: Array<{ scoutId: string; task: string }>;
}

export interface ScoutGuardDecision {
  allow: boolean;
  code?: string;
  message?: string;
}
