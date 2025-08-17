import type { ComputedRef } from 'vue';
import openaiService from '../../../lib/openai/openaiService';
import logger from '../../app/services/loggerService';
import { createPacedStream } from '../../../lib/streaming/streamingService';
import type { Message } from '../types';
import type { MessageManager } from '../stores/messageManager';

export class AgentApiService {
  private activeConfig: ComputedRef<any>;
  private messageManager: MessageManager;

  constructor(
    messageManager: MessageManager,
    activeConfig: ComputedRef<any>
  ) {
    this.messageManager = messageManager;
    this.activeConfig = activeConfig;
  }

  private formatMessagesForApi(history: Message[]): any[] {
    const uiOnlyTypes = ['tool_status', 'tool_result', 'error'];
    return history
      .filter(m => m.type && !uiOnlyTypes.includes(m.type))
      .map(m => {
        const messageForApi: any = { role: m.role, content: m.content, name: m.name };
        if (m.role === 'user') {
          messageForApi.content = Array.isArray(m.content)
            ? m.content.map(part => (part.type === 'doc' ? { type: 'text', text: part.content } : part))
            : [{ type: 'text', text: m.content }];
        }
        if (m.role === 'tool') {
          messageForApi.tool_call_id = m.name;
          messageForApi.content = String(m.content);
          delete messageForApi.name;
        }
        if (m.role === 'assistant' && m.tool_calls) {
          messageForApi.tool_calls = m.tool_calls;
          const toolXmls = m.tool_calls.map(tc => tc.xml).join('');
          messageForApi.content = (m.content || '') + toolXmls;
        }
        if (m.role !== 'assistant' || !m.tool_calls) delete messageForApi.name;
        if (m.role !== 'tool') delete messageForApi.tool_call_id;
        return messageForApi;
      });
  }

  public async callApi(history: Message[], signal: AbortSignal): Promise<any> {
    if (!this.activeConfig.value?.apiUrl || !this.activeConfig.value?.apiKey) {
      const errorMsg = "没有激活的有效AI配置。请在设置中选择或创建一个配置。";
      logger.error(`[AgentApiService] ${errorMsg}`);
      throw new Error(errorMsg);
    }

    const apiMessages = this.formatMessagesForApi(history);
    const requestBody = {
      model: this.activeConfig.value.modelName,
      messages: apiMessages,
      temperature: this.activeConfig.value.temperature,
      stream: this.activeConfig.value.stream,
    };

    logger.log("[AgentApiService] 准备调用 API...", { messages: JSON.parse(JSON.stringify(apiMessages)) });
    logger.setLastRequest(requestBody);

    try {
      return await openaiService.createChatCompletion(requestBody, this.activeConfig.value, signal);
    } catch (error) {
      logger.error("[AgentApiService] 调用 API 失败:", error);
      throw error;
    }
  }

  public async handleStream(openaiStream: any, abortSignal: AbortSignal): Promise<Message | null> {
    let assistantMessage: Message | null = null;
    let messageId: string | null = null;
    const pacedStream = createPacedStream(openaiStream);

    logger.log('[AgentApiService] 开始消费 paced stream...');

    try {
      for await (const chunk of pacedStream) {
        if (abortSignal.aborted) {
          logger.warn('[AgentApiService] Stream 消费被中止。');
          break;
        }
        if (chunk.done) break;
        if (!assistantMessage && chunk.value) {
          const newMsg = await this.messageManager.addMessage({
            role: 'assistant', content: '', type: 'text', status: 'streaming',
          });
          if (newMsg) {
            assistantMessage = newMsg;
            messageId = newMsg.id;
          }
        }
        if (messageId && chunk.value) {
          await this.messageManager.appendMessageContent({ messageId, chunk: chunk.value });
        }
      }
    } catch (err: any) {
      logger.error('[AgentApiService] 消费 stream 时发生意外错误:', err);
      if (messageId) {
        await this.messageManager.updateMessage({ messageId, updates: { status: 'error' } });
      }
      throw new Error(`Stream 消费失败: ${err.message}`);
    }

    if (messageId) {
      await this.messageManager.updateMessage({ messageId, updates: { streamCompleted: true, status: 'done' } });
    }

    return assistantMessage;
  }
}