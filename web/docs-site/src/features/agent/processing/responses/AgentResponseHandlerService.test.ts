import { describe, it, expect, vi } from 'vitest';
import { computed } from 'vue';
import { AgentResponseHandlerService } from './AgentResponseHandlerService';

function createHandler() {
  const updateMessage = vi.fn().mockResolvedValue(undefined);
  const messageManager = {
    updateMessage,
    addMessage: vi.fn(),
    removeMessage: vi.fn(),
    replaceMessage: vi.fn(),
    appendMessageContent: vi.fn(),
    markStreamAsCompleted: vi.fn(),
  };

  const assistantMessage = {
    id: 'assistant-1',
    role: 'assistant' as const,
    content: ':happy: 你好！[?你想了解什么|角色背景|技能机制]',
    createdAt: new Date().toISOString(),
  };

  const currentSession = computed(() => ({
    messagesById: {
      [assistantMessage.id]: assistantMessage,
    }
  }));

  const handler = new AgentResponseHandlerService(messageManager as any, currentSession as any);
  return { handler, updateMessage, assistantMessage };
}

describe('AgentResponseHandlerService', () => {
  it('updates message status to done', async () => {
    const { handler, assistantMessage, updateMessage } = createHandler();

    const result = await handler.handleApiResponse(assistantMessage as any);

    expect(result.type).toBe('complete');
    expect(updateMessage).toHaveBeenCalledWith({
      messageId: assistantMessage.id,
      updates: { status: 'done' },
    });
  });

  it('returns no_op when message not found', async () => {
    const updateMessage = vi.fn().mockResolvedValue(undefined);
    const messageManager = { updateMessage };
    const emptySession = computed(() => ({ messagesById: {} }));

    const handler = new AgentResponseHandlerService(messageManager as any, emptySession as any);
    const result = await handler.handleApiResponse({ id: 'non-existent' } as any);

    expect(result.type).toBe('no_op');
    expect(updateMessage).not.toHaveBeenCalled();
  });
});
