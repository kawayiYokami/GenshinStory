/**
 * @fileoverview 代理API服务类
 * @description 负责与AI API进行通信，处理API调用和流式响应
 * @author yokami
 */
import type { ComputedRef } from 'vue';
import openaiService from '../../../lib/openai/openaiService';
import logger from '../../app/services/loggerService';
import { createPacedStream } from '../../../lib/streaming/streamingService';
import type { Message } from '../types';
import type { MessageManager } from '../stores/messageManager';

/**
 * 代理API服务类
 * @description 提供与AI API交互的功能，包括消息格式化、API调用和流式响应处理
 */
export class AgentApiService {
  private activeConfig: ComputedRef<any>;
  private messageManager: MessageManager;

  /**
   * 构造函数
   * @description 初始化API服务，设置消息管理器和配置引用
   * @param {MessageManager} messageManager 消息管理器
   * @param {ComputedRef<any>} activeConfig 活跃配置
   */
  constructor(
    messageManager: MessageManager,
    activeConfig: ComputedRef<any>
  ) {
    this.messageManager = messageManager;
    this.activeConfig = activeConfig;
  }

  /**
   * 格式化消息用于API调用
   * @description 将内部消息格式转换为API兼容格式，过滤掉UI专用消息类型
   * @param {Message[]} history 消息历史记录
   * @return {any[]} 格式化后的消息数组
   */
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
          // 从API请求中移除tool_calls属性，防止不兼容结构被发送
          const toolXmls = m.tool_calls.map(tc => tc.xml).join('');
          messageForApi.content = (m.content || '') + toolXmls;
        }
        // 确保tool_calls不会被发送到API，即使它存在于其他角色的消息中
        delete messageForApi.tool_calls;
        if (m.role !== 'assistant' || !m.tool_calls) delete messageForApi.name;
        if (m.role !== 'tool') delete messageForApi.tool_call_id;
        return messageForApi;
      });
  }

  /**
   * 调用AI API
   * @description 向AI API发送聊天完成请求
   * @param {Message[]} history 消息历史记录
   * @param {AbortSignal} signal 中止信号
   * @return {Promise<any>} API响应结果
   * @throws {Error} 当API调用失败或配置无效时抛出异常
   */
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

  /**
   * 处理流式响应
   * @description 处理AI API的流式响应，逐步构建助手消息
   * @param {any} openaiStream OpenAI流式响应
   * @param {AbortSignal} abortSignal 中止信号
   * @return {Promise<Message | null>} 创建的助手消息
   * @throws {Error} 当处理流式响应失败时抛出异常
   */
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