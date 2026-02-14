import type { AgentEvent } from './AgentEvent';
import {
  normalizeToolCall,
  normalizeToolResult,
  toToolInput,
} from '../stream/toolEventNormalizer';

export function toAgentEventFromStreamPart(part: any): AgentEvent | null {
  switch (part?.type) {
    case 'reasoning-delta':
      if (typeof part.text !== 'string') return null;
      return { type: 'reasoning-delta', source: 'stream', text: part.text };

    case 'text-delta':
      if (typeof part.text !== 'string') return null;
      return { type: 'text-delta', source: 'stream', text: part.text };

    case 'tool-call': {
      const toolInput = toToolInput(part.args ?? part.input ?? {});
      return {
        type: 'tool-called',
        source: 'stream',
        toolName: String(part.toolName || ''),
        toolCallId: typeof part.toolCallId === 'string' ? part.toolCallId : undefined,
        toolInput,
      };
    }

    case 'tool-result':
      return {
        type: 'tool-resulted',
        source: 'stream',
        toolName: typeof part.toolName === 'string' ? part.toolName : undefined,
        toolCallId: typeof part.toolCallId === 'string' ? part.toolCallId : undefined,
        toolInput: toToolInput(part.input ?? part.args ?? {}),
        output: part.result ?? part.output ?? part.content ?? '',
      };

    case 'step-start':
      return {
        type: 'step-start',
        source: 'stream',
        stepNumber: typeof part.stepNumber === 'number' ? part.stepNumber : undefined,
      };

    case 'step-finish':
      return {
        type: 'step-finish',
        source: 'stream',
        finishReason: typeof part.finishReason === 'string' ? part.finishReason : undefined,
      };

    case 'error':
      return { type: 'error', source: 'stream', error: part.error };

    default:
      return null;
  }
}

export function buildBackfillEvents(result: any, steps: any[]): AgentEvent[] {
  const events: AgentEvent[] = [];
  const candidateSteps: any[] = Array.isArray(steps) ? [...steps] : [];
  const topToolCalls = Array.isArray(result?.toolCalls) ? result.toolCalls : [];
  const topToolResults = Array.isArray(result?.toolResults) ? result.toolResults : [];
  if (candidateSteps.length === 0 && (topToolCalls.length > 0 || topToolResults.length > 0)) {
    candidateSteps.push({ toolCalls: topToolCalls, toolResults: topToolResults });
  }

  for (let stepIndex = 0; stepIndex < candidateSteps.length; stepIndex += 1) {
    const step = candidateSteps[stepIndex];
    const stepToolCalls = Array.isArray(step?.toolCalls) ? step.toolCalls : [];
    const stepToolResults = Array.isArray(step?.toolResults) ? step.toolResults : [];

    const resultsById = new Map<string, any>();
    for (let resultIndex = 0; resultIndex < stepToolResults.length; resultIndex += 1) {
      const normalized = normalizeToolResult(stepToolResults[resultIndex], `step_${stepIndex}_result_${resultIndex}`);
      if (normalized.toolCallId) {
        resultsById.set(normalized.toolCallId, normalized);
      }
    }

    for (let callIndex = 0; callIndex < stepToolCalls.length; callIndex += 1) {
      const call = normalizeToolCall(stepToolCalls[callIndex], `step_${stepIndex}_call_${callIndex}`);
      if (!call.toolName || call.toolName === 'ask_choice') {
        continue;
      }

      events.push({
        type: 'tool-called',
        source: 'step-backfill',
        toolName: call.toolName,
        toolCallId: call.toolCallId,
        toolInput: call.toolInput || {},
      });

      const matched = resultsById.get(call.toolCallId);
      events.push({
        type: 'tool-resulted',
        source: 'step-backfill',
        toolName: call.toolName,
        toolCallId: call.toolCallId,
        toolInput: call.toolInput || {},
        output: matched?.output ?? '',
      });
    }
  }

  return events;
}
