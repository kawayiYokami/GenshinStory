import { createOpenAI } from '@ai-sdk/openai';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { streamText, generateText, type CoreMessage } from 'ai';
import logger from '../../features/app/services/loggerService';
import type { Config } from '@/features/app/stores/config';

/**
 * @class OpenaiService
 * @description 使用 Vercel AI SDK 统一管理多模态模型调用 (OpenAI Compatible & Gemini Native)
 */
class OpenaiService {
    /**
     * 根据配置创建对应的 Provider 实例
     * @param config 配置对象
     * @param extraParams 自定义参数(将注入到请求体中)
     */
    private _createProvider(config: Config, extraParams: Record<string, any> = {}) {
        const { apiKey, apiUrl, provider } = config;

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
                logger.log(`[OpenaiService] Google BaseURL 自动修正为: ${baseUrl}`);
            }

            return createGoogleGenerativeAI({
                baseURL: baseUrl || undefined,
                apiKey: apiKey,
                // Google Provider 也可以支持 customFetch，但通常参数格式不同，暂时也加上以防万一
                fetch: Object.keys(extraParams).length > 0 ? customFetch : undefined,
            });
        } else {
            if (baseUrl && baseUrl.includes('/chat/completions')) {
                baseUrl = baseUrl.split('/chat/completions')[0];
                logger.log(`[OpenaiService] OpenAI BaseURL 自动修正为: ${baseUrl}`);
            }

            return createOpenAI({
                baseURL: baseUrl || undefined,
                apiKey: apiKey,
                fetch: Object.keys(extraParams).length > 0 ? customFetch : undefined,
            });
        }
    }

    /**
     * 将任意格式的消息转换为 Vercel SDK 严格要求的 CoreMessage
     */
    private _normalizeMessages(rawMessages: any[]): CoreMessage[] {
        return rawMessages.map((msg, index) => {
            // 1. 规范化 Role
            let role = msg.role;
            if (role !== 'user' && role !== 'assistant' && role !== 'system') {
                logger.warn(`[OpenaiService] 消息 ${index} 的 role '${role}' 不合法，重置为 'user'`);
                role = 'user';
            }

            // 2. 规范化 Content
            let content = msg.content;

            if (content === null || content === undefined) {
                content = '';
            }

            // 如果是数组，检查每一项是否合法
            if (Array.isArray(content)) {
                content = content.map((part: any) => {
                    // 确保 part 有 type，或者尝试推断
                    if (!part.type) {
                        if (part.image_url || part.image) {
                             const url = part.image || part.image_url?.url;
                             if (url) return { type: 'image', image: url };
                        }
                        return { type: 'text', text: String(part) };
                    }

                    // 文本类型
                    if (part.type === 'text') {
                        return { type: 'text', text: part.text || '' };
                    }

                    // 图片类型
                    if (part.type === 'image' || part.type === 'image_url') {
                        // 提取 URL
                        const imageUrl = part.image || (part.image_url ? part.image_url.url : null);

                        // 关键修复：必须有有效的 URL
                        if (imageUrl && typeof imageUrl === 'string' && imageUrl.trim() !== '') {
                             // 如果是 base64 但没前缀，尝试补全 (虽然通常不推荐猜，但为了容错)
                             // Vercel SDK 需要完整的 data URI 或 HTTP URL
                             return { type: 'image', image: imageUrl };
                        } else {
                            // 如果图片 URL 无效，降级为空文本或者警告
                            logger.warn(`[OpenaiService] 消息 ${index} 包含无效的图片 URL，已忽略。`, part);
                            // 返回空文本 part 占位，避免 map 返回 null (需要 filter)
                            return null;
                        }
                    }

                    // 其他类型转 json string
                    return { type: 'text', text: JSON.stringify(part) };
                }).filter(p => p !== null); // 过滤掉无效的 part
            }

            // 3. 构建 CoreMessage
            if (role === 'assistant') {
                // Assistant content must be string or TextPart[]
                if (Array.isArray(content)) {
                    content = content
                        .filter((p: any) => p.type === 'text')
                        .map((p: any) => ({ type: 'text', text: p.text }));

                    if (content.length === 0) content = '';
                }
                return { role: 'assistant', content } as CoreMessage;
            }

            if (role === 'system') {
                // System content must be string
                if (Array.isArray(content)) {
                    content = content.map((p: any) => p.text).join('\n');
                }
                return { role: 'system', content } as CoreMessage;
            }

            // User: 必须保证 content 不为空 (如果是数组)
            if (role === 'user' && Array.isArray(content) && content.length === 0) {
                 content = ''; // 空数组转空字符串
            }

            return { role: 'user', content } as CoreMessage;
        });
    }

    /**
     * 统一的聊天完成接口
     */
    public async createChatCompletion(requestBody: any, config: Config, signal: AbortSignal): Promise<any> {
        if (!config || !config.apiKey) {
            throw new Error("[OpenaiService] AI 配置无效: 缺少 API Key");
        }

        // 1. 提取自定义参数 (从 requestBody 中排除标准字段)
        const standardKeys = ['messages', 'model', 'stream', 'temperature'];
        const extraParams: Record<string, any> = {};
        Object.keys(requestBody).forEach(key => {
            if (!standardKeys.includes(key)) {
                extraParams[key] = requestBody[key];
            }
        });

        if (Object.keys(extraParams).length > 0) {
            logger.log("[OpenaiService] 检测到自定义参数，将注入请求体:", extraParams);
        }

        // 2. 创建 Provider (传入 extraParams 以便注入 Fetch)
        const provider = this._createProvider(config, extraParams);
        const modelName = config.modelName || (config.provider === 'google' ? 'gemini-2.5-flash' : '请输入模型名');

        // 3. 严格清洗消息
        const messages = this._normalizeMessages(requestBody.messages);

        const options = {
            model: config.provider === 'google'
                ? provider(modelName)
                : (provider as any).chat(modelName),
            messages: messages,
            temperature: config.temperature,
            abortSignal: signal,
        };

        logger.log(`[OpenaiService] 调用 Vercel AI SDK. Provider: ${config.provider}, Model: ${modelName}`);

        try {
            if (config.stream) {
                return await streamText(options);
            } else {
                return await generateText(options);
            }
        } catch (error) {
            logger.error("[OpenaiService] API 调用失败:", error);
            throw error;
        }
    }
}

const openaiService = new OpenaiService();
export default openaiService;