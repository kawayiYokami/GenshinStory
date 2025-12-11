import type { ComputedRef } from 'vue';
import contextOptimizerService from './contextOptimizerService';
import logger from '@/features/app/services/loggerService';
import type { Message, Session } from '../types';
import type { MessageManager } from '../stores/messageManager';

export class AgentContextService {
  private currentSession: ComputedRef<Session | null>;
  private activeConfig: ComputedRef<any>;
  private messageManager: MessageManager;

  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>,
    activeConfig: ComputedRef<any>
  ) {
    this.messageManager = messageManager;
    this.currentSession = currentSession;
    this.activeConfig = activeConfig;
  }

  private get orderedMessages(): Message[] {
    const session = this.currentSession.value;
    if (!session) return [];
    return session.messageIds.map(id => session.messagesById[id]);
  }

  public async checkAndCompressContextIfNeeded(): Promise<void> {
    const currentHistory = this.orderedMessages;
    const currentTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
    const maxContextLength = this.activeConfig.value?.maxContextLength || 128000;
    const threshold = maxContextLength * 0.9;

    if (currentTokens > threshold) {
      logger.log(`[AgentContextService] 上下文 (${currentTokens}) 超出动态阈值 (${threshold})，触发主动压缩。`);
      const optimizationResult = await contextOptimizerService.processContext(currentHistory, maxContextLength);

      if (optimizationResult.status === 'SUCCESS' && optimizationResult.history) {
        const newMessagesById: { [key: string]: Message } = {};
        const newMessageIds: string[] = [];
        for (const message of optimizationResult.history) {
          if (!message.id) {
            message.id = `msg_${Date.now()}_${Math.random()}`;
          }
          newMessagesById[message.id] = message;
          newMessageIds.push(message.id);
        }
        if (this.currentSession.value) {
          this.currentSession.value.messagesById = newMessagesById;
          this.currentSession.value.messageIds = newMessageIds;
        }
        logger.log(`[AgentContextService] 上下文压缩成功。新 token 数: ${optimizationResult.tokens}`);
      } else if (optimizationResult.status !== 'SUCCESS') {
        logger.error(`[AgentContextService] 主动压缩失败:`, optimizationResult.userMessage);
        await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: `上下文压缩失败: ${optimizationResult.userMessage}` });
      }
    }
  }
}