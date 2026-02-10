import { ref, type ComputedRef } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Message, Session } from '../types';
import type { MessageManager } from '../stores/messageManager';
import type { Config } from '@/features/app/stores/config';
import { AgentContextService } from '../context/AgentContextService';
import { AgentApiService, type StreamResult } from '../communication/AgentApiService';
import { AgentResponseHandlerService } from '../processing/responses/AgentResponseHandlerService';

/**
 * Agent 流程服务
 *
 * 现代化重构：
 * - 移除命令队列循环，SDK 自动管理工具执行
 * - 只处理用户消息发送和 ask_choice UI 工具
 */
export class AgentFlowService {
  public isProcessing = ref(false);
  public consecutiveAiTurns = ref(0);
  private abortController: AbortController | null = null;
  private isForceStopped = ref(false);
  private stopPromiseResolver: (() => void) | null = null;

  private messageManager: MessageManager;
  private contextService: AgentContextService;
  private apiService: AgentApiService;
  private responseHandlerService: AgentResponseHandlerService;
  private activeConfig: ComputedRef<Config | null>;

  constructor(
    messageManager: MessageManager,
    private currentSession: ComputedRef<Session | null>,
    contextService: AgentContextService,
    apiService: AgentApiService,
    _toolService: any, // 保留参数兼容性，但不再使用
    responseHandlerService: AgentResponseHandlerService,
    activeConfig: ComputedRef<Config | null>
  ) {
    this.messageManager = messageManager;
    this.contextService = contextService;
    this.apiService = apiService;
    this.responseHandlerService = responseHandlerService;
    this.activeConfig = activeConfig;
  }

  private get orderedMessages(): Message[] {
    const session = this.currentSession.value;
    if (!session) return [];
    return session.messageIds.map(id => session.messagesById[id]);
  }

  public stopAgent(): Promise<void> {
    logger.log('[AgentFlowService] 正在停止代理...');

    const stopPromise = new Promise<void>((resolve) => {
      this.stopPromiseResolver = resolve;
    });

    this.isForceStopped.value = true;

    if (this.abortController) {
      this.abortController.abort();
      logger.log('[AgentFlowService] 已中断 AbortController');
    }

    // 处理正在流式传输的消息
    if (this.isProcessing.value) {
      const streamingMessage = this.orderedMessages.find(m => m.status === 'streaming');
      if (streamingMessage) {
        this.messageManager.updateMessage({
          messageId: streamingMessage.id,
          updates: { status: 'error', content: `${streamingMessage.content}\n\n---\n*已手动中断*` }
        });
        logger.log('[AgentFlowService] 已更新流式消息状态为中断');
      }
    }

    // 重置状态
    this.consecutiveAiTurns.value = 0;
    this.isProcessing.value = false;
    this.abortController = null;

    logger.log('[AgentFlowService] 代理停止完成');

    if (this.stopPromiseResolver) {
      this.stopPromiseResolver();
      this.stopPromiseResolver = null;
    }

    return stopPromise;
  }

  public waitForStop(): Promise<void> {
    if (!this.isProcessing.value) {
      return Promise.resolve();
    }

    return new Promise<void>((resolve) => {
      if (this.stopPromiseResolver) {
        const originalResolver = this.stopPromiseResolver;
        this.stopPromiseResolver = () => {
          originalResolver();
          resolve();
        };
      } else {
        this.stopPromiseResolver = resolve;
      }
    });
  }

  /**
   * 开始新的 AI 轮次
   */
  public startTurn() {
    this.isForceStopped.value = false;
    this.handleApiCall();
  }

  /**
   * 处理 API 调用
   * SDK 自动执行工具，此方法只负责 UI 更新和 ask_choice 处理
   */
  private async handleApiCall() {
    if (this.isForceStopped.value) return;

    this.isProcessing.value = true;
    this.abortController = new AbortController();
    this.consecutiveAiTurns.value = 0;

    try {
      // 检查并压缩上下文
      await this.contextService.checkAndCompressContextIfNeeded();

      // 调用 API（SDK 自动执行工具）
      const apiResponse = await this.apiService.callApi(
        this.orderedMessages,
        this.abortController.signal
      );

      // 处理流式响应，更新 UI
      const streamResult: StreamResult = await this.apiService.handleStream(
        apiResponse.result,
        this.abortController.signal
      );

      // 检查是否有 ask_choice 工具调用（UI 工具）
      if (streamResult.steps && streamResult.steps.length > 0) {
        const lastStep = streamResult.steps[streamResult.steps.length - 1];
        const askChoiceCall = lastStep?.toolCalls?.find(
          (call: any) => (call.toolName || call.name) === 'ask_choice'
        );

        if (askChoiceCall && streamResult.assistantMessage) {
          // 处理 ask_choice UI 工具
          logger.log('[AgentFlowService] 检测到 ask_choice 工具调用');
          await this.responseHandlerService.handleAskChoice(
            streamResult.assistantMessage,
            askChoiceCall
          );
        }
      }

      // 处理简化语法（表情和问题）- 两种模式都需要处理
      if (streamResult.assistantMessage) {
        await this.responseHandlerService.handleApiResponse(streamResult.assistantMessage);
      }

      logger.log(`[AgentFlowService] API 调用完成: finishReason=${streamResult.finishReason}`);

    } catch (err: any) {
      if (err.name !== 'AbortError') {
        await this.messageManager.addMessage({
          role: 'assistant',
          type: 'error',
          content: `处理请求时出错: ${err.message}`
        });
      }
    } finally {
      this.isProcessing.value = false;
      this.abortController = null;
    }
  }
}
