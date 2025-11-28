import { ref, type ComputedRef } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Command, Message, Session } from '../types';
import type { ParsedToolCall } from './toolParserService';
import type { MessageManager } from '../stores/messageManager';
import { AgentContextService } from './AgentContextService';
import { AgentApiService } from './AgentApiService';
import { AgentToolService } from './AgentToolService';
import { AgentResponseHandlerService, type HandleResponseResult } from './AgentResponseHandlerService';

export class AgentFlowService {
  public isProcessing = ref(false);
  public consecutiveToolErrors = ref(0);
  public consecutiveAiTurns = ref(0);
  private commandQueue = ref<Command[]>([]);
  private abortController: AbortController | null = null;
  private isForceStopped = ref(false);
  private stopPromiseResolver: (() => void) | null = null;

  private messageManager: MessageManager;
  private contextService: AgentContextService;
  private apiService: AgentApiService;
  private toolService: AgentToolService;
  private responseHandlerService: AgentResponseHandlerService;

  constructor(
    messageManager: MessageManager,
    private currentSession: ComputedRef<Session | null>,
    contextService: AgentContextService,
    apiService: AgentApiService,
    toolService: AgentToolService,
    responseHandlerService: AgentResponseHandlerService
  ) {
    this.messageManager = messageManager;
    this.contextService = contextService;
    this.apiService = apiService;
    this.toolService = toolService;
    this.responseHandlerService = responseHandlerService;
  }

  private get orderedMessages(): Message[] {
    const session = this.currentSession.value;
    if (!session) return [];
    return session.messageIds.map(id => session.messagesById[id]);
  }

  public stopAgent(): Promise<void> {
    logger.log('[AgentFlowService] 正在停止代理...');

    // 创建一个新的 Promise，当停止完成时 resolve
    const stopPromise = new Promise<void>((resolve) => {
      this.stopPromiseResolver = resolve;
    });

    // 设置强制停止标志
    this.isForceStopped.value = true;

    // 中断当前的 AbortController
    if (this.abortController) {
      this.abortController.abort();
      logger.log('[AgentFlowService] 已中断 AbortController');
    }

    // 清空命令队列
    this.commandQueue.value = [];
    logger.log('[AgentFlowService] 已清空命令队列');

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

    // 重置所有状态
    this.consecutiveToolErrors.value = 0;
    this.consecutiveAiTurns.value = 0;
    this.isProcessing.value = false;
    this.abortController = null;

    logger.log('[AgentFlowService] 代理停止完成');

    // 解决 Promise，表示停止已完成
    if (this.stopPromiseResolver) {
      this.stopPromiseResolver();
      this.stopPromiseResolver = null;
    }

    return stopPromise;
  }

  /**
   * 等待停止操作完成
   * @description 返回一个 Promise，当代理停止完成时解决
   * @return {Promise<void>} 停止完成的 Promise
   */
  public waitForStop(): Promise<void> {
    // 如果当前没有在处理中，直接返回一个已解决的 Promise
    if (!this.isProcessing.value) {
      return Promise.resolve();
    }

    // 否则返回一个新的 Promise，等待停止完成
    return new Promise<void>((resolve) => {
      // 检查是否已经有停止解析器
      if (this.stopPromiseResolver) {
        // 如果有，说明停止过程已经开始，我们需要等待它完成
        // 创建一个新的解析器，在原有的解析器之后调用
        const originalResolver = this.stopPromiseResolver;
        this.stopPromiseResolver = () => {
          originalResolver();
          resolve();
        };
      } else {
        // 如果没有，说明停止过程还没有开始，我们创建一个新的解析器
        this.stopPromiseResolver = resolve;
      }
    });
  }

  public startTurn() {
    this.isForceStopped.value = false;
    this.initiateAiTurn();
  }

  private initiateAiTurn() {
    if (this.isForceStopped.value) return;
    if (this.commandQueue.value.some(c => c.type === 'CALL_AI')) return;

    this.abortController = new AbortController();
    this.commandQueue.value.push({ type: 'CALL_AI' });
    if (!this.isProcessing.value) this.processQueue();
  }

  private async processQueue() {
    this.isProcessing.value = true;
    this.consecutiveAiTurns.value = 0;
    this.responseHandlerService.noToolCallRetries.value = 0;

    while (this.commandQueue.value.length > 0) {
      if (this.abortController?.signal.aborted) break;

      const command = this.commandQueue.value.shift();
      if (!command) continue;

      try {
        if (command.type === 'CALL_AI') {
          if (this.consecutiveAiTurns.value++ >= 10) {
            await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "AI已连续迭代10次，自动中断。" });
            break;
          }
          await this.handleApiCall();
        } else if (command.type === 'EXECUTE_TOOL') {
          await this.handleToolExecution(command.payload.parsedTool as ParsedToolCall);
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: `处理命令'${command.type}'时出错: ${err.message}` });
        }
        this.commandQueue.value = [];
        break;
      }
    }
    this.isProcessing.value = false;
    this.abortController = null;
  }

  private async handleApiCall() {
    await this.contextService.checkAndCompressContextIfNeeded();

    const response = await this.apiService.callApi(this.orderedMessages, this.abortController!.signal);
    const assistantMessage = await this.apiService.handleStream(response, this.abortController!.signal);

    if (!assistantMessage?.id) return;

    const result: HandleResponseResult = await this.responseHandlerService.handleApiResponse(assistantMessage);

    if (result.type === 'tool_call') {
      this.commandQueue.value.push({ type: 'EXECUTE_TOOL', payload: { parsedTool: result.payload } });
    } else if (result.type === 'retry_no_tool_call') {
      this.initiateAiTurn();
    }
  }

  private async handleToolExecution(parsedTool: ParsedToolCall) {
    const result = await this.toolService.handleToolExecution(parsedTool);
    if (result.status === 'success') {
      this.consecutiveToolErrors.value = 0;
      this.initiateAiTurn();
    } else {
      this.consecutiveToolErrors.value++;
    }
  }
}