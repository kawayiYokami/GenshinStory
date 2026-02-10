import { createOpenAI } from '@ai-sdk/openai';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createDeepSeek } from '@ai-sdk/deepseek';
import { streamText, generateText, stepCountIs, hasToolCall, type CoreMessage } from 'ai';
import logger from '../../features/app/services/loggerService';
import type { Config } from '@/features/app/stores/config';
import type { ProviderCapabilities } from '@/features/agent/types';

/**
 * @class LLMProviderService
 * @description 使用 Vercel AI SDK 统一管理多模态模型调用 (OpenAI, Google, DeepSeek)
 */
class LLMProviderService {
    private _resolveProvider(config: Config): 'openai' | 'google' | 'deepseek' {
        const model = (config.modelName || '').toLowerCase();

        if (model.includes('gemini')) {
            return 'google';
        }

        if (model.includes('deepseek') || model.includes('kimi')) {
            return 'deepseek';
        }

        return 'openai';
    }

    public getCapabilities(config: Config): ProviderCapabilities {
        const effectiveProvider = this._resolveProvider(config);
        const supportsStructuredToolCalls = (effectiveProvider === 'openai' || effectiveProvider === 'google' || effectiveProvider === 'deepseek')
            && (config.enableStructuredTools ?? true);

        return {
            supportsStructuredToolCalls,
            supportsStrictTools: false,
        };
    }

    /**
     * 根据配置创建对应的 Provider 实例
     * @param config 配置对象
     * @param extraParams 自定义参数(将注入到请求体中)
     */
    private _createProvider(config: Config, extraParams: Record<string, any> = {}) {
        const { apiKey, apiUrl } = config;
        const provider = this._resolveProvider(config);

        // 自定义 Fetch：用于将 extraParams 注入到请求体中
        const customFetch = async (input: RequestInfo | URL, init?: RequestInit) => {
            // 仅拦截 POST 请求 (API 调用)
            if (init && init.method === 'POST' && init.body && typeof init.body === 'string') {
                try {
                    const bodyObj = JSON.parse(init.body);
                    // 合并 extraParams
                    const newBody = { ...bodyObj, ...extraParams };
                    init.body = JSON.stringify(newBody);
                } catch (e) {
                    // 忽略解析错误，保持原样
                }
            }
            return fetch(input, init);
        };

        let baseUrl = apiUrl;

        if (provider === 'google') {
            if (baseUrl && !baseUrl.includes('/v1beta')) {
                baseUrl = baseUrl.replace(/\/$/, '');
                baseUrl = `${baseUrl}/v1beta`;
                logger.log(`[LLMProviderService] Google BaseURL 自动修正为: ${baseUrl}`);
            }

            return createGoogleGenerativeAI({
                baseURL: baseUrl || undefined,
                apiKey: apiKey,
                fetch: Object.keys(extraParams).length > 0 ? customFetch : undefined,
            });
        } else if (provider === 'deepseek') {
            if (baseUrl && baseUrl.includes('/chat/completions')) {
                baseUrl = baseUrl.split('/chat/completions')[0];
                logger.log(`[LLMProviderService] DeepSeek BaseURL 自动修正为: ${baseUrl}`);
            }

            return createDeepSeek({
                baseURL: baseUrl || undefined,
                apiKey: apiKey,
                fetch: Object.keys(extraParams).length > 0 ? customFetch : undefined,
            });
        } else {
            if (baseUrl && baseUrl.includes('/chat/completions')) {
                baseUrl = baseUrl.split('/chat/completions')[0];
                logger.log(`[LLMProviderService] OpenAI BaseURL 自动修正为: ${baseUrl}`);
            }

            return createOpenAI({
                baseURL: baseUrl || undefined,
                apiKey: apiKey,
                fetch: Object.keys(extraParams).length > 0 ? customFetch : undefined,
            });
        }
    }

