export type AgentEventSource = 'stream' | 'step-backfill';

export type AgentEvent =
  | {
      type: 'reasoning-delta';
      source: AgentEventSource;
      text: string;
    }
  | {
      type: 'text-delta';
      source: AgentEventSource;
      text: string;
    }
  | {
      type: 'tool-called';
      source: AgentEventSource;
      toolName: string;
      toolCallId?: string;
      toolInput: Record<string, unknown>;
    }
  | {
      type: 'tool-resulted';
      source: AgentEventSource;
      toolName?: string;
      toolCallId?: string;
      toolInput: Record<string, unknown>;
      output: unknown;
    }
  | {
      type: 'step-start';
      source: AgentEventSource;
      stepNumber?: number;
    }
  | {
      type: 'step-finish';
      source: AgentEventSource;
      finishReason?: string;
    }
  | {
      type: 'error';
      source: AgentEventSource;
      error: unknown;
    };
