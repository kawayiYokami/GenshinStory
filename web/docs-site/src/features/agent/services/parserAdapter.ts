import { XMLParser, XMLBuilder } from 'fast-xml-parser'
import logger from '../../app/services/loggerService'

export interface ParserError {
  code: string
  message: string
  severity: 'error' | 'warn'
  tool?: string
  line?: number
  column?: number
  snippet?: string
  suggestion?: string
}

export interface ParsedToolCall {
  name: string
  params: Record<string, any>
  xml: string
}

// 解析器配置
const PARSER_OPTIONS = {
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  textNodeName: '#text',
  cdataPropName: '#cdata',
  commentPropName: '#comment',
  removeNSPrefix: false,
  parseAttributeValue: true,
  parseTrueNumberOnly: true,
  arrayMode: true, // 自动将重复节点转为数组
  stopNodes: ['*.pre', '*.script'], // 停止解析的节点
  processEntities: false, // 禁用实体解析防止 XXE
  htmlEntities: false,
  // 安全限制
  maxNodeLength: 1000000, // 单个节点最大 1MB
  maxAttributes: 100, // 单个节点最多属性
}

const BUILDER_OPTIONS = {
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  textNodeName: '#text',
  cdataPropName: '#cdata',
  format: true,
  indentBy: '  ',
}

// 创建解析器实例
const parser = new XMLParser(PARSER_OPTIONS)
const builder = new XMLBuilder(BUILDER_OPTIONS)

/**
 * 结构化错误工厂
 */
function createParserError(
  code: string,
  message: string,
  severity: 'error' | 'warn' = 'error',
  options: Partial<Omit<ParserError, 'code' | 'message' | 'severity'>> = {}
): ParserError {
  return new ParserError(code, message, { severity, ...options });
}

/**
 * 验证 XML 大小和深度
 */
function validateXMLSize(xmlString: string): ParserError | null {
  const MAX_XML_SIZE = 5 * 1024 * 1024 // 5MB
  const MAX_DEPTH = 100

  if (xmlString.length > MAX_XML_SIZE) {
    return createParserError(
      'XML_TOO_LARGE',
      `XML 内容过大 (${Math.round(xmlString.length / 1024)}KB)，超过 ${Math.round(MAX_XML_SIZE / 1024)}KB 限制`,
      'error',
      { suggestion: '请减少查询范围或分批处理' }
    )
  }

  // 更准确的深度检查
  let depth = 0;
  let maxDepth = 0;
  const tagRegex = /<([a-zA-Z0-9_:-]+)(?:\s[^>]*)?>|<\/([a-zA-Z0-9_:-]+)>/g;
  let match;

  while ((match = tagRegex.exec(xmlString)) !== null) {
    if (match[1] && !match[0].endsWith('/>')) {
      // 开标签
      depth++;
      if (depth > maxDepth) maxDepth = depth;
    } else if (match[2]) {
      // 闭标签
      depth = Math.max(0, depth - 1);
    }
  }

  if (maxDepth > MAX_DEPTH) {
    return createParserError(
      'DEPTH_LIMIT',
      `XML 嵌套过深 (${maxDepth} 层)，超过 ${MAX_DEPTH} 层限制`,
      'error',
      { suggestion: '请简化查询结构' }
    )
  }

  return null
}

/**
 * 解析多个工具调用
 */
