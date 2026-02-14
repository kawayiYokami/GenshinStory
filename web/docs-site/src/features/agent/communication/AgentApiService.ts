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
        const tools = toolRegistryService.toSdkToolDefinitions({
          includedTools: ['search_docs', 'read_doc', 'explore', 'ask_choice'],
        });
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
    const streamedToolCallIds = new Set<string>();
    const streamedToolResultIds = new Set<string>();

    const toPlainResultContent = (value: unknown): string => {
      if (typeof value === 'string') return value;
      if (value === undefined || value === null) return '';
      try {
        return JSON.stringify(value);
      } catch {
        return String(value);
      }
    };

    const toToolInput = (raw: unknown): Record<string, unknown> => {
      const parseJsonObject = (text: string): Record<string, unknown> => {
        try {
          const parsed = JSON.parse(text);
          if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
            return parsed as Record<string, unknown>;
          }
        } catch {
          // ignore
        }
        return {};
      };

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
    };

    const normalizeToolCall = (toolCall: any, fallbackId: string) => {
      const toolName = String(toolCall?.toolName || toolCall?.name || '');
      const toolCallId = String(toolCall?.toolCallId || toolCall?.id || toolCall?.callId || fallbackId);
      const toolInput = toToolInput(toolCall?.input ?? toolCall?.args ?? {});
      return { toolName, toolCallId, toolInput };
    };

    const normalizeToolResult = (toolResult: any, fallbackId: string) => {
      const toolName = String(toolResult?.toolName || toolResult?.name || '');
      const toolCallId = String(toolResult?.toolCallId || toolResult?.id || toolResult?.callId || fallbackId);
      let output = toolResult?.result ?? toolResult?.output ?? toolResult?.content ?? toolResult?.value ?? '';
      if (output && typeof output === 'object' && 'value' in output) {
        output = (output as { value: unknown }).value;
      }
      return { toolName, toolCallId, output };
    };

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
              const normalizedToolInput = toToolInput(part.args ?? part.input ?? {});

              // 保存工具调用信息，供 tool-result 时使用
              currentToolCall = {
                toolCallId: part.toolCallId,
                toolName: part.toolName,
                toolInput: normalizedToolInput,
              };
              if (part.toolCallId) {
                streamedToolCallIds.add(String(part.toolCallId));
              }

              // 先闭合当前文本消息（如果有）
              if (messageId) {
                await this.messageManager.updateMessage({
                  messageId,
                  updates: { status: 'done', streamCompleted: true },
                });
                // 重置 messageId，让工具执行后的文本创建新消息
                messageId = null;
              }

              // 关键修复：为执行工具补齐 assistant.tool_calls 历史，
              // 确保后续的 tool_result 在协议层有合法前置。
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
                  assistantMessage = toolCallMessage;
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
              const toolInput = toToolInput(part.input ?? part.args ?? currentToolCall?.toolInput ?? {});
              if (toolCallId) {
                streamedToolResultIds.add(String(toolCallId));
              }

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

    // 关键修复：当 provider 未通过 fullStream 派发工具事件时，
    // 依赖 steps 回填 tool_call/tool_result，确保 explore 等工具一定进入会话记录。
    try {
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

          if (!streamedToolCallIds.has(call.toolCallId)) {
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
            streamedToolCallIds.add(call.toolCallId);
          }

          if (!streamedToolResultIds.has(call.toolCallId)) {
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
            streamedToolResultIds.add(call.toolCallId);
          }
        }
      }
    } catch (e) {
      logger.warn('[AgentApiService] 从 steps 回填工具消息失败:', e);
    }

    // 如果流结束时还没计算思维耗时，现在计算
    if (reasoningStartTime && reasoningDuration === null) {
      reasoningDuration = Math.round((Date.now() - reasoningStartTime) / 1000);
      logger.log(`[AgentApiService] 思维链完成（流结束），耗时: ${reasoningDuration}s`);
    }

    // 非流式模式下可能没有 text-delta，兜底补一条 assistant 文本消息
    if (!assistantMessage && !messageId) {
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
          assistantMessage = finalMsg;
          messageId = finalMsg.id;
        }
      }
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
