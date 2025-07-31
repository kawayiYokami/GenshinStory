import logger from './loggerService.js';
import { useConfigStore } from '@/stores/config';
import { useAgentStore } from '@/stores/agent';
import { storeToRefs } from 'pinia';
import openaiService from './openaiService.js';
import { createPacedStream } from './streamingService.js';
import contextOptimizerService from './contextOptimizerService.js';
import toolParserService from './toolParserService.js';
import localTools from './localToolsService.js';

// Agent 核心逻辑
class AgentService {
    constructor() {
        this.commandQueue = [];
        this.isProcessing = false;
        this.abortController = null;
    }
    
    stop() {
        if (this.abortController) {
            this.abortController.abort();
            logger.log("Agent: 请求被用户中止。");
        }
    }

    /**
     * 统一的用户消息入口点。
     * @param {string} userContent - The text content from the user.
     */
    async sendMessage(userContent) {
        const agentStore = useAgentStore();
        
        // 1. Add user message to the store
        agentStore.addMessage({ role: 'user', content: userContent, id: `msg_${Date.now()}` });
        
        // 2. Proactively check context and compress if needed
        await this._checkAndCompressContextIfNeeded();

        // 3. Start the AI processing turn
        this._initiateAiTurn();
    }
    
    // This is a placeholder now, the new entry point is sendMessage
    startTurn() {
        this._initiateAiTurn();
    }

    _initiateAiTurn() {
        this.abortController = new AbortController();
        this.commandQueue.push({ type: 'CALL_AI' });
        if (!this.isProcessing) {
            this.processQueue();
        }
    }

    async processQueue() {
        const agentStore = useAgentStore();
        this.isProcessing = true;
        agentStore.isLoading = true;
        agentStore.resetCounters();

        while (this.commandQueue.length > 0) {
            if (this.abortController.signal.aborted) {
                logger.log("Command queue processing was aborted.");
                this.commandQueue = [];
                break;
            }
            
            const command = this.commandQueue.shift();
            logger.log("Processing command:", command);

            try {
                if (command.type === 'CALL_AI') {
                    if (agentStore.consecutiveAiTurns >= 10) {
                        logger.error("AI turn limit reached. Aborting.");
                        agentStore.addMessage({ role: 'assistant', type: 'error', content: "AI已连续迭代10次，为防止失控，已自动中断。" });
                        break;
                    }
                    await this._handleApiCall();
                } else if (command.type === 'EXECUTE_TOOL') {
                    await this._handleToolExecution(command.payload);
                }
            } catch (error) {
                 if (error.name !== 'AbortError') {
                    logger.error("Error processing command:", { command, error });
                    agentStore.addMessage({ role: 'assistant', type: 'error', content: `处理命令'${command.type}'时出错: ${error.message}` });
                } else {
                    logger.log("Command processing was aborted during execution.");
                }
                this.commandQueue = [];
                break;
            }
        }

        this.isProcessing = false;
        agentStore.isLoading = false;
        this.abortController = null;
        logger.log("Command queue processing finished.");
    }

    async _handleApiCall() {
        const agentStore = useAgentStore();
        const configStore = useConfigStore();

        let assistantMessage = null;
        let finalContent = '';

        const { response } = await this._callApi(agentStore.orderedMessages);

        if (configStore.activeConfig.stream) {
            assistantMessage = await this._handleStream(response);
        } else {
            const responseData = await response.json();
            logger.log("Agent: 收到 API 响应 (非流式):", responseData);
            const message = responseData.choices[0].message;

            if (message.tool_calls) {
                const parsedTool = toolParserService.parseJsonToolCall(message.tool_calls[0]);
                if (parsedTool) {
                    logger.log("Agent: 在非流式响应中发现结构化工具调用。", parsedTool);
                    this.commandQueue.push({ type: 'EXECUTE_TOOL', payload: { parsedTool } });
                    agentStore.addMessage({ role: 'assistant', content: null, tool_calls: message.tool_calls });
                } else {
                    logger.error("Agent: 无法解析来自 API 的工具调用。", message.tool_calls[0]);
                }
                return;
            }
            
            assistantMessage = agentStore.addMessage(message);
        }
        
        if (!assistantMessage || !assistantMessage.id) {
            throw new Error("AI 未返回任何有效数据。");
        }

        const updatedMessage = agentStore.messagesById[assistantMessage.id];
        finalContent = this._removePartialXmlTags(updatedMessage.content || '');
        
        agentStore.updateMessage({
            messageId: assistantMessage.id,
            updates: {
                status: 'done'
            }
        });

        // 优先检查 <ask_question> 指令
        const parsedQuestion = toolParserService.parseAskQuestionCall(finalContent);
        if (parsedQuestion) {
            logger.log("Agent: 在流结束后发现 <ask_question> 指令。", parsedQuestion);
            
            // 从消息气泡中移除XML原文
            const cleanContent = finalContent.replace(parsedQuestion.xml, '').trim();
            agentStore.updateMessage({
                messageId: assistantMessage.id,
                updates: { content: cleanContent }
            });

            // 将解析出的问题和选项附加到消息对象上，供UI使用
            agentStore.updateMessage({
                messageId: assistantMessage.id,
                updates: {
                    question: {
                        text: parsedQuestion.question,
                        suggestions: parsedQuestion.suggestions
                    }
                }
            });
            
            // 回合结束，不需要进一步操作
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
    
    async _handleToolExecution(payload) {
        const { parsedTool } = payload;
        const agentStore = useAgentStore();
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);
        
        const statusMessage = agentStore.addMessage({
            id: `msg_${Date.now()}`,
            role: 'assistant', type: 'tool_status',
            content: toolParserService.createStatusMessage(parsedTool),
        });

        const toolResult = await toolParserService.executeTool(parsedTool);
        
        // --- Smart Guard: Pre-flight Check ---
        const currentHistory = agentStore.orderedMessages;
        const currentHistoryTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
        
        const toolMessage = { role: "tool", name: parsedTool.name, content: toolResult };
        const toolMessageTokens = contextOptimizerService.calculateHistoryTokens([toolMessage]);

        const maxTokens = activeConfig.value.maxTokens;
        const threshold = maxTokens * 0.9;
        const futureTotalTokens = currentHistoryTokens + toolMessageTokens;

        if (futureTotalTokens > threshold) {
            const availableSpace = Math.max(0, Math.floor(threshold - currentHistoryTokens));
            logger.error(`[AgentGuard] 工具结果过大，将导致上下文溢出。`, { futureTotalTokens, threshold, availableSpace });

            let feedback = `错误：工具返回结果过大 (${toolMessageTokens} tokens)，超过了当前可用的空间 (${availableSpace} tokens)。为避免对话崩溃，该结果已被丢弃。`;
            
            if (parsedTool.name === 'read_doc' && parsedTool.params.args) {
                const docRequests = toolParserService.parseReadDocRequests(parsedTool.params.args);
                const metadataPromises = docRequests.map(req => localTools.getDocMetadata(req.path));
                const metadataResults = await Promise.all(metadataPromises);
                const fileSizes = metadataResults
                    .map((meta, index) => meta ? `${docRequests[index].path}: ${meta.totalTokens} tokens` : `${docRequests[index].path}: 未知大小`)
                    .join(', ');
                feedback += ` 各文件大小如下: [${fileSizes}]。请减少请求文件数量，或对大文件使用 \`line_range\` 参数。`;
            }

            agentStore.replaceMessage(statusMessage.id, {
                id: `msg_${Date.now()}`,
                role: 'assistant', type: 'error',
                content: feedback, status: 'done'
            });

            return; // Abort the AI turn.
        }

        // --- Check Passed: Add to store and continue ---
        agentStore.replaceMessage(statusMessage.id, {
            id: statusMessage.id,
            role: 'assistant', type: 'tool_result',
            content: toolResult, status: 'done'
        });
        
        agentStore.addMessage({ ...toolMessage, id: `msg_${Date.now()}`, is_hidden: true });

        if (toolResult.startsWith("错误：")) {
            agentStore.incrementToolErrors();
            if (agentStore.consecutiveToolErrors >= 3) {
                 logger.error("AI has failed 3 consecutive tool calls. Aborting.");
                 agentStore.addMessage({ role: 'assistant', type: 'error', content: "AI可能遇到了困难，它连续3次工具调用失败或返回了错误的结果。" });
                 return; // Abort the queue
            }
        } else {
            agentStore.resetToolErrors();
        }

        // --- Proactive Compression Check ---
        await this._checkAndCompressContextIfNeeded();

        // --- Continue the turn ---
        agentStore.incrementAiTurns();
        this._initiateAiTurn();
    }

    async _callApi(history) {
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);

        if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
            const errorMsg = "没有激活的有效AI配置。请在设置中选择或创建一个配置。";
            logger.error(`Agent: ${errorMsg}`);
            throw new Error(errorMsg);
        }
        
        const apiMessages = history
            .filter(m => m.type !== 'tool_status' && m.type !== 'tool_result')
            .map(({ role, content, name, tool_calls }) => {
                const msg = { role, content };
                if (name) msg.name = name;
                if (tool_calls) msg.tool_calls = tool_calls;
                return msg;
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
            // The new service handles client initialization and rate limiting internally.
            const response = await openaiService.createChatCompletion(requestBody, activeConfig.value);
            return { response }; // Context is no longer passed from here
        } catch (error) {
            logger.error("Agent: 调用 API 失败:", error);
            throw error; // Re-throw for the caller to handle.
        }
    }

    _removePartialXmlTags(content) {
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

    async _handleStream(openaiStream) {
        const agentStore = useAgentStore();
        let assistantMessage = null;
        let messageId = null;
        
        const pacedStream = createPacedStream(openaiStream);

        logger.log('[AgentService] > _handleStream: Starting to consume paced stream...');

        try {
            for await (const chunk of pacedStream) {
                if (this.abortController.signal.aborted) {
                    logger.warn('[AgentService] > _handleStream: Stream consumption was aborted.');
                    break;
                }

                if (chunk.done) {
                    break;
                }
                
                // Create the message object on the first valid text chunk.
                if (!assistantMessage && chunk.value) {
                    assistantMessage = agentStore.addMessage({
                        role: 'assistant',
                        content: '',
                        type: 'text',
                        status: 'streaming',
                    });
                    messageId = assistantMessage.id;
                    logger.log(`[AgentService] > _handleStream: Created new message (ID: ${messageId}).`);
                }
                
                if (messageId && chunk.value) {
                    agentStore.appendMessageContent({ messageId, chunk: chunk.value });
                }
            }
            
            logger.log('[AgentService] > _handleStream: Paced stream finished.');

        } catch (error) {
           // AbortError is now handled by the check inside the loop, so we only need to catch unexpected errors.
           logger.error('[AgentService] > _handleStream: Unexpected error while consuming stream:', error);
           if (messageId) {
               agentStore.updateMessage({
                   messageId,
                   updates: { status: 'error' }
               });
           }
           throw new Error(`Stream consumption failed: ${error.message}`);
        }
        
        if (messageId) {
            // Mark the stream as fully completed in the store. This is the final, crucial step.
            agentStore.updateMessage({
                messageId,
                updates: { streamCompleted: true, status: 'done' }
            });
            logger.log(`[AgentService] > _handleStream: Message (ID: ${messageId}) marked as streamCompleted and status done.`);
        } else {
            logger.log('[AgentService] > _handleStream: Stream ended without any content, no message created.');
        }
        
        return assistantMessage;
    }

    async _checkAndCompressContextIfNeeded() {
        const agentStore = useAgentStore();
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);
        
        const currentHistory = agentStore.orderedMessages;
        const currentTokens = contextOptimizerService.calculateHistoryTokens(currentHistory);
        const maxTokens = activeConfig.value.maxTokens;
        const threshold = maxTokens * 0.9;

        if (currentTokens > threshold) {
            logger.log(`[AgentCompress] 上下文 (${currentTokens}) 超出动态阈值 (${threshold})，触发主动压缩。`);
            const optimizationResult = await contextOptimizerService.processContext(currentHistory, maxTokens);

            if (optimizationResult.status === 'SUCCESS' && optimizationResult.history) {
                // Replace the entire history state with the compressed version.
                const newMessagesById = {};
                const newMessageIds = [];
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
window.agentService = agentService;
export default agentService;