import { defineStore, storeToRefs } from 'pinia';
import { ref, computed, watch, nextTick } from 'vue';
import { nanoid } from 'nanoid';
import localforage from 'localforage';
import promptService from '@/services/promptService';
import logger, { logs } from '@/services/loggerService';
import { useAppStore } from '@/stores/app';
import localTools from '@/services/localToolsService';
import type { Ref } from 'vue';
import type { LogEntry } from '@/services/loggerService';
import { useConfigStore } from '@/stores/config';
import openaiService from '@/services/openaiService';
import { createPacedStream } from '@/services/streamingService';
import contextOptimizerService from '@/services/contextOptimizerService';
import toolParserService from '@/services/toolParserService';

// --- 类型定义 ---
export interface MessageContentPart {
    type: 'text' | 'image_url' | 'doc';
    text?: string;
    image_url?: { url: string };
    content?: string; // for doc
    name?: string; // for doc
    path?: string; // for doc
    error?: boolean; // for doc
}

export interface Message {
    id: string;
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | MessageContentPart[];
    type?: 'text' | 'error' | 'tool_status' | 'tool_result' | 'system';
    status?: 'streaming' | 'done' | 'error';
    streamCompleted?: boolean;
    is_hidden?: boolean;
    name?: string; // for tool role
    tool_calls?: any[];
    question?: {
        text: string;
        suggestions: string[];
    };
}

export interface Session {
    id: string;
    domain: string;
    roleId: string;
    name: string;
    createdAt: string;
    messagesById: { [key: string]: Message };
    messageIds: string[];
}

export interface AgentInfo {
    id: string;
    name: string;
    description: string;
}

interface Command {
    type: 'CALL_AI' | 'EXECUTE_TOOL';
    payload?: any;
}

// --- Localforage 和 debounce 设置 ---
const AGENT_CACHE_VERSION = '2.0';
const sessionsStore = localforage.createInstance({ name: 'agentSessions' });
const lastUsedRolesStore = localforage.createInstance({ name: 'lastUsedRoles' });

export async function forceClearAgentCache(): Promise<void> {
  await sessionsStore.clear();
  await lastUsedRolesStore.clear();
  logger.warn('[AgentStore] 缓存因数据过时或损坏已被清除。');
}
if (import.meta.env.DEV) {
  (window as any).forceClearAgentCache = forceClearAgentCache;
}

function debounce(func: (...args: any[]) => void, wait: number) {
  let timeout: number;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = window.setTimeout(later, wait);
  };
}

