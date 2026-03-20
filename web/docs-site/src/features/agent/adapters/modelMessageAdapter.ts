import type { ModelMessage, ToolModelMessage } from 'ai';
import type { Message, ToolCall } from '../types';

function toTextContent(content: Message['content']): string {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';

  return content
    .map(part => {
      if (part.type === 'text') return part.text || '';
      if (part.type === 'doc') return part.content || '';
      return '';
    })
    .join('\n');
}

function toUserTextContent(content: Message['content']): string {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';

  const textParts = content
    .filter(part => part.type === 'text')
    .map(part => part.text || '')
    .filter(Boolean);
  const firstText = textParts[0] || '';
  const memoryTextBlocks = textParts
    .slice(1)
    .filter(text => /<记忆>|<\/记忆>|<系统提醒>|<用户指示记忆>|<\/用户指示记忆>|<世界树记忆>|<\/世界树记忆>|\[记忆文本块\]/.test(text));
  const docParts = content
    .filter(part => part.type === 'doc')
    .map(part => part.content || '')
    .filter(Boolean);

  return [firstText, ...memoryTextBlocks, ...docParts].filter(Boolean).join('\n');
}

function toUserModelContent(content: Message['content']): string | Array<{ type: 'text'; text: string }> {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';

  const textParts = content
    .filter(part => part.type === 'text')
    .map(part => String(part.text || '').trim())
    .filter(Boolean)
    .map(text => ({ type: 'text' as const, text }));

  const docAsTextParts = content
    .filter(part => part.type === 'doc')
    .map(part => String(part.content || '').trim())
    .filter(Boolean)
    .map(text => ({ type: 'text' as const, text }));

  const mergedParts = [...textParts, ...docAsTextParts];
  if (mergedParts.length > 0) return mergedParts;

  return toUserTextContent(content);
}

function toolCallIdFrom(toolCall: ToolCall, messageId: string, index: number): string {
  return toolCall.action_id || `tc_${messageId}_${index}`;
}

function fallbackMessageId(message: Message, index: number): string {
  if (typeof message.id === 'string' && message.id.trim() !== '') {
    return message.id;
  }

  const random = Math.random().toString(36).slice(2, 8);
  return `legacy_msg_${index}_${random}`;
}

function toolInputFrom(toolCall: ToolCall): Record<string, unknown> {
  const {
    tool,
    action_id,
    timestamp,
    result,
    status,
    ...rest
  } = toolCall;

  return rest as Record<string, unknown>;
}

export function toModelMessages(storeMessages: Message[]): ModelMessage[] {
  const result: ModelMessage[] = [];
  const pendingToolPairs: Array<{ toolCallId: string; toolName: string }> = [];

  for (let index = 0; index < storeMessages.length; index += 1) {
    const message = storeMessages[index];

    // 跳过 tool_status 和 error 类型
    if (message.type === 'tool_status' || message.type === 'error') {
      continue;
    }

    if (message.role === 'system') {
      result.push({ role: 'system', content: toTextContent(message.content) });
      continue;
    }

    if (message.role === 'user') {
      // 用户消息保持为分段文本块，确保记忆块以独立 content part 传给模型。
      const userContent = toUserModelContent(message.content);
      result.push({ role: 'user', content: userContent });
      continue;
    }

    if (message.role === 'assistant') {
      const parts: Array<any> = [];
      const messageId = fallbackMessageId(message, index);
      const text = toTextContent(message.content);
      if (text) parts.push({ type: 'text', text });

      if (typeof message.reasoning === 'string' && message.reasoning.trim() !== '') {
        parts.push({ type: 'reasoning', text: message.reasoning });
      }

      if (Array.isArray(message.tool_calls)) {
        for (let toolIndex = 0; toolIndex < message.tool_calls.length; toolIndex += 1) {
          const toolCall = message.tool_calls[toolIndex];
          const toolCallId = toolCallIdFrom(toolCall, messageId, toolIndex);
          pendingToolPairs.push({
            toolCallId,
            toolName: toolCall.tool,
          });

          parts.push({
            type: 'tool-call',
            toolCallId,
            toolName: toolCall.tool,
            input: toolInputFrom(toolCall),
          });
        }
      }

      result.push({ role: 'assistant', content: parts.length > 0 ? parts : '' });
      continue;
    }

    // 处理 tool_result 消息
    if (message.role === 'tool' || message.type === 'tool_result') {
      // 关键约束：tool 消息必须响应前置 assistant.tool_calls。
      // 当前会话存储里通常只有 tool_result，没有结构化的 assistant tool_calls，
      // 因此这里必须在存在 pendingToolPairs 时才允许序列化为 role=tool。
      if (pendingToolPairs.length === 0) {
        continue;
      }

      const fallbackPair = pendingToolPairs[0];
      const toolCallId = message.toolCallId || fallbackPair?.toolCallId;
      const toolName = message.toolName || fallbackPair?.toolName;

      // 优先使用消息中保存的 toolCallId 和 toolName
      if (toolCallId && toolName) {
        const toolMessage: ToolModelMessage = {
          role: 'tool',
          content: [{
            type: 'tool-result',
            toolCallId,
            toolName,
            output: {
              type: 'text',
              value: toTextContent(message.content),
            },
          }],
        };
        result.push(toolMessage);

        if (fallbackPair && fallbackPair.toolCallId === toolCallId) {
          pendingToolPairs.shift();
        }
      }
      // 注意：如果没有 toolCallId，跳过该消息（无法正确关联）
    }
  }

  return result;
}
