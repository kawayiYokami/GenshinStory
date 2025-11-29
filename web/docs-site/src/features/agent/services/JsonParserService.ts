import { FlatToolCall, isFlatToolCall } from '../types';

/**
 * 将带转义符的 JSON 字符串（通常作为另一个 JSON 字段的值）还原为可用的 JSON 对象。
 *
 * @param escapedJsonString - 包含转义 JSON 结构的外部 JSON 字符串。
 * @param keyToUnescape - 包含内部转义 JSON 字符串的字段名。
 * @returns 还原后的内部 JSON 对象。
 */
function unescapeAndParseJson(escapedJsonString: string, keyToUnescape: string): any {
    // 1. 第一次解析：解析外部 JSON 结构。
    const outerObject = JSON.parse(escapedJsonString);

    // 检查字段是否存在
    if (!outerObject || typeof outerObject[keyToUnescape] !== 'string') {
        throw new Error(`字段 '${keyToUnescape}' 不存在或不是字符串类型。`);
    }

    // 获取内部带转义符的 JSON 字符串值
    const innerEscapedString: string = outerObject[keyToUnescape];

    // 2. 第二次解析：解析内部字符串值，完成还原。
    // JSON.parse() 会自动处理 " 还原为 "，\\n 还原为 \n 等操作。
    const finalJsonObject = JSON.parse(innerEscapedString);

    return finalJsonObject;
}

interface ExtractionResult {
  json: Record<string, any>;
  startIndex: number;
  endIndex: number;
  original: string;
  repairs?: string[];
}

function stripCodeFences(text: string): string {
  if (!text) return text;
  return text.replace(/```json/gi, '').replace(/```/g, '').trim();
}

/**
 * 简化的JSON解析服务 - 只保留核心功能
 */
export class JsonParserService {
  private readonly VALID_TOOLS = ['search_docs', 'read_doc', 'ask_choice'];

  /**
   * 根据字段类型智能匹配工具参数
   */
  private matchToolFields(obj: Record<string, any>): FlatToolCall | null {
    const result: any = {};
    let toolName: string | undefined;

    // 遍历所有字段进行分类
    for (const [key, value] of Object.entries(obj)) {
      // 1. 识别工具名
      if (this.isValidToolName(key)) {
        toolName = key;
        // 根据工具类型映射默认值
        if (typeof value === 'string') {
          switch (key) {
            case 'search_docs':
              result.query = value;
              break;
            case 'ask_choice':
              result.question = value;
              break;
            case 'read_doc':
              result.path = value;
              break;
          }
        } else if (Array.isArray(value) && key === 'ask_choice') {
          // 处理quest格式的suggestions数组
          result.suggestions = value;
        }
        continue;
      }

      // 2. 路径识别
      if (typeof value === 'string' && value.includes('/') && this.isValidPath(value)) {
        result.path = value;
        continue;
      }

      // 3. 行范围识别
      if (typeof value === 'string' && value.includes('-') && /^\d+-\d+$/.test(value)) {
        result.line_range = value;
        continue;
      }

      // 4. 数组直接保留
      if (Array.isArray(value)) {
        result[key] = value;
        continue;
      }

      // 5. 其他字段直接保留
      result[key] = value;
    }

    // 如果没有找到工具名，尝试通过name字段
    if (!toolName && obj.name && typeof obj.name === 'string' && this.isValidToolName(obj.name)) {
      toolName = obj.name;
    }

    // 修复：同时检查标准的 'tool' 字段
    if (!toolName && obj.tool && typeof obj.tool === 'string' && this.isValidToolName(obj.tool)) {
      toolName = obj.tool;
    }

    if (!toolName) {
      return null;
    }

    return {
      tool: toolName,
      ...result
    };
  }

  /**
   * 验证是否为有效路径
   */
  private isValidPath(path: string): boolean {
    const invalidChars = [' ', '&', '<', '>', '|', '"', "'", '`', '\n', '\r', '\t', '\0'];

    for (const char of invalidChars) {
      if (path.includes(char)) return false;
    }

    if (path.startsWith('.') || path.endsWith('.') || path.endsWith(' ') || path.startsWith(' ')) {
      return false;
    }

    if (/^\d+\.\d+\/\d+\.\d+$/.test(path) || /^v\d+\.\d+\/\w+/.test(path)) {
      return false;
    }

    if (path.includes('version') || path.includes('release') || path.includes('alpha') || path.includes('beta') || path.includes('patch')) {
      return false;
    }

    return true;
  }

  /**
   * 展开嵌套结构为平铺对象
   */
  private flattenNestedObject(obj: any): Record<string, any> {
    if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
      return obj;
    }

    // 处理嵌套的 tool_call 结构
    if (obj.tool_call && obj.tool_call.name) {
      const flattened: Record<string, any> = {
        name: obj.tool_call.name
      };

      // 展开arguments或args中的所有字段
      const args = obj.tool_call.arguments || obj.tool_call.args || {};
      if (typeof args === 'object' && args !== null && !Array.isArray(args)) {
        Object.assign(flattened, args);
      }

      return flattened;
    }