export function parseMultipleToolCalls(xmlString: string): {
  calls: ParsedToolCall[]
  errors: ParserError[]
} {
  const calls: ParsedToolCall[] = []
  const errors: ParserError[] = []

  // 基础验证
  if (!xmlString || typeof xmlString !== 'string') {
    errors.push(createParserError(
      'INVALID_INPUT',
      '输入必须是有效的 XML 字符串',
      'error'
    ))
    return { calls: [], errors }
  }

  // 大小验证
  const sizeError = validateXMLSize(xmlString)
  if (sizeError) {
    errors.push(sizeError)
    return { calls: [], errors }
  }

  try {
    // 包装在根节点中解析
    const wrappedXml = `<root>${xmlString}</root>`
    const result = parser.parse(wrappedXml)

    // 提取工具调用节点
    const toolNodes = result.root ? Object.keys(result.root).filter(key =>
      !key.startsWith('#') && typeof result.root[key] === 'object'
    ) : []

    /**
     * 从原始 XML 字符串中提取工具的原始 XML
     */
    function extractOriginalToolXml(xmlString: string, toolName: string): string {
      // 使用正则表达式匹配工具标签
      const regex = new RegExp(`<${toolName}[^>]*>([\\s\\S]*?)<\\/${toolName}>`, 'i');
      const match = xmlString.match(regex);
      if (match) {
        return match[0];
      }

      // 如果没找到，尝试自闭合标签
      const selfClosingRegex = new RegExp(`<${toolName}[^>]*/>`, 'i');
      const selfClosingMatch = xmlString.match(selfClosingRegex);
      if (selfClosingMatch) {
        return selfClosingMatch[0];
      }

      // 如果还是没找到，返回重建的XML作为备选
      return buildToolXml(toolName, {});
    }

    const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask']

    // 工具名称别名映射
    const TOOL_ALIASES: Record<string, string> = {
      'read': 'read_doc',
      'read_file': 'read_doc',
      'read_document': 'read_doc',
      'open': 'read_doc',
      'show': 'read_doc',
      'search': 'search_docs',
      'find': 'search_docs',
      'list': 'list_docs',
      'ls': 'list_docs',
      'dir': 'list_docs',
      'question': 'ask',
      'query': 'ask'
    }

    for (const toolName of toolNodes) {
      let finalToolName = toolName

      // 检查是否是别名
      if (!VALID_TOOLS.includes(toolName)) {
        if (TOOL_ALIASES[toolName]) {
          finalToolName = TOOL_ALIASES[toolName]
          logger.warn(`[ParserAdapter] 工具名称别名映射: ${toolName} -> ${finalToolName}`)
        } else {
          errors.push(createParserError(
            'INVALID_TOOL',
            `无效的工具名称 "${toolName}"`,
            'warn',
            { tool: toolName }
          ))
          continue
        }
      }

      const toolData = result.root[toolName]
      const params = extractParams(toolData)
      // 使用原始 XML 而不是重建的
      const xml = extractOriginalToolXml(xmlString, toolName)

      calls.push({
        name: finalToolName,
        params,
        xml,
      })
    }
  } catch (error: any) {
    logger.error('[ParserAdapter] XML 解析错误:', error)

    errors.push(createParserError(
      'PARSE_ERROR',
      `XML 解析失败: ${error.message}`,
      'error',
      {
        snippet: xmlString.slice(0, 200) + (xmlString.length > 200 ? '...' : ''),
        suggestion: '请检查 XML 格式是否正确'
      }
    ))
  }

  return { calls, errors }
}

/**
 * 解析单个工具调用（兼容旧接口）
 */
export function parseSingleToolCall(xmlString: string): ParsedToolCall | null {
  const { calls, errors } = parseMultipleToolCalls(xmlString)

  if (errors.length > 0) {
    // 只记录第一个错误
    logger.error('[ParserAdapter] 解析错误:', errors[0])
    return null
  }

  return calls[0] || null
}

/**
 * 提取参数对象
 */
function extractParams(toolData: any): Record<string, any> {
  const params: Record<string, any> = {}

  // 处理简单值
  if (typeof toolData === 'string' || typeof toolData === 'number') {
    params.args = String(toolData)
    return params
  }

  // 处理对象
  for (const [key, value] of Object.entries(toolData)) {
    if (key.startsWith('#')) continue // 跳过元数据

    if (Array.isArray(value)) {
      // 如果是数组，检查是否可以简化
      if (value.length === 1 && typeof value[0] === 'string') {
        params[key] = value[0]
      } else {
        params[key] = value
      }
    } else if (typeof value === 'object' && value !== null) {
      // 处理嵌套对象
      params[key] = flattenObject(value)
    } else {
      params[key] = value
    }
  }

  // 如果没有提取到参数，将整个内容作为 args
  if (Object.keys(params).length === 0) {
    params.args = builder.build(toolData)
  }

  return params
}

/**
 * 扁平化对象（将嵌套对象转为点记法）
 */
function flattenObject(obj: any, prefix = ''): Record<string, any> {
  const result: Record<string, any> = {}

  for (const [key, value] of Object.entries(obj)) {
    if (key.startsWith('#')) continue

    const fullKey = prefix ? `${prefix}.${key}` : key

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      Object.assign(result, flattenObject(value, fullKey))
    } else {
      result[fullKey] = value
    }
  }

  return result
}

