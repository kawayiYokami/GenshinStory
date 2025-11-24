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
  /** 原始的工具调用字符串（JSON格式） */
  original: string
}

/**
 * 检测并解析JSON格式的工具调用
 */
export function parseJsonToolCallFormat(input: string): ParsedToolCall | null {
  if (!input || typeof input !== 'string') return null;

  try {
    // 首先尝试解析整个字符串为JSON
    const parsed = JSON.parse(input);

    // 检查是否符合我们的工具调用格式
    if (parsed.tool_call && typeof parsed.tool_call === 'object') {
      const { name, arguments: args } = parsed.tool_call;

      // 验证工具名称
      const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask'];
      if (!VALID_TOOLS.includes(name)) {
        logger.log(`[ParserAdapter] 忽略无效工具: ${name}`);
        return null;
      }

      // 构建返回对象
      return {
        name,
        params: args || {},
        original: input // 保持原始JSON字符串
      };
    }

    return null;
  } catch (error) {
    // 不是有效的JSON格式，返回null
    logger.error('[ParserAdapter] JSON解析错误:', error);
    return null;
  }
}

/**
 * 解析单个工具调用（仅支持JSON格式）
 */
export function parseSingleToolCall(input: string): ParsedToolCall | null {
  if (!input || typeof input !== 'string') return null;

  // 只支持JSON格式
  const jsonResult = parseJsonToolCallFormat(input);
  if (jsonResult) {
    return jsonResult;
  }

  // 如果JSON解析失败，记录错误并返回null
  logger.error('[ParserAdapter] 无效的工具调用格式，仅支持JSON格式');
  return null;
}

/**
 * 解析 ask 调用（仅支持JSON格式）
 */
export function parseAskCall(jsonString: string): {
  original: string
  question: string
  suggestions: string[]
} | null {
  const result = parseSingleToolCall(jsonString);

  if (!result || result.name !== 'ask') {
    return null;
  }

  const params = result.params;

  // 检查是否缺少 question
  if (!params.question) {
    logger.warn('[ParserAdapter] ask 调用缺少 question');
    return null;
  }

  const question = params.question;

  // 处理 suggestions，限制在2-4个之间
  let suggestions: string[] = [];
  if (Array.isArray(params.suggest)) {
    suggestions = params.suggest.filter((s: any) => typeof s === 'string');
  }

  // 检查建议数量是否在有效范围内
  if (suggestions.length < 2 || suggestions.length > 4) {
    logger.warn(`[ParserAdapter] ask 调用建议数量错误: ${suggestions.length}`);
    return null;
  }

  return {
    original: result.original,
    question: question,
    suggestions,
  };
}

/**
 * 解析 read_doc 请求（仅支持JSON格式）
 */
export function parseReadDocRequests(argsContent: string): any[] {
  try {
    const parsed = JSON.parse(argsContent);

    if (!parsed || typeof parsed !== 'object') {
      return [];
    }

    const docRequests: any[] = [];

    // 处理单个文档请求
    if (parsed.doc) {
      const docs = Array.isArray(parsed.doc) ? parsed.doc : [parsed.doc];
      for (const doc of docs) {
        if (doc.path) {
          const lineRanges = doc.line_range ?
            (Array.isArray(doc.line_range) ? doc.line_range : [doc.line_range]) : [];
          docRequests.push({
            path: doc.path,
            lineRanges: lineRanges.filter((r: any) => typeof r === 'string')
          });
        }
      }
    }

    // 处理简单路径列表
    if (parsed.path) {
      const paths = Array.isArray(parsed.path) ? parsed.path : [parsed.path];
      for (const path of paths) {
        if (typeof path === 'string') {
          docRequests.push({
            path: path,
            lineRanges: []
          });
        }
      }
    }

    return docRequests;
  } catch (error) {
    logger.error('[ParserAdapter] read_doc 参数解析错误:', error);
    return [];
  }
}

export default {
  parseSingleToolCall,
  parseReadDocRequests,
  parseAskCall,
};