import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { CoreMessage } from 'ai';
import { toModelMessages } from '@/features/agent/adapters/modelMessageAdapter';
import type { Message } from '@/features/agent/types';

// Mock Vercel AI SDK 的 createDeepSeek，捕获发送的消息
let capturedMessages: CoreMessage[] = [];

vi.mock('@ai-sdk/deepseek', () => ({
  createDeepSeek: vi.fn(() => {
    return (modelName: string) => ({
      modelId: modelName,
      provider: 'deepseek',
    });
  }),
}));

vi.mock('ai', async () => {
  const actual = await vi.importActual('ai');
  return {
    ...actual,
    streamText: vi.fn(async (options: any) => {
      capturedMessages = options.messages;
      return {
        textStream: (async function* () { yield 'mock response'; })(),
        text: 'mock response',
      };
    }),
    generateText: vi.fn(async (options: any) => {
      capturedMessages = options.messages;
      return {
        text: 'mock response',
        toolCalls: [],
      };
    }),
  };
});

// 在 mock 之后导入 llmProviderService
import llmProviderService from './llmProviderService';

describe('LLMProviderService reasoning_content', () => {
  beforeEach(() => {
    capturedMessages = [];
    vi.clearAllMocks();
  });

  describe('toModelMessages adapter', () => {
    it('should preserve reasoning in assistant messages', () => {
      const messages: Message[] = [
        {
          id: '1',
          role: 'user',
          content: '你好',
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'assistant',
          content: '你好！',
          reasoning: '用户在打招呼，我应该友好地回应。',
          createdAt: new Date().toISOString(),
        },
      ];

      const result = toModelMessages(messages);

      // 验证 assistant 消息包含 reasoning part
      const assistantMsg = result.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeDefined();
      expect(Array.isArray(assistantMsg?.content)).toBe(true);

      const content = assistantMsg?.content as any[];
      const reasoningPart = content.find((p: any) => p.type === 'reasoning');
      expect(reasoningPart).toBeDefined();
      expect(reasoningPart.text).toBe('用户在打招呼，我应该友好地回应。');
    });

    it('should preserve reasoning with tool calls', () => {
      const messages: Message[] = [
        {
          id: '1',
          role: 'user',
          content: '搜索编队推荐',
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'assistant',
          content: '',
          reasoning: '用户想要搜索编队推荐，我应该调用 search_docs 工具。',
          tool_calls: [
            {
              tool: 'search_docs',
              action_id: 'call_001',
              query: '编队推荐',
            },
          ],
          createdAt: new Date().toISOString(),
        },
      ];

      const result = toModelMessages(messages);

      const assistantMsg = result.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeDefined();
      expect(Array.isArray(assistantMsg?.content)).toBe(true);

      const content = assistantMsg?.content as any[];

      // 验证 reasoning part 存在
      const reasoningPart = content.find((p: any) => p.type === 'reasoning');
      expect(reasoningPart).toBeDefined();
      expect(reasoningPart.text).toBe('用户想要搜索编队推荐，我应该调用 search_docs 工具。');

      // 验证 tool-call part 存在
      const toolCallPart = content.find((p: any) => p.type === 'tool-call');
      expect(toolCallPart).toBeDefined();
      expect(toolCallPart.toolName).toBe('search_docs');
    });
  });

  describe('llmProviderService integration', () => {
    it('should pass messages with reasoning to SDK', async () => {
      const messages: CoreMessage[] = [
        { role: 'user', content: '你好' },
        {
          role: 'assistant',
          content: [
            { type: 'text', text: '你好！' },
            { type: 'reasoning', text: '用户在打招呼。' },
          ],
        },
      ];

      const mockConfig = {
        apiKey: 'test-key',
        apiUrl: 'https://api.deepseek.com',
        provider: 'deepseek' as const,
        modelName: 'deepseek-reasoner',
        temperature: 0.7,
        stream: false,
      };

      await llmProviderService.createChatCompletion(
        messages,
        mockConfig as any,
        new AbortController().signal
      );

      // 验证传递给 SDK 的消息保留了 reasoning
      expect(capturedMessages.length).toBe(2);

      const assistantMsg = capturedMessages[1];
      expect(assistantMsg.role).toBe('assistant');
      expect(Array.isArray(assistantMsg.content)).toBe(true);

      const content = assistantMsg.content as any[];
      const reasoningPart = content.find((p: any) => p.type === 'reasoning');
      expect(reasoningPart).toBeDefined();
      expect(reasoningPart.text).toBe('用户在打招呼。');
    });
  });
});