    // 处理quest格式：{ask_choice: {question: "...", suggestions: [...]}}
    if (obj.ask_choice && typeof obj.ask_choice === 'object') {
      const flattened: Record<string, any> = {
        ask_choice: obj.ask_choice.question || ''
      };

      // 展开suggestions
      if (Array.isArray(obj.ask_choice.suggestions)) {
        flattened.suggestions = obj.ask_choice.suggestions;
      }

      // 展开其他字段
      for (const [key, value] of Object.entries(obj.ask_choice)) {
        if (key !== 'question' && key !== 'suggestions') {
          flattened[key] = value;
        }
      }

      return flattened;
    }

    return obj;
  }

  /**
   * 验证工具名称
   */
  private isValidToolName(name: string): boolean {
    return this.VALID_TOOLS.includes(name);
  }

  /**
   * 解析LLM响应 - 统一重新构造平铺格式
   */
  parseLlmResponse(responseText: string): Record<string, any> | null {
    if (typeof responseText !== 'string' || !responseText.trim()) {
      return null;
    }

    // 策略优化：不再依赖脆弱的行遍历寻找最后一个 {，而是尝试解析所有可能的 JSON 块
    // 优先尝试整个字符串（处理纯 JSON 响应）
    try {
      const fullParsed = JSON.parse(stripCodeFences(responseText));
      if (typeof fullParsed === 'object' && fullParsed !== null && !Array.isArray(fullParsed)) {
        return this.processParsedObject(fullParsed, responseText);
      }
    } catch (e) {
      // 忽略错误，继续寻找子串
    }

    // 查找所有 { 的位置
    const braceIndices: number[] = [];
    let idx = responseText.indexOf('{');
    while (idx !== -1) {
      braceIndices.push(idx);
      idx = responseText.indexOf('{', idx + 1);
    }

    // 如果没有找到 {，直接返回 null
    if (braceIndices.length === 0) {
      return null;
    }

    // 从后往前尝试（通常工具调用在最后），或者从前往后？
    // 如果是嵌套结构 {"a": {"b": 1}}，我们需要最外层的 {。
    // 如果是多个独立块 A... {B} ... {C}，通常最后一个是有效的工具调用。
    // 但是考虑到嵌套，如果从后往前找，会先找到 {"b": 1}，这可能不是我们要的（如果它只是参数的一部分）。
    // 不过 parseLlmResponse 的目标通常是提取整个工具调用对象。
    // 如果工具调用本身包含嵌套对象，JSON.parse 会成功解析最外层。
    // 所以应该优先尝试“最外层且最后”的块。
    // 简单的策略：尝试每一个 { 开始的子串，直到找到一个合法的对象。
    // 为了性能和准确性，我们从第一个 { 开始尝试。如果有多个平行的 JSON，这会返回第一个。
    // 如果需要最后一个，应该倒序遍历？
    // 通常 LLM 输出为： "Analysis... \n { Tool Call }"
    // 此时只有一个顶层 JSON。
    // 如果输出为： "{Status} \n {Tool}", 我们可能想要 Tool。
    // 这里我们保留原有逻辑的意图：寻找“最后”的有效 JSON。
    // 所以我们倒序遍历 braceIndices。

    for (let i = braceIndices.length - 1; i >= 0; i--) {
      const start = braceIndices[i];
      const candidate = responseText.substring(start);
      const cleaned = stripCodeFences(candidate);

      try {
        const parsed = JSON.parse(cleaned);
        if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
          // 成功解析！
          return this.processParsedObject(parsed, cleaned);
        }
      } catch (e) {
        // 解析失败，尝试下一个候选
      }
    }

    return null;
  }

  /**
   * 统一处理解析后的对象（处理 feedback_data、展开嵌套、匹配工具字段）
   */
  private processParsedObject(parsed: any, rawJsonString: string): Record<string, any> | null {
      // 处理feedback_data格式
      let finalObj = parsed;
      if ('feedback_data' in parsed) {
        let feedbackData = parsed.feedback_data;
        if (typeof feedbackData === 'string') {
          // 尝试使用反转义方法
          try {
            feedbackData = unescapeAndParseJson(rawJsonString, 'feedback_data');
          } catch (e) {
            // 如果失败，尝试直接解析
            try {
              feedbackData = JSON.parse(feedbackData);
            } catch (e2) {
              // 如果还是失败，尝试使用简单的字符替换
              feedbackData = JSON.parse(feedbackData.replace(/\\\\/g, '\\').replace(/\\"/g, '"').replace(/\\n/g, '\n'));
            }
          }
        }
        finalObj = feedbackData as Record<string, any>;
      }

      // 展开嵌套结构
      const flattenedObj = this.flattenNestedObject(finalObj);

      // 统一对所有格式进行字段匹配和重新构造
      const toolCall = this.matchToolFields(flattenedObj);
      if (toolCall) {
        return toolCall;
      }

      return flattenedObj;
  }
}

export default new JsonParserService();