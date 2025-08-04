import tokenizer from './tokenizerService.js';
import yaml from 'js-yaml';
import logger from './loggerService.js';
import { useConfigStore } from '@/stores/config';
import { storeToRefs } from 'pinia';

/**
 * @typedef {Object} OptimizationResult
 * @property {'SUCCESS' | 'ACTION_REQUIRED' | 'FATAL_ERROR'} status - 优化的结果状态。
 * @property {Array<Object>} [history] - 优化成功后的历史记录 (仅在 SUCCESS 时提供)。
 * @property {string} [userMessage] - 需要显示给用户的消息 (在 ACTION_REQUIRED 或 FATAL_ERROR 时提供)。
 */

/**
 * Service responsible for managing the conversation context to keep it within token limits.
 * It orchestrates a multi-step process of evaluation and optimization based on the approved specification.
 */
class ContextOptimizerService {
    constructor() {
        this.promptTemplate = null;
    }

    /**
     * 主公共入口点，用于处理和优化对话历史记录。
     * @param {Array<Object>} history - 完整的当前消息历史记录。
     * @param {number} maxTokens - 模型上下文允许的最大 Token 数。
     * @returns {Promise<OptimizationResult>} 一个包含优化状态和结果的对象。
     */
    async processContext(history, maxTokens) {
        logger.log('[Optimizer] 开始上下文处理...');

        const threshold = maxTokens * 0.9;
        const initialTokenCount = this._calculateTotalTokens(history);

        if (initialTokenCount <= threshold) {
            logger.log(`[Optimizer] 上下文在限制内 (${initialTokenCount} <= ${threshold})。无需优化。`);
            return { status: 'SUCCESS', history: history, tokens: initialTokenCount };
        }

        logger.log(`[Optimizer] 上下文超出限制 (${initialTokenCount} > ${threshold})。启动优化...`);

        // 步骤 1: 分离系统提示词和对话历史，确保系统提示词永远不被压缩。
        const systemPrompt = history.find(m => m.role === 'system');
        const chatHistory = history.filter(m => m.role !== 'system');

        // 步骤 2: 对纯粹的对话历史进行分割。
        const { earlyHistory, recentHistory } = this._separateHistory(chatHistory);
        logger.log(`[Optimizer] 分离完成。早期历史: ${earlyHistory.length}条, 近期历史: ${recentHistory.length}条。`);

        if (!earlyHistory || earlyHistory.length === 0) {
            logger.warn('[Optimizer] 最近的对话本身已超出 Token 限制，无法压缩。');
            return {
                status: 'ACTION_REQUIRED',
                userMessage: '本次调用返回的资料过多，为保证对话顺畅，请尝试减少请求的资料量或缩小查询范围。'
            };
        }

        // 步骤 3: 压缩早期对话。
        let summary;
        try {
            logger.log('[Optimizer] 准备摘要的早期历史内容:', earlyHistory);
            summary = await this._summarizeHistory(earlyHistory);
            logger.log('[Optimizer] 从AI获取的摘要内容:', summary);
        } catch (error) {
            logger.error('[Optimizer] AI 摘要失败:', error);
            return {
                status: 'FATAL_ERROR',
                userMessage: `上下文摘要生成失败: ${error.message}`
            };
        }

        const summaryMessage = { role: 'user', content: `[系统摘要] ${summary}` };
        const summaryTokenCount = this._calculateTotalTokens([summaryMessage]);

        // 风险评估：场景三 - 仅摘要部分就已超限。
        if (summaryTokenCount > threshold) {
            logger.error(`[Optimizer] 致命错误: 摘要本身 (${summaryTokenCount} tokens) 已超出最大限制 (${threshold})。`);
            return {
                status: 'FATAL_ERROR',
                userMessage: '对话已崩溃，无法继续处理。请开启新的对话。'
            };
        }

        // 步骤 4: 重组上下文。
        // 注意：systemPrompt 已在流程开始时被安全分离。
        const newHistory = [systemPrompt, summaryMessage, ...recentHistory].filter(Boolean);
        const finalTokenCount = this._calculateTotalTokens(newHistory);

        // 风险评估：场景二 - 组合后依然超限。
        if (finalTokenCount > threshold) {
            logger.warn(`[Optimizer] 压缩后上下文仍然超限 (${finalTokenCount} > ${threshold})。`);
            return {
                status: 'ACTION_REQUIRED',
                userMessage: '本次调用返回的资料过多，为保证对话顺畅，请尝试减少请求的资料量或缩小查询范围。'
            };
        }

        // 风险评估：场景一 - 成功。
        logger.log(`[Optimizer] 优化成功。最终 Token 数: ${finalTokenCount}`);
        logger.log('[Optimizer] 返回的最终历史记录:', newHistory);
        return { status: 'SUCCESS', history: newHistory, tokens: finalTokenCount };
    }

