import { OpenAI } from 'openai';
import logger from './loggerService.js';

/**
 * @class OpenaiService
 * @description Manages the OpenAI client instance and handles API calls.
 * This service ensures that the OpenAI client is always configured with the latest
 * settings from the application's configuration store.
 */
class OpenaiService {
    constructor() {
        this.openai = null;
        this.currentConfig = {
            apiKey: null,
            baseURL: null,
        };
    }

    /**
     * Updates the OpenAI client instance if the configuration has changed.
     * This method is called before every API request to ensure the client is up-to-date.
     * @param {object} config - The active AI configuration from the config store.
     * @param {string} config.apiKey - The OpenAI API key.
     * @param {string} config.apiUrl - The base URL for the OpenAI API.
     * @private
     */
    _updateClient(config) {
        const { apiKey, apiUrl } = config;

        // Check if the configuration has actually changed to avoid unnecessary re-initialization.
        if (this.currentConfig.apiKey === apiKey && this.currentConfig.baseURL === apiUrl) {
            return; // No changes, no need to update.
        }

        logger.log('[OpenaiService] Configuration has changed. Re-initializing OpenAI client...');

        this.openai = new OpenAI({
            apiKey: apiKey,
            baseURL: apiUrl,
            dangerouslyAllowBrowser: true, // Necessary for client-side usage.
            timeout: 300 * 1000, // 5-minute timeout
        });

        this.currentConfig = { apiKey, baseURL: apiUrl };
        logger.log('[OpenaiService] OpenAI client re-initialized successfully.');
    }

    /**
     * Creates a chat completion request using the official OpenAI library.
     * It dynamically handles both streaming and non-streaming responses.
     * @param {object} requestBody - The body of the request to be sent to the OpenAI API.
     * @param {string} requestBody.model - The model name.
     * @param {Array<object>} requestBody.messages - The conversation history.
     * @param {number} requestBody.temperature - The temperature for sampling.
     * @param {boolean} requestBody.stream - Whether to stream the response.
     * @param {object} config - The active AI configuration.
     * @returns {Promise<OpenAI.Chat.Completions.ChatCompletion | Stream<OpenAI.Chat.Completions.ChatCompletionChunk>>}
     *          Returns a stream object if stream is true, otherwise returns the completion object.
     */
    async createChatCompletion(requestBody, config) {
        if (!config || !config.apiKey || !config.apiUrl) {
            throw new Error("[OpenaiService] AI configuration is missing or invalid.");
        }

        // Ensure the client is configured correctly before making a call.
        this._updateClient(config);

        try {
            logger.log("[OpenaiService] Calling 'openai.chat.completions.create' with body:", requestBody);
            const response = await this.openai.chat.completions.create(requestBody);
            return response;
        } catch (error) {
            logger.error("[OpenaiService] OpenAI API call failed:", error);
            // Re-throw the error so the calling service can handle it.
            throw error;
        }
    }
}

const openaiService = new OpenaiService();
export default openaiService;