export const useAgentStore = defineStore('agent', () => {
  const MAX_SESSIONS_PER_DOMAIN = 10;

  // --- AgentService State ---
  const commandQueue = ref<Command[]>([]);
  const isProcessing = ref(false);
  let abortController: AbortController | null = null;

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
  const consecutiveToolErrors = ref(0);
  const consecutiveAiTurns = ref(0);

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

  // --- AgentService Logic (as actions) ---

  function stop() {
    if (abortController) {
        abortController.abort();
        logger.log("Agent: 请求被用户中止。");
    }
  }

  function startTurn() {
    _initiateAiTurn();
  }

  function _initiateAiTurn() {
    abortController = new AbortController();
    commandQueue.value.push({ type: 'CALL_AI' });
    if (!isProcessing.value) {
        processQueue();
    }
  }

  async function processQueue() {
    isProcessing.value = true;
    isLoading.value = true;
    resetCounters();

    while (commandQueue.value.length > 0) {
        if (abortController?.signal.aborted) {
            logger.log("命令队列处理被中止。");
            commandQueue.value = [];
            break;
        }
        
        const command = commandQueue.value.shift();
        if (!command) continue;

        logger.log("正在处理命令:", command);

        try {
            if (command.type === 'CALL_AI') {
                if (consecutiveAiTurns.value >= 10) {
                    logger.error("已达到 AI 回合上限。正在中止。");
                    await addMessage({ role: 'assistant', type: 'error', content: "AI已连续迭代10次，为防止失控，已自动中断。" });
                    break;
                }
                await _handleApiCall();
            } else if (command.type === 'EXECUTE_TOOL') {
                await _handleToolExecution(command.payload);
            }
        } catch (err: any) {
             if (err.name !== 'AbortError') {
                logger.error("处理命令时出错:", { command, error: err });
                await addMessage({ role: 'assistant', type: 'error', content: `处理命令'${command.type}'时出错: ${err.message}` });
            } else {
                logger.log("命令处理在执行期间被中止。");
            }
            commandQueue.value = [];
            break;
        }
    }

    isProcessing.value = false;
    isLoading.value = false;
    abortController = null;
    logger.log("命令队列处理完成。");
  }

  async function _handleApiCall() {
    let assistantMessage: Message | null = null;
    const { response } = await _callApi(orderedMessages.value);

    if (configStore.activeConfig?.stream) {
        assistantMessage = await _handleStream(response);
    } else {
        const responseData = response;
        logger.log("Agent: 收到 API 响应 (非流式):", responseData);
        const message = responseData.choices[0].message;

        const placeholderMessage = await addMessage({
            role: 'assistant',
            content: '',
            type: 'text',
            status: 'streaming'
        });
        
        if (placeholderMessage) {
            await updateMessage({
                messageId: placeholderMessage.id,
                updates: {
                    content: message.content,
                    status: 'done',
                    streamCompleted: true
                }
            });
            assistantMessage = messagesById.value[placeholderMessage.id];
        }
    }
    
    if (!assistantMessage || !assistantMessage.id) {
        throw new Error("AI 未返回任何有效数据。");
    }

    const updatedMessage = messagesById.value[assistantMessage.id];
    const content = typeof updatedMessage.content === 'string' ? updatedMessage.content :
                   Array.isArray(updatedMessage.content) ? updatedMessage.content.map(c => c.text).join('') : '';
    const finalContent = _removePartialXmlTags(content);
    logger.log(`[LOG] _handleApiCall: Final stream content for message ${assistantMessage.id}`, { finalContent });
    
    await updateMessage({
        messageId: assistantMessage.id,
        updates: { status: 'done' }
    });

    const parsedQuestion = toolParserService.parseAskQuestionCall(finalContent);
    if (parsedQuestion) {
        logger.log("Agent: 在流结束后发现 <ask_question> 指令。", parsedQuestion);
        const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
        await updateMessage({
            messageId: assistantMessage.id,
            updates: { content: cleanContent, question: {
                text: parsedQuestion.question,
                suggestions: parsedQuestion.suggestions
            }}
        });
        logger.log("Agent: 问题指令处理完毕，回合结束。");
        return;
    }

    const parsedTool = toolParserService.parseXmlToolCall(finalContent);
    if (parsedTool) {
        logger.log("Agent: V3: 在流结束后发现工具调用。", parsedTool);
        const cleanContent = finalContent.replace(parsedTool.xml, '').trim();
        await updateMessage({
            messageId: assistantMessage.id,
            updates: { content: cleanContent }
        });

        commandQueue.value.push({ type: 'EXECUTE_TOOL', payload: { parsedTool } });
        return;
    }
    
    logger.log("Agent: V3: 在流结束后未发现工具调用。回合结束。", { content: finalContent });
  }
  
  async function _handleToolExecution(payload: any) {
    const { parsedTool } = payload;
    
    const statusMessage = await addMessage({
        role: 'assistant', type: 'tool_status',
        content: toolParserService.createStatusMessage(parsedTool),
    });

    if (!statusMessage) return;

    const toolResult = await toolParserService.executeTool(parsedTool);
    logger.log(`[LOG] _handleToolExecution: Raw toolResult for tool "${parsedTool.name}"`, { toolResult });
    
    const currentHistory = orderedMessages.value;
    const currentHistoryTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
    
    const toolMessage: Message = { role: "tool", name: parsedTool.name, content: toolResult, id: '' };
    const toolMessageTokens = contextOptimizerService.calculateHistoryTokens([toolMessage]);

    const maxTokens = activeConfig.value?.maxTokens || 128000;
    const threshold = maxTokens * 0.9;
    const futureTotalTokens = currentHistoryTokens + toolMessageTokens;

    if (futureTotalTokens > threshold) {
        const availableSpace = Math.max(0, Math.floor(threshold - currentHistoryTokens));
        logger.error(`[AgentGuard] 工具结果过大，将导致上下文溢出。`, { futureTotalTokens, threshold, availableSpace });
        let feedback = `错误：工具返回结果过大 (${toolMessageTokens} tokens)，超过了当前可用的空间 (${availableSpace} tokens)。为避免对话崩溃，该结果已被丢弃。`;
        if (statusMessage) {
            await replaceMessage(statusMessage.id, {
                id: statusMessage.id,
                role: 'assistant', type: 'error',
                content: feedback, status: 'done'
            });
        }
        return;
    }

    if (statusMessage) {
        const toolResultMessage = {
            id: statusMessage.id,
            role: 'assistant' as const, type: 'tool_result' as const,
            content: toolResult, status: 'done' as const
        };
        logger.log(`[LOG] _handleToolExecution: Replacing status message with tool_result`, { toolResultMessage });
        await replaceMessage(statusMessage.id, toolResultMessage);
    }
    
    const hiddenToolMessage = { ...toolMessage, is_hidden: true };
    logger.log(`[LOG] _handleToolExecution: Adding hidden tool message`, { hiddenToolMessage });
    await addMessage(hiddenToolMessage);

    if (toolResult.startsWith("错误：")) {
        incrementToolErrors();
        if (consecutiveToolErrors.value >= 3) {
             logger.error("AI 已连续3次工具调用失败。正在中止。");
             await addMessage({ role: 'assistant', type: 'error', content: "AI可能遇到了困难，它连续3次工具调用失败或返回了错误的结果。" });
             return;
        }
    } else {
        resetToolErrors();
    }

    await _checkAndCompressContextIfNeeded();

    incrementAiTurns();
    _initiateAiTurn();
  }

  async function _callApi(history: Message[]) {
    if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
        const errorMsg = "没有激活的有效AI配置。请在设置中选择或创建一个配置。";
        logger.error(`Agent: ${errorMsg}`);
        throw new Error(errorMsg);
    }

    const apiMessages = history
        .filter(m => m.type !== 'tool_status' && !m.is_hidden)
        .map(m => {
            const messageForApi: any = {
                role: m.role,
                content: m.content,
                name: m.name,
            };
            if (m.role === 'user') {
                if (Array.isArray(m.content)) {
                    messageForApi.content = m.content.map(part => {
                        if (part.type === 'doc') {
                            return { type: 'text', text: part.content };
                        }
                        return part;
                    });
                } else {
                    messageForApi.content = [{ type: 'text', text: m.content }];
                }
            }
            if (m.role === 'tool') {
                messageForApi.tool_call_id = m.name;
                messageForApi.content = String(m.content);
                delete messageForApi.name;
            }
            if (m.role === 'assistant' && m.tool_calls) {
                messageForApi.tool_calls = m.tool_calls;
            }
            if (m.role !== 'assistant' || !m.tool_calls) {
                delete messageForApi.name;
            }
             if (m.role !== 'tool') {
                delete messageForApi.tool_call_id;
            }
            return messageForApi;
        });

    const requestBody = {
        model: activeConfig.value.modelName,
        messages: apiMessages,
        temperature: activeConfig.value.temperature,
        stream: activeConfig.value.stream,
    };
    
    logger.log("Agent: 准备调用 API...", { messages: JSON.parse(JSON.stringify(apiMessages)) });
    logger.setLastRequest(requestBody);

    try {
        const response = await openaiService.createChatCompletion(requestBody, activeConfig.value);
        return { response };
    } catch (error) {
        logger.error("Agent: 调用 API 失败:", error);
        throw error;
    }
  }

  function _removePartialXmlTags(content: string) {
    const lastOpenBracketIndex = content.lastIndexOf('<');
    if (lastOpenBracketIndex > -1) {
        const possibleTag = content.substring(lastOpenBracketIndex);
        if (!possibleTag.includes('>')) {
            if (/^<[a-zA-Z0-9_]*$/.test(possibleTag)) {
                return content.substring(0, lastOpenBracketIndex);
            }
        }
    }
    return content;
  }

  async function _handleStream(openaiStream: any) {
    let assistantMessage: Message | null = null;
    let messageId: string | null = null;
    const pacedStream = createPacedStream(openaiStream);

    logger.log('[AgentService] > _handleStream: 开始消费 paced stream...');

    try {
        for await (const chunk of pacedStream) {
            if (abortController?.signal.aborted) {
                logger.warn('[AgentService] > _handleStream: Stream 消费被中止。');
                break;
            }
            if (chunk.done) break;
            if (!assistantMessage && chunk.value) {
                const newMsg = await addMessage({
                    role: 'assistant',
                    content: '',
                    type: 'text',
                    status: 'streaming',
                });
                if (newMsg) {
                    assistantMessage = newMsg;
                    messageId = newMsg.id;
                    logger.log(`[AgentService] > _handleStream: 已创建新消息 (ID: ${messageId})。`);
                }
            }
            if (messageId && chunk.value) {
                await appendMessageContent({ messageId, chunk: chunk.value });
            }
        }
        logger.log('[AgentService] > _handleStream: Paced stream 完成。');
    } catch (err: any) {
       logger.error('[AgentService] > _handleStream: 消费 stream 时发生意外错误:', err);
       if (messageId) {
           await updateMessage({ messageId, updates: { status: 'error' } });
       }
       throw new Error(`Stream 消费失败: ${err.message}`);
    }
    
    if (messageId) {
        await updateMessage({ messageId, updates: { streamCompleted: true, status: 'done' } });
        logger.log(`[AgentService] > _handleStream: 消息 (ID: ${messageId}) 已标记为 streamCompleted 和 status done。`);
    } else {
        logger.log('[AgentService] > _handleStream: Stream 结束但没有任何内容，未创建消息。');
    }
    
    return assistantMessage;
  }

  async function _checkAndCompressContextIfNeeded() {
    const currentHistory = orderedMessages.value;
    const currentTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
    const maxTokens = activeConfig.value?.maxTokens || 128000;
    const threshold = maxTokens * 0.9;

    if (currentTokens > threshold) {
        logger.log(`[AgentCompress] 上下文 (${currentTokens}) 超出动态阈值 (${threshold})，触发主动压缩。`);
        const optimizationResult = await contextOptimizerService.processContext(currentHistory, maxTokens);

        if (optimizationResult.status === 'SUCCESS' && optimizationResult.history) {
            const newMessagesById: { [key: string]: Message } = {};
            const newMessageIds: string[] = [];
            for (const message of optimizationResult.history) {
                if (!message.id) {
                    logger.error("压缩后的消息缺少ID:", message);
                    message.id = `msg_${Date.now()}_${Math.random()}`;
                }
                newMessagesById[message.id] = message;
                newMessageIds.push(message.id);
            }
            if (currentSession.value) {
                currentSession.value.messagesById = newMessagesById;
                currentSession.value.messageIds = newMessageIds;
            }
            logger.log(`[AgentCompress] 上下文压缩成功。新 token 数: ${optimizationResult.tokens}`);
        } else if (optimizationResult.status !== 'SUCCESS') {
            logger.error(`[AgentCompress] 主动压缩失败:`, optimizationResult.userMessage);
            await addMessage({ role: 'assistant', type: 'error', content: `上下文压缩失败: ${optimizationResult.userMessage}` });
        }
    }
  }

  // --- Original Store Actions ---
  async function switchSession(sessionId: string): Promise<void> {
    const domain = currentDomain.value;
    if (!domain || !sessions.value[sessionId] || activeSessionIds.value[domain] === sessionId) return;

    const targetSession = sessions.value[sessionId];
    const targetRoleId = targetSession.roleId;

    if (!targetRoleId) {
      logger.warn(`[AgentStore] 会话 ${sessionId} 没有 roleId。无法切换。`);
      return;
    }
    
    activeSessionIds.value[domain] = sessionId;
    activeRoleId.value[domain] = targetRoleId;
    await lastUsedRolesStore.setItem(domain, targetRoleId);
    
    const agent = availableAgents.value[domain]?.find(a => a.id === targetRoleId);
    if (agent) {
      activeAgentName.value = agent.name;
    }

    logger.log(`[AgentStore] 已切换到会话 ${sessionId} (Agent: ${targetRoleId})。`);
  }
  
  function deleteSession(sessionId: string): void {
    const domain = currentDomain.value;
    if (!domain || !sessions.value[sessionId]) return;

    if (activeSessionIds.value[domain] === sessionId) {
      delete sessions.value[sessionId];
      logger.log(`[AgentStore] 已删除活动会话 ${sessionId}。正在开启一个新会话。`);
      startNewSession(domain, currentRoleId.value);
    } else {
      delete sessions.value[sessionId];
      logger.log(`[AgentStore] 已删除会话 ${sessionId}。`);
    }
  }

  function renameSession(sessionId: string, newName: string): void {
    if (sessions.value[sessionId]) {
      sessions.value[sessionId].name = newName;
      logger.log(`[AgentStore] 已将会话 ${sessionId} 重命名为 "${newName}"`);
    }
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
    const roleId = roleIdToLoad || currentRoleId.value;
    if (!roleId) {
      logger.error(`Agent Store: 无法开启新会话，因为没有提供或设置 roleId。`);
      error.value = new Error("无法开启新会话，因为没有选择任何 Agent。");
      return;
    }
    logger.log(`Agent Store: 为域 '${domain}' (角色: ${roleId}) 开启新会话...`);

    const domainSessions = Object.values(sessions.value).filter(s => s.domain === domain);
    if (domainSessions.length >= MAX_SESSIONS_PER_DOMAIN) {
      domainSessions.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
      const oldestSession = domainSessions[0];
      logger.log(`Agent Store: 会话数量达到上限(${MAX_SESSIONS_PER_DOMAIN})，正在删除最旧的会话: ${oldestSession.id}`);
      delete sessions.value[oldestSession.id];
    }

    isLoading.value = true;
    error.value = null;
    try {
      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
      activeAgentName.value = agentName;
      activeRoleId.value[domain] = roleId;
      const newSessionId = `session_${Date.now()}`;
      const newSession: Session = {
        id: newSessionId,
        domain: domain,
        roleId: roleId,
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

    } catch (e: any) {
      error.value = e;
      logger.error("Agent Store: 开启新会话失败:", e);
    } finally {
      isLoading.value = false;
    }
  }

  async function switchDomainContext(domain: string): Promise<void> {
    logger.log(`Agent Store: 切换域上下文至 '${domain}'...`);
    const ensuredRoleId = await fetchAvailableAgents(domain);

    if (!activeSessionIds.value[domain] || !sessions.value[activeSessionIds.value[domain]]) {
      logger.log(`[AgentStore] '${domain}' 无活动会话。正在以角色 '${ensuredRoleId}' 开启新会话。`);
      await startNewSession(domain, ensuredRoleId);
    } else {
      const currentRole = availableAgents.value[domain]?.find(a => a.id === currentRoleId.value);
      if (currentRole) {
        activeAgentName.value = currentRole.name;
      }
      logger.log(`Agent Store: 已激活 '${domain}' 的现有会话 '${activeSessionIds.value[domain]}'。`);
    }
  }

  async function startNewChatWithAgent(roleId: string): Promise<void> {
    const domain = currentDomain.value;
    if (!domain || !roleId) return;
  
    logger.log(`[AgentStore] 用户请求以 agent '${roleId}' 开始新聊天。`);
    
    const session = currentSession.value;
    const isSessionEmpty = !session || session.messageIds.length <= 1;
  
    if (isSessionEmpty && session) {
      logger.log(`[AgentStore] 当前会话为空。正在为新 agent 转换它。`);
      isLoading.value = true;
      stop();
      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
      session.messagesById = {};
      session.messageIds = [];
      addMessage({ role: 'system', content: systemPrompt, type: 'system' });
      session.roleId = roleId;
      activeRoleId.value[domain] = roleId;
      activeAgentName.value = agentName;
      await lastUsedRolesStore.setItem(domain, roleId);
      logger.log(`[AgentStore] 会话 ${session.id} 已为 agent ${roleId} 转换。`);
      isLoading.value = false;
    } else {
      logger.log(`[AgentStore] 当前会话不为空。正在开启一个新会话。`);
      await startNewSession(domain, roleId);
    }
  }
  
  async function switchAgent(roleId: string): Promise<void> {
    await startNewChatWithAgent(roleId);
  }

  async function addMessage(messageData: Partial<Message>): Promise<Message | null> {
    if (!currentSession.value) return null;
    
    const id = messageData.id || nanoid();
    const message: Message = {
      id,
      type: 'text',
      role: 'user', // default role
      ...messageData,
    } as Message;

    currentSession.value.messagesById[id] = message;
    currentSession.value.messageIds.push(id);
    await nextTick();
    return message;
  }

  async function updateMessage({ messageId, updates }: { messageId: string, updates: Partial<Message> }): Promise<void> {
    const message = currentSession.value?.messagesById?.[messageId];
    if (message) {
      logger.log(`[LOG] agentStore: Updating message ${messageId}`, { updates });
      Object.assign(message, updates);
      await nextTick();
    }
  }

  async function removeMessage(messageId: string): Promise<void> {
    const session = currentSession.value;
    if (!session || !session.messagesById[messageId]) return;

    const index = session.messageIds.indexOf(messageId);
    if (index > -1) {
      session.messageIds.splice(index, 1);
    }
    delete session.messagesById[messageId];
    await nextTick();
  }

  async function replaceMessage(oldId: string, newMessageData: Partial<Message>): Promise<void> {
    logger.log(`[LOG] agentStore: Replacing message ${oldId}`, { newMessageData });
    const session = currentSession.value;
    if (!session || !session.messagesById[oldId]) return;

    const index = session.messageIds.indexOf(oldId);
    if (index === -1) return;

    const newId = newMessageData.id || nanoid();
    const message = { ...newMessageData, id: newId } as Message;

    delete session.messagesById[oldId];
    session.messagesById[newId] = message;

    session.messageIds.splice(index, 1, newId);
    await nextTick();
  }

  async function appendMessageContent({ messageId, chunk }: { messageId: string, chunk: string }): Promise<void> {
    const session = currentSession.value;
    if (!session) return;

    const message = session.messagesById[messageId];
    if (message) {
        const oldContent = message.content;
        const newContent = (Array.isArray(oldContent) ? oldContent.map(c=>c.text).join('') : (oldContent || '')) + chunk;
        session.messagesById[messageId] = {
            ...message,
            content: newContent,
        };
        await nextTick();
    }
  }

  function markStreamAsCompleted({ messageId }: { messageId: string }): void {
    const message = currentSession.value?.messagesById?.[messageId];
    if (message) {
      message.streamCompleted = true;
    }
  }

  async function sendMessage(payload: string | { text: string; images?: string[]; references?: any[] }): Promise<void> {
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

    addMessage({
      role: 'user',
      content: contentPayload.length === 1 && contentPayload[0].type === 'text'
               ? contentPayload[0].text!
               : contentPayload,
    });
    
    startTurn();
  }

  async function resetAgent(): Promise<void> {
    logger.log("Agent Store: 重置 Agent... (将开启新会话)");
    if(currentDomain.value) {
        await startNewSession(currentDomain.value, activeRoleId.value[currentDomain.value]);
    }
  }

  function incrementToolErrors(): void {
    consecutiveToolErrors.value++;
  }
  function resetToolErrors(): void {
    consecutiveToolErrors.value = 0;
  }
  function incrementAiTurns(): void {
    consecutiveAiTurns.value++;
  }
  function resetCounters(): void {
    consecutiveToolErrors.value = 0;
    consecutiveAiTurns.value = 0;
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
    stop();
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
      removeMessage(lastMessage.id);
      startTurn();
    } else {
      logger.warn(`[AgentStore] 调用重试，但最后一条消息不是可重试的错误。`);
    }
  }

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
      logger.log(`[AgentStore] 会话状态已持久化 (v${AGENT_CACHE_VERSION})。`);
    } catch (e) {
      logger.error('[AgentStore] 持久化状态失败:', e);
    }
  }, 1000);

  async function initializeStoreFromCache(): Promise<void> {
    try {
      logger.log('[AgentStore] 正在从缓存初始化 store...');
      const cachedState = await sessionsStore.getItem<any>('state');
      
      if (!cachedState || cachedState.version !== AGENT_CACHE_VERSION) {
        logger.error(`[AgentStore] 检测到过时或损坏的缓存。正在清除缓存并重新开始。`, {
            foundVersion: cachedState?.version,
            expectedVersion: AGENT_CACHE_VERSION,
        });
        await forceClearAgentCache();
        
        sessions.value = {};
        activeSessionIds.value = { gi: null, hsr: null };

      } else {
        const { sessions: cachedSessions, activeSessionIds: cachedActiveIds } = cachedState.data;
        sessions.value = (typeof cachedSessions === 'object' && cachedSessions !== null) ? cachedSessions : {};
        logger.log(`[AgentStore] 已恢复 ${Object.keys(sessions.value).length} 个会话。`);
        
        const defaultIds = { gi: null, hsr: null };
        activeSessionIds.value = (typeof cachedActiveIds === 'object' && cachedActiveIds !== null)
                                 ? { ...defaultIds, ...cachedActiveIds }
                                 : defaultIds;
        logger.log('[AgentStore] 已恢复活动会话 ID。');
      }
      
      watch(sessions, persistState, { deep: true });
      watch(activeSessionIds, persistState, { deep: true });

    } catch (e) {
      logger.error('[AgentStore] 缓存初始化期间发生严重错误。正在清除缓存并重新开始。', e);
      await forceClearAgentCache();
      sessions.value = {};
      activeSessionIds.value = { gi: null, hsr: null };
    }
  }

  return {
    sessions, activeSessionIds, isLoading, error, logMessages, activeSessionId,
    currentSession, activeAgentName, availableAgents, currentRoleId, messagesById,
    orderedMessages, consecutiveToolErrors, consecutiveAiTurns,
    switchDomainContext, fetchAvailableAgents, switchAgent, startNewSession,
    sendMessage, stop, resetAgent, addMessage, updateMessage, removeMessage,
    replaceMessage, appendMessageContent, markStreamAsCompleted, incrementToolErrors,
    resetToolErrors, incrementAiTurns, resetCounters, markAllAsSent, deleteMessagesFrom,
    initializeStoreFromCache, switchSession, deleteSession, renameSession, startNewChatWithAgent,
    retryLastTurn,
  };
});