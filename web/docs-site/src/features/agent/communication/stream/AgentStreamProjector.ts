import logger from '@/features/app/services/loggerService';
import type { Message } from '@/features/agent/types';
import type { MessageManager } from '@/features/agent/stores/messageManager';
import type { AgentEvent } from '../events/AgentEvent';
import { toPlainResultContent } from './toolEventNormalizer';

interface CurrentToolCall {
  toolCallId?: string;
  toolName?: string;
  toolInput: Record<string, unknown>;
}

export class AgentStreamProjector {
  private assistantMessage: Message | null = null;
  private messageId: string | null = null;
  private collectedReasoning = '';
  private currentToolStatusId: string | null = null;
  private reasoningStartTime: number | null = null;
  private reasoningDuration: number | null = null;

  private currentToolCall: CurrentToolCall | null = null;
  private projectedToolCallIds = new Set<string>();
  private projectedToolResultIds = new Set<string>();

  constructor(private messageManager: MessageManager) {}

  getAssistantMessage(): Message | null {
    return this.assistantMessage;
  }

  async consumeEvent(event: AgentEvent): Promise<void> {
    switch (event.type) {
      case 'reasoning-delta':
        this.onReasoningDelta(event.text);
        break;
      case 'text-delta':
        await this.onTextDelta(event.text);
        break;
      case 'tool-called':
        await this.onToolCalled(event);
        break;
      case 'tool-resulted':
        await this.onToolResulted(event);
        break;
      case 'step-start':
        logger.log(`[AgentApiService] step-start 事件: step ${event.stepNumber}`);
        break;
      case 'step-finish':
        logger.log(`[AgentApiService] step-finish 事件: finishReason=${event.finishReason}`);
        break;
      case 'error':
        logger.error('[AgentApiService] 流中收到错误事件:', event.error);
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

  private onReasoningDelta(text: string): void {
    if (!this.reasoningStartTime) {
      this.reasoningStartTime = Date.now();
    }
    this.collectedReasoning += text;
  }

  private async onTextDelta(text: string): Promise<void> {
    if (this.reasoningStartTime && this.reasoningDuration === null) {
      this.reasoningDuration = Math.round((Date.now() - this.reasoningStartTime) / 1000);
      logger.log(`[AgentApiService] 思维链完成，耗时: ${this.reasoningDuration}s`);
    }

    if (!text) return;
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
      await this.messageManager.appendMessageContent({ messageId: this.messageId, chunk: text });
    }
  }

  private async onToolCalled(event: Extract<AgentEvent, { type: 'tool-called' }>): Promise<void> {
    const toolCallId = event.toolCallId ? String(event.toolCallId) : undefined;
    if (toolCallId && this.projectedToolCallIds.has(toolCallId)) {
      return;
    }

    if (event.source === 'stream') {
      logger.log(`[AgentApiService] tool-call 事件: ${event.toolName}`, {
        toolCallId,
        args: event.toolInput,
      });
      this.currentToolCall = {
        toolCallId,
        toolName: event.toolName,
        toolInput: event.toolInput,
      };
      if (this.messageId) {
        await this.messageManager.updateMessage({
          messageId: this.messageId,
          updates: { status: 'done', streamCompleted: true },
        });
        this.messageId = null;
      }
    }

    if (toolCallId) {
      this.projectedToolCallIds.add(toolCallId);
    }

    if (event.toolName && event.toolName !== 'ask_choice') {
      const toolCallMessage = await this.messageManager.addMessage({
        role: 'assistant',
        type: 'text',
        content: '',
        status: 'done',
        streamCompleted: true,
        tool_calls: [{
          tool: event.toolName,
          action_id: toolCallId,
          ...event.toolInput,
        }] as any,
      });

      if (toolCallMessage) {
        this.assistantMessage = toolCallMessage;
      }
    }

    if (event.source !== 'stream') {
      return;
    }

    let statusContent = `正在执行工具: ${event.toolName}...`;
    if (event.toolName === 'explore') {
      const tasks = Array.isArray(event.toolInput.tasks)
        ? event.toolInput.tasks.map(task => String(task || '').trim()).filter(Boolean)
        : [];
      if (tasks.length > 0) {
        statusContent = `正在执行工具: ${event.toolName}（${tasks.length} 个任务）...`;
      }
    }

    const statusMsg = await this.messageManager.addMessage({
      role: 'assistant',
      type: 'tool_status',
      content: statusContent,
      status: 'rendering',
      toolCallId,
      toolName: event.toolName,
      toolInput: event.toolInput,
    });
    if (statusMsg) {
      this.currentToolStatusId = statusMsg.id;
    }
  }

  private async onToolResulted(event: Extract<AgentEvent, { type: 'tool-resulted' }>): Promise<void> {
    const toolCallId = event.toolCallId || this.currentToolCall?.toolCallId;
    const toolName = event.toolName || this.currentToolCall?.toolName;
    const toolInput =
      Object.keys(event.toolInput || {}).length > 0
        ? event.toolInput
        : (this.currentToolCall?.toolInput || {});

    if (event.source === 'stream') {
      logger.log(`[AgentApiService] tool-result 事件: ${toolName}`, { toolCallId });
    }

    if (toolCallId && this.projectedToolResultIds.has(toolCallId)) {
      return;
    }

    const resultContent = toPlainResultContent(event.output);
    if (toolCallId) {
      this.projectedToolResultIds.add(toolCallId);
    }

    if (event.source === 'stream' && this.currentToolStatusId) {
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

    if (event.source === 'stream') {
      this.currentToolCall = null;
    }
  }
}