    /**
     * 公共方法，用于计算给定历史记录数组的总 Token 数。
     * @param {Array<Object>} history - 消息历史记录。
     * @returns {number} 总 Token 数。
     */
    calculateHistoryTokens(history) {
        return this._calculateTotalTokens(history);
    }

    /**
     * 将历史记录分割为“早期历史”（待压缩）和“近期历史”（保留）。
     * 策略：保留最后两条消息作为近期历史，其余的作为早期历史。
     * @param {Array<Object>} history - 完整的消息历史记录。
     * @returns {{earlyHistory: Array<Object>, recentHistory: Array<Object>}}
     * @private
     */
    _separateHistory(history) {
        // 如果历史记录不足或等于2条，则没有可供压缩的“早期历史”。
        // 整个历史都将被视为“近期历史”，以处理对话初期的边界情况。
        if (history.length <= 2) {
            return { earlyHistory: [], recentHistory: history };
        }

        // 分割点是倒数第二条消息的位置。
        const separationIndex = history.length - 2;
        const earlyHistory = history.slice(0, separationIndex);
        const recentHistory = history.slice(separationIndex);

        return { earlyHistory, recentHistory };
    }

    /**
     * 调用模型对历史记录块进行摘要。
     * @param {Array<Object>} historyChunk - 需要摘要的历史记录部分。
     * @returns {Promise<string>} 摘要文本。
     * @private
     */
    async _summarizeHistory(historyChunk) {
        logger.log(`[Optimizer] 正在摘要 ${historyChunk.length} 条消息...`);

        // 1. 确保 Prompt 模板已加载
        await this._loadPromptTemplate();

        // 2. 预处理历史记录
        const { dialogue_block, data_block } = this._preprocessHistoryForSummary(historyChunk);

        // 3. 组装最终 Prompt
        if (!this.promptTemplate) {
            throw new Error("摘要器提示词模板未加载。");
        }
        const { final_prompt_structure, role_definition, compression_guide } = this.promptTemplate;
        const full_guide = `${role_definition}\n\n${compression_guide}`;
        const finalPrompt = final_prompt_structure
            .replace('{dialogue_block}', dialogue_block)
            .replace('{data_block}', data_block || '无')
            .replace('{compression_guide}', full_guide);

        // 4. 调用 AI 进行压缩
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
            temperature: 0.5, // Factual summary
            stream: false,
        };

        logger.log('[Optimizer] 正在调用摘要 AI...', { url: chatUrl });
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
        
        logger.log('[Optimizer] 摘要成功。');
        return compressedContent;
    }

    /**
     * Loads the JSON prompt template for the compressor AI.
     * Caches the template after the first load.
     * @returns {Promise<void>}
     * @private
     */
    async _loadPromptTemplate() {
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
            this.promptTemplate = yaml.load(yamlText);
            logger.log('[Optimizer] 压缩器提示词模板加载成功。');
        } catch (error) {
            logger.error('[Optimizer] 加载压缩器提示词模板失败:', error);
            this.promptTemplate = {
              "role_definition": "你是一个精通对话摘要的AI助手。你的任务是阅读一段包含'用户'和'助理'的对话历史，以及助理调用工具返回的'相关资料'，然后生成一个简洁、精确、保留所有关键信息的摘要。",
              "compression_guide": "请遵循以下规则生成摘要：\n1. 摘要必须以第三人称视角编写。\n2. 必须提及所有重要的事实、决策、问题和解决方案。\n3. 如果对话中包含了工具的使用（如 search_docs, read_doc），必须在摘要中明确指出工具调用的目的和其返回的关键结果。\n4. 保持摘要的客观性和中立性。\n5. 最终输出只包含摘要内容，不要有任何额外的解释或对话。",
              "final_prompt_structure": "## 对话记录\n{dialogue_block}\n\n## 相关资料\n{data_block}\n\n## 摘要指令\n{compression_guide}"
            };
        }
    }

    /**
     * Pre-processes the history chunk into dialogue and data blocks for summary.
     * @param {Array<Object>} historyChunk - The part of history to be summarized.
     * @returns {{dialogue_block: string, data_block: string}}
     * @private
     */
    _preprocessHistoryForSummary(historyChunk) {
        const dialogueEntries = [];
        const dataEntries = [];

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
     * @param {Array<Object>} history - 消息历史记录。
     * @returns {number} 总 Token 数。
     * @private
     */
    _calculateTotalTokens(history) {
        if (!history) return 0;
        return history.reduce((acc, msg) => {
            const contentTokens = tokenizer.countTokens(msg.content || '');
            return acc + contentTokens;
        }, 0);
    }
}

const contextOptimizerService = new ContextOptimizerService();
export default contextOptimizerService;