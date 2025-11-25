import { ref, type Ref, type ComputedRef } from 'vue';
import toolParserService from '@/features/agent/services/toolParserService';
import logger from '@/features/app/services/loggerService';
import jsonParserService from '@/features/agent/services/JsonParserService';
import { ContentProcessor } from './ContentProcessor';
import type { Message, Session } from '../types';
import type { ParsedToolCall } from './toolParserService';
import type { MessageManager } from '../stores/messageManager';

export type HandleResponseResult =
  | { type: 'tool_call', payload: ParsedToolCall }
  | { type: 'ask_question' }
  | { type: 'no_op' }
  | { type: 'retry_no_tool_call' };

export class AgentResponseHandlerService {
  private messageManager: MessageManager;
  private currentSession: ComputedRef<Session | null>;
  private toolFeedbackPromptContent: string | null = null;
  public noToolCallRetries: Ref<number> = ref(0);

  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>
  ) {
    this.messageManager = messageManager;
    this.currentSession = currentSession;
  }


  private async getToolFeedbackPrompt(): Promise<string> {
    if (this.toolFeedbackPromptContent) return this.toolFeedbackPromptContent;
    try {
      const response = await fetch(`/prompts/tool_feedback_prompt.md?v=${Date.now()}`);
      if (!response.ok) throw new Error('Failed to load prompt');
      this.toolFeedbackPromptContent = await response.text();
      return this.toolFeedbackPromptContent;
    } catch (error) {
      logger.error("加载 tool_feedback_prompt.md 时出错:", error);
      return "你的回复中没有包含任何工具调用。";
    }
  }

  public async handleApiResponse(assistantMessage: Message): Promise<HandleResponseResult> {
    const updatedMessage = this.currentSession.value?.messagesById[assistantMessage.id];
    if (!updatedMessage) throw new Error("无法找到更新后的消息。");

    const content = typeof updatedMessage.content === 'string' ? updatedMessage.content : '';

    await this.messageManager.updateMessage({
      messageId: assistantMessage.id,
      updates: { content: content, status: 'done' }
    });

    // 直接使用 ContentProcessor 统一处理内容
    const processed = ContentProcessor.extract(content);

    // 特殊处理 ask 工具调用
    const askToolCall = processed.toolCalls.find(tool => tool.name === 'ask');
    if (askToolCall) {

      await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: {
          content: processed.cleanedContent,
          question: {
            text: askToolCall.params.question,
            suggestions: askToolCall.params.suggest || []
          }
        }
      });
      return { type: 'ask_question' };
    }

    // 处理其他工具调用
    if (processed.toolCalls.length > 0) {

      // 更新消息内容为清洗后的内容，并添加工具调用
      await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: { content: processed.cleanedContent, tool_calls: processed.toolCalls }
      });

      // 返回第一个工具调用（保持原有逻辑）
      return { type: 'tool_call', payload: processed.toolCalls[0] };
    }

    // 如果没有工具调用，直接返回no_op，不再重试以避免token浪费
    await this.messageManager.updateMessage({
      messageId: assistantMessage.id,
      updates: { content: processed.cleanedContent, status: 'done' }
    });

    return { type: 'no_op' };
  }
}