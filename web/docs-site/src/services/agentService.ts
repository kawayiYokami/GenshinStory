import logger from './loggerService';
import { useConfigStore } from '@/stores/config';
import { useAgentStore } from '@/stores/agent';
import { storeToRefs } from 'pinia';
import openaiService from './openaiService';
import { createPacedStream } from './streamingService';
import contextOptimizerService from './contextOptimizerService';
import toolParserService from './toolParserService';
import type { Message, ToolCall } from '@/stores/agent';
import type { Config } from '@/stores/config';

// --- 类型定义 ---

interface Command {
    type: 'CALL_AI' | 'EXECUTE_TOOL';
    payload?: any;
}

// --- Agent 核心逻辑 ---

class AgentService {
    private commandQueue: Command[];
    private isProcessing: boolean;
    private abortController: AbortController | null;

    constructor() {
        this.commandQueue = [];
        this.isProcessing = false;
        this.abortController = null;
    }
    
    public stop(): void {
        if (this.abortController) {
            this.abortController.abort();
            logger.log("Agent: 请求被用户中止。");
        }
    }

    /**
     * 统一的用户消息入口点。
     * @param userContent 用户的文本内容。
     */
    public async sendMessage(userContent: string): Promise<void> {
        const agentStore = useAgentStore();
        
        // 1. 将用户消息添加到 store
        agentStore.addMessage({ role: 'user', content: userContent, id: `msg_${Date.now()}` });
        
        // 2. 主动检查并根据需要压缩上下文
        await this._checkAndCompressContextIfNeeded();

        // 3. 启动 AI 处理回合
        this._initiateAiTurn();
    }
    
    public startTurn(): void {
        this._initiateAiTurn();
    }

    private _initiateAiTurn(): void {
        this.abortController = new AbortController();
        this.commandQueue.push({ type: 'CALL_AI' });
        if (!this.isProcessing) {
            this.processQueue();
        }
    }

    private async processQueue(): Promise<void> {
        const agentStore = useAgentStore();
        this.isProcessing = true;
        agentStore.isLoading = true;
        agentStore.resetCounters();

        while (this.commandQueue.length > 0) {
            if (this.abortController?.signal.aborted) {
                logger.log("命令队列处理被中止。");
                this.commandQueue = [];
                break;
            }
            
            const command = this.commandQueue.shift();
            if (!command) continue;

            logger.log("正在处理命令:", command);

            try {
                if (command.type === 'CALL_AI') {
                    if (agentStore.consecutiveAiTurns >= 10) {
                        logger.error("已达到 AI 回合上限。正在中止。");
                        agentStore.addMessage({ role: 'assistant', type: 'error', content: "AI已连续迭代10次，为防止失控，已自动中断。" });
                        break;
                    }
                    await this._handleApiCall();
                } else if (command.type === 'EXECUTE_TOOL') {
                    await this._handleToolExecution(command.payload);
                }
            } catch (error: any) {
                 if (error.name !== 'AbortError') {
                    logger.error("处理命令时出错:", { command, error });
                    agentStore.addMessage({ role: 'assistant', type: 'error', content: `处理命令'${command.type}'时出错: ${error.message}` });
                } else {
                    logger.log("命令处理在执行期间被中止。");
                }
                this.commandQueue = [];
                break;
            }
        }

        this.isProcessing = false;
        agentStore.isLoading = false;
        this.abortController = null;
        logger.log("命令队列处理完成。");
    }

    private async _handleApiCall(): Promise<void> {
        const agentStore = useAgentStore();
        const configStore = useConfigStore();

        let assistantMessage: Message | null = null;
        
        const { response } = await this._callApi(agentStore.orderedMessages);

        if (configStore.activeConfig?.stream) {
            assistantMessage = await this._handleStream(response);
        } else {
            const responseData = response;
            logger.log("Agent: 收到 API 响应 (非流式):", responseData);
            const message = responseData.choices[0].message;

            const placeholderMessage = agentStore.addMessage({
                role: 'assistant',
                content: '', 
                type: 'text',
                status: 'streaming'
            });
            
            if (placeholderMessage) {
                agentStore.updateMessage({
                    messageId: placeholderMessage.id,
                    updates: {
                        content: message.content,
                        status: 'done',
                        streamCompleted: true
                    }
                });
                assistantMessage = agentStore.messagesById[placeholderMessage.id];
            }
        }
        
        if (!assistantMessage || !assistantMessage.id) {
            throw new Error("AI 未返回任何有效数据。");
        }

        const updatedMessage = agentStore.messagesById[assistantMessage.id];
        const finalContent = this._removePartialXmlTags(updatedMessage.content || '');
        
        agentStore.updateMessage({
            messageId: assistantMessage.id,
            updates: { status: 'done' }
        });

        const parsedQuestion = toolParserService.parseAskQuestionCall(finalContent);
        if (parsedQuestion) {
            logger.log("Agent: 在流结束后发现 <ask_question> 指令。", parsedQuestion);
            const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
            agentStore.updateMessage({
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
            agentStore.updateMessage({
                messageId: assistantMessage.id,
                updates: { content: cleanContent }
            });

            this.commandQueue.push({ type: 'EXECUTE_TOOL', payload: { parsedTool } });
            return;
        }
        
        logger.log("Agent: V3: 在流结束后未发现工具调用。回合结束。", { content: finalContent });
    }
    
    private async _handleToolExecution(payload: any): Promise<void> {
        const { parsedTool } = payload;
        const agentStore = useAgentStore();
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);
        
        const statusMessage = agentStore.addMessage({
            id: `msg_${Date.now()}`,
            role: 'assistant', type: 'tool_status',
            content: toolParserService.createStatusMessage(parsedTool),
        });

        if (!statusMessage) return;

        const toolResult = await toolParserService.executeTool(parsedTool);
        
        // --- 智能守卫: 执行前检查 ---
        const currentHistory = agentStore.orderedMessages;
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
            
            agentStore.replaceMessage(statusMessage.id, {
                id: `msg_${Date.now()}`,
                role: 'assistant', type: 'error',
                content: feedback, status: 'done'
            });

            return; // 中止 AI 回合
        }

        // --- 检查通过: 添加到 store 并继续 ---
        agentStore.replaceMessage(statusMessage.id, {
            id: statusMessage.id,
            role: 'assistant', type: 'tool_result',
            content: toolResult, status: 'done'
        });
        
        agentStore.addMessage({ ...toolMessage, id: `msg_${Date.now()}`, is_hidden: true });

        if (toolResult.startsWith("错误：")) {
            agentStore.incrementToolErrors();
            if (agentStore.consecutiveToolErrors >= 3) {
                 logger.error("AI 已连续3次工具调用失败。正在中止。");
                 agentStore.addMessage({ role: 'assistant', type: 'error', content: "AI可能遇到了困难，它连续3次工具调用失败或返回了错误的结果。" });
                 return; // 中止队列
            }
        } else {
            agentStore.resetToolErrors();
        }

        // --- 主动压缩检查 ---
        await this._checkAndCompressContextIfNeeded();

        // --- 继续回合 ---
        agentStore.incrementAiTurns();
        this._initiateAiTurn();
    }

