/**
 * @fileoverview Agent Store 模块
 * @description 智能代理系统的核心状态管理模块，负责管理会话、消息和代理状态
 * @author yokami
 */

// 引入Vue和Pinia核心功能
import { ref, computed, watch, nextTick } from 'vue';
import { defineStore, storeToRefs } from 'pinia';
import { nanoid } from 'nanoid';
import logger, { logs } from '@/features/app/services/loggerService';
import { useAppStore } from '@/features/app/stores/app';
import localTools from '../tools/implementations/localToolsService';
import type { Ref } from 'vue';
import type { LogEntry } from '@/features/app/services/loggerService';
import { useConfigStore } from '@/features/app/stores/config';
import type { MessageContentPart, Message, Session, AgentInfo, Command } from '../types';


// --- 导入管理器和服务模块 ---
import { MessageManagerImpl } from './messageManager';
import { SessionManagerImpl, type SessionManager } from '../state/sessionManager';
import { PersistenceManagerImpl, sessionsStore, lastUsedRolesStore, forceClearAgentCache } from './persistence';
import promptService from '../tools/implementations/promptService';
import { AgentService } from '../engine/agentService';
import contextOptimizerService from '../context/contextOptimizerService';

// --- 导入类型定义 ---

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
  const activeInstructionId = ref('chat'); // 默认闲聊模式
  const isLoading = ref(false);
  const isCompressing = ref(false);
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
  const currentInstructionId = computed(() => activeInstructionId.value);
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
  const persistState = persistenceManager.persistState(sessions, activeSessionIds, activeInstructionId);

  // --- Original Store Actions (refactored to use managers/services) ---
  /**
   * 切换到指定会话
   * @description 切换到指定ID的会话，加载会话数据
   * @param {string} sessionId 要切换到的会话ID
   * @return {Promise<void>}
   */
  async function switchSession(sessionId: string): Promise<void> {
    // 在切换会话前先停止当前正在进行的请求
    await stopAgent();

    await sessionManager.switchSession(sessionId, currentDomain.value);
  }

  /**
   * 删除指定会话
   * @description 删除指定ID的会话，如果删除的是当前会话则创建新会话
   * @param {string} sessionId 要删除的会话ID
   */
  function deleteSession(sessionId: string): void {
    sessionManager.deleteSession(sessionId, currentDomain.value, startNewSession);
  }

  /**
   * 重命名会话
   * @description 修改指定会话的名称
   * @param {string} sessionId 要重命名的会话ID
   * @param {string} newName 新的会话名称
   */
  function renameSession(sessionId: string, newName: string): void {
    sessionManager.renameSession(sessionId, newName);
  }

  /**
   * 获取指定域的可用代理列表
   * @description 从服务器获取指定域的可用代理列表，包含缓存机制
   * @param {string} domain 域名
   * @return {Promise<string | null>} 当前激活的角色ID
   * @throws {Error} 当获取代理列表失败时抛出异常
   */
  async function fetchAvailableAgents(domain: string, force = false): Promise<string | null> {
    if (!force && (_isFetchingAgents.value[domain] || availableAgents.value[domain]?.length > 0)) {
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

  /**
   * 刷新当前域的可用代理列表
   */
  async function refreshAvailableAgents(): Promise<void> {
    const domain = currentDomain.value;
    if (domain) {
      await fetchAvailableAgents(domain, true);
    }
  }

  /**
   * 创建新会话
   * @description 在指定域中创建新的聊天会话，加载系统提示词
   * @param {string} domain 域名
   * @param {string | null} roleIdToLoad 要加载的角色ID
   * @return {Promise<void>}
   * @throws {Error} 当创建会话失败时抛出异常
   */
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
        const { systemPrompt } = await promptService.loadSystemPrompt(domain, newSession.roleId, activeInstructionId.value);
        await messageManager.addMessage({
          role: 'system',
          content: systemPrompt,
          type: 'system',
        });
      }
    }
  }

  /**
   * 使用当前智能体开启新会话
   * @description 便利方法：自动获取当前域和角色，创建新会话
   * @return {Promise<void>}
   * @throws {Error} 当没有激活域时抛出异常
   */
  async function startNewSessionWithCurrentAgent(): Promise<void> {
    const domain = currentDomain.value;
    const roleId = currentRoleId.value;
    if (!domain) {
      throw new Error('当前没有激活的域，无法开启新会话');
    }
    await startNewSession(domain, roleId);
  }

  /**
   * 使用当前智能体开启新聊天
   * @description 便利方法：自动获取当前角色，开启新聊天（用于压缩后）
   * @return {Promise<string>} 返回系统提示词
   * @throws {Error} 当没有激活角色时抛出异常
   */
  async function startNewChatWithCurrentAgent(): Promise<string> {
    const roleId = currentRoleId.value;
    if (!roleId) {
      throw new Error('当前没有激活的角色，无法开启新聊天');
    }

    // 获取系统提示词
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
      return systemPrompt;
    }

    // 如果没有系统提示词，创建新会话并返回默认系统提示词
    await startNewSession(currentDomain.value!, roleId);
    const { systemPrompt: defaultPrompt } = await promptService.loadSystemPrompt(currentDomain.value!, roleId, activeInstructionId.value);
    return defaultPrompt;
  }

  /**
   * 切换域上下文
   * @description 切换到指定域，加载对应的代理和会话数据
   * @param {string} domain 要切换到的域名
   * @return {Promise<void>}
   * @throws {Error} 当切换域失败时抛出异常
   */
  async function switchDomainContext(domain: string): Promise<void> {
    // 在切换域前先停止当前正在进行的请求
    await stopAgent();

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
          const { systemPrompt } = await promptService.loadSystemPrompt(domain, roleId, activeInstructionId.value);
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

  /**
   * 发送消息到当前会话
   * @description 处理文本、图片和引用文档，构建消息内容并发送
   * @param {string | { text: string; images?: string[]; references?: any[] }} payload 消息负载，可以是纯文本或包含图片和引用的复合内容
   * @return {Promise<void>}
   * @throws {Error} 当发送消息失败时抛出异常
   */
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

  /**
   * 重置代理
   * @description 停止当前会话并创建新的会话
   * @return {Promise<void>}
   */
  async function resetAgent(): Promise<void> {
    logger.log("Agent Store: 重置 Agent... (将开启新会话)");

    // 在重置前先停止当前正在进行的请求
    await stopAgent();

    if(currentDomain.value) {
        await startNewSession(currentDomain.value, activeRoleId.value[currentDomain.value]);
    }
  }

  async function setInstruction(instructionId: string) {
    activeInstructionId.value = instructionId;
    await updateCurrentSessionSystemPrompt();
  }

  async function updateCurrentSessionSystemPrompt(): Promise<void> {
    const domain = currentDomain.value;
    const session = currentSession.value;
    if (!domain || !session || !session.roleId) return;

    try {
      const { systemPrompt } = await promptService.loadSystemPrompt(domain, session.roleId, activeInstructionId.value);

      // Find the first system message
      const firstMessageId = session.messageIds[0];
      if (firstMessageId) {
        const firstMessage = session.messagesById[firstMessageId];
        if (firstMessage && firstMessage.role === 'system') {
          await messageManager.updateMessage({ messageId: firstMessageId, updates: { content: systemPrompt } });
          logger.log(`[AgentStore] 已更新会话 ${session.id} 的系统提示词 (指令: ${activeInstructionId.value})`);
        }
      }
    } catch (e) {
      logger.error(`[AgentStore] 更新系统提示词失败:`, e);
    }
  }

  /**
   * 压缩上下文并开启新对话
   * @description 压缩当前对话内容并创建新的会话，以压缩内容作为首条消息
   * @return {Promise<void>}
   */
  async function compressAndStartNewChat(): Promise<void> {
    if (!orderedMessages.value || orderedMessages.value.length === 0) {
      logger.error("[AgentStore] 压缩上下文失败：没有可压缩的消息");
      return;
    }

    // 设置压缩状态
    isCompressing.value = true;
    await stopAgent(); // 停止当前对话

    try {
      logger.log("[AgentStore] 开始压缩上下文...");

      // 使用原有的AI压缩服务强制压缩消息（不管是否超限）
      const configStore = useConfigStore();
      const { activeConfig } = storeToRefs(configStore);
      const maxContextLength = activeConfig.value?.maxContextLength || 128000;

      // 强制进行压缩，不检查阈值
      const result = await contextOptimizerService.processContext(orderedMessages.value, maxContextLength);

      // 如果没有压缩（因为上下文未超限），强制进行摘要
      if (result.status === 'SUCCESS' && result.history === orderedMessages.value) {
        logger.log("[AgentStore] 强制压缩：即使未超限也进行摘要");
        // 手动调用摘要功能
        const systemPrompt = orderedMessages.value.find(m => m.role === 'system');
        const chatHistory = orderedMessages.value.filter(m => m.role !== 'system');

        const summary = await contextOptimizerService['_summarizeHistory'](chatHistory);
        const summaryMessage: Message = {
          role: 'user',
          content: `[系统摘要] ${summary}`,
          id: `msg_${Date.now()}`,
          createdAt: new Date().toISOString(),
          type: 'compression_summary',
          isCompressed: true
        };

        const compressedMessages = [systemPrompt!, summaryMessage].filter(Boolean) as Message[];

        // 创建新会话
        if (!currentRoleId.value) {
          logger.error("[AgentStore] 压缩失败：当前没有激活的角色");
          return;
        }

        await startNewChatWithCurrentAgent();

        // 将压缩后的消息添加到新会话中
        for (const message of compressedMessages) {
          if (message.role !== 'system') { // 系统消息会自动添加
            await messageManager.addMessage(message);
          }
        }
      } else if (result.status === 'SUCCESS') {
        // 正常的压缩结果
        const compressedMessages = result.history!;

        // 创建新会话
        if (!currentRoleId.value) {
          logger.error("[AgentStore] 压缩失败：当前没有激活的角色");
          return;
        }

        await startNewChatWithCurrentAgent();

        // 将压缩后的消息添加到新会话中
        for (const message of compressedMessages) {
          if (message.role !== 'system') { // 系统消息会自动添加
            await messageManager.addMessage(message);
          }
        }
      } else {
        logger.error(`[AgentStore] 压缩失败: ${result.userMessage}`);
        throw new Error(result.userMessage || '压缩失败');
      }

      logger.log("[AgentStore] 上下文压缩完成，已开启新对话");
    } catch (error) {
      logger.error("[AgentStore] 压缩上下文失败:", error);
      throw error;
    } finally {
      // 无论成功失败都要重置压缩状态
      isCompressing.value = false;
    }
  }

  async function stopAgent() {
    await agentService.stopAgent();
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

  async function deleteMessagesFrom(messageId: string): Promise<void> {
    await stopAgent();
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
    await persistenceManager.initializeStoreFromCache(sessions, activeSessionIds, activeInstructionId);

    // Set up watchers after initialization
    watch(sessions, persistState, { deep: true });
    watch(activeSessionIds, persistState, { deep: true });
    watch(activeInstructionId, persistState, { deep: true });
  }

  // Expose AgentService getters
  const isProcessing = computed(() => agentService.getIsProcessing());
  const consecutiveAiTurns = computed(() => agentService.getConsecutiveAiTurns());

  return {
    // State
    sessions, activeSessionIds, isLoading, isCompressing, error, logMessages, activeSessionId,
    currentSession, activeAgentName, availableAgents, currentRoleId, messagesById,
    orderedMessages, consecutiveAiTurns, currentInstructionId,
    isProcessing, // Exposed from AgentService

    // Actions
    switchDomainContext, fetchAvailableAgents, refreshAvailableAgents, switchAgent, startNewSession,
    sendMessage, stopAgent, resetAgent, compressAndStartNewChat, setInstruction,
    // MessageManager actions (proxies)
    addMessage: messageManager.addMessage,
    updateMessage: messageManager.updateMessage,
    removeMessage: messageManager.removeMessage,
    replaceMessage: messageManager.replaceMessage,
    appendMessageContent: messageManager.appendMessageContent,
    markStreamAsCompleted: messageManager.markStreamAsCompleted,
    // SessionManager actions (proxies or direct)
    switchSession, deleteSession, renameSession, startNewChatWithAgent, startNewSessionWithCurrentAgent, startNewChatWithCurrentAgent,
    markAllAsSent, deleteMessagesFrom, initializeStoreFromCache,
    // SessionManager utility methods
    isSessionEmpty: (session: Session | null) => sessionManager.isSessionEmpty(session),
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