import { describe, it, expect, vi, beforeEach } from 'vitest';
import { computed } from 'vue';
import { AgentApiService } from './AgentApiService';

const {
  createChatCompletionMock,
  createStructuredChatCompletionMock,
  getCapabilitiesMock,
  loadToolsMock,
  toSdkToolDefinitionsMock,
} = vi.hoisted(() => ({
  createChatCompletionMock: vi.fn(),
  createStructuredChatCompletionMock: vi.fn(),
  getCapabilitiesMock: vi.fn(),
  loadToolsMock: vi.fn(async () => undefined),
  toSdkToolDefinitionsMock: vi.fn(() => ({ search_docs: {} })),
}));

vi.mock('@/lib/llm/llmProviderService', () => ({
  default: {
    createChatCompletion: createChatCompletionMock,
    createStructuredChatCompletion: createStructuredChatCompletionMock,
    getCapabilities: getCapabilitiesMock,
  }
}));

vi.mock('../tools/registry/toolRegistryService', () => ({
  toolRegistryService: {
    loadTools: loadToolsMock,
    toSdkToolDefinitions: toSdkToolDefinitionsMock,
  }
}));

vi.mock('@/features/agent/tools/registry/toolRegistryService', () => ({
  toolRegistryService: {
    loadTools: loadToolsMock,
    toSdkToolDefinitions: toSdkToolDefinitionsMock,
  }
}));

function createService(protocolMode: 'auto' | 'structured' | 'fallback' = 'auto') {
  const messageManager = {
    addMessage: vi.fn(),
    updateMessage: vi.fn(),
    removeMessage: vi.fn(),
    replaceMessage: vi.fn(),
    appendMessageContent: vi.fn(),
    markStreamAsCompleted: vi.fn(),
  } as any;

  const activeConfig = computed(() => ({
    apiUrl: 'https://example.com/v1',
    apiKey: 'test-key',
    modelName: 'test-model',
    temperature: 0.7,
    stream: false,
    customParams: [],
    provider: 'openai',
    agentProtocolMode: protocolMode,
    enableStructuredTools: true,
  }));

  return new AgentApiService(messageManager, activeConfig);
}

describe('AgentApiService protocol routing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uses structured path in auto mode when capability enabled', async () => {
    getCapabilitiesMock.mockReturnValue({ supportsStructuredToolCalls: true, supportsStrictTools: false });
    createStructuredChatCompletionMock.mockResolvedValue({ text: 'ok', toolCalls: [] });

    const service = createService('auto');
    const result = await service.callApi([
      { role: 'user', content: 'hi', id: '1', createdAt: new Date().toISOString() } as any
    ], new AbortController().signal);

    expect(result.protocolMode).toBe('structured');
    expect(createStructuredChatCompletionMock).toHaveBeenCalledTimes(1);
    expect(createChatCompletionMock).toHaveBeenCalledTimes(0);
  });

  it('falls back when structured path fails in auto mode', async () => {
    getCapabilitiesMock.mockReturnValue({ supportsStructuredToolCalls: true, supportsStrictTools: false });
    createStructuredChatCompletionMock.mockRejectedValue(new Error('structured fail'));
    createChatCompletionMock.mockResolvedValue({ text: 'fallback ok' });

    const service = createService('auto');
    const result = await service.callApi([
      { role: 'user', content: 'hi', id: '1', createdAt: new Date().toISOString() } as any
    ], new AbortController().signal);

    expect(result.protocolMode).toBe('fallback');
    expect(createStructuredChatCompletionMock).toHaveBeenCalledTimes(1);
    expect(createChatCompletionMock).toHaveBeenCalledTimes(1);
  });
});
