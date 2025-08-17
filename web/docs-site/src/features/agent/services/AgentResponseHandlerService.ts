import { ref, type Ref, type ComputedRef } from 'vue';
import toolParserService from '@/features/agent/services/toolParserService';
import logger from '@/features/app/services/loggerService';
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

  private removePartialXmlTags(content: string): string {
    const lastOpenBracketIndex = content.lastIndexOf('<');
    if (lastOpenBracketIndex > -1) {
      const possibleTag = content.substring(lastOpenBracketIndex);
      if (!possibleTag.includes('>') && /^<[a-zA-Z0-9_]*$/.test(possibleTag)) {
        return content.substring(0, lastOpenBracketIndex);
      }
    }
    return content;
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
    const finalContent = this.removePartialXmlTags(content);
    
    await this.messageManager.updateMessage({
      messageId: assistantMessage.id,
      updates: { content: finalContent, status: 'done' }
    });

    const parsedQuestion = toolParserService.parseAskCall(finalContent);
    if (parsedQuestion) {
      const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
      await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: { content: cleanContent, question: { text: parsedQuestion.question, suggestions: parsedQuestion.suggestions } }
      });
      return { type: 'ask_question' };
    }

    const parsedTool = toolParserService.parseXmlToolCall(finalContent);
    if (parsedTool) {
      const cleanContent = finalContent.replace(parsedTool.xml, '').trim();
      await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: { content: cleanContent, tool_calls: [parsedTool] }
      });
      return { type: 'tool_call', payload: parsedTool };
    }

    if (this.noToolCallRetries.value >= 2) {
      await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "抱歉，我似乎无法找到合适的指令来回应您的问题。" });
      return { type: 'no_op' };
    }

    this.noToolCallRetries.value++;
    const feedbackPrompt = await this.getToolFeedbackPrompt();
    await this.messageManager.addMessage({ role: 'user', content: feedbackPrompt, is_hidden: true });
    return { type: 'retry_no_tool_call' };
  }
}