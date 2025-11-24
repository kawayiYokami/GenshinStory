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
    logger.log('[AgentResponseHandler] 开始处理API响应');
    const updatedMessage = this.currentSession.value?.messagesById[assistantMessage.id];
    if (!updatedMessage) throw new Error("无法找到更新后的消息。");

    const content = typeof updatedMessage.content === 'string' ? updatedMessage.content : '';
    logger.log('[AgentResponseHandler] 原始消息内容:', content);

    await this.messageManager.updateMessage({
      messageId: assistantMessage.id,
      updates: { content: content, status: 'done' }
    });

    // 直接使用 ContentProcessor 统一处理内容
    const processed = ContentProcessor.extract(content);
    logger.log('[AgentResponseHandler] ContentProcessor 处理结果:', {
      toolCallsCount: processed.toolCalls.length,
      cleanedContentLength: processed.cleanedContent.length
    });

    // 特殊处理 ask 工具调用
    const askToolCall = processed.toolCalls.find(tool => tool.name === 'ask');
    if (askToolCall) {
      logger.log('[AgentResponseHandler] 检测到 ask 工具调用，使用清洗后的内容');
      logger.log('[AgentResponseHandler] 清洗后的内容:', processed.cleanedContent);

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
      logger.log('[AgentResponseHandler] 已更新消息内容和问题');
      return { type: 'ask_question' };
    }

    // 处理其他工具调用
    if (processed.toolCalls.length > 0) {
      logger.log('[AgentResponseHandler] 检测到工具调用，使用清洗后的内容');
      logger.log('[AgentResponseHandler] 清洗后的内容:', processed.cleanedContent);
      logger.log('[AgentResponseHandler] 工具调用数量:', processed.toolCalls.length);

      // 更新消息内容为清洗后的内容，并添加工具调用
      await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: { content: processed.cleanedContent, tool_calls: processed.toolCalls }
      });
      logger.log('[AgentResponseHandler] 已更新消息内容和工具调用');

      // 返回第一个工具调用（保持原有逻辑）
      return { type: 'tool_call', payload: processed.toolCalls[0] };
    }

    if (this.noToolCallRetries.value >= 2) {
      logger.log('[AgentResponseHandler] 已达到最大重试次数，添加错误消息');
      await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "抱歉，我似乎无法找到合适的指令来回应您的问题。" });
      return { type: 'no_op' };
    }

    logger.log('[AgentResponseHandler] 未检测到工具调用，准备重试');
    this.noToolCallRetries.value++;
    const feedbackPrompt = await this.getToolFeedbackPrompt();
    await this.messageManager.addMessage({ role: 'user', content: feedbackPrompt, is_hidden: true });
    return { type: 'retry_no_tool_call' };
  }
}