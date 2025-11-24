import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AgentToolService } from '@/features/agent/services/AgentToolService'
import toolParserService from '@/features/agent/services/toolParserService'
import contextOptimizerService from '@/features/agent/services/contextOptimizerService'
import tokenizerService from '@/lib/tokenizer/tokenizerService'
import logger from '@/features/app/services/loggerService'
import type { ComputedRef } from 'vue'
import type { Session, Message } from '@/features/agent/types'
import type { ParsedToolCall } from '@/features/agent/services/toolParserService'
import type { MessageManager } from '@/features/agent/stores/messageManager'
import {
  createMockSession,
  createMockMessage,
  createMockMessageManager,
  createMockSessionWithMessages,
  mockToolResults,
  mockErrors
} from '@/test/mocks'

// Mock services
const mockedToolParserService = vi.mocked(toolParserService)
const mockedContextOptimizerService = vi.mocked(contextOptimizerService)
const mockedTokenizerService = vi.mocked(tokenizerService)
const mockedLogger = vi.mocked(logger)

describe('AgentToolService', () => {
  let agentToolService: AgentToolService
  let messageManager: MessageManager
  let currentSession: ComputedRef<Session | null>
  let activeConfig: ComputedRef<any>

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mocks
    messageManager = createMockMessageManager()
    const currentSessionRef = {
      value: null as Session | null
    }
    currentSession = currentSessionRef as unknown as ComputedRef<Session | null>

    const activeConfigRef = {
      value: null as any
    }
    activeConfig = activeConfigRef as unknown as ComputedRef<any>

    // Default session with some messages
    const session = createMockSessionWithMessages([
      createMockMessage({ role: 'user', content: 'Search for Vue 3 docs' }),
      createMockMessage({
        role: 'assistant',
        content: 'I\'ll search for Vue 3 documentation.',
        tool_calls: [
          {
            id: 'call_1',
            type: 'function',
            function: { name: 'search_docs', arguments: '{"query":"Vue 3"}' }
          }
        ]
      })
    ])
    currentSessionRef.value = session

    activeConfigRef.value = { maxTokens: 128000 }

    agentToolService = new AgentToolService(
      messageManager,
      currentSession,
      activeConfig
    )
  })

  describe('handleToolExecution', () => {
    it('应该成功执行工具并显示状态消息', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage({ id: 'status-msg-1' })

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)
        .mockResolvedValueOnce(createMockMessage())
        .mockResolvedValueOnce(createMockMessage())

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索 "Vue 3" 的相关文档...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: mockToolResults.search_docs.result,
          followUpPrompt: '建议使用 read_doc 查看具体内容'
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(5000)

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(60000)

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('success')
      expect(messageManager.addMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          role: 'assistant',
          type: 'tool_status',
          content: '正在搜索 "Vue 3" 的相关文档...'
        })
      )
      expect(messageManager.replaceMessage).toHaveBeenCalledWith(
        'status-msg-1',
        expect.objectContaining({
          role: 'assistant',
          type: 'tool_result',
          status: 'done'
        })
      )
    })

    it('应该处理工具执行错误', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage({ id: 'status-msg-1' })

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)
        .mockResolvedValueOnce(createMockMessage())

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索 "Vue 3" 的相关文档...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'error',
          result: mockErrors.executionError.result
        })

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('error')
      expect(messageManager.replaceMessage).toHaveBeenCalledWith(
        'status-msg-1',
        expect.objectContaining({
          role: 'assistant',
          type: 'error',
          status: 'done'
        })
      )
    })

    it('应该处理上下文大小超限的情况', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'read_doc',
        params: { args: '<path>/large/file.vue</path>' },
        original: '<read_doc><path>/large/file.vue</path></read_doc>'
      }

      const statusMessage = createMockMessage({ id: 'status-msg-1' })

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在读取文档...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: 'x'.repeat(1000000) // Large result
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(120000) // Large token count

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(130000) // Exceeds threshold

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('error')
      expect(messageManager.replaceMessage).toHaveBeenCalledWith(
        'status-msg-1',
        expect.objectContaining({
          role: 'assistant',
          type: 'error',
          content: expect.stringContaining('工具返回的结果过大')
        })
      )
    })

    it('应该正确添加后续提示作为隐藏消息', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'read_doc',
        params: { args: '<path>/test.vue</path>' },
        original: '<read_doc><path>/test.vue</path></read_doc>'
      }

      const statusMessage = createMockMessage({ id: 'status-msg-1' })

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)
        .mockResolvedValueOnce(createMockMessage({ id: 'tool-result-1' }))
        .mockResolvedValueOnce(createMockMessage({ id: 'follow-up-1' }))

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在读取文档...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: 'Document content',
          followUpPrompt: '感谢你帮我读取了文档。请先对刚才读取的文档内容做一个简要的总结和汇报...'
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(1000)

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(50000)

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('success')

      // Check that follow-up prompt was added as hidden message
      expect(messageManager.addMessage).toHaveBeenNthCalledWith(3,
        expect.objectContaining({
          role: 'user',
          content: '感谢你帮我读取了文档。请先对刚才读取的文档内容做一个简要的总结和汇报...',
          is_hidden: true
        })
      )
    })

    it('应该处理添加状态消息失败的情况', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(null) // Failed to add status message

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('error')
      expect(mockedToolParserService.executeTool).not.toHaveBeenCalled()
    })

    it('应该处理没有工具调用的情况', async () => {
      // Arrange
      const session = createMockSessionWithMessages([
        createMockMessage({ role: 'user', content: 'Hello' }),
        createMockMessage({ role: 'assistant', content: 'Hi there!' })
      ])
      const currentSessionRef = {
        value: session as Session | null
      }
      currentSession = currentSessionRef as unknown as ComputedRef<Session | null>

      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage()

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)
        .mockResolvedValueOnce(createMockMessage())
        .mockResolvedValueOnce(createMockMessage())

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索 "Vue 3" 的相关文档...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: 'Search results'
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(1000)

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(50000)

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('success')
      // Should add new tool message since no existing tool call to replace
      expect(messageManager.addMessage).toHaveBeenCalledTimes(3)
    })
  })

  describe('上下文大小预测', () => {
    it('应该正确计算新的上下文大小', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage()

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: mockToolResults.search_docs.result
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(8000)

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(90000)

      // Act
      await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(mockedContextOptimizerService.calculateHistoryTokens).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            role: 'tool',
            name: 'search_docs',
            content: mockToolResults.search_docs.result
          })
        ])
      )
    })

    it('应该使用自定义的最大令牌配置', async () => {
      // Arrange
      const activeConfigRef = {
        value: { maxTokens: 64000 } as any // Smaller limit
      }
      activeConfig = activeConfigRef as unknown as ComputedRef<any>

      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage()

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索...')

      mockedToolParserService.executeTool
        .mockResolvedValue({
          status: 'success',
          result: mockToolResults.search_docs.result
        })

      mockedTokenizerService.countTokens
        .mockReturnValue(50000)

      mockedContextOptimizerService.calculateHistoryTokens
        .mockResolvedValue(60000) // Exceeds 90% of 64000

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('error')
      expect(messageManager.replaceMessage).toHaveBeenCalledWith(
        statusMessage.id,
        expect.objectContaining({
          role: 'assistant',
          type: 'error',
          content: expect.stringContaining('超过 57600 tokens 的限制')
        })
      )
    })
  })

  describe('错误处理', () => {
    it('应该记录工具执行异常', async () => {
      // Arrange
      const parsedTool: ParsedToolCall = {
        name: 'search_docs',
        params: { query: 'Vue 3' },
        original: '<search_docs><query>Vue 3</query></search_docs>'
      }

      const statusMessage = createMockMessage()

      vi.mocked(messageManager.addMessage)
        .mockResolvedValueOnce(statusMessage)
        .mockResolvedValueOnce(createMockMessage())

      mockedToolParserService.createStatusMessage
        .mockReturnValue('正在搜索...')

      mockedToolParserService.executeTool
        .mockRejectedValue(new Error('Network error'))

      // Act
      const result = await agentToolService.handleToolExecution(parsedTool)

      // Assert
      expect(result.status).toBe('error')
      expect(mockedLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('执行工具 \'search_docs\' 异常'),
        expect.any(Error)
      )
    })
  })
})