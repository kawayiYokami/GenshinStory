import logger from '@/features/app/services/loggerService';
import type { Message } from '@/features/agent/types';
import type { MessageManager } from '@/features/agent/stores/messageManager';
import {
  normalizeToolCall,
  normalizeToolResult,
  toPlainResultContent,
  toToolInput,
  type NormalizedToolCall,
} from './toolEventNormalizer';

export class AgentStreamProjector {
  private assistantMessage: Message | null = null;
  private messageId: string | null = null;
  private collectedReasoning = '';
  private currentToolStatusId: string | null = null;
  private reasoningStartTime: number | null = null;
  private reasoningDuration: number | null = null;

  private currentToolCall: NormalizedToolCall | null = null;
  private streamedToolCallIds = new Set<string>();
  private streamedToolResultIds = new Set<string>();

  constructor(private messageManager: MessageManager) {}

  getAssistantMessage(): Message | null {
    return this.assistantMessage;
  }

  async consumePart(part: any): Promise<void> {
    switch (part?.type) {
      case 'reasoning-delta':
        this.onReasoningDelta(part);
        break;
      case 'text-delta':
        await this.onTextDelta(part);
        break;
      case 'tool-call':
        await this.onToolCall(part);
        break;
      case 'tool-result':
        await this.onToolResult(part);
        break;
      case 'step-start':
        logger.log(`[AgentApiService] step-start 事件: step ${part.stepNumber}`);
        break;
      case 'step-finish':
        logger.log(`[AgentApiService] step-finish 事件: finishReason=${part.finishReason}`);
        break;
      case 'error':
        logger.error('[AgentApiService] 流中收到错误事件:', part.error);
        break;
      default:
        break;
    }
  }

  async markCurrentMessageAsError(): Promise<void> {
    if (!this.messageId) return;
    await this.messageManager.updateMessage({
      messageId: this.messageId,
      updates: { status: 'error' },
    });
  }

