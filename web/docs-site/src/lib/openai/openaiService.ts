import { OpenAI } from 'openai';
import type { ClientOptions } from 'openai';
import logger from '../../features/app/services/loggerService';
import type { Config } from '@/features/app/stores/config';

/**
 * @class OpenaiService
 * @description 管理 OpenAI 客户端实例并处理 API 调用。
 * 此服务确保 OpenAI 客户端始终配置为应用程序配置存储中的最新设置。
 * 已修复CORS问题：移除X-Stainless-*请求头
 */
class OpenaiService {
    private openai: OpenAI | null = null;
    private currentConfig: Partial<ClientOptions> & { baseURL?: string | null } = {
        apiKey: undefined,
        baseURL: null,
    };

    /**
     * 如果配置已更改，则更新 OpenAI 客户端实例。
     * 在每个 API 请求之前调用此方法，以确保客户端是最新的。
     * @param config 来自配置存储的活动 AI 配置。
     */
    private _updateClient(config: Config): void {
        const { apiKey, apiUrl } = config;

        if (this.currentConfig.apiKey === apiKey && this.currentConfig.baseURL === apiUrl) {
            return; // 没有变化，无需更新。
        }

        logger.log('[OpenaiService] 配置已更改。正在重新初始化 OpenAI 客户端...');

        this.openai = new OpenAI({
            apiKey: apiKey,
            baseURL: apiUrl,
            dangerouslyAllowBrowser: true, // 客户端使用所必需。
            timeout: 300 * 1000, // 5分钟超时
            defaultHeaders: {
                // 移除导致CORS问题的请求头，使用null值（网上验证的有效方法）
                'x-stainless-arch': null,
                'x-stainless-lang': null,
                'x-stainless-os': null,
                'x-stainless-package-version': null,
                'x-stainless-retry-count': null,
                'x-stainless-runtime': null,
                'x-stainless-runtime-version': null,
                'x-stainless-timeout': null,
                'x-stainless-async': null,
                // 设置为Python客户端的User-Agent，避免被识别为浏览器客户端
                'User-Agent': 'OpenAI/Python 1.14.3'
            }
        });

        this.currentConfig = { apiKey, baseURL: apiUrl };
        logger.log('[OpenaiService] OpenAI 客户端重新初始化成功。');
    }

    /**
     * 使用官方 OpenAI 库创建聊天完成请求。
     * 它动态处理流式和非流式响应。
     * @param requestBody 要发送到 OpenAI API 的请求正文。
     * @param config 活动的 AI 配置。
     * @returns 如果 stream 为 true，则返回流对象，否则返回完成对象。
     */
    public async createChatCompletion(requestBody: any, config: Config, signal: AbortSignal): Promise<any> {
        if (!config || !config.apiKey || !config.apiUrl) {
            throw new Error("[OpenaiService] AI 配置缺失或无效。");
        }

        this._updateClient(config);

        if (!this.openai) {
            throw new Error("[OpenaiService] OpenAI 客户端未初始化。");
        }

        try {
            logger.log("[OpenaiService] 正在调用 'openai.chat.completions.create'，请求正文:", requestBody);
            const response = await this.openai.chat.completions.create(requestBody, { signal });
            return response;
        } catch (error) {
            logger.error("[OpenaiService] OpenAI API 调用失败:", error);
            throw error; // 重新抛出错误，以便调用服务可以处理它。
        }
    }
}

const openaiService = new OpenaiService();
export default openaiService;