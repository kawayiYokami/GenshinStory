import type { Config } from '@/features/app/stores/config';

export interface ExploreEvidence {
  source: string;
  note: string;
}

export interface ExploreReport {
  task: string;
  status: 'success' | 'partial' | 'failed' | 'timeout';
  answer: string;
  insights: string[];
  references: string[];
  summary: string;
  evidence: ExploreEvidence[];
  confidence: number;
  usedCalls: number;
  maxToolCalls: number;
  error?: string;
}

export interface RunChildSessionOptions {
  config: Config;
  task: string;
  maxToolCalls: number;
  timeoutMs?: number;
  progressSessionId?: string;
}

export const MAX_CHILD_SESSION_CONCURRENCY = 5;
export const DEFAULT_CHILD_TIMEOUT_MS = 30 * 60 * 1000;
export const SINGLE_TOOL_TIMEOUT_MS = 5 * 60 * 1000;