  async backfillToolMessagesFromSteps(result: any, steps: any[]): Promise<void> {
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

        if (!this.streamedToolCallIds.has(call.toolCallId)) {
          await this.messageManager.addMessage({
            role: 'assistant',
            type: 'text',
            content: '',
            status: 'done',
            streamCompleted: true,
            tool_calls: [{
              tool: call.toolName,
              action_id: call.toolCallId,
              ...(call.toolInput || {}),
            }] as any,
          });
          this.streamedToolCallIds.add(call.toolCallId);
        }

        if (!this.streamedToolResultIds.has(call.toolCallId)) {
          const matched = resultsById.get(call.toolCallId);
          const rawOutput = matched?.output ?? '';
          const resultContent = toPlainResultContent(rawOutput);

          await this.messageManager.addMessage({
            role: 'tool',
            type: 'tool_result',
            content: resultContent,
            status: 'done',
            toolCallId: call.toolCallId,
            toolName: call.toolName,
            toolInput: call.toolInput || {},
          });
          this.streamedToolResultIds.add(call.toolCallId);
        }
      }
    }
  }

  async finalize(result: any): Promise<void> {
    if (this.reasoningStartTime && this.reasoningDuration === null) {
      this.reasoningDuration = Math.round((Date.now() - this.reasoningStartTime) / 1000);
      logger.log(`[AgentApiService] 思维链完成（流结束），耗时: ${this.reasoningDuration}s`);
    }

    if (!this.assistantMessage && !this.messageId) {
      const finalText = typeof result?.text === 'string'
        ? result.text
        : (typeof result?.outputText === 'string' ? result.outputText : '');
      if (finalText && finalText.trim()) {
        const finalMsg = await this.messageManager.addMessage({
          role: 'assistant',
          content: finalText,
          type: 'text',
          status: 'done',
          streamCompleted: true,
        });
        if (finalMsg) {
          this.assistantMessage = finalMsg;
          this.messageId = finalMsg.id;
        }
      }
    }

    if (!this.messageId && this.collectedReasoning) {
      const newMsg = await this.messageManager.addMessage({
        role: 'assistant',
        content: '',
        type: 'text',
        status: 'done',
        reasoning: this.collectedReasoning,
        reasoningDuration: this.reasoningDuration ?? undefined,
      });
      if (newMsg) {
        this.assistantMessage = newMsg;
        this.messageId = newMsg.id;
      }
    }

    if (this.messageId) {
      await this.messageManager.updateMessage({
        messageId: this.messageId,
        updates: {
          streamCompleted: true,
          status: 'done',
          reasoning: this.collectedReasoning || undefined,
          reasoningDuration: this.reasoningDuration ?? undefined,
        },
      });
    }
  }

  private onReasoningDelta(part: any): void {
    if (typeof part?.text !== 'string') return;
    if (!this.reasoningStartTime) {
      this.reasoningStartTime = Date.now();
    }
    this.collectedReasoning += part.text;
  }

  private async onTextDelta(part: any): Promise<void> {
    if (this.reasoningStartTime && this.reasoningDuration === null) {
      this.reasoningDuration = Math.round((Date.now() - this.reasoningStartTime) / 1000);
      logger.log(`[AgentApiService] 思维链完成，耗时: ${this.reasoningDuration}s`);
    }

    if (typeof part?.text !== 'string' || !part.text) return;
    if (!this.messageId) {
      const newMsg = await this.messageManager.addMessage({
        role: 'assistant',
        content: '',
        type: 'text',
        status: 'streaming',
      });
      if (newMsg) {
        this.assistantMessage = newMsg;
        this.messageId = newMsg.id;
      }
    }
    if (this.messageId) {
      await this.messageManager.appendMessageContent({ messageId: this.messageId, chunk: part.text });
    }
  }

  private async onToolCall(part: any): Promise<void> {
    logger.log(`[AgentApiService] tool-call 事件: ${part.toolName}`, { toolCallId: part.toolCallId, args: part.args });
    const normalizedToolInput = toToolInput(part.args ?? part.input ?? {});

    this.currentToolCall = {
      toolCallId: part.toolCallId,
      toolName: part.toolName,
      toolInput: normalizedToolInput,
    };
    if (part.toolCallId) {
      this.streamedToolCallIds.add(String(part.toolCallId));
    }

    if (this.messageId) {
      await this.messageManager.updateMessage({
        messageId: this.messageId,
        updates: { status: 'done', streamCompleted: true },
      });
      this.messageId = null;
    }

    if (part.toolName && part.toolName !== 'ask_choice') {
      const toolCallMessage = await this.messageManager.addMessage({
        role: 'assistant',
        type: 'text',
        content: '',
        status: 'done',
        streamCompleted: true,
        tool_calls: [{
          tool: part.toolName,
          action_id: part.toolCallId,
          ...normalizedToolInput,
        }] as any,
      });

      if (toolCallMessage) {
        this.assistantMessage = toolCallMessage;
      }
    }

    let statusContent = `正在执行工具: ${part.toolName}...`;
    if (part.toolName === 'explore') {
      const tasks = Array.isArray(normalizedToolInput.tasks)
        ? normalizedToolInput.tasks.map(task => String(task || '').trim()).filter(Boolean)
        : [];
      if (tasks.length > 0) {
        statusContent = `正在执行工具: ${part.toolName}（${tasks.length} 个任务）...`;
      }
    }

    const statusMsg = await this.messageManager.addMessage({
      role: 'assistant',
      type: 'tool_status',
      content: statusContent,
      status: 'rendering',
      toolCallId: part.toolCallId,
      toolName: part.toolName,
      toolInput: normalizedToolInput,
    });
    if (statusMsg) {
      this.currentToolStatusId = statusMsg.id;
    }
  }

  private async onToolResult(part: any): Promise<void> {
    logger.log(`[AgentApiService] tool-result 事件: ${part.toolName}`, { toolCallId: part.toolCallId });

    const toolResult = part.result ?? part.output ?? part.content ?? '';
    const resultContent = typeof toolResult === 'string' ? toolResult : JSON.stringify(toolResult);

    const toolCallId = part.toolCallId || this.currentToolCall?.toolCallId;
    const toolName = part.toolName || this.currentToolCall?.toolName;
    const toolInput = toToolInput(part.input ?? part.args ?? this.currentToolCall?.toolInput ?? {});
    if (toolCallId) {
      this.streamedToolResultIds.add(String(toolCallId));
    }

    if (this.currentToolStatusId) {
      await this.messageManager.replaceMessage(this.currentToolStatusId, {
        role: 'tool',
        type: 'tool_result',
        content: resultContent,
        status: 'done',
        toolCallId,
        toolName,
        toolInput,
      });
      this.currentToolStatusId = null;
    } else {
      await this.messageManager.addMessage({
        role: 'tool',
        type: 'tool_result',
        content: resultContent,
        status: 'done',
        toolCallId,
        toolName,
        toolInput,
      });
    }

    this.currentToolCall = null;
  }
}
