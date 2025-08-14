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
import { StreamingMarkdownParser } from '@/services/StreamingMarkdownParser'; // 新增：导入实时渲染解析器
import { renderMarkdownSync, replaceLinkPlaceholders } from '@/services/MarkdownRenderingService'; // 新增：导入 Markdown 渲染服务
// import markdownPostprocessorService from '@/services/MarkdownPostprocessorService'; // 已移除：不再需要后处理器

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
    renderedContent?: string; // 用于存储实时渲染的 HTML
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
  let toolFeedbackPromptContent: string | null = null;

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
  const noToolCallRetries = ref(0);
  const isForceStopped = ref(false);

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
  
  /**
   * 立即停止所有正在进行的 Agent 活动。
   * 这包括中止网络请求、清空命令队列、更新 UI 状态并提供用户反馈。
   */
  function stopAgent() {
    // 0. 设置全局中止标志，防止任何后续的自动重试
    isForceStopped.value = true;

    // 1. 立即中止网络请求
    if (abortController) {
        abortController.abort();
        logger.log("Agent: 请求被用户中止。");
    }

    // 2. 立即清空命令队列，防止任何后续任务被执行
    commandQueue.value = [];

    // 3. 立即重置 UI 状态，为用户提供即时反馈
    // 检查 isProcessing 是为了防止在非处理状态下误操作
    if (isProcessing.value) {
        isLoading.value = false;
        isProcessing.value = false;
        
        // 4. 找到任何正在“流式输出”的消息，并将其状态更新为“已手动中断”
        const streamingMessage = orderedMessages.value.find(m => m.status === 'streaming');
        if (streamingMessage) {
            updateMessage({
                messageId: streamingMessage.id,
                updates: { status: 'error', content: `${streamingMessage.content}\n\n---\n*已手动中断*` }
            });
        }
    }
    
    // 5. 重置 AbortController
    abortController = null;
    
    logger.log("Agent: 所有活动已停止。");
  }

  function startTurn() {
    // 用户主动发起新回合时，重置全局中止标志
    isForceStopped.value = false;
    _initiateAiTurn();
  }

  function _initiateAiTurn() {
    // 检查全局中止标志，如果为 true 则拒绝开始新的回合
    if (isForceStopped.value) {
      logger.log("Agent 已被强制停止，新的回合将不会开始。");
      isForceStopped.value = false; // 重置标志
      return;
    }
    
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

  /**
   * 加载并缓存 tool_feedback_prompt.md 的内容
   */
  async function _getToolFeedbackPrompt(): Promise<string> {
    // 如果已经缓存了内容，则直接返回
    if (toolFeedbackPromptContent) {
      return toolFeedbackPromptContent;
    }

    try {
      // 构造提示词文件的URL，添加时间戳以避免缓存
      const v = Date.now();
      const response = await fetch(`/prompts/tool_feedback_prompt.md?v=${v}`);
      
      // 检查响应是否成功
      if (!response.ok) {
        logger.error("无法加载 tool_feedback_prompt.md");
        return "你的回复中没有包含任何工具调用。你的每一次回复都必须是 'search_docs', 'read_doc', 'list_docs', 或 'ask_question' 中的一种。请重新评估并选择一个指令来回应。";
      }
      
      // 获取并缓存内容
      toolFeedbackPromptContent = await response.text();
      return toolFeedbackPromptContent;
    } catch (error) {
      // 如果加载失败，记录错误并返回默认提示
      logger.error("加载 tool_feedback_prompt.md 时出错:", error);
      return "你的回复中没有包含任何工具调用。你的每一次回复都必须是 'search_docs', 'read_doc', 'list_docs', 或 'ask_question' 中的一种。请重新评估并选择一个指令来回应。";
    }
  }

  async function _handleApiCall() {
    let assistantMessage: Message | null = null;
    
    try {
      const { response } = await _callApi(orderedMessages.value, abortController!.signal);

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
    } catch (error: any) {
      // 专门处理 AbortError，避免不友好的错误信息
      if (error.name === 'AbortError') {
        logger.log("Agent: API 调用被用户中止。");
        // 直接返回，不执行后续逻辑
        return;
      }
      // 如果是其他错误，则重新抛出
      throw error;
    }
    
    // 只有在没有被中止的情况下，才继续执行后续逻辑
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
    const parsedTool = toolParserService.parseXmlToolCall(finalContent);

    if (parsedQuestion) {
        // 发现 <ask_question> 指令，正常处理并结束回合
        logger.log("Agent: 在流结束后发现 <ask_question> 指令。", parsedQuestion);
        const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
        // 使用 MarkdownRenderingService 渲染 cleanContent
        const renderedHtmlWithPlaceholders = renderMarkdownSync(cleanContent);
        const finalRenderedHtml = await replaceLinkPlaceholders(renderedHtmlWithPlaceholders);
        await updateMessage({
            messageId: assistantMessage.id,
            updates: {
                content: cleanContent,
                renderedContent: finalRenderedHtml, // 更新 renderedContent
                question: {
                    text: parsedQuestion.question,
                    suggestions: parsedQuestion.suggestions
                }
            }
        });
        logger.log("Agent: 问题指令处理完毕，回合结束。");
        return;
    }

    if (parsedTool) {
        // 发现标准工具调用，正常处理并移交执行
        logger.log("Agent: V3: 在流结束后发现工具调用。", parsedTool);
        const cleanContent = finalContent.replace(parsedTool.xml, '').trim();
        // 使用 MarkdownRenderingService 渲染 cleanContent
        const renderedHtmlWithPlaceholders = renderMarkdownSync(cleanContent);
        const finalRenderedHtml = await replaceLinkPlaceholders(renderedHtmlWithPlaceholders);
        await updateMessage({
            messageId: assistantMessage.id,
            updates: {
                content: cleanContent,
                renderedContent: finalRenderedHtml // 更新 renderedContent
            }
        });

        commandQueue.value.push({ type: 'EXECUTE_TOOL', payload: { parsedTool } });
        return;
    }

    // 如果代码执行到这里，意味着既没有工具调用，也没有提问指令
    // 这将被视为"无工具调用"
    if (noToolCallRetries.value >= 2) {
        logger.error("AI 在收到反馈后仍未调用任何指令，中止循环。");
        await addMessage({ role: 'assistant', type: 'error', content: "抱歉，我似乎无法找到合适的指令来回应您的问题。" });
        return; // 必须中止
    }

    noToolCallRetries.value++; // 增加重试计数

    const feedbackPrompt = await _getToolFeedbackPrompt(); // 加载外部提示词
    await addMessage({
        role: 'system',
        content: feedbackPrompt,
        is_hidden: true,
    });

    logger.log(`第 ${noToolCallRetries.value} 次追加"无指令调用"反馈，并重新发起AI调用。`);
    _initiateAiTurn(); // 重新发起AI调用
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
    setTimeout(() => _initiateAiTurn(), 100); 
  }

  async function _callApi(history: Message[], signal: AbortSignal) {
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
        const response = await openaiService.createChatCompletion(requestBody, activeConfig.value, signal);
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
    // 新增：为每条新消息创建一个解析器实例
    let markdownParser: StreamingMarkdownParser | null = null;

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
                    // 新增：初始化 renderedContent 为空字符串
                    renderedContent: '',
                    type: 'text',
                    status: 'streaming',
                });
                if (newMsg) {
                    assistantMessage = newMsg;
                    messageId = newMsg.id;
                    // 新增：创建解析器实例
                    markdownParser = new StreamingMarkdownParser();
                    logger.log(`[AgentService] > _handleStream: 已创建新消息 (ID: ${messageId})。`);
                }
            }
            // 修改：处理文本块并更新渲染内容
            if (messageId && chunk.value && markdownParser) {
                // 使用新服务处理文本块，获取实时渲染的 HTML
                const renderedHtml = await markdownParser.processChunk(chunk.value);
                // 更新消息的渲染内容
                await updateMessage({ messageId, updates: { renderedContent: renderedHtml } });
                // 保留原始的纯文本追加，以供后处理使用
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
    noToolCallRetries.value = 0; // 重置"无工具调用"重试计数器
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
    sendMessage, stopAgent, resetAgent, addMessage, updateMessage, removeMessage,
    replaceMessage, appendMessageContent, markStreamAsCompleted, incrementToolErrors,
    resetToolErrors, incrementAiTurns, resetCounters, markAllAsSent, deleteMessagesFrom,
    initializeStoreFromCache, switchSession, deleteSession, renameSession, startNewChatWithAgent,
    retryLastTurn,
  };
});