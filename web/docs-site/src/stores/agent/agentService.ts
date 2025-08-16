import { ref, type Ref, type ComputedRef } from 'vue';
import { nanoid } from 'nanoid';
import localforage from 'localforage';
import logger from '@/services/loggerService';
import { useAppStore } from '@/stores/app';
import openaiService from '@/services/openaiService';
import { createPacedStream } from '@/services/streamingService';
import contextOptimizerService from '@/services/contextOptimizerService';
import toolParserService from '@/services/toolParserService';
import { StreamingMarkdownParser } from '@/services/StreamingMarkdownParser';
import { renderMarkdownSync, replaceLinkPlaceholders } from '@/services/MarkdownRenderingService';
import type { Message, Command, Session } from './types';
import type { MessageManager } from './messageManager';
import MessageManagerImpl from './messageManager';

// --- Localforage 和 debounce 设置 ---
const AGENT_CACHE_VERSION = '2.0';
const sessionsStore = localforage.createInstance({ name: 'agentSessions' });
const lastUsedRolesStore = localforage.createInstance({ name: 'lastUsedRoles' });

export async function forceClearAgentCache(): Promise<void> {
  await sessionsStore.clear();
  await lastUsedRolesStore.clear();
  logger.warn('[AgentStore] 缓存因数据过时或损坏已被清除。');
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

// --- AgentService 类定义 ---
export class AgentService {
  // --- AgentService State ---
  private commandQueue: Ref<Command[]> = ref([]);
  private isProcessing: Ref<boolean> = ref(false);
  private abortController: AbortController | null = null;
  private toolFeedbackPromptContent: string | null = null;
  
  private consecutiveToolErrors: Ref<number> = ref(0);
  private consecutiveAiTurns: Ref<number> = ref(0);
  private noToolCallRetries: Ref<number> = ref(0);
  private isForceStopped: Ref<boolean> = ref(false);
  
  // --- 依赖注入 ---
  private messageManager: MessageManager;
  private currentSession: ComputedRef<Session | null>;
  private activeConfig: ComputedRef<any>;
  private currentDomain: ComputedRef<string | null>;
  
  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>,
    activeConfig: ComputedRef<any>,
    currentDomain: ComputedRef<string | null>
  ) {
    this.messageManager = messageManager;
    this.currentSession = currentSession;
    this.activeConfig = activeConfig;
    this.currentDomain = currentDomain;
  }

  // --- Getters / 计算属性 ---
  private get orderedMessages(): Message[] {
    const session = this.currentSession.value;
    if (!session) return [];
    return session.messageIds.map(id => session.messagesById[id]);
  }

  // --- AgentService Logic (as actions) ---
  
  /**
   * 立即停止所有正在进行的 Agent 活动。
   * 这包括中止网络请求、清空命令队列、更新 UI 状态并提供用户反馈。
   */
  stopAgent() {
    // 0. 设置全局中止标志，防止任何后续的自动重试
    this.isForceStopped.value = true;

    // 1. 立即中止网络请求
    if (this.abortController) {
        this.abortController.abort();
        logger.log("Agent: 请求被用户中止。");
    }

    // 2. 立即清空命令队列，防止任何后续任务被执行
    this.commandQueue.value = [];

    // 3. 立即重置 UI 状态，为用户提供即时反馈
    // 检查 isProcessing 是为了防止在非处理状态下误操作
    if (this.isProcessing.value) {
        // 4. 找到任何正在“流式输出”的消息，并将其状态更新为“已手动中断”
        const streamingMessage = this.orderedMessages.find(m => m.status === 'streaming');
        if (streamingMessage) {
            this.messageManager.updateMessage({
                messageId: streamingMessage.id,
                updates: { status: 'error', content: `${streamingMessage.content}\n\n---\n*已手动中断*` }
            });
        }
    }
    
    // 5. 重置 AbortController
    this.abortController = null;
    
    logger.log("Agent: 所有活动已停止。");
  }

  startTurn() {
    // 用户主动发起新回合时，重置全局中止标志
    this.isForceStopped.value = false;
    this._initiateAiTurn();
  }

  private _initiateAiTurn() {
    // 检查全局中止标志，如果为 true 则拒绝开始新的回合
    if (this.isForceStopped.value) {
      logger.log("Agent 已被强制停止，新的回合将不会开始。");
      this.isForceStopped.value = false; // 重置标志
      return;
    }
    
    this.abortController = new AbortController();
    this.commandQueue.value.push({ type: 'CALL_AI' });
    if (!this.isProcessing.value) {
        this.processQueue();
    }
  }

  async processQueue() {
    this.isProcessing.value = true;
    this.resetCounters();

    while (this.commandQueue.value.length > 0) {
        if (this.abortController?.signal.aborted) {
            logger.log("命令队列处理被中止。");
            this.commandQueue.value = [];
            break;
        }
        
        const command = this.commandQueue.value.shift();
        if (!command) continue;

        logger.log("正在处理命令:", command);

        try {
            if (command.type === 'CALL_AI') {
                if (this.consecutiveAiTurns.value >= 10) {
                    logger.error("已达到 AI 回合上限。正在中止。");
                    await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "AI已连续迭代10次，为防止失控，已自动中断。" });
                    break;
                }
                await this._handleApiCall();
            } else if (command.type === 'EXECUTE_TOOL') {
                await this._handleToolExecution(command.payload);
            }
        } catch (err: any) {
             if (err.name !== 'AbortError') {
                logger.error("处理命令时出错:", { command, error: err });
                await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: `处理命令'${command.type}'时出错: ${err.message}` });
            } else {
                logger.log("命令处理在执行期间被中止。");
            }
            this.commandQueue.value = [];
            break;
        }
    }

    this.isProcessing.value = false;
    this.abortController = null;
    logger.log("命令队列处理完成。");
  }

  /**
   * 加载并缓存 tool_feedback_prompt.md 的内容
   */
  private async _getToolFeedbackPrompt(): Promise<string> {
    // 如果已经缓存了内容，则直接返回
    if (this.toolFeedbackPromptContent) {
      return this.toolFeedbackPromptContent;
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
      this.toolFeedbackPromptContent = await response.text();
      return this.toolFeedbackPromptContent;
    } catch (error) {
      // 如果加载失败，记录错误并返回默认提示
      logger.error("加载 tool_feedback_prompt.md 时出错:", error);
      return "你的回复中没有包含任何工具调用。你的每一次回复都必须是 'search_docs', 'read_doc', 'list_docs', 或 'ask_question' 中的一种。请重新评估并选择一个指令来回应。";
    }
  }

  private async _handleApiCall() {
    let assistantMessage: Message | null = null;
    
    try {
      const { response } = await this._callApi(this.orderedMessages, this.abortController!.signal);

      if (this.activeConfig.value?.stream) {
          assistantMessage = await this._handleStream(response);
      } else {
          const responseData = response;
          logger.log("Agent: 收到 API 响应 (非流式):", responseData);
          const message = responseData.choices[0].message;

          const placeholderMessage = await this.messageManager.addMessage({
              role: 'assistant',
              content: '',
              type: 'text',
              status: 'streaming'
          });
          
          if (placeholderMessage) {
              await this.messageManager.updateMessage({
                  messageId: placeholderMessage.id,
                  updates: {
                      content: message.content,
                      status: 'done',
                      streamCompleted: true
                  }
              });
              // 重新获取更新后的消息
              assistantMessage = this.currentSession.value?.messagesById[placeholderMessage.id] || null;
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

    const updatedMessage = this.currentSession.value?.messagesById[assistantMessage.id];
    if (!updatedMessage) {
        throw new Error("无法找到更新后的消息。");
    }
    
    const content = typeof updatedMessage.content === 'string' ? updatedMessage.content :
                   Array.isArray(updatedMessage.content) ? updatedMessage.content.map(c => c.text).join('') : '';
    const finalContent = this._removePartialXmlTags(content);
    logger.log(`[LOG] _handleApiCall: Final stream content for message ${assistantMessage.id}`, { finalContent });
    
    await this.messageManager.updateMessage({
        messageId: assistantMessage.id,
        updates: { status: 'done' }
    });

    const parsedQuestion = toolParserService.parseAskQuestionCall(finalContent);
    const parsedTool = toolParserService.parseXmlToolCall(finalContent);

    if (parsedQuestion) {
        // 发现 <ask_question> 指令，正常处理并结束回合
        logger.log("Agent: 在流结束后发现 <ask_question> 指令。", parsedQuestion);
        const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
        console.log('[AgentStore] _handleApiCall cleanContent:', JSON.stringify(cleanContent));
        // 使用 MarkdownRenderingService 渲染 cleanContent
        const renderedHtmlWithPlaceholders = renderMarkdownSync(cleanContent);
        const finalRenderedHtml = await replaceLinkPlaceholders(renderedHtmlWithPlaceholders);
        await this.messageManager.updateMessage({
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
        await this.messageManager.updateMessage({
            messageId: assistantMessage.id,
            updates: {
                content: cleanContent,
                renderedContent: finalRenderedHtml // 更新 renderedContent
            }
        });

        this.commandQueue.value.push({ type: 'EXECUTE_TOOL', payload: { parsedTool } });
        return;
    }

    // 如果代码执行到这里，意味着既没有工具调用，也没有提问指令
    // 这将被视为"无工具调用"
    if (this.noToolCallRetries.value >= 2) {
        logger.error("AI 在收到反馈后仍未调用任何指令，中止循环。");
        await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "抱歉，我似乎无法找到合适的指令来回应您的问题。" });
        return; // 必须中止
    }

    this.noToolCallRetries.value++; // 增加重试计数

    const feedbackPrompt = await this._getToolFeedbackPrompt(); // 加载外部提示词
    await this.messageManager.addMessage({
        role: 'system',
        content: feedbackPrompt,
        is_hidden: true,
    });

    logger.log(`第 ${this.noToolCallRetries.value} 次追加"无指令调用"反馈，并重新发起AI调用。`);
    this._initiateAiTurn(); // 重新发起AI调用
  }
  
  private async _handleToolExecution(payload: any) {
    const { parsedTool } = payload;
    
    const statusMessage = await this.messageManager.addMessage({
        role: 'assistant', type: 'tool_status',
        content: toolParserService.createStatusMessage(parsedTool),
    });

    if (!statusMessage) return;

    const { status, result: toolResult } = await toolParserService.executeTool(parsedTool);
    logger.log(`[LOG] _handleToolExecution: Raw toolResult for tool "${parsedTool.name}"`, { toolResult });
    
    const currentHistory = this.orderedMessages;
    const currentHistoryTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
    
    const toolMessage: Message = { role: "tool", name: parsedTool.name, content: toolResult, id: '' };
    const toolMessageTokens = contextOptimizerService.calculateHistoryTokens([toolMessage]);

    const maxTokens = this.activeConfig.value?.maxTokens || 128000;
    const threshold = maxTokens * 0.9;
    const futureTotalTokens = currentHistoryTokens + toolMessageTokens;

    if (futureTotalTokens > threshold) {
        const availableSpace = Math.max(0, Math.floor(threshold - currentHistoryTokens));
        logger.error(`[AgentGuard] 工具结果过大，将导致上下文溢出。`, { futureTotalTokens, threshold, availableSpace });
        let feedback = `错误：工具返回结果过大 (${toolMessageTokens} tokens)，超过了当前可用的空间 (${availableSpace} tokens)。为避免对话崩溃，该结果已被丢弃。`;
        if (statusMessage) {
            await this.messageManager.replaceMessage(statusMessage.id, {
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
        await this.messageManager.replaceMessage(statusMessage.id, toolResultMessage);
    }
    
    const hiddenToolMessage = { ...toolMessage, is_hidden: true };
    logger.log(`[LOG] _handleToolExecution: Adding hidden tool message`, { hiddenToolMessage });
    await this.messageManager.addMessage(hiddenToolMessage);

    if (status === 'error') {
        this.incrementToolErrors();
        if (this.consecutiveToolErrors.value >= 3) {
             logger.error("AI 已连续3次工具调用失败。正在中止。");
             await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: "AI可能遇到了困难，它连续3次工具调用失败或返回了错误的结果。" });
             return;
        }
    } else {
        this.resetToolErrors();
    }

    await this._checkAndCompressContextIfNeeded();

    this.incrementAiTurns();
    // 直接将 CALL_AI 命令推入队列，由正在运行的 processQueue 处理
    this.commandQueue.value.push({ type: 'CALL_AI' });
  }

  private async _callApi(history: Message[], signal: AbortSignal) {
    if (!this.activeConfig.value || !this.activeConfig.value.apiUrl || !this.activeConfig.value.apiKey) {
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
        model: this.activeConfig.value.modelName,
        messages: apiMessages,
        temperature: this.activeConfig.value.temperature,
        stream: this.activeConfig.value.stream,
    };
    
    logger.log("Agent: 准备调用 API...", { messages: JSON.parse(JSON.stringify(apiMessages)) });
    console.log("即将发送给 AI 的 messages:", JSON.parse(JSON.stringify(apiMessages)));
    logger.setLastRequest(requestBody);

    try {
        const response = await openaiService.createChatCompletion(requestBody, this.activeConfig.value, signal);
        return { response };
    } catch (error) {
        logger.error("Agent: 调用 API 失败:", error);
        throw error;
    }
  }

  private _removePartialXmlTags(content: string) {
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

  private async _handleStream(openaiStream: any) {
    let assistantMessage: Message | null = null;
    let messageId: string | null = null;
    const pacedStream = createPacedStream(openaiStream);
    // 新增：为每条新消息创建一个解析器实例
    let markdownParser: StreamingMarkdownParser | null = null;

    logger.log('[AgentService] > _handleStream: 开始消费 paced stream...');

    try {
        for await (const chunk of pacedStream) {
            if (this.abortController?.signal.aborted) {
                logger.warn('[AgentService] > _handleStream: Stream 消费被中止。');
                break;
            }
            if (chunk.done) break;
            if (!assistantMessage && chunk.value) {
                const newMsg = await this.messageManager.addMessage({
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
                await this.messageManager.updateMessage({ messageId, updates: { renderedContent: renderedHtml } });
                // 保留原始的纯文本追加，以供后处理使用
                await this.messageManager.appendMessageContent({ messageId, chunk: chunk.value });
            }
        }
        logger.log('[AgentService] > _handleStream: Paced stream 完成。');
    } catch (err: any) {
       logger.error('[AgentService] > _handleStream: 消费 stream 时发生意外错误:', err);
       if (messageId) {
           await this.messageManager.updateMessage({ messageId, updates: { status: 'error' } });
       }
       throw new Error(`Stream 消费失败: ${err.message}`);
    }
    
    if (messageId) {
        await this.messageManager.updateMessage({ messageId, updates: { streamCompleted: true, status: 'done' } });
        logger.log(`[AgentService] > _handleStream: 消息 (ID: ${messageId}) 已标记为 streamCompleted 和 status done。`);
    } else {
        logger.log('[AgentService] > _handleStream: Stream 结束但没有任何内容，未创建消息。');
    }
    
    return assistantMessage;
  }

  private async _checkAndCompressContextIfNeeded() {
    const currentHistory = this.orderedMessages;
    const currentTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
    const maxTokens = this.activeConfig.value?.maxTokens || 128000;
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
            if (this.currentSession.value) {
                this.currentSession.value.messagesById = newMessagesById;
                this.currentSession.value.messageIds = newMessageIds;
            }
            logger.log(`[AgentCompress] 上下文压缩成功。新 token 数: ${optimizationResult.tokens}`);
        } else if (optimizationResult.status !== 'SUCCESS') {
            logger.error(`[AgentCompress] 主动压缩失败:`, optimizationResult.userMessage);
            await this.messageManager.addMessage({ role: 'assistant', type: 'error', content: `上下文压缩失败: ${optimizationResult.userMessage}` });
        }
    }
  }
  
  // --- Counters Management ---
  incrementToolErrors(): void {
    this.consecutiveToolErrors.value++;
  }
  resetToolErrors(): void {
    this.consecutiveToolErrors.value = 0;
  }
  incrementAiTurns(): void {
    this.consecutiveAiTurns.value++;
  }
  resetCounters(): void {
    this.consecutiveToolErrors.value = 0;
    this.consecutiveAiTurns.value = 0;
  }
  
  // --- Getters for store ---
  getIsProcessing(): boolean {
      return this.isProcessing.value;
  }
  
  getConsecutiveToolErrors(): number {
      return this.consecutiveToolErrors.value;
  }
  
  getConsecutiveAiTurns(): number {
      return this.consecutiveAiTurns.value;
  }
}