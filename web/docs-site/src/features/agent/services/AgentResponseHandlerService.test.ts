import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AgentResponseHandlerService } from '@/features/agent/services/AgentResponseHandlerService'
import toolParserService from '@/features/agent/services/toolParserService'
import type { ComputedRef } from 'vue'
import type { Session, Message } from '@/features/agent/types'
import type { MessageManager } from '@/features/agent/stores/messageManager'
import { createMockSessionWithMessages, createMockMessage, createMockMessageManager } from '@/test/mocks'

// Mock services
const mockedToolParserService = vi.mocked(toolParserService)

describe('AgentResponseHandlerService', () => {
  let agentResponseHandlerService: AgentResponseHandlerService
  let messageManager: MessageManager
  let currentSession: ComputedRef<Session | null>

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mocks
    messageManager = createMockMessageManager()
    const currentSessionRef = {
      value: null as Session | null
    }
    currentSession = currentSessionRef as unknown as ComputedRef<Session | null>

    // Default session with some messages
    const session = createMockSessionWithMessages([
      createMockMessage({ role: 'user', content: 'Hello' }),
      createMockMessage({
        role: 'assistant',
        id: 'assistant-msg-1',
        content: '你好，有什么我可以帮你的吗？\n\n{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想了解的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "关于提瓦特的世界观",\n        "关于某个角色",\n        "其他问题"\n      ]\n    }\n  }\n}',
        question: {
          text: '你有什么想了解的吗？',
          suggestions: [
            '关于须弥的剧情',
            '关于提瓦特的世界观',
            '关于某个角色',
            '其他问题'
          ]
        }
      })
    ])
    currentSessionRef.value = session

    agentResponseHandlerService = new AgentResponseHandlerService(
      messageManager,
      currentSession
    )
  })

  describe('handleApiResponse', () => {
    it('应该正确处理 ask 工具调用并清理内容中的 JSON', async () => {
      // Arrange
      const assistantMessage = createMockMessage({
        id: 'assistant-msg-1',
        role: 'assistant',
        content: '你好，有什么我可以帮你的吗？\n\n{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想了解的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "关于提瓦特的世界观",\n        "关于某个角色",\n        "其他问题"\n      ]\n    }\n  }\n}'
      })

      // Mock the message manager methods
      vi.mocked(messageManager.updateMessage).mockImplementation(async (update) => {
        // Simulate updating the message
        return Promise.resolve()
      })

      // Mock tool parser service
      mockedToolParserService.parseAskCall.mockReturnValue({
        original: '{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想了解的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "关于提瓦特的世界观",\n        "关于某个角色",\n        "其他问题"\n      ]\n    }\n  }\n}',
        question: '你有什么想了解的吗？',
        suggestions: [
          '关于须弥的剧情',
          '关于提瓦特的世界观',
          '关于某个角色',
          '其他问题'
        ]
      })

      // Act
      const result = await agentResponseHandlerService.handleApiResponse(assistantMessage)

      // Assert
      expect(result.type).toBe('ask_question')
      // Verify that updateMessage was called with cleaned content
      expect(messageManager.updateMessage).toHaveBeenCalledWith({
        messageId: 'assistant-msg-1',
        updates: {
          content: '你好，有什么我可以帮你的吗？',
          question: {
            text: '你有什么想了解的吗？',
            suggestions: [
              '关于须弥的剧情',
              '关于提瓦特的世界观',
              '关于某个角色',
              '其他问题'
            ]
          }
        }
      })
    })

    it('应该正确处理普通工具调用并清理内容中的 JSON', async () => {
      // Arrange
      const assistantMessage = createMockMessage({
        id: 'assistant-msg-2',
        role: 'assistant',
        content: '我将为你搜索相关信息。\n\n{\n  "tool_call": {\n    "name": "search_docs",\n    "arguments": {\n      "query": "Vue 3 composition API"\n    }\n  }\n}'
      })

      // Mock the message manager methods
      vi.mocked(messageManager.updateMessage).mockImplementation(async (update) => {
        // Simulate updating the message
        return Promise.resolve()
      })

      // Mock tool parser service
      mockedToolParserService.parseToolCall.mockReturnValue({
        name: 'search_docs',
        params: { query: 'Vue 3 composition API' },
        original: '{\n  "tool_call": {\n    "name": "search_docs",\n    "arguments": {\n      "query": "Vue 3 composition API"\n    }\n  }\n}'
      })

      // Act
      const result = await agentResponseHandlerService.handleApiResponse(assistantMessage)

      // Assert
      expect(result.type).toBe('tool_call')
      // Verify that updateMessage was called with cleaned content
      expect(messageManager.updateMessage).toHaveBeenCalledWith({
        messageId: 'assistant-msg-2',
        updates: {
          content: '我将为你搜索相关信息。',
          tool_calls: [{
            name: 'search_docs',
            params: { query: 'Vue 3 composition API' },
            original: '{\n  "tool_call": {\n    "name": "search_docs",\n    "arguments": {\n      "query": "Vue 3 composition API"\n    }\n  }\n}'
          }]
        }
      })
    })
  })
})