import { type ComputedRef } from 'vue';
import type { Session } from '../types';
import type { MessageManager } from '../stores/messageManager';
import { AgentFlowService } from './AgentFlowService';
import { AgentContextService } from './AgentContextService';
import { AgentApiService } from './AgentApiService';
import { AgentToolService } from './AgentToolService';
import { AgentResponseHandlerService } from './AgentResponseHandlerService';
import { agentCacheService } from './AgentCacheService';

export class AgentService {
  private flowService: AgentFlowService;

  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>,
    activeConfig: ComputedRef<any>
  ) {
    const contextService = new AgentContextService(messageManager, currentSession, activeConfig);
    const apiService = new AgentApiService(messageManager, activeConfig);
    const toolService = new AgentToolService(messageManager, currentSession, activeConfig);
    const responseHandlerService = new AgentResponseHandlerService(messageManager, currentSession);

    this.flowService = new AgentFlowService(
      messageManager,
      currentSession,
      contextService,
      apiService,
      toolService,
      responseHandlerService
    );
  }

  public stopAgent() {
    this.flowService.stopAgent();
  }

  public startTurn() {
    this.flowService.startTurn();
  }

  public getIsProcessing(): boolean {
    return this.flowService.isProcessing.value;
  }

  public static async forceClearAgentCache(): Promise<void> {
    await agentCacheService.forceClearAgentCache();
  }
}