    /**
     * 统一的聊天完成接口
     * @param messages 已转换的 CoreMessage[] (由 modelMessageAdapter.toModelMessages 生成)
     * @param config 配置对象
     * @param signal 中止信号
     * @param extraParams 自定义参数
     */
    public async createChatCompletion(
        messages: CoreMessage[],
        config: Config,
        signal: AbortSignal,
        extraParams: Record<string, any> = {}
    ): Promise<any> {
        if (!config || !config.apiKey) {
            throw new Error("[LLMProviderService] AI 配置无效: 缺少 API Key");
        }

        if (Object.keys(extraParams).length > 0) {
            logger.log("[LLMProviderService] 检测到自定义参数，将注入请求体:", extraParams);
        }

        const provider = this._createProvider(config, extraParams);
        const effectiveProvider = this._resolveProvider(config);
        const modelName = config.modelName || (effectiveProvider === 'google' ? 'gemini-2.5-flash' : '请输入模型名');

        const options = {
            model: effectiveProvider === 'google'
                ? provider(modelName)
                : effectiveProvider === 'deepseek'
                    ? provider(modelName)
                : (provider as any).chat(modelName),
            messages,
            temperature: config.temperature,
            abortSignal: signal,
        };

        logger.log(`[LLMProviderService] 调用 Vercel AI SDK. Provider: ${effectiveProvider}, Model: ${modelName}`);

        try {
            if (config.stream) {
                return await streamText(options);
            } else {
                return await generateText(options);
            }
        } catch (error) {
            logger.error("[LLMProviderService] API 调用失败:", error);
            throw error;
        }
    }

    /**
     * 结构化工具调用聊天接口（AI SDK tools）
     * @param messages 已转换的 CoreMessage[] (由 modelMessageAdapter.toModelMessages 生成)
     * @param config 配置对象
     * @param signal 中止信号
     * @param tools 工具定义（包含 execute 函数的会被 SDK 自动执行）
     * @param extraParams 自定义参数
     * @param maxSteps 最大步数（默认为配置的 maxIterations 或 10）
     */
    public async createStructuredChatCompletion(
        messages: CoreMessage[],
        config: Config,
        signal: AbortSignal,
        tools: Record<string, any>,
        extraParams: Record<string, any> = {},
        maxSteps?: number
    ): Promise<any> {
        if (!config || !config.apiKey) {
            throw new Error("[LLMProviderService] AI 配置无效: 缺少 API Key");
        }

        if (Object.keys(extraParams).length > 0) {
            logger.log("[LLMProviderService] Structured 模式检测到自定义参数，将注入请求体:", extraParams);
        }

        const provider = this._createProvider(config, extraParams);
        const effectiveProvider = this._resolveProvider(config);
        const modelName = config.modelName || (effectiveProvider === 'google' ? 'gemini-2.5-flash' : '请输入模型名');

        // 使用配置的 maxIterations 或传入的 maxSteps，默认 10
        const effectiveMaxSteps = maxSteps ?? config.maxIterations ?? 10;

        const options: any = {
            model: effectiveProvider === 'google'
                ? provider(modelName)
                : effectiveProvider === 'deepseek'
                    ? provider(modelName)
                : (provider as any).chat(modelName),
            messages,
            tools,
            // 使用 stopWhen 控制循环：
            // - stepCountIs: 限制最大步数
            // - hasToolCall('ask_choice'): 遇到 UI 工具时停止，等待用户交互
            stopWhen: [
                stepCountIs(effectiveMaxSteps),
                hasToolCall('ask_choice'),
            ],
            temperature: config.temperature,
            abortSignal: signal,
        };

        logger.log(`[LLMProviderService] 调用 Vercel AI SDK Structured Tools. Provider: ${effectiveProvider}, Model: ${modelName}, MaxSteps: ${effectiveMaxSteps}`);

        try {
            if (config.stream) {
                return await streamText(options);
            }
            return await generateText(options);
        } catch (error) {
            logger.error("[LLMProviderService] Structured API 调用失败:", error);
            throw error;
        }
    }
}

const llmProviderService = new LLMProviderService();
export default llmProviderService;
