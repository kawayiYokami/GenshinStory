import { defineStore, storeToRefs } from 'pinia';
import { ref, computed, watch, nextTick } from 'vue';
import { nanoid } from 'nanoid';
import logger, { logs } from '@/features/app/services/loggerService';
import { useAppStore } from '@/features/app/stores/app';
import localTools from '@/features/agent/services/localToolsService';
import type { Ref } from 'vue';
import type { LogEntry } from '@/features/app/services/loggerService';
import { useConfigStore } from '@/features/app/stores/config';

// --- Import types from new module ---
import type { MessageContentPart, Message, Session, AgentInfo, Command } from '../types';

// --- Import managers and services from new modules ---
import { MessageManagerImpl } from './messageManager';
import { SessionManagerImpl, type SessionManager } from '@/features/agent/services/sessionManager';
import { PersistenceManagerImpl, sessionsStore, lastUsedRolesStore, forceClearAgentCache } from './persistence';
import promptService from '@/features/agent/services/promptService';
import { AgentService } from '../services/agentService';

export type { MessageContentPart, Message, Session, AgentInfo, Command };

// --- Original Store State ---
const MAX_SESSIONS_PER_DOMAIN = 10;

export const useAgentStore = defineStore('agent', () => {
  // --- AgentService State (managed by AgentService) ---
  // 这些状态现在由 AgentService 管理
  // const commandQueue = ref<Command[]>([]);
  // const isProcessing = ref(false);
  // let abortController: AbortController | null = null;
  // let toolFeedbackPromptContent: string | null = null;
  // const consecutiveToolErrors = ref(0);
  // const consecutiveAiTurns = ref(0);
  // const noToolCallRetries = ref(0);
  // const isForceStopped = ref(false);

  // --- Original Store State ---
  const sessions = ref<{ [key: string]: Session }>({});
  const activeSessionIds = ref<{ [key: string]: string | null }>({ gi: null, hsr: null });
  const availableAgents = ref<{ [key: string]: AgentInfo[] }>({ gi: [], hsr: [] });
  const activeRoleId = ref<{ [key: string]: string | null }>({ gi: null, hsr: null });
  const isLoading = ref(false);
  const error = ref<Error | string | null>(null);
  const logMessages: Ref<LogEntry[]> = ref(logs);
  const activeAgentName = ref('AI');
  const _isFetchingAgents = ref<{ [key: string]: boolean }>({ gi: false, hsr: false });
  // consecutiveToolErrors, consecutiveAiTurns, noToolCallRetries, isForceStopped moved to AgentService

  // --- Getters / 计算属性 ---
  const appStore = useAppStore();
  const configStore = useConfigStore();
  const { activeConfig } = storeToRefs(configStore);
  const currentDomain = computed(() => appStore.currentDomain);
  const activeSessionId = computed(() => currentDomain.value ? activeSessionIds.value[currentDomain.value] : null);
  const currentRoleId = computed(() => currentDomain.value ? activeRoleId.value[currentDomain.value] : null);
  const currentSession = computed(() => activeSessionId.value ? sessions.value[activeSessionId.value] : null);
  const messagesById = computed(() => currentSession.value?.messagesById || {});
  const messageIds = computed(() => currentSession.value?.messageIds || []);
  const orderedMessages = computed(() => {
    if (!currentSession.value) return [];
    return messageIds.value.map(id => messagesById.value[id]);
  });

  // --- Managers and Services ---
  const messageManager: MessageManagerImpl = new MessageManagerImpl(currentSession.value || null);
  // Update messageManager when currentSession changes
  watch(currentSession, (newSession) => {
    (messageManager as MessageManagerImpl).setCurrentSession(newSession || null);
  });
  
  const sessionManager: SessionManager = new SessionManagerImpl(
    sessions,
    activeSessionIds,
    activeRoleId,
    activeAgentName,
    lastUsedRolesStore,
    availableAgents
  );
  const persistenceManager = new PersistenceManagerImpl();
  
  // Create AgentService with dependencies
  const agentService = new AgentService(
    messageManager,
    currentSession,
    activeConfig
  );
  
  // Create persist function
  const persistState = persistenceManager.persistState(sessions, activeSessionIds);

  // --- Original Store Actions (refactored to use managers/services) ---
  async function switchSession(sessionId: string): Promise<void> {
    await sessionManager.switchSession(sessionId, currentDomain.value);
  }
  
  function deleteSession(sessionId: string): void {
    sessionManager.deleteSession(sessionId, currentDomain.value, startNewSession);
  }

  function renameSession(sessionId: string, newName: string): void {
    sessionManager.renameSession(sessionId, newName);
  }
  
  async function fetchAvailableAgents(domain: string): Promise<string | null> {
    if (_isFetchingAgents.value[domain] || availableAgents.value[domain]?.length > 0) {
      return activeRoleId.value[domain];
    }
    _isFetchingAgents.value[domain] = true;

    try {
      const cachedRoleId = await lastUsedRolesStore.getItem<string>(domain);
      if (cachedRoleId) {
        activeRoleId.value[domain] = cachedRoleId;
        logger.log(`[AgentStore] 已加载域 '${domain}' 的上次使用角色 '${cachedRoleId}'。`);
      }

      logger.log(`Agent Store: 正在为域 '${domain}' 获取可用 Agent 列表...`);
      const agents = await promptService.listAvailableAgents(domain);
      availableAgents.value[domain] = agents;

      if (!activeRoleId.value[domain] && agents && agents.length > 0) {
        const defaultId = agents[0].id;
        activeRoleId.value[domain] = defaultId;
        logger.log(`[AgentStore] '${domain}' 无缓存角色。已设置默认 agent 为 '${defaultId}'。`);
        await lastUsedRolesStore.setItem(domain, defaultId);
      }
    } catch (e) {
      logger.error(`Agent Store: 获取 '${domain}' 的 Agent 列表失败:`, e);
    } finally {
      _isFetchingAgents.value[domain] = false;
      return activeRoleId.value[domain];
    }
  }

  async function startNewSession(domain: string, roleIdToLoad: string | null): Promise<void> {
    await sessionManager.startNewSession(
      domain,
      roleIdToLoad,
      availableAgents,
      activeRoleId,
      activeAgentName,
      lastUsedRolesStore,
      sessions,
      activeSessionIds
    );
    
    // Add system message after session is created
    const newSessionId = activeSessionIds.value[domain];
    if (newSessionId) {
      const newSession = sessions.value[newSessionId];
      if (newSession) {
        const { systemPrompt } = await promptService.loadSystemPrompt(domain, newSession.roleId);
        await messageManager.addMessage({
          role: 'system',
          content: systemPrompt,
          type: 'system',
        });
      }
    }
  }

  async function switchDomainContext(domain: string): Promise<void> {
    await sessionManager.switchDomainContext(
      domain,
      fetchAvailableAgents,
      startNewSession,
      availableAgents,
      activeRoleId,
      activeAgentName,
      sessions,
      activeSessionIds
    );
    
    // 确保为当前会话加载正确的系统提示词
    const sessionId = activeSessionIds.value[domain];
    if (sessionId && sessions.value[sessionId]) {
      const session = sessions.value[sessionId];
      const roleId = session.roleId;
      if (roleId) {
        try {
          const { systemPrompt } = await promptService.loadSystemPrompt(domain, roleId);
          // 更新会话中的第一条系统消息
          const firstMessageId = session.messageIds[0];
          if (firstMessageId) {
            const firstMessage = session.messagesById[firstMessageId];
            if (firstMessage && firstMessage.role === 'system') {
              // 如果第一条消息是系统消息，则更新其内容
              await messageManager.updateMessage({ messageId: firstMessageId, updates: { content: systemPrompt } });
            } else {
              // 如果第一条消息不是系统消息，则在最前面插入一条
              await messageManager.addMessage({
                role: 'system',
                content: systemPrompt,
                type: 'system',
              });
            }
          } else {
            // 如果会话为空，则添加系统消息
            await messageManager.addMessage({
              role: 'system',
              content: systemPrompt,
              type: 'system',
            });
          }
        } catch (e) {
          logger.error(`[AgentStore] 为会话 ${sessionId} 加载系统提示词失败:`, e);
        }
      }
    }
  }

  async function startNewChatWithAgent(roleId: string): Promise<void> {
    const systemPrompt = await sessionManager.startNewChatWithAgent(
      roleId,
      currentDomain.value,
      currentSession.value,
      isLoading,
      stopAgent, // stop function
      fetchAvailableAgents,
      startNewSession,
      availableAgents,
      activeRoleId,
      activeAgentName,
      lastUsedRolesStore,
      sessions,
      activeSessionIds
    );

    if (systemPrompt) {
      await messageManager.addMessage({
        role: 'system',
        content: systemPrompt,
        type: 'system',
      });
    }
  }
  
  async function switchAgent(roleId: string): Promise<void> {
    const domain = currentDomain.value;
    if (!domain) return;
    await fetchAvailableAgents(domain);
    await sessionManager.switchAgent(
      roleId,
      domain,
      currentSession.value,
      isLoading,
      stopAgent, // stop function
      fetchAvailableAgents,
      startNewSession,
      availableAgents,
      activeRoleId,
      activeAgentName,
      lastUsedRolesStore,
      sessions,
      activeSessionIds
    );
  }

  async function sendMessage(payload: string | { text: string; images?: string[]; references?: any[] }): Promise<void> {
    // 重置"无工具调用"重试计数器
    // This should be handled by AgentService
    // noToolCallRetries.value = 0;
    
    if (!currentSession.value) {
      const initError = "没有激活的会话。";
      logger.error(initError);
      error.value = initError;
      return;
    }

    const isRichContent = typeof payload === 'object' && payload !== null;
    const text = isRichContent ? payload.text : payload;
    const images = isRichContent ? payload.images : [];
    const references = isRichContent ? payload.references : [];
    const contentPayload: MessageContentPart[] = [];

    if (text && text.trim()) {
      contentPayload.push({ type: 'text', text: text });
    }

    if (references && references.length > 0) {
      logger.log(`[AgentStore] 正在为 ${references.length} 个引用获取内容...`);
      for (const ref of references) {
        try {
          const logicalPath = (localTools as any)._getLogicalPathFromFrontendPath(ref.path);
          const content = await localTools.readDoc([{ path: logicalPath }]);
          contentPayload.push({
            type: 'doc',
            content: `--- 参考文档: ${logicalPath} ---\n${content}\n--- 文档结束 ---`,
            name: ref.name,
            path: ref.path
          });
        } catch (e) {
            logger.error(`[AgentStore] 获取引用内容失败: ${ref.path}`, e);
            contentPayload.push({
                type: 'doc',
                content: `错误: 加载文档 ${ref.path} 失败`,
                name: ref.name,
                path: ref.path,
                error: true
            });
        }
      }
      logger.log(`[AgentStore] 已向负载添加 ${references.length} 个文档部分。`);
    }

    if (images && images.length > 0) {
      for (const imageUrl of images) {
        contentPayload.push({
          type: 'image_url',
          image_url: { url: imageUrl }
        });
      }
    }
    
    if (contentPayload.length === 0) {
      logger.warn("调用 sendMessage 但负载为空。");
      return;
    }

    await messageManager.addMessage({
      role: 'user',
      content: contentPayload.length === 1 && contentPayload[0].type === 'text'
               ? contentPayload[0].text!
               : contentPayload,
    });
    
    agentService.startTurn();
  }

  async function resetAgent(): Promise<void> {
    logger.log("Agent Store: 重置 Agent... (将开启新会话)");
    if(currentDomain.value) {
        await startNewSession(currentDomain.value, activeRoleId.value[currentDomain.value]);
    }
  }

  function stopAgent() {
    agentService.stopAgent();
  }

  function markAllAsSent(): void {
    if (!currentSession.value) return;
    logger.log(`Agent Store: 正在标记所有消息为已发送。`);
    messageIds.value.forEach(id => {
      const message = messagesById.value[id];
      if (message) {
        (message as any).isSent = true;
      }
    });
  }

  function deleteMessagesFrom(messageId: string): void {
    stopAgent();
    const session = currentSession.value;
    if (!session) return;
    
    const index = session.messageIds.indexOf(messageId);
    if (index === -1) {
      logger.warn(`[AgentStore] 尝试从一个不存在的消息 ID 删除: ${messageId}`);
      return;
    }

    const idsToRemove = session.messageIds.splice(index);
    
    logger.log(`[AgentStore] 正在从 ${messageId} 开始删除 ${idsToRemove.length} 条消息。`);
    for (const id of idsToRemove) {
      delete session.messagesById[id];
    }
  }

  function retryLastTurn(): void {
    if (!currentSession.value) return;
    const lastMessage = orderedMessages.value[orderedMessages.value.length - 1];

    if (lastMessage && lastMessage.type === 'error') {
      logger.log(`[AgentStore] 正在从错误消息 ${lastMessage.id} 重试`);
      messageManager.removeMessage(lastMessage.id);
      agentService.startTurn();
    } else {
      logger.warn(`[AgentStore] 调用重试，但最后一条消息不是可重试的错误。`);
    }
  }


  async function initializeStoreFromCache(): Promise<void> {
    await persistenceManager.initializeStoreFromCache(sessions, activeSessionIds);
    
    // Set up watchers after initialization
    watch(sessions, persistState, { deep: true });
    watch(activeSessionIds, persistState, { deep: true });
  }

  // Expose AgentService getters
  const isProcessing = computed(() => agentService.getIsProcessing());
  const consecutiveToolErrors = computed(() => agentService.getConsecutiveToolErrors());
  const consecutiveAiTurns = computed(() => agentService.getConsecutiveAiTurns());

  return {
    // State
    sessions, activeSessionIds, isLoading, error, logMessages, activeSessionId,
    currentSession, activeAgentName, availableAgents, currentRoleId, messagesById,
    orderedMessages, consecutiveToolErrors, consecutiveAiTurns,
    isProcessing, // Exposed from AgentService
    
    // Actions
    switchDomainContext, fetchAvailableAgents, switchAgent, startNewSession,
    sendMessage, stopAgent, resetAgent,
    // MessageManager actions (proxies)
    addMessage: messageManager.addMessage,
    updateMessage: messageManager.updateMessage,
    removeMessage: messageManager.removeMessage,
    replaceMessage: messageManager.replaceMessage,
    appendMessageContent: messageManager.appendMessageContent,
    markStreamAsCompleted: messageManager.markStreamAsCompleted,
    // SessionManager actions (proxies or direct)
    switchSession, deleteSession, renameSession, startNewChatWithAgent,
    markAllAsSent, deleteMessagesFrom, initializeStoreFromCache,
    markMessageAsRendered(messageId: string) {
      const message = messagesById.value[messageId];
      if (message && message.status === 'rendering') {
        messageManager.updateMessage({
          messageId,
          updates: { status: 'done' }
        });
        agentService.startTurn();
      }
    },
    confirmMessageRendered(messageId: string) {
      const message = messagesById.value[messageId];
      if (message && message.status === 'rendering') {
        messageManager.updateMessage({
          messageId,
          updates: { status: 'done' }
        });
        agentService.startTurn();
      }
    },
    retryLastTurn,
  };
});