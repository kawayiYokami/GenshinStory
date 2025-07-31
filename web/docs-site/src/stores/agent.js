import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { nanoid } from 'nanoid';
import localforage from 'localforage';
import agentService from '@/services/agentService';
import promptService from '@/services/promptService';
import logger, { logs } from '@/services/loggerService';
import { useAppStore } from '@/stores/app';

// --- Localforage an d debounce setup ---
const sessionsStore = localforage.createInstance({ name: 'agentSessions' });

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export const useAgentStore = defineStore('agent', () => {
  const MAX_SESSIONS_PER_GAME = 10;

  // --- State ---

  const sessions = ref({});
  const activeSessionIds = ref({ gi: null, hsr: null });
  const availableAgents = ref({ gi: [], hsr: [] });
  const activeRoleId = ref({ gi: null, hsr: null });

  const isLoading = ref(false);
  const error = ref(null);
  const logMessages = ref(logs);
  const activeAgentName = ref('AI');

  // --- Safety Net State ---
  const consecutiveToolErrors = ref(0);
  const consecutiveAiTurns = ref(0);

  watch(isLoading, () => {
    // Watcher for reactivity safeguards
  });


  // --- Getters / Computed ---

  const appStore = useAppStore();
  const currentGame = computed(() => appStore.currentGame);
  const activeSessionId = computed(() => activeSessionIds.value[currentGame.value]);
  const currentRoleId = computed(() => activeRoleId.value[currentGame.value]);
  const currentSession = computed(() => sessions.value[activeSessionId.value] || null);
  
  const messagesById = computed(() => currentSession.value?.messagesById || {});
  const messageIds = computed(() => currentSession.value?.messageIds || []);
  const orderedMessages = computed(() => {
    if (!currentSession.value) return [];
    return messageIds.value.map(id => messagesById.value[id]);
  });


  // --- Actions ---

  function switchSession(sessionId) {
    const game = currentGame.value;
    if (sessions.value[sessionId] && activeSessionIds.value[game] !== sessionId) {
      activeSessionIds.value[game] = sessionId;
      logger.log(`[AgentStore] Switched to session ${sessionId}`);
    }
  }
  
  function deleteSession(sessionId) {
    const game = currentGame.value;
    if (!sessions.value[sessionId]) return;

    // Avoid deleting the last active session, create a new one instead
    if (activeSessionIds.value[game] === sessionId) {
      delete sessions.value[sessionId];
      logger.log(`[AgentStore] Deleted active session ${sessionId}. Starting a new one.`);
      startNewSession(game, currentRoleId.value);
    } else {
      delete sessions.value[sessionId];
      logger.log(`[AgentStore] Deleted session ${sessionId}.`);
    }
  }

  function renameSession(sessionId, newName) {
    if (sessions.value[sessionId]) {
      sessions.value[sessionId].name = newName;
      logger.log(`[AgentStore] Renamed session ${sessionId} to "${newName}"`);
    }
  }
  
  async function fetchAvailableAgents(game) {
    if (availableAgents.value[game]?.length > 0) {
      logger.log(`Agent Store: '${game}' 的 Agent 列表已存在，跳过获取。`);
      return;
    }
    try {
      logger.log(`Agent Store: 正在为游戏 '${game}' 获取可用 Agent 列表...`);
      // <-- 使用 promptService
      const agents = await promptService.listAvailableAgents(game);
      availableAgents.value[game] = agents;
      if (agents.length > 0 && !activeRoleId.value[game]) {
        const defaultRoles = {
          gi: 'gi_role',
          hsr: 'hsr_herta_role'
        };
        const defaultId = defaultRoles[game] || agents[0]?.id;
        activeRoleId.value[game] = defaultId;
        logger.log(`Agent Store: 已为 '${game}' 设置默认 Agent: ${defaultId}`);
      }
    } catch (e) {
      logger.error(`Agent Store: 获取 '${game}' 的 Agent 列表失败:`, e);
    }
  }

  async function startNewSession(game, roleIdToLoad) {
    const roleId = roleIdToLoad || currentRoleId.value;
    if (!roleId) {
      logger.error(`Agent Store: 无法开启新会话，因为没有提供或设置 roleId。`);
      error.value = new Error("无法开启新会话，因为没有选择任何 Agent。");
      return;
    }
    logger.log(`Agent Store: 为游戏 '${game}' (角色: ${roleId}) 开启新会话...`);

    // --- Rolling Cleanup Logic ---
    const gameSessions = Object.values(sessions.value).filter(s => s.game === game);
    if (gameSessions.length >= MAX_SESSIONS_PER_GAME) {
      gameSessions.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
      const oldestSession = gameSessions[0];
      logger.log(`Agent Store: 会话数量达到上限(${MAX_SESSIONS_PER_GAME})，正在删除最旧的会话: ${oldestSession.id}`);
      delete sessions.value[oldestSession.id];
    }
    // --- End Cleanup Logic ---

    isLoading.value = true;
    error.value = null;
    try {
      // <-- 使用 promptService
      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(roleId);
      activeAgentName.value = agentName;
      activeRoleId.value[game] = roleId;
      const newSessionId = `session_${Date.now()}`;
      const newSession = {
        id: newSessionId,
        game: game,
        name: `会话 ${new Date().toLocaleString()}`,
        createdAt: new Date().toISOString(),
        messagesById: {},
        messageIds: [],
      };
      
      sessions.value[newSessionId] = newSession;
      activeSessionIds.value[game] = newSessionId;

      addMessage({
        role: 'system',
        content: systemPrompt,
        type: 'system',
      });
      logger.log(`Agent Store: 新会话 '${newSessionId}' 已创建并激活。`);

    } catch (e) {
      error.value = e;
      logger.error("Agent Store: 开启新会话失败:", e);
    } finally {
      isLoading.value = false;
    }
  }

  async function switchGameContext(game) {
    logger.log(`Agent Store: 切换游戏上下文至 '${game}'...`);
    await fetchAvailableAgents(game);
    if (!activeSessionIds.value[game] || !sessions.value[activeSessionIds.value[game]]) {
      await startNewSession(game, activeRoleId.value[game]);
    } else {
      const currentRole = availableAgents.value[game]?.find(a => a.id === currentRoleId.value);
      if (currentRole) {
        activeAgentName.value = currentRole.name;
      }
      logger.log(`Agent Store: 已激活 '${game}' 的现有会话 '${activeSessionIds.value[game]}'。`);
    }
  }

  async function switchAgent(roleId) {
    if (!roleId || currentRoleId.value === roleId) return;
    logger.log(`Agent Store: 正在切换 Agent 至 '${roleId}'...`);
    await startNewSession(currentGame.value, roleId);
  }

  // --- New Atomic Actions ---
  function addMessage(messageData) {
    if (!currentSession.value) return null;
    
    const id = messageData.id || nanoid();
    const message = {
      id,
      type: 'text',
      ...messageData,
    };

    currentSession.value.messagesById[id] = message;
    currentSession.value.messageIds.push(id);
    return message;
  }

  function updateMessage({ messageId, updates }) {
    const message = currentSession.value?.messagesById?.[messageId];
    if (message) {
      Object.assign(message, updates);
    }
  }

  function removeMessage(messageId) {
    const session = currentSession.value;
    if (!session || !session.messagesById[messageId]) return;

    const index = session.messageIds.indexOf(messageId);
    if (index > -1) {
      session.messageIds.splice(index, 1);
    }

    delete session.messagesById[messageId];
  }

  function replaceMessage(oldId, newMessageData) {
    const session = currentSession.value;
    if (!session || !session.messagesById[oldId]) return;

    const index = session.messageIds.indexOf(oldId);
    if (index === -1) return;

    const newId = newMessageData.id || nanoid();
    const message = { ...newMessageData, id: newId };

    delete session.messagesById[oldId];
    session.messagesById[newId] = message;

    session.messageIds.splice(index, 1, newId);
  }

  function appendMessageContent({ messageId, chunk }) {
    const session = currentSession.value;
    if (!session) return;

    const message = session.messagesById[messageId];
    if (message) {
      session.messagesById[messageId] = {
        ...message,
        content: (message.content || '') + chunk,
      };
    }
  }

  function markStreamAsCompleted({ messageId }) {
    const message = currentSession.value?.messagesById?.[messageId];
    if (message) {
      message.streamCompleted = true;
    }
  }

  async function sendMessage(userMessageContent) {
    if (!currentSession.value) {
      const initError = "没有激活的会话。";
      logger.error(initError);
      error.value = initError;
      return;
    }

    addMessage({
      role: 'user',
      content: userMessageContent,
      type: 'text'
    });
    
    agentService.startTurn();
  }

  function stopAgent() {
      agentService.stop();
      logger.log("Agent Store: 已触发停止。");
  }

  async function resetAgent() {
    logger.log("Agent Store: 重置 Agent... (将开启新会话)");
    await startNewSession(currentGame.value);
  }

  // --- Safety Net Actions ---
  function incrementToolErrors() {
    consecutiveToolErrors.value++;
  }
  function resetToolErrors() {
    consecutiveToolErrors.value = 0;
  }
  function incrementAiTurns() {
    consecutiveAiTurns.value++;
  }
  function resetCounters() {
    consecutiveToolErrors.value = 0;
    consecutiveAiTurns.value = 0;
  }

  function markAllAsSent() {
    if (!currentSession.value) return;
    
    logger.log(`Agent Store: Marking all messages as sent.`);
    messageIds.value.forEach(id => {
      const message = messagesById.value[id];
      if (message) {
        message.isSent = true;
      }
    });
  }

  function deleteMessagesFrom(messageId) {
    // 1. Stop any ongoing AI activity immediately.
    stopAgent();

    const session = currentSession.value;
    if (!session) return;
    
    const index = session.messageIds.indexOf(messageId);
    if (index === -1) {
      logger.warn(`[AgentStore] Tried to delete from a non-existent message ID: ${messageId}`);
      return;
    }

    // 2. Truncate the history
    const idsToRemove = session.messageIds.splice(index);
    
    // 3. Clean up the lookup map
    logger.log(`[AgentStore] Deleting ${idsToRemove.length} messages starting from ${messageId}.`);
    for (const id of idsToRemove) {
      delete session.messagesById[id];
    }
  }

  // --- Persistence ---
  const persistState = debounce(async () => {
    try {
      await sessionsStore.setItem('sessions', JSON.parse(JSON.stringify(sessions.value)));
      await sessionsStore.setItem('activeSessionIds', JSON.parse(JSON.stringify(activeSessionIds.value)));
      logger.log('[AgentStore] Session state persisted.');
    } catch (e) {
      logger.error('[AgentStore] Failed to persist state:', e);
    }
  }, 1000);

  async function initializeStoreFromCache() {
    try {
      logger.log('[AgentStore] Initializing store from cache...');
      const cachedSessions = await sessionsStore.getItem('sessions');
      const cachedActiveIds = await sessionsStore.getItem('activeSessionIds');

      if (cachedSessions) {
        sessions.value = cachedSessions;
        logger.log(`[AgentStore] Restored ${Object.keys(cachedSessions).length} sessions.`);
      }
      if (cachedActiveIds) {
        activeSessionIds.value = cachedActiveIds;
        logger.log('[AgentStore] Restored active session IDs.');
      }
      
      // Set up watchers to persist state after initial load
      watch(sessions, persistState, { deep: true });
      watch(activeSessionIds, persistState, { deep: true });

    } catch (e) {
      logger.error('[AgentStore] Failed to initialize from cache:', e);
    }
  }

  return {
    sessions,
    activeSessionIds,
    isLoading,
    error,
    logMessages,
    activeSessionId,
    currentSession,
    activeAgentName,
    availableAgents,
    currentRoleId,
    messagesById,
    orderedMessages,
    consecutiveToolErrors,
    consecutiveAiTurns,
    switchGameContext,
    fetchAvailableAgents,
    switchAgent,
    startNewSession,
    sendMessage,
    stopAgent,
    resetAgent,
    addMessage,
    updateMessage,
    removeMessage,
    replaceMessage,
    appendMessageContent,
    markStreamAsCompleted,
    incrementToolErrors,
    resetToolErrors,
    incrementAiTurns,
    resetCounters,
    markAllAsSent,
    deleteMessagesFrom,
    // New actions
    initializeStoreFromCache,
    switchSession,
    deleteSession,
    renameSession,
  };
});