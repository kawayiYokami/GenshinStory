export interface NormalizedToolCall {
  toolName: string;
  toolCallId: string;
  toolInput: Record<string, unknown>;
}

export interface NormalizedToolResult {
  toolName: string;
  toolCallId: string;
  output: unknown;
}

function parseJsonObject(text: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // ignore
  }
  return {};
}

export function toPlainResultContent(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value === undefined || value === null) return '';
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function toToolInput(raw: unknown): Record<string, unknown> {
  if (raw === null || raw === undefined) return {};
  if (typeof raw === 'string') {
    return parseJsonObject(raw);
  }
  if (typeof raw !== 'object' || Array.isArray(raw)) return {};

  const obj = raw as Record<string, unknown>;
  const nestedInput = obj.input;
  const nestedArgs = obj.args;

  if (nestedInput && typeof nestedInput === 'object' && !Array.isArray(nestedInput)) {
    return nestedInput as Record<string, unknown>;
  }
  if (typeof nestedInput === 'string') {
    const parsed = parseJsonObject(nestedInput);
    if (Object.keys(parsed).length > 0) return parsed;
  }
  if (nestedArgs && typeof nestedArgs === 'object' && !Array.isArray(nestedArgs)) {
    return nestedArgs as Record<string, unknown>;
  }
  if (typeof nestedArgs === 'string') {
    const parsed = parseJsonObject(nestedArgs);
    if (Object.keys(parsed).length > 0) return parsed;
  }

  return obj;
}

export function normalizeToolCall(toolCall: any, fallbackId: string): NormalizedToolCall {
  const toolName = String(toolCall?.toolName || toolCall?.name || '');
  const toolCallId = String(toolCall?.toolCallId || toolCall?.id || toolCall?.callId || fallbackId);
  const toolInput = toToolInput(toolCall?.input ?? toolCall?.args ?? {});
  return { toolName, toolCallId, toolInput };
}

export function normalizeToolResult(toolResult: any, fallbackId: string): NormalizedToolResult {
  const toolName = String(toolResult?.toolName || toolResult?.name || '');
  const toolCallId = String(toolResult?.toolCallId || toolResult?.id || toolResult?.callId || fallbackId);
  let output = toolResult?.result ?? toolResult?.output ?? toolResult?.content ?? toolResult?.value ?? '';
  if (output && typeof output === 'object' && 'value' in output) {
    output = (output as { value: unknown }).value;
  }
  return { toolName, toolCallId, output };
}
