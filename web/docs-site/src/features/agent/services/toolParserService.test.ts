import { describe, it, expect, vi, beforeEach } from 'vitest'
import toolParserService from '@/features/agent/services/toolParserService'
import logger from '@/features/app/services/loggerService'

// Mock logger
const mockedLogger = vi.mocked(logger)

// Extract functions from the default export for easier testing
const { 
  parseXmlToolCall, 
  parseJsonToolCall, 
  parseReadDocRequests,
  parseAskCall,
  isToolRetryable 
} = toolParserService

describe('ToolParserService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('parseXmlToolCall', () => {
    it('应该正确解析标准的 XML 工具调用', () => {
      const xml = `<search_docs>
  <query>Vue 3 composition API</query>
</search_docs>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toEqual({
        name: 'search_docs',
        params: { query: 'Vue 3 composition API' },
        xml: expect.stringContaining('<search_docs>')
      })
    })

    it('应该正确处理包含换行的 XML', () => {
      const xml = `<read_doc>
  <doc>
    <path>/src/components/Test.vue</path>
    <line_range>1-10</line_range>
    <line_range>20-30</line_range>
  </doc>
</read_doc>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeTruthy()
      expect(result?.name).toBe('read_doc')
      // fast-xml-parser 会解析嵌套结构
      expect(result?.params.doc).toBeTruthy()
      if (result?.params.doc) {
        const doc = Array.isArray(result.params.doc) ? result.params.doc[0] : result.params.doc
        expect(doc.path).toBe('/src/components/Test.vue')
        expect(doc.line_range).toEqual(['1-10', '20-30'])
      }
    })

    it('应该正确处理带有内部换行的参数', () => {
      const xml = `<read_doc>
  <doc>
    <path>/src/components/Test.vue</path>
  </doc>
  <doc>
    <path>/src/utils/helper.ts</path>
  </doc>
</read_doc>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeTruthy()
      expect(result?.name).toBe('read_doc')
      // fast-xml-parser 会解析为数组
      expect(result?.params.doc).toBeTruthy()
      const docs = Array.isArray(result?.params.doc) ? result?.params.doc : [result?.params.doc]
      expect(docs.length).toBe(2)
      expect(docs[0].path).toBe('/src/components/Test.vue')
      expect(docs[1].path).toBe('/src/utils/helper.ts')
    })

    it('应该拒绝无效的工具名称', () => {
      const xml = `<invalid_tool>
  <param>value</param>
</invalid_tool>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeNull()
      // parserAdapter 使用不同的日志消息
      expect(mockedLogger.error).toHaveBeenCalledWith(
        '[ParserAdapter] 解析错误:',
        expect.objectContaining({
          message: expect.stringContaining('无效的工具名称')
        })
      )
    })

    it('应该处理空的 XML 字符串', () => {
      const result = parseXmlToolCall('')
      expect(result).toBeNull()
    })

    it('应该处理非字符串输入', () => {
      const result = parseXmlToolCall(null as any)
      expect(result).toBeNull()
    })

    it('应该处理格式错误的 XML', () => {
      const xml = `<search_docs>
  <query>test
  </unclosed_tag>`

      const result = parseXmlToolCall(xml)
      
      // fast-xml-parser 可能能处理一些格式错误的 XML
      // 如果解析成功，至少应该返回正确的工具名
      if (result) {
        expect(result.name).toBe('search_docs')
      } else {
        expect(mockedLogger.error).toHaveBeenCalledWith(
          '[ParserAdapter] 解析错误:',
          expect.any(Object)
        )
      }
    })

    it('应该处理没有子元素的简单 XML', () => {
      const xml = `<list_docs>/src/components</list_docs>`

      const result = parseXmlToolCall(xml)
      
      // fast-xml-parser 会将文本内容作为 #text 属性
      expect(result).toBeTruthy()
      expect(result?.name).toBe('list_docs')
      expect(result?.params['#text']).toBe('/src/components')
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
      const args = `<doc>
  <path>/src/test.vue</path>
</doc>`

      const result = parseReadDocRequests(args)
      
      expect(result).toEqual([
        { path: '/src/test.vue', lineRanges: [] }
      ])
    })

    it('应该解析多个文档请求', () => {
      const args = `<doc>
  <path>/src/test.vue</path>
  <line_range>1-10</line_range>
</doc>
<doc>
  <path>/src/utils.ts</path>
</doc>`

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
      const args = `<path>/src/test.vue</path>
<path>/src/utils.ts</path>`

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
      const xml = `<ask>
  <question>您想要继续分析这个组件吗？</question>
  <suggest>是的，请继续</suggest>
  <suggest>不，先看看其他文件</suggest>
  <suggest>给我一些建议</suggest>
</ask>`

      const result = parseAskCall(xml)
      
      expect(result).toEqual({
        xml: expect.stringContaining('<ask>'),
        question: '您想要继续分析这个组件吗？',
        suggestions: [
          '是的，请继续',
          '不，先看看其他文件',
          '给我一些建议'
        ]
      })
    })

    it('应该拒绝建议数量不足的 ask 调用', () => {
      const xml = `<ask>
  <question>问题？</question>
  <suggest>选项1</suggest>
</ask>`

      const result = parseAskCall(xml)
      
      expect(result).toBeNull()
      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[ParserAdapter] ask 调用建议数量错误: 1'
      )
    })

    it('应该拒绝没有 question 的 ask 调用', () => {
      const xml = `<ask>
  <suggest>选项1</suggest>
  <suggest>选项2</suggest>
</ask>`

      const result = parseAskCall(xml)
      
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

  describe('边缘情况测试', () => {
    it('应该处理带有注释的 XML', () => {
      const xml = `<!-- 这是一个注释 -->
<search_docs>
  <query>Vue 3</query>
</search_docs>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeTruthy()
      expect(result?.name).toBe('search_docs')
    })

    it('应该处理带有 CDATA 的 XML', () => {
      const xml = `<search_docs>
  <query><![CDATA[Vue 3 & React]]></query>
</search_docs>`

      const result = parseXmlToolCall(xml)
      
      // fast-xml-parser 会自动处理 CDATA
      expect(result).toBeTruthy()
      expect(result?.name).toBe('search_docs')
      expect(result?.params.query).toBe('Vue 3 & React')
    })

    it('应该处理混合大小写的标签', () => {
      const xml = `<SEARCH_DOCS>
  <query>test</query>
</SEARCH_DOCS>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeNull() // 因为 VALID_TOOLS 是小写的
    })

    it('应该处理带有命名空间的 XML', () => {
      const xml = `<ns:search_docs xmlns:ns="http://example.com">
  <ns:query>test</ns:query>
</ns:search_docs>`

      const result = parseXmlToolCall(xml)
      
      // DOMParser 可能能处理，但标签名会包含命名空间
      expect(result?.name).not.toBe('search_docs')
    })
  })

  describe('性能测试', () => {
    it('应该能快速处理大量 XML', () => {
      const largeXml = Array(100).fill(0).map((_, i) => 
        `<doc>
          <path>/src/file${i}.vue</path>
          <line_range>${i}-${i+10}</line_range>
        </doc>`
      ).join('\n')

      const xml = `<read_doc>${largeXml}</read_doc>`
      
      const start = performance.now()
      const result = parseXmlToolCall(xml)
      const end = performance.now()
      
      expect(result).toBeTruthy()
      expect(end - start).toBeLessThan(100) // 应该在 100ms 内完成
    })

    it('应该能处理深层嵌套的 XML', () => {
      const xml = `<read_doc>
  <doc>
    <metadata>
      <source>test</source>
    </metadata>
    <path>/src/test.vue</path>
  </doc>
</read_doc>`

      const result = parseXmlToolCall(xml)
      
      expect(result).toBeTruthy()
      expect(result?.name).toBe('read_doc')
      // fast-xml-parser 会保留嵌套结构
      expect(result?.params.doc).toBeTruthy()
      if (result?.params.doc) {
        const doc = Array.isArray(result.params.doc) ? result.params.doc[0] : result.params.doc
        expect(doc.metadata.source).toBe('test')
        expect(doc.path).toBe('/src/test.vue')
      }
    })
  })
})