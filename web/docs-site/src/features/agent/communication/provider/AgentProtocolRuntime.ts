import type { ComputedRef } from 'vue';
import llmProviderService from '@/lib/llm/llmProviderService';
import logger from '@/features/app/services/loggerService';
import type { Message, AgentProtocolMode, ProtocolMode } from '@/features/agent/types';
import { paramsToRequestBody } from '@/features/app/utils/paramUtils';
import { toolRegistryService } from '@/features/agent/tools/registry/toolRegistryService';
import { toModelMessages } from '@/features/agent/adapters/modelMessageAdapter';

export interface ApiCallResult {
  result: any;
  protocolMode: ProtocolMode;
}

export class AgentProtocolRuntime {
  constructor(private activeConfig: ComputedRef<any>) {}

  async callApi(history: Message[], signal: AbortSignal): Promise<ApiCallResult> {
    if (!this.activeConfig.value?.apiUrl || !this.activeConfig.value?.apiKey) {
      const errorMsg = '没有激活的有效AI配置。请在设置中选择或创建一个配置。';
      logger.error(`[AgentApiService] ${errorMsg}`);
      throw new Error(errorMsg);
    }

    const apiMessages = toModelMessages(history);
    const customParamsBody = paramsToRequestBody(this.activeConfig.value.customParams);

    logger.log('[AgentApiService] 准备调用 API...', { messageCount: apiMessages.length });
    logger.setLastRequest({
      model: this.activeConfig.value.modelName,
      messages: apiMessages,
      temperature: this.activeConfig.value.temperature,
      stream: this.activeConfig.value.stream,
      ...customParamsBody,
    });

    const useStructured = this.shouldUseStructured();
    const selectedMode: ProtocolMode = useStructured ? 'structured' : 'fallback';
    this.emitProtocolEvent('PROTOCOL_SELECTED', { mode: selectedMode });

    if (useStructured) {
      try {
        await toolRegistryService.loadTools();
        const tools = toolRegistryService.toSdkToolDefinitions({
          includedTools: ['search_docs', 'read_doc', 'explore', 'memory', 'ask_choice'],
        });
        const structuredResult = await llmProviderService.createStructuredChatCompletion(
          apiMessages,
          this.activeConfig.value,
          signal,
          tools,
          customParamsBody
        );
        this.emitProtocolEvent('STRUCTURED_API_CALLED', { note: 'SDK will auto-execute tools' });

        return {
          result: structuredResult,
          protocolMode: 'structured',
        };
      } catch (error: any) {
        this.emitProtocolEvent('STRUCTURED_FAILED', { reason: error?.message || String(error) });

        if (this.getProtocolMode() === 'structured') {
          logger.error('[AgentApiService] 强制 structured 模式失败，不执行 fallback。', error);
          throw error;
        }

        this.emitProtocolEvent('FALLBACK_ACTIVATED');
        const fallbackResult = await llmProviderService.createChatCompletion(
          apiMessages,
          this.activeConfig.value,
          signal,
          customParamsBody
        );
        return {
          result: fallbackResult,
          protocolMode: 'fallback',
        };
      }
    }

    const fallbackResult = await llmProviderService.createChatCompletion(
      apiMessages,
      this.activeConfig.value,
      signal,
      customParamsBody
    );
    return {
      result: fallbackResult,
      protocolMode: 'fallback',
    };
  }

  private getProtocolMode(): AgentProtocolMode {
    return this.activeConfig.value?.agentProtocolMode || 'auto';
  }

  private shouldUseStructured(): boolean {
    const configuredMode = this.getProtocolMode();
    if (configuredMode === 'structured') return true;
    if (configuredMode === 'fallback') return false;

    const capabilities = llmProviderService.getCapabilities(this.activeConfig.value);
    return capabilities.supportsStructuredToolCalls;
  }

  private emitProtocolEvent(eventName: string, payload?: Record<string, unknown>) {
    logger.log(`[AgentApiService][ProtocolEvent] ${eventName}`, payload || {});
  }
}
