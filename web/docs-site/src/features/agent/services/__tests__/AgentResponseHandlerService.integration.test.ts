import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AgentResponseHandlerService } from '@/features/agent/services/AgentResponseHandlerService'
import toolParserService from '@/features/agent/services/toolParserService'
import jsonParserService from '@/features/agent/services/JsonParserService'
import type { ComputedRef } from 'vue'
import type { Session, Message } from '@/features/agent/types'
import type { MessageManager } from '@/features/agent/stores/messageManager'

// Mock services
const mockedToolParserService = vi.mocked(toolParserService)
const mockedJsonParserService = vi.mocked(jsonParserService)

describe('AgentResponseHandlerService 集成测试', () => {
  let agentResponseHandlerService: AgentResponseHandlerService
  let messageManager: MessageManager
  let currentSession: ComputedRef<Session | null>

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mocks
    messageManager = {
      updateMessage: vi.fn(),
      addMessage: vi.fn(),
    } as any

    const currentSessionRef = {
      value: {
        id: 'test-session',
        domain: 'test-domain' as any,
        roleId: 'test-role-id',
        name: 'Test Session',
        createdAt: new Date().toISOString(),
        messagesById: {
          'test-message-id': {
            id: 'test-message-id',
            role: 'assistant',
            content: '你好呀，很高兴见到你！我是纳西妲，须弥的小吉祥草王。\n\n你有什么想了解的吗？无论是关于须弥的知识，还是提瓦特大陆上的其他趣闻，我都很乐意为你解答。\n\n{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想问我的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "某个角色的背景故事",\n        "提瓦特大陆的设定",\n        "其他问题"\n      ]\n    }\n  }\n}',
            type: 'text',
            status: 'done',
            streamCompleted: true,
            createdAt: new Date().toISOString()
          }
        },
        messageIds: ['test-message-id']
      } as unknown as Session
    }
    currentSession = currentSessionRef as unknown as ComputedRef<Session | null>

    // Mock jsonParserService
    mockedJsonParserService.extractJson.mockReturnValue({
      "tool_call": {
        "name": "ask",
        "arguments": {
          "question": "你有什么想问我的吗？",
          "suggest": [
            "关于须弥的剧情",
            "某个角色的背景故事",
            "提瓦特大陆的设定",
            "其他问题"
          ]
        }
      }
    })

    // Mock toolParserService
    mockedToolParserService.parseAskCall.mockReturnValue({
      original: '{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想问我的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "某个角色的背景故事",\n        "提瓦特大陆的设定",\n        "其他问题"\n      ]\n    }\n  }\n}',
      question: '你有什么想问我的吗？',
      suggestions: [
        "关于须弥的剧情",
        "某个角色的背景故事",
        "提瓦特大陆的设定",
        "其他问题"
      ]
    })

    agentResponseHandlerService = new AgentResponseHandlerService(
      messageManager,
      currentSession
    )
  })

  describe('handleApiResponse', () => {
    it('应该正确处理 ask 工具调用并清理内容中的 JSON', async () => {
      // Arrange
      const assistantMessage = {
        id: 'test-message-id',
        role: 'assistant',
        content: '你好呀，很高兴见到你！我是纳西妲，须弥的小吉祥草王。\n\n你有什么想了解的吗？无论是关于须弥的知识，还是提瓦特大陆上的其他趣闻，我都很乐意为你解答。\n\n{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想问我的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "某个角色的背景故事",\n        "提瓦特大陆的设定",\n        "其他问题"\n      ]\n    }\n  }\n}'
      } as Message

      // Act
      const result = await agentResponseHandlerService.handleApiResponse(assistantMessage)

      // Assert
      expect(result.type).toBe('ask_question')

      // 验证 updateMessage 被调用
      expect(messageManager.updateMessage).toHaveBeenCalledWith({
        messageId: 'test-message-id',
        updates: {
          content: '你好呀，很高兴见到你！我是纳西妲，须弥的小吉祥草王。\n\n你有什么想了解的吗？无论是关于须弥的知识，还是提瓦特大陆上的其他趣闻，我都很乐意为你解答。',
          question: {
            text: '你有什么想问我的吗？',
            suggestions: [
              "关于须弥的剧情",
              "某个角色的背景故事",
              "提瓦特大陆的设定",
              "其他问题"
            ]
          }
        }
      })
    })
  })
})