    private async _callApi(history: Message[]): Promise<{ response: any }> {
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);

        if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
            const errorMsg = "没有激活的有效AI配置。请在设置中选择或创建一个配置。";
            logger.error(`Agent: ${errorMsg}`);
            throw new Error(errorMsg);
        }

        const apiMessages = history
            .filter(m => m.type !== 'tool_status' && m.type !== 'tool_result' && !m.is_hidden)
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
                    delete messageForApi.name;
                    messageForApi.content = String(m.content);
                }

                if (m.role === 'assistant' && m.tool_calls) {
                    messageForApi.tool_calls = m.tool_calls;
                }
                
                if (m.role !== 'assistant' || !m.tool_calls) {
                    delete messageForApi.name;
                }
                if(m.role !== 'tool'){
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
        
        logger.log("Agent: 准备调用 API...", { last_message: apiMessages.at(-1) });
        logger.setLastRequest(requestBody);

        try {
            const response = await openaiService.createChatCompletion(requestBody, activeConfig.value);
            return { response };
        } catch (error) {
            logger.error("Agent: 调用 API 失败:", error);
            throw error;
        }
    }

    private _removePartialXmlTags(content: string): string {
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

    private async _handleStream(openaiStream: any): Promise<Message | null> {
        const agentStore = useAgentStore();
        let assistantMessage: Message | null = null;
        let messageId: string | null = null;
        
        const pacedStream = createPacedStream(openaiStream);

        logger.log('[AgentService] > _handleStream: 开始消费 paced stream...');

        try {
            for await (const chunk of pacedStream) {
                if (this.abortController?.signal.aborted) {
                    logger.warn('[AgentService] > _handleStream: Stream 消费被中止。');
                    break;
                }

                if (chunk.done) {
                    break;
                }
                
                if (!assistantMessage && chunk.value) {
                    const newMsg = agentStore.addMessage({
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
                    agentStore.appendMessageContent({ messageId, chunk: chunk.value });
                }
            }
            
            logger.log('[AgentService] > _handleStream: Paced stream 完成。');

        } catch (error: any) {
           logger.error('[AgentService] > _handleStream: 消费 stream 时发生意外错误:', error);
           if (messageId) {
               agentStore.updateMessage({
                   messageId,
                   updates: { status: 'error' }
               });
           }
           throw new Error(`Stream 消费失败: ${error.message}`);
        }
        
        if (messageId) {
            agentStore.updateMessage({
                messageId,
                updates: { streamCompleted: true, status: 'done' }
            });
            logger.log(`[AgentService] > _handleStream: 消息 (ID: ${messageId}) 已标记为 streamCompleted 和 status done。`);
        } else {
            logger.log('[AgentService] > _handleStream: Stream 结束但没有任何内容，未创建消息。');
        }
        
        return assistantMessage;
    }

    private async _checkAndCompressContextIfNeeded(): Promise<void> {
        const agentStore = useAgentStore();
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);
        
        const currentHistory = agentStore.orderedMessages;
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
                agentStore.$patch({
                    messagesById: newMessagesById,
                    messageIds: newMessageIds,
                });

                logger.log(`[AgentCompress] 上下文压缩成功。新 token 数: ${optimizationResult.tokens}`);
            } else if (optimizationResult.status !== 'SUCCESS') {
                logger.error(`[AgentCompress] 主动压缩失败:`, optimizationResult.userMessage);
                agentStore.addMessage({ role: 'assistant', type: 'error', content: `上下文压缩失败: ${optimizationResult.userMessage}` });
            }
        }
    }
}

const agentService = new AgentService();
(window as any).agentService = agentService;
export default agentService;