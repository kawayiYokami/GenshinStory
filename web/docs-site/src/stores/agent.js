import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { nanoid } from 'nanoid';
import localforage from 'localforage';
import agentService from '@/services/agentService';
import promptService from '@/services/promptService';
import logger, { logs } from '@/services/loggerService';
import { useAppStore } from '@/stores/app';
import localTools from '@/services/localToolsService'; // Import localTools

// --- Localforage an d debounce setup ---
const AGENT_CACHE_VERSION = '2.0'; // Define a cache version
const sessionsStore = localforage.createInstance({ name: 'agentSessions' });
const lastUsedRolesStore = localforage.createInstance({ name: 'lastUsedRoles' });

// --- Cache Cleaning Tool (for emergency recovery) ---
export async function forceClearAgentCache() {
  await sessionsStore.clear();
  await lastUsedRolesStore.clear();
  // The reload is removed to allow for diagnostics without a refresh loop.
  logger.warn('[AgentStore] Cache has been cleared due to outdated or corrupt data.');
}
// Expose to window for easy manual access during development
if (import.meta.env.DEV) {
  window.forceClearAgentCache = forceClearAgentCache;
}
// --- End Cache Cleaning Tool ---

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
  const MAX_SESSIONS_PER_DOMAIN = 10;

  // --- State ---

  const sessions = ref({});
  const activeSessionIds = ref({ gi: null, hsr: null });
  const availableAgents = ref({ gi: [], hsr: [] });
  const activeRoleId = ref({ gi: null, hsr: null });

  const isLoading = ref(false);
  const error = ref(null);
  const logMessages = ref(logs);
  const activeAgentName = ref('AI');

  // --- Internal State ---
  const _isFetchingAgents = ref({ gi: false, hsr: false });

  // --- Safety Net State ---
  const consecutiveToolErrors = ref(0);
  const consecutiveAiTurns = ref(0);

  watch(isLoading, () => {
    // Watcher for reactivity safeguards
  });


  // --- Getters / Computed ---

  const appStore = useAppStore();
  const currentDomain = computed(() => appStore.currentDomain);
  const activeSessionId = computed(() => activeSessionIds.value[currentDomain.value]);
  const currentRoleId = computed(() => activeRoleId.value[currentDomain.value]);
  const currentSession = computed(() => sessions.value[activeSessionId.value] || null);
  
  const messagesById = computed(() => currentSession.value?.messagesById || {});
  const messageIds = computed(() => currentSession.value?.messageIds || []);
  const orderedMessages = computed(() => {
    if (!currentSession.value) return [];
    return messageIds.value.map(id => messagesById.value[id]);
  });


  // --- Actions ---

  async function switchSession(sessionId) {
    const domain = currentDomain.value;
    if (!sessions.value[sessionId] || activeSessionIds.value[domain] === sessionId) return;

    const targetSession = sessions.value[sessionId];
    const targetRoleId = targetSession.roleId;

    if (!targetRoleId) {
      logger.warn(`[AgentStore] Session ${sessionId} has no roleId. Cannot switch.`);
      return;
    }
    
    // Switch the active session ID
    activeSessionIds.value[domain] = sessionId;

    // Update the active role to match the session's role
    activeRoleId.value[domain] = targetRoleId;
    await lastUsedRolesStore.setItem(domain, targetRoleId);
    
    // Update the agent name display
    const agent = availableAgents.value[domain]?.find(a => a.id === targetRoleId);
    if (agent) {
      activeAgentName.value = agent.name;
    }

    logger.log(`[AgentStore] Switched to session ${sessionId} (Agent: ${targetRoleId}).`);
  }
  
  function deleteSession(sessionId) {
    const domain = currentDomain.value;
    if (!sessions.value[sessionId]) return;

    // Avoid deleting the last active session, create a new one instead
    if (activeSessionIds.value[domain] === sessionId) {
      delete sessions.value[sessionId];
      logger.log(`[AgentStore] Deleted active session ${sessionId}. Starting a new one.`);
      startNewSession(domain, currentRoleId.value);
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
  
  async function fetchAvailableAgents(domain) {
    // 1. Prevent concurrent executions
    if (_isFetchingAgents.value[domain]) return activeRoleId.value[domain];
    // If agents are already loaded, we can confidently return the active role ID.
    if (availableAgents.value[domain]?.length > 0) {
      return activeRoleId.value[domain];
    }
    _isFetchingAgents.value[domain] = true;

    try {
      // 2. Try to load the last used role from cache first.
      const cachedRoleId = await lastUsedRolesStore.getItem(domain);
      if (cachedRoleId) {
        activeRoleId.value[domain] = cachedRoleId;
        logger.log(`[AgentStore] Loaded last used role '${cachedRoleId}' for domain '${domain}'.`);
      }

      // 3. Fetch from service
      logger.log(`Agent Store: 正在为域 '${domain}' 获取可用 Agent 列表...`);
      const agents = await promptService.listAvailableAgents(domain);
      availableAgents.value[domain] = agents;

      // 4. If after fetching, there's still no active role ID, set a default.
      if (!activeRoleId.value[domain] && agents && agents.length > 0) {
        const defaultId = agents[0].id;
        activeRoleId.value[domain] = defaultId;
        logger.log(`[AgentStore] No cached role for '${domain}'. Set default agent to '${defaultId}'.`);
        await lastUsedRolesStore.setItem(domain, defaultId);
      }
    } catch (e) {
      logger.error(`Agent Store: 获取 '${domain}' 的 Agent 列表失败:`, e);
    } finally {
      _isFetchingAgents.value[domain] = false;
      // Always return the determined (or pre-existing) active role ID
      return activeRoleId.value[domain];
    }
  }

  async function startNewSession(domain, roleIdToLoad) {
    const roleId = roleIdToLoad || currentRoleId.value;
    if (!roleId) {
      logger.error(`Agent Store: 无法开启新会话，因为没有提供或设置 roleId。`);
      error.value = new Error("无法开启新会话，因为没有选择任何 Agent。");
      return;
    }
    logger.log(`Agent Store: 为域 '${domain}' (角色: ${roleId}) 开启新会话...`);

    // --- Rolling Cleanup Logic ---
    const domainSessions = Object.values(sessions.value).filter(s => s.domain === domain);
    if (domainSessions.length >= MAX_SESSIONS_PER_DOMAIN) {
      domainSessions.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
      const oldestSession = domainSessions[0];
      logger.log(`Agent Store: 会话数量达到上限(${MAX_SESSIONS_PER_DOMAIN})，正在删除最旧的会话: ${oldestSession.id}`);
      delete sessions.value[oldestSession.id];
    }
    // --- End Cleanup Logic ---

    isLoading.value = true;
    error.value = null;
    try {
      // <-- 使用 promptService
      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
      activeAgentName.value = agentName;
      activeRoleId.value[domain] = roleId;
      const newSessionId = `session_${Date.now()}`;
      const newSession = {
        id: newSessionId,
        domain: domain,
        roleId: roleId, // <-- BIND THE AGENT TO THE SESSION
        name: `会话 ${new Date().toLocaleString()}`,
        createdAt: new Date().toISOString(),
        messagesById: {},
        messageIds: [],
      };
      
      sessions.value[newSessionId] = newSession;
      activeSessionIds.value[domain] = newSessionId;

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

  async function switchDomainContext(domain) {
    logger.log(`Agent Store: 切换域上下文至 '${domain}'...`);
    // Ensure we get a valid roleId from the fetch function
    const ensuredRoleId = await fetchAvailableAgents(domain);

    if (!activeSessionIds.value[domain] || !sessions.value[activeSessionIds.value[domain]]) {
      logger.log(`[AgentStore] No active session for '${domain}'. Starting new session with role '${ensuredRoleId}'.`);
      await startNewSession(domain, ensuredRoleId);
    } else {
      // If a session exists, ensure its role is still valid and update the agent name.
      const currentRole = availableAgents.value[domain]?.find(a => a.id === currentRoleId.value);
      if (currentRole) {
        activeAgentName.value = currentRole.name;
      }
      logger.log(`Agent Store: 已激活 '${domain}' 的现有会话 '${activeSessionIds.value[domain]}'。`);
    }
  }

    // This is now for creating a NEW chat with a specific agent
    async function startNewChatWithAgent(roleId) {
      const domain = currentDomain.value;
      if (!roleId) return;
  
      logger.log(`[AgentStore] User requested to start a new chat with agent '${roleId}'.`);
      
      // Logic: If the current session is empty, just transform it. Otherwise, create a new one.
      const session = currentSession.value;
      const isSessionEmpty = !session || session.messageIds.length <= 1; // (only system message)
  
      if (isSessionEmpty && session) {
        logger.log(`[AgentStore] Current session is empty. Transforming it for new agent.`);
        isLoading.value = true;
        // 1. Stop any ongoing activity
        stopAgent();
        // 2. Load the new prompt
        const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
        // 3. Clear existing messages (should just be the old system prompt)
        session.messagesById = {};
        session.messageIds = [];
        // 4. Add the new system message
        addMessage({ role: 'system', content: systemPrompt, type: 'system' });
        // 5. Update session and active state
        session.roleId = roleId;
        activeRoleId.value[domain] = roleId;
        activeAgentName.value = agentName;
        await lastUsedRolesStore.setItem(domain, roleId);
        logger.log(`[AgentStore] Session ${session.id} transformed for agent ${roleId}.`);
        isLoading.value = false;
      } else {
        logger.log(`[AgentStore] Current session is not empty. Starting a new session.`);
        await startNewSession(domain, roleId);
      }
    }
  
    // Legacy function, now just an alias for clarity.
    async function switchAgent(roleId) {
      await startNewChatWithAgent(roleId);
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

  async function sendMessage(payload) {
    if (!currentSession.value) {
      const initError = "没有激活的会话。";
      logger.error(initError);
      error.value = initError;
      return;
    }

    // Adapt to handle both rich content object {text, ...} and simple strings
    const isRichContent = typeof payload === 'object' && payload !== null;
    const text = isRichContent ? payload.text : payload; // Handles both cases
    const images = isRichContent ? payload.images : [];
    const references = isRichContent ? payload.references : [];

    const contentPayload = [];

    // 1. Add text part if it exists
    if (text && text.trim()) {
      contentPayload.push({
        type: 'text',
        text: text
      });
    }

    // 2. Fetch and add references as structured 'doc' parts
    if (references && references.length > 0) {
      logger.log(`[AgentStore] Fetching content for ${references.length} references...`);
      for (const ref of references) {
        try {
          const logicalPath = localTools._getLogicalPathFromFrontendPath(ref.path);
          const content = await localTools.readDoc([{ path: logicalPath }]); // readDoc expects an array
          
          contentPayload.push({
            type: 'doc',
            content: `--- 参考文档: ${logicalPath} ---\n${content}\n--- 文档结束 ---`,
            name: ref.name,
            path: ref.path // Keep original path for UI linking
          });

        } catch (e) {
            logger.error(`[AgentStore] Failed to fetch content for reference: ${ref.path}`, e);
            // Add a placeholder to the UI to show that it failed
            contentPayload.push({
                type: 'doc',
                content: `Error: Failed to load document ${ref.path}`,
                name: ref.name,
                path: ref.path,
                error: true
            });
        }
      }
      logger.log(`[AgentStore] Added ${references.length} doc parts to payload.`);
    }

    // 3. Add image parts if they exist
    if (images && images.length > 0) {
      for (const imageUrl of images) {
        contentPayload.push({
          type: 'image_url',
          image_url: {
            url: imageUrl
          }
        });
      }
    }
    
    if (contentPayload.length === 0) {
      logger.warn("sendMessage called with empty payload.");
      return;
    }

    addMessage({
      role: 'user',
      // If there's only a single text part, keep content as a simple string for backward compatibility.
      // Otherwise, use the array payload for multimodal content.
      content: contentPayload.length === 1 && contentPayload[0].type === 'text'
               ? contentPayload[0].text
               : contentPayload,
    });
    
    agentService.startTurn();
  }

  function stopAgent() {
      agentService.stop();
      logger.log("Agent Store: 已触发停止。");
  }

  async function resetAgent() {
    logger.log("Agent Store: 重置 Agent... (将开启新会话)");
    await startNewSession(currentDomain.value);
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

  function retryLastTurn() {
    if (!currentSession.value) return;

    // 1. Get the last message
    const lastMessage = orderedMessages.value[orderedMessages.value.length - 1];

    // 2. Validate it's a retryable error message
    if (lastMessage && lastMessage.type === 'error') {
      logger.log(`[AgentStore] Retrying from error message ${lastMessage.id}`);
      
      // 3. Remove the error message
      removeMessage(lastMessage.id);
      
      // 4. Restart the agent's turn. The service will pick up the history.
      agentService.startTurn();

    } else {
      logger.warn(`[AgentStore] Retry called, but the last message was not a retryable error.`);
    }
  }

  // --- Persistence ---
  const persistState = debounce(async () => {
    try {
      const stateToPersist = {
        version: AGENT_CACHE_VERSION,
        data: {
          sessions: JSON.parse(JSON.stringify(sessions.value)),
          activeSessionIds: JSON.parse(JSON.stringify(activeSessionIds.value)),
        }
      };
      await sessionsStore.setItem('state', stateToPersist);
      logger.log(`[AgentStore] Session state persisted (v${AGENT_CACHE_VERSION}).`);
    } catch (e) {
      logger.error('[AgentStore] Failed to persist state:', e);
    }
  }, 1000);

  async function initializeStoreFromCache() {
    try {
      logger.log('[AgentStore] Initializing store from cache...');
      const cachedState = await sessionsStore.getItem('state');
      
      // --- Diagnostic & Auto-Healing ---
      if (!cachedState || cachedState.version !== AGENT_CACHE_VERSION) {
        logger.error(`[AgentStore] Outdated or corrupt cache detected. Clearing cache and starting fresh.`, {
            foundVersion: cachedState?.version,
            expectedVersion: AGENT_CACHE_VERSION,
            invalidData: cachedState
        });
        await forceClearAgentCache();
        
        // Gracefully degrade: initialize with clean state and continue
        sessions.value = {};
        activeSessionIds.value = { gi: null, hsr: null };

      } else {
        // --- Cache is valid, proceed with loading ---
        const { sessions: cachedSessions, activeSessionIds: cachedActiveIds } = cachedState.data;

        // Add extra validation for restored data
        sessions.value = (typeof cachedSessions === 'object' && cachedSessions !== null) ? cachedSessions : {};
        logger.log(`[AgentStore] Restored ${Object.keys(sessions.value).length} sessions.`);
        
        const defaultIds = { gi: null, hsr: null };
        activeSessionIds.value = (typeof cachedActiveIds === 'object' && cachedActiveIds !== null)
                                 ? { ...defaultIds, ...cachedActiveIds }
                                 : defaultIds;
        logger.log('[AgentStore] Restored active session IDs.');
      }
      
      // Set up watchers to persist state AFTER initialization is complete
      watch(sessions, persistState, { deep: true });
      watch(activeSessionIds, persistState, { deep: true });

    } catch (e) {
      logger.error('[AgentStore] Critical error during cache initialization. Clearing cache and starting fresh.', e);
      await forceClearAgentCache();
      // Ensure state is clean after a critical failure
      sessions.value = {};
      activeSessionIds.value = { gi: null, hsr: null };
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
    switchDomainContext,
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
    startNewChatWithAgent,
    retryLastTurn,
  };
});