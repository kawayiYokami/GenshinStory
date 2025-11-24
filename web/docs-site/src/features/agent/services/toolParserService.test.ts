import { describe, it, expect, vi, beforeEach } from 'vitest'
import toolParserService from '@/features/agent/services/toolParserService'
import logger from '@/features/app/services/loggerService'

// Mock logger
const mockedLogger = vi.mocked(logger)

// Extract functions from the default export for easier testing
const {
  parseToolCall,
  parseJsonToolCall,
  parseReadDocRequests,
  parseAskCall,
  isToolRetryable
} = toolParserService

describe('ToolParserService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('parseToolCall', () => {
    it('应该正确解析 JSON 格式的工具调用', () => {
      const json = `{
  "tool_call": {
    "name": "search_docs",
    "arguments": {
      "query": "Vue 3 composition API"
    }
  }
}`

      const result = parseToolCall(json)

      expect(result).toEqual({
        name: 'search_docs',
        params: { query: 'Vue 3 composition API' },
        original: json
      })
    })

    it('应该拒绝 XML 格式的工具调用', () => {
      const xml = `<search_docs>
  <query>Vue 3 composition API</query>
</search_docs>`

      const result = parseToolCall(xml)

      expect(result).toBeNull()
    })

    it('应该正确处理 JSON 格式的 read_doc 工具调用', () => {
      const json = `{
  "tool_call": {
    "name": "read_doc",
    "arguments": {
      "args": {
        "doc": [
          {
            "path": "/src/components/Test.vue",
            "line_range": "1-10"
          }
        ]
      }
    }
  }
}`

      const result = parseToolCall(json)

      expect(result).toBeTruthy()
      expect(result?.name).toBe('read_doc')
      expect(result?.params.args.doc[0].path).toBe('/src/components/Test.vue')
      expect(result?.params.args.doc[0].line_range).toBe('1-10')
    })

    it('应该正确处理 JSON 格式的 list_docs 工具调用', () => {
      const json = `{
  "tool_call": {
    "name": "list_docs",
    "arguments": {
      "path": "/src/components"
    }
  }
}`

      const result = parseToolCall(json)

      expect(result).toBeTruthy()
      expect(result?.name).toBe('list_docs')
      expect(result?.params.path).toBe('/src/components')
    })

    it('应该正确处理 JSON 格式的 ask 工具调用', () => {
      const json = `{
  "tool_call": {
    "name": "ask",
    "arguments": {
      "question": "您想搜索哪个游戏的角色信息？",
      "suggest": [
        "原神",
        "星穹铁道"
      ]
    }
  }
}`

      const result = parseToolCall(json)

      expect(result).toBeTruthy()
      expect(result?.name).toBe('ask')
      expect(result?.params.question).toBe('您想搜索哪个游戏的角色信息？')
      // JSON解析会将数组转换为字符串
      expect(result?.params.suggest).toBe('["原神","星穹铁道"]')
    })

    it('应该拒绝无效的 JSON 工具名称', () => {
      const json = `{
  "tool_call": {
    "name": "invalid_tool",
    "arguments": {
      "query": "test"
    }
  }
}`

      const result = parseToolCall(json)

      expect(result).toBeNull()
    })

    it('应该处理无效的 JSON 字符串', () => {
      const invalidJson = `{
  "tool_call": {
    "name": "search_docs",
    "arguments": {
      "query": "test"
    }
  }
  // Missing closing brace`

      const result = parseToolCall(invalidJson)

      // 无效的 JSON 应返回 null
      expect(result).toBeNull()
    })
  })

  describe('parseJsonToolCall', () => {
    it('应该正确解析 JSON 格式的工具调用', () => {
      const toolCall = {
        function: {
          name: 'search_docs',
          arguments: JSON.stringify({ query: 'Vue 3' })
        }
      }

      const result = parseJsonToolCall(toolCall)

      expect(result).toEqual({
        name: 'search_docs',
        params: { query: 'Vue 3' },
        xml: '<search_docs>{"query":"Vue 3"}</search_docs>'
      })
    })

    it('应该拒绝无效的工具名称', () => {
      const toolCall = {
        function: {
          name: 'invalid_tool',
          arguments: '{}'
        }
      }

      const result = parseJsonToolCall(toolCall)

      expect(result).toBeNull()
      expect(mockedLogger.log).toHaveBeenCalledWith(
        '[ParserAdapter] 忽略无效工具: invalid_tool'
      )
    })

    it('应该处理无效的 JSON 参数', () => {
      const toolCall = {
        function: {
          name: 'search_docs',
          arguments: 'invalid json'
        }
      }

      const result = parseJsonToolCall(toolCall)

      // fast-xml-parser 的 parseJsonToolCall 会将无效 JSON 作为字符串参数
      expect(result).toBeTruthy()
      expect(result?.name).toBe('search_docs')
      expect(result?.params.args).toBe('invalid json')
    })
  })

  describe('parseReadDocRequests', () => {
    it('应该解析单个文档请求', () => {
      const args = JSON.stringify({
        doc: {
          path: '/src/test.vue'
        }
      });

      const result = parseReadDocRequests(args)

      expect(result).toEqual([
        { path: '/src/test.vue', lineRanges: [] }
      ])
    })

    it('应该解析多个文档请求', () => {
      const args = JSON.stringify({
        doc: [
          {
            path: '/src/test.vue',
            line_range: '1-10'
          },
          {
            path: '/src/utils.ts'
          }
        ]
      });

      const result = parseReadDocRequests(args)

      expect(result).toHaveLength(2)
      expect(result[0].path).toBe('/src/test.vue')
      expect(result[0].lineRanges || []).toEqual(['1-10'])
      expect(result[1]).toEqual({
        path: '/src/utils.ts',
        lineRanges: []
      })
    })

    it('应该处理简单的路径列表', () => {
      const args = JSON.stringify({
        path: [
          '/src/test.vue',
          '/src/utils.ts'
        ]
      });

      const result = parseReadDocRequests(args)

      expect(result).toEqual([
        { path: '/src/test.vue', lineRanges: [] },
        { path: '/src/utils.ts', lineRanges: [] }
      ])
    })

    it('应该处理空的参数', () => {
      const result = parseReadDocRequests('')
      expect(result).toEqual([])
    })
  })

  describe('parseAskCall', () => {
    it('应该正确解析 ask 调用', () => {
      const json = JSON.stringify({
        tool_call: {
          name: 'ask',
          arguments: {
            question: '您想要继续分析这个组件吗？',
            suggest: [
              '是的，请继续',
              '不，先看看其他文件',
              '给我一些建议'
            ]
          }
        }
      });

      const result = parseAskCall(json)

      expect(result).toEqual({
        original: json,
        question: '您想要继续分析这个组件吗？',
        suggestions: [
          '是的，请继续',
          '不，先看看其他文件',
          '给我一些建议'
        ]
      })
    })

    it('应该拒绝建议数量不足的 ask 调用', () => {
      const json = JSON.stringify({
        tool_call: {
          name: 'ask',
          arguments: {
            question: '问题？',
            suggest: ['选项1']
          }
        }
      });

      const result = parseAskCall(json)

      expect(result).toBeNull()
      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[ParserAdapter] ask 调用建议数量错误: 1'
      )
    })

    it('应该拒绝没有 question 的 ask 调用', () => {
      const json = JSON.stringify({
        tool_call: {
          name: 'ask',
          arguments: {
            suggest: ['选项1', '选项2']
          }
        }
      });

      const result = parseAskCall(json)

      expect(result).toBeNull()
      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[ParserAdapter] ask 调用缺少 question'
      )
    })
  })

  describe('isToolRetryable', () => {
    it('应该为可重试的工具返回 true', () => {
      expect(isToolRetryable('search_docs')).toBe(true)
      expect(isToolRetryable('read_doc')).toBe(true)
      expect(isToolRetryable('list_docs')).toBe(true)
    })

    it('应该为不可重试的工具返回 false', () => {
      expect(isToolRetryable('ask')).toBe(false)
      expect(isToolRetryable('invalid_tool')).toBe(false)
    })
  })
})