/**
 * 构建 XML 字符串
 */
function buildToolXml(toolName: string, toolData: any): string {
  try {
    const xmlObj = { [toolName]: toolData }
    return builder.build(xmlObj)
  } catch (error) {
    logger.error('[ParserAdapter] XML 构建错误:', error)
    return `<${toolName}>${JSON.stringify(toolData)}</${toolName}>`
  }
}

/**
 * 解析 read_doc 请求（兼容旧接口）
 */
export function parseReadDocRequests(argsContent: string): any[] {
  if (!argsContent) return []

  // 检查是否是 JSON 字符串格式
  if (argsContent.trim().startsWith('{') && argsContent.trim().endsWith('}')) {
    try {
      const parsed = JSON.parse(argsContent)
      return parseJsonDocRequests(parsed)
    } catch (error) {
      // JSON 解析失败，继续尝试 XML 解析
      logger.warn('[ParserAdapter] JSON 解析失败，尝试 XML 解析:', error)
    }
  }

  // 使用 fast-xml-parser 解析 XML
  try {
    const result = parser.parse(`<root>${argsContent}</root>`)
    const docRequests: any[] = []

    const docs = result.root?.doc || []
    const docsArray = Array.isArray(docs) ? docs : [docs]

    for (const doc of docsArray) {
      if (doc.path) {
        const request: any = {
          path: typeof doc.path === 'string' ? doc.path : doc.path['#text'] || '',
          lineRanges: []
        }

        // 处理 line_range
        const lineRanges = doc.line_range || []
        const rangesArray = Array.isArray(lineRanges) ? lineRanges : [lineRanges]

        for (const range of rangesArray) {
          if (typeof range === 'string') {
            request.lineRanges.push(range)
          } else if (range && range['#text']) {
            request.lineRanges.push(range['#text'])
          }
        }

        docRequests.push(request)
      }
    }

    // 如果没有 doc 节点，尝试直接解析 path
    if (docRequests.length === 0 && result.root?.path) {
      const paths = Array.isArray(result.root.path) ? result.root.path : [result.root.path]
      for (const path of paths) {
        docRequests.push({
          path: typeof path === 'string' ? path : path['#text'] || '',
          lineRanges: []
        })
      }
    }

    return docRequests
  } catch (error) {
    logger.error('[ParserAdapter] read_doc XML 解析错误:', error)
    return []
  }
}

/**
 * 规范化 lineRanges 为字符串数组
 */
function _normalizeLineRanges(ranges: unknown): string[] {
  if (Array.isArray(ranges)) {
    // 确保数组内都是字符串
    return ranges.filter(r => typeof r === 'string');
  }
  if (typeof ranges === 'string') {
    // 如果是单个字符串，放入数组
    return [ranges];
  }
  // 其他情况返回空数组
  return [];
}

/**
 * 从 JSON 对象解析文档请求
 */
function parseJsonDocRequests(parsed: any): any[] {
  const docRequests: any[] = []

  // 处理嵌套格式: { doc: { path: "file.md" } }
  if (parsed.doc) {
    const docs = Array.isArray(parsed.doc) ? parsed.doc : [parsed.doc]
    for (const doc of docs) {
      if (doc.path) {
        const ranges = doc.line_range || doc.lineRanges;
        docRequests.push({
          path: doc.path,
          lineRanges: _normalizeLineRanges(ranges)
        })
      }
    }
  }
  // 处理扁平化格式: { "doc.path": "file.md" }
  else if (parsed['doc.path']) {
    const ranges = parsed['doc.lineRanges'] || parsed['doc.line_range'] || parsed['line_range'];
    docRequests.push({
      path: parsed['doc.path'],
      lineRanges: _normalizeLineRanges(ranges)
    })
  }
  // 处理 args 包装格式: { args: { doc: { path: "file.md" } } }
  else if (parsed.args && (parsed.args.doc || parsed.args['doc.path'])) {
    const argsDocs = parseJsonDocRequests(parsed.args)
    docRequests.push(...argsDocs)
  }

  return docRequests
}

/**
 * 解析 JSON 工具调用
 */
export function parseJsonToolCall(toolCall: any): ParsedToolCall | null {
  if (!toolCall || !toolCall.function) return null

  const { name, arguments: args } = toolCall.function
  const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask']

  if (!VALID_TOOLS.includes(name)) {
    logger.log(`[ParserAdapter] 忽略无效工具: ${name}`)
    return null
  }

  try {
    let params: any

    if (typeof args === 'string') {
      // 处理字符串形式的 JSON
      try {
        params = JSON.parse(args)
      } catch (jsonError) {
        // 如果 JSON 解析失败，将整个字符串作为 args 参数
        params = { args }
      }
    } else if (args !== null && typeof args === 'object') {
      // 处理已经是对象的参数
      params = args
    } else {
      // 处理其他类型（包括 null 和 undefined）
      params = { args: String(args) }
    }

    // 构建 XML 字符串，确保对 JSON 进行转义
    let xmlContent: string;
    try {
      xmlContent = JSON.stringify(params);
    } catch (stringifyError) {
      // 如果 stringify 失败，使用一个简单的表示
      xmlContent = '[Object object]';
    }

    return {
      name,
      params,
      xml: `<${name}>${xmlContent}</${name}>`,
    }
  } catch (error) {
    logger.error(`[ParserAdapter] JSON 解析错误 (${name}):`, error)
    return null
  }
}

/**
 * 解析 ask 调用
 */
export function parseAskCall(xmlString: string): {
  xml: string
  question: string
  suggestions: string[]
} | null {
  const { calls, errors } = parseMultipleToolCalls(xmlString)

  if (errors.length > 0 || !calls[0] || calls[0].name !== 'ask') {
    return null
  }

  const params = calls[0].params

  // 自动补全 question
  const question = params.question || '请选择'
  if (!params.question) {
    logger.warn('[ParserAdapter] ask 调用缺少 question，自动补全为"请选择"')
  }

  // 处理 suggestions，限制在2-4个之间
  let suggestions = Array.isArray(params.suggest)
    ? params.suggest.filter((s: any) => typeof s === 'string')
    : []

  // 如果没有 suggestions，尝试从其他字段获取
  if (suggestions.length === 0 && params.suggestions) {
    suggestions = Array.isArray(params.suggestions)
      ? params.suggestions.filter((s: any) => typeof s === 'string')
      : []
  }

  // 限制建议数量
  if (suggestions.length > 4) {
    logger.warn(`[ParserAdapter] ask 调用建议过多 (${suggestions.length})，只保留前4个`)
    suggestions = suggestions.slice(0, 4)
  } else if (suggestions.length < 2 && suggestions.length > 0) {
    // 如果只有1个建议，这不太合理，但也可以接受
    logger.warn(`[ParserAdapter] ask 调用建议过少 (${suggestions.length})`)
  }

  return {
    xml: calls[0].xml,
    question: question,
    suggestions,
  }
}

// 兼容旧接口的导出
export function parseMultiple(xmlString: string, config?: any) {
  const { calls, errors } = parseMultipleToolCalls(xmlString)

  if (errors.length > 0) {
    throw errors[0]
  }

  return calls.map(call => ({
    tagName: call.name,
    parsed: call.params,
    rawXml: call.xml
  }))
}

export function nodeToParams(parsed: any): Record<string, string> {
  const params: Record<string, string> = {}

  for (const [key, value] of Object.entries(parsed)) {
    if (typeof value === 'string') {
      params[key] = value
    } else if (typeof value === 'object') {
      params[key] = JSON.stringify(value)
    } else {
      params[key] = String(value)
    }
  }

  return params
}

export class ParserError extends Error {
  code: string
  severity: 'error' | 'warn'
  tool?: string
  line?: number
  column?: number
  snippet?: string
  suggestion?: string

  constructor(code: string, message: string, opts?: Partial<ParserError>) {
    super(message)
    this.name = 'ParserError'
    this.code = code
    this.severity = opts?.severity || 'error'
    this.tool = opts?.tool
    this.line = opts?.line
    this.column = opts?.column
    this.snippet = opts?.snippet
    this.suggestion = opts?.suggestion
  }
}

export default {
  parseMultipleToolCalls,
  parseSingleToolCall,
  parseReadDocRequests,
  parseJsonToolCall,
  parseAskCall,
  parseMultiple,
  nodeToParams,
  ParserError
}