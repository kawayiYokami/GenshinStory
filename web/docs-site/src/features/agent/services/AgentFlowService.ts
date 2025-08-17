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
  private commandQueue = ref<Command[]>([]);
  private abortController: AbortController | null = null;
  private isForceStopped = ref(false);
  private consecutiveAiTurns = ref(0);

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

  public stopAgent() {
    this.isForceStopped.value = true;
    this.abortController?.abort();
    this.commandQueue.value = [];
    if (this.isProcessing.value) {
      const streamingMessage = this.orderedMessages.find(m => m.status === 'streaming');
      if (streamingMessage) {
        this.messageManager.updateMessage({
          messageId: streamingMessage.id,
          updates: { status: 'error', content: `${streamingMessage.content}\n\n---\n*已手动中断*` }
        });
      }
    }
    this.abortController = null;
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
    if (result.status === 'success') this.initiateAiTurn();
  }
}