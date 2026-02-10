import tokenizerService from '@/lib/tokenizer/tokenizerService';
import yaml from 'js-yaml';
import logger from '../../app/services/loggerService';
import { useConfigStore } from '@/features/app/stores/config';
import { storeToRefs } from 'pinia';
import type { Message, MessageContentPart } from '@/features/agent/stores/agentStore';

// --- 类型定义 ---

type OptimizationStatus = 'SUCCESS' | 'ACTION_REQUIRED' | 'FATAL_ERROR';

interface OptimizationResult {
    status: OptimizationStatus;
    history?: Message[];
    userMessage?: string;
    tokens?: number;
}

interface PromptTemplate {
    final_prompt_structure: string;
    role_definition: string;
    compression_guide: string;
    [key: string]: any;
}

/**
 * 负责管理对话上下文以使其保持在 token 限制内的服务。
 * 它根据批准的规范协调一个多步骤的评估和优化过程。
 */
class ContextOptimizerService {
    private promptTemplate: PromptTemplate | null = null;

    /**
     * 主公共入口点，用于处理和优化对话历史记录。
     * @param history 完整的当前消息历史记录。
     * @param maxContextLength 模型上下文允许的最大 Token 数。
     * @returns 一个包含优化状态和结果的对象。
     */
    public async processContext(history: Message[], maxContextLength: number): Promise<OptimizationResult> {
        logger.log('[优化器] 开始上下文处理...');

        const threshold = maxContextLength * 0.9;
        const initialTokenCount = this._calculateTotalTokens(history);

        if (initialTokenCount <= threshold) {
            logger.log(`[优化器] 上下文在限制内 (${initialTokenCount} <= ${threshold})。无需优化。`);
            return { status: 'SUCCESS', history: history, tokens: initialTokenCount };
        }

        logger.log(`[优化器] 上下文超出限制 (${initialTokenCount} > ${threshold})。启动优化...`);

        // 分离系统提示和聊天历史
        const systemPrompt = history.find(m => m.role === 'system');
        const chatHistory = history.filter(m => m.role !== 'system');

        // 检查最后一条消息是否是用户消息，如果是则保留
        let lastUserMessage: Message | null = null;
        if (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'user') {
            lastUserMessage = chatHistory[chatHistory.length - 1];
            // 从聊天历史中移除最后一条用户消息，因为它将被单独保留
            chatHistory.pop();
        }

        // 对剩余的聊天历史进行摘要
        let summary: string;
        try {
            logger.log('[优化器] 准备摘要的聊天历史内容:', chatHistory);
            summary = await this._summarizeHistory(chatHistory);
            logger.log('[优化器] 从AI获取的摘要内容:', summary);
        } catch (error: any) {
            logger.error('[优化器] AI 摘要失败:', error);
            return {
                status: 'FATAL_ERROR',
                userMessage: `上下文摘要生成失败: ${error.message}`
            };
        }

        const summaryMessage: Message = { role: 'user', content: `[系统摘要] ${summary}`, id: `msg_${Date.now()}`, createdAt: new Date().toISOString() };
        const summaryTokenCount = this._calculateTotalTokens([summaryMessage]);

        if (summaryTokenCount > threshold) {
            logger.error(`[优化器] 致命错误: 摘要本身 (${summaryTokenCount} tokens) 已超出最大限制 (${threshold})。`);
            return {
                status: 'FATAL_ERROR',
                userMessage: '对话已崩溃，无法继续处理。请开启新的对话。'
            };
        }

        // 按照 [系统提示] + [摘要] + [被保留的用户消息（如果存在）] 的结构重组上下文
        const newHistory = [systemPrompt, summaryMessage, lastUserMessage].filter(Boolean) as Message[];
        const finalTokenCount = this._calculateTotalTokens(newHistory);

        if (finalTokenCount > threshold) {
            logger.warn(`[优化器] 压缩后上下文仍然超限 (${finalTokenCount} > ${threshold})。`);
            return {
                status: 'ACTION_REQUIRED',
                userMessage: '本次调用返回的资料过多，为保证对话顺畅，请尝试减少请求的资料量或缩小查询范围。'
            };
        }

        logger.log(`[优化器] 优化成功。最终 Token 数: ${finalTokenCount}`);
        logger.log('[优化器] 返回的最终历史记录:', newHistory);

        return { status: 'SUCCESS', history: newHistory, tokens: finalTokenCount };
    }

    /**
     * 公共方法，用于计算给定历史记录数组的总 Token 数。
     * @param history 消息历史记录。
     * @returns 总 Token 数。
     */
    public calculateHistoryTokens(history: Message[]): number {
        return this._calculateTotalTokens(history);
    }

    /**
     * 将历史记录分割为“早期历史”（待压缩）和“近期历史”（保留）。
     */
    private _separateHistory(history: Message[]): { earlyHistory: Message[], recentHistory: Message[] } {
        if (history.length <= 2) {
            return { earlyHistory: [], recentHistory: history };
        }
        const separationIndex = history.length - 2;
        const earlyHistory = history.slice(0, separationIndex);
        const recentHistory = history.slice(separationIndex);
        return { earlyHistory, recentHistory };
    }

    /**
     * 调用模型对历史记录块进行摘要。
     */
    private async _summarizeHistory(historyChunk: Message[]): Promise<string> {
        logger.log(`[优化器] 正在摘要 ${historyChunk.length} 条消息...`);
        await this._loadPromptTemplate();

        const { dialogue_block, data_block } = this._preprocessHistoryForSummary(historyChunk);

        if (!this.promptTemplate) {
            throw new Error("摘要器提示词模板未加载。");
        }
        const { final_prompt_structure, role_definition, compression_guide } = this.promptTemplate;
        const full_guide = `${role_definition}\n\n${compression_guide}`;
        const finalPrompt = final_prompt_structure
            .replace('{dialogue_block}', dialogue_block)
            .replace('{data_block}', data_block || '无')
            .replace('{compression_guide}', full_guide);

        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);

        if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
            throw new Error("没有激活的有效AI配置，无法执行摘要。");
        }

        const baseUrl = activeConfig.value.apiUrl.replace(/\/$/, '');
        const chatUrl = `${baseUrl}/chat/completions`;

        const requestBody = {
            model: activeConfig.value.modelName,
            messages: [{ role: 'user', content: finalPrompt }],
            temperature: 0.5,
            stream: false,
        };

        logger.log('[优化器] 正在调用摘要 AI...', { url: chatUrl });
        const response = await fetch(chatUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${activeConfig.value.apiKey}` },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`摘要器AI API 请求失败: ${response.status} - ${response.statusText}. 响应: ${errorText}`);
        }

        const responseData = await response.json();
        const compressedContent = responseData.choices[0]?.message?.content;

        if (!compressedContent) {
            throw new Error("摘要器AI响应无效或为空。");
        }

        logger.log('[优化器] 摘要成功。');
        return compressedContent;
    }

    /**
     * 加载用于压缩器 AI 的 JSON 提示模板。
     */
    private async _loadPromptTemplate(): Promise<void> {
        if (this.promptTemplate) {
            return;
        }
        try {
            const v = Date.now();
            const response = await fetch(`/prompts/optimizers/context_compressor_prompt.yaml?v=${v}`);
            if (!response.ok) {
                throw new Error(`无法加载压缩器提示词模板: ${response.statusText}`);
            }
            const yamlText = await response.text();
            this.promptTemplate = yaml.load(yamlText) as PromptTemplate;
            logger.log('[优化器] 压缩器提示词模板加载成功。');
        } catch (error) {
            logger.error('[优化器] 加载压缩器提示词模板失败:', error);
            this.promptTemplate = {
              "role_definition": "你是一个精通对话摘要的AI助手。你的任务是阅读一段包含'用户'和'助理'的对话历史，以及助理调用工具返回的'相关资料'，然后生成一个简洁、精确、保留所有关键信息的摘要。",
              "compression_guide": "请遵循以下规则生成摘要：\n1. 摘要必须以第三人称视角编写。\n2. 必须提及所有重要的事实、决策、问题和解决方案。\n3. 如果对话中包含了工具的使用（如 search_docs, read_doc），必须在摘要中明确指出工具调用的目的和其返回的关键结果。\n4. 保持摘要的客观性和中立性。\n5. 最终输出只包含摘要内容，不要有任何额外的解释或对话。",
              "final_prompt_structure": "## 对话记录\n{dialogue_block}\n\n## 相关资料\n{data_block}\n\n## 摘要指令\n{compression_guide}"
            };
        }
    }

    /**
     * 将历史记录块预处理为对话和数据块以供摘要。
     */
    private _preprocessHistoryForSummary(historyChunk: Message[]): { dialogue_block: string, data_block: string } {
        const dialogueEntries: string[] = [];
        const dataEntries: string[] = [];

        for (const message of historyChunk) {
            if (message.role === 'user' && message.content) {
                dialogueEntries.push(`用户: ${message.content}`);
            } else if (message.role === 'assistant' && message.content) {
                dialogueEntries.push(`助理: ${message.content}`);
            } else if (message.role === 'tool') {
                const source = message.name || '未知工具';
                const content = message.content || '无内容';
                dataEntries.push(`资料来源: ${source}\n内容: ${content}\n---`);
            }
        }

        return {
            dialogue_block: dialogueEntries.join('\n'),
            data_block: dataEntries.join('\n')
        };
    }

    /**
     * 计算给定历史记录数组的总 Token 数。
     */
    private _calculateTotalTokens(history: Message[]): number {
        if (!history) return 0;
        return history.reduce((acc, msg) => {
            const content = Array.isArray(msg.content) ? msg.content.map((c: MessageContentPart) => c.text || '').join(' ') : msg.content;
            const contentTokens = tokenizerService.countTokens(content || '');
            return acc + contentTokens;
        }, 0);
    }
}

const contextOptimizerService = new ContextOptimizerService();
export default contextOptimizerService;
export { ContextOptimizerService };