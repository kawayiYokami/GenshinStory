/**
 * @fileoverview 代理API服务类
 * @description 负责与AI API进行通信，处理API调用和流式响应
 * @author yokami
 *
 * 现代化重构：使用 AI SDK 标准模式
 * - 工具执行由 SDK 自动管理（通过 tool.execute）
 * - 使用 stopWhen 控制循环
 * - handleStream 只负责 UI 更新
 */
import type { ComputedRef } from 'vue';
import llmProviderService from '../../../lib/llm/llmProviderService';
import logger from '../../app/services/loggerService';
import type { Message } from '../types';
import type { MessageManager } from '../stores/messageManager';
import { paramsToRequestBody } from '../../app/utils/paramUtils';
import type { AgentProtocolMode, ProtocolMode } from '../types';
import { toolRegistryService } from '../tools/registry/toolRegistryService';
import { toModelMessages } from '../adapters/modelMessageAdapter';

/**
 * handleStream 返回结果
 */
export interface StreamResult {
  assistantMessage: Message | null;
  finishReason: string;
  steps: any[];
}

/**
 * 代理API服务类
 * @description 提供与AI API交互的功能，SDK 自动管理工具执行
 */
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

  private getProtocolMode(): AgentProtocolMode {
    return this.activeConfig.value?.agentProtocolMode || 'auto';
  }

  private shouldUseStructured(): boolean {
    const configuredMode = this.getProtocolMode();
    if (configuredMode === 'structured') return true;
    if (configuredMode === 'fallback') return false;

    const capabilities = llmProviderService.getCapabilities(this.activeConfig.value);
    return capabilities.supportsStructuredToolCalls;
  }

  private emitProtocolEvent(eventName: string, payload?: Record<string, unknown>) {
    logger.log(`[AgentApiService][ProtocolEvent] ${eventName}`, payload || {});
  }

  /**
   * 调用AI API
   * @description 向AI API发送聊天完成请求，SDK 自动执行工具
   */
  public async callApi(history: Message[], signal: AbortSignal): Promise<{ result: any; protocolMode: ProtocolMode }> {
    if (!this.activeConfig.value?.apiUrl || !this.activeConfig.value?.apiKey) {
      const errorMsg = "没有激活的有效AI配置。请在设置中选择或创建一个配置。";
      logger.error(`[AgentApiService] ${errorMsg}`);
      throw new Error(errorMsg);
    }

    const apiMessages = toModelMessages(history);
    const customParamsBody = paramsToRequestBody(this.activeConfig.value.customParams);

    logger.log("[AgentApiService] 准备调用 API...", { messageCount: apiMessages.length });
    logger.setLastRequest({
      model: this.activeConfig.value.modelName,
      messages: apiMessages,
      temperature: this.activeConfig.value.temperature,
      stream: this.activeConfig.value.stream,
      ...customParamsBody,
    });

    const useStructured = this.shouldUseStructured();
    const selectedMode: ProtocolMode = useStructured ? 'structured' : 'fallback';
    this.emitProtocolEvent('PROTOCOL_SELECTED', { mode: selectedMode });

    if (useStructured) {
      try {
        await toolRegistryService.loadTools();
        const tools = toolRegistryService.toSdkToolDefinitions();
        const structuredResult = await llmProviderService.createStructuredChatCompletion(
          apiMessages,
          this.activeConfig.value,
          signal,
          tools,
          customParamsBody
        );
        this.emitProtocolEvent('STRUCTURED_API_CALLED', { note: 'SDK will auto-execute tools' });

        return {
          result: structuredResult,
          protocolMode: 'structured',
        };
      } catch (error: any) {
        this.emitProtocolEvent('STRUCTURED_FAILED', { reason: error?.message || String(error) });

        if (this.getProtocolMode() === 'structured') {
          logger.error('[AgentApiService] 强制 structured 模式失败，不执行 fallback。', error);
          throw error;
        }

        this.emitProtocolEvent('FALLBACK_ACTIVATED');
        const fallbackResult = await llmProviderService.createChatCompletion(
          apiMessages,
          this.activeConfig.value,
          signal,
          customParamsBody
        );
        return {
          result: fallbackResult,
          protocolMode: 'fallback',
        };
      }
    }

    const fallbackResult = await llmProviderService.createChatCompletion(
      apiMessages,
      this.activeConfig.value,
      signal,
      customParamsBody
    );
    return {
      result: fallbackResult,
      protocolMode: 'fallback',
    };
  }

  /**
   * 处理 AI 响应流
   * @description 消费 fullStream，更新 UI（文本、工具状态、工具结果）
   * SDK 自动执行工具，此方法只负责 UI 更新
   */
  public async handleStream(result: any, abortSignal: AbortSignal): Promise<StreamResult> {
    let assistantMessage: Message | null = null;
    let messageId: string | null = null;
    let collectedReasoning = '';
    let currentToolStatusId: string | null = null;
    let reasoningStartTime: number | null = null;
    let reasoningDuration: number | null = null;

    // 保存当前工具调用信息，用于关联 tool-result
    let currentToolCall: {
      toolCallId: string;
      toolName: string;
      toolInput: Record<string, unknown>;
    } | null = null;

    logger.log('[AgentApiService] 开始消费 fullStream...');

    try {
      if (result?.fullStream && Symbol.asyncIterator in Object(result.fullStream)) {
        for await (const part of result.fullStream) {
          if (abortSignal.aborted) {
            logger.warn('[AgentApiService] fullStream 消费被中止。');
            break;
          }

          switch (part?.type) {
            case 'reasoning-delta':
              if (typeof part.text === 'string') {
                // 记录思维开始时间
                if (!reasoningStartTime) {
                  reasoningStartTime = Date.now();
                }
                collectedReasoning += part.text;
              }
              break;

            case 'text-delta':
              // 收到正文时，思维链结束，计算耗时
              if (reasoningStartTime && reasoningDuration === null) {
                reasoningDuration = Math.round((Date.now() - reasoningStartTime) / 1000);
                logger.log(`[AgentApiService] 思维链完成，耗时: ${reasoningDuration}s`);
              }

              if (typeof part.text === 'string' && part.text) {
                if (!messageId) {
                  const newMsg = await this.messageManager.addMessage({
                    role: 'assistant',
                    content: '',
                    type: 'text',
                    status: 'streaming',
                  });
                  if (newMsg) {
                    assistantMessage = newMsg;
                    messageId = newMsg.id;
                  }
                }
                if (messageId) {
                  await this.messageManager.appendMessageContent({ messageId, chunk: part.text });
                }
              }
              break;

            case 'tool-call':
              // SDK 自动执行工具，这里只更新 UI 状态
              logger.log(`[AgentApiService] tool-call 事件: ${part.toolName}`, { toolCallId: part.toolCallId, args: part.args });

              // 保存工具调用信息，供 tool-result 时使用
              currentToolCall = {
                toolCallId: part.toolCallId,
                toolName: part.toolName,
                toolInput: part.args || {},
              };

              // 先闭合当前文本消息（如果有）
              if (messageId) {
                await this.messageManager.updateMessage({
                  messageId,
                  updates: { status: 'done', streamCompleted: true },
                });
                // 重置 messageId，让工具执行后的文本创建新消息
                messageId = null;
              }

              const statusMsg = await this.messageManager.addMessage({
                role: 'assistant',
                type: 'tool_status',
                content: `正在执行工具: ${part.toolName}...`,
                status: 'rendering',
                toolCallId: part.toolCallId,
                toolName: part.toolName,
                toolInput: part.args || {},
              });
              if (statusMsg) {
                currentToolStatusId = statusMsg.id;
              }
              break;

            case 'tool-result':
              // 工具执行完成，更新工具结果到 UI
              logger.log(`[AgentApiService] tool-result 事件: ${part.toolName}`, { toolCallId: part.toolCallId });

              // 获取工具结果（兼容不同字段名）
              const toolResult = part.result ?? part.output ?? part.content ?? '';
              const resultContent = typeof toolResult === 'string' ? toolResult : JSON.stringify(toolResult);

              // 获取工具调用信息（优先使用 part 中的，其次使用保存的）
              const toolCallId = part.toolCallId || currentToolCall?.toolCallId;
              const toolName = part.toolName || currentToolCall?.toolName;
              const toolInput = part.input || part.args || currentToolCall?.toolInput || {};

              // 如果有状态消息，替换为结果消息
              if (currentToolStatusId) {
                await this.messageManager.replaceMessage(currentToolStatusId, {
                  role: 'tool',  // AI SDK 要求 tool 角色
                  type: 'tool_result',
                  content: resultContent,
                  status: 'done',
                  toolCallId,
                  toolName,
                  toolInput,
                });
                currentToolStatusId = null;
              } else {
                // 直接添加结果消息
                await this.messageManager.addMessage({
                  role: 'tool',  // AI SDK 要求 tool 角色
                  type: 'tool_result',
                  content: resultContent,
                  status: 'done',
                  toolCallId,
                  toolName,
                  toolInput,
                });
              }

              // 清理当前工具调用信息
              currentToolCall = null;
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
          }
        }
      }
    } catch (err: any) {
      // 处理 AI_NoOutputGeneratedError - 纯工具调用场景
      if (err?.name === 'AI_NoOutputGeneratedError') {
        logger.warn('[AgentApiService] 流无文本输出（纯工具调用场景）');
      } else {
        logger.error('[AgentApiService] 消费 fullStream 时发生错误:', err);
        if (messageId) {
          await this.messageManager.updateMessage({ messageId, updates: { status: 'error' } });
        }
        throw err;
      }
    }

    // 获取最终结果
    let finishReason = 'unknown';
    let steps: any[] = [];

    try {
      finishReason = await result.finishReason;
      steps = await result.steps || [];
      logger.log(`[AgentApiService] 流完成: finishReason=${finishReason}, steps=${steps.length}`);
    } catch (e) {
      logger.warn('[AgentApiService] 获取 finishReason/steps 失败:', e);
    }

    // 如果流结束时还没计算思维耗时，现在计算
    if (reasoningStartTime && reasoningDuration === null) {
      reasoningDuration = Math.round((Date.now() - reasoningStartTime) / 1000);
      logger.log(`[AgentApiService] 思维链完成（流结束），耗时: ${reasoningDuration}s`);
    }

    // 如果没有创建消息但有 reasoning，创建一个空消息承载
    if (!messageId && collectedReasoning) {
      const newMsg = await this.messageManager.addMessage({
        role: 'assistant',
        content: '',
        type: 'text',
        status: 'done',
        reasoning: collectedReasoning,
        reasoningDuration: reasoningDuration ?? undefined,
      });
      if (newMsg) {
        assistantMessage = newMsg;
        messageId = newMsg.id;
      }
    }

    // 更新消息状态
    if (messageId) {
      await this.messageManager.updateMessage({
        messageId,
        updates: {
          streamCompleted: true,
          status: 'done',
          reasoning: collectedReasoning || undefined,
          reasoningDuration: reasoningDuration ?? undefined,
        },
      });
    }

    return { assistantMessage, finishReason, steps };
  }
}
