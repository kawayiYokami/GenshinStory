/**
 * Angel Eye 插件 - JSON 解析工具
 * 提供健壮的 JSON 提取功能，用于从模型返回的文本中安全地解析 JSON 数据
 */

// 创建一个默认的 logger 实现，以防在非测试环境中使用
const defaultLogger = {
  debug: function(...args: any[]) { console.log('[DEBUG]', ...args); },
  info: function(...args: any[]) { console.log('[INFO]', ...args); },
  warn: function(...args: any[]) { console.log('[WARN]', ...args); },
  error: function(...args: any[]) { console.log('[ERROR]', ...args); },
  log: function(...args: any[]) { console.log('[LOG]', ...args); }
};

import logger from '../../app/services/loggerService';

interface JsonCandidate {
  json: any;
  score: number;
  startIndex: number;
  endIndex: number;
  original: string;
}

export interface ExtractionResult {
  json: Record<string, any>;
  startIndex: number;
  endIndex: number;
  original: string;
}

/**
 * 去除常见的 Markdown 代码块围栏，避免干扰解析。
 * 例如: ```json ... ``` 或 ``` ... ```
 */
function stripCodeFences(text: string): string {
  if (!text) return text;
  // 仅移除围栏标记，不移除内部内容
  return text.replace(/```json/gi, '').replace(/```/g, '').trim();
}

/**
 * 在文本中扫描并返回所有"平衡的大括号"子串，作为潜在的 JSON 候选。
 * - 跳过字符串字面量中的花括号
 * - 支持嵌套
 * 返回顺序为出现顺序（从左到右）
 */
function findJsonCandidates(text: string): { content: string; startIndex: number; endIndex: number }[] {
  const candidates: { content: string; startIndex: number; endIndex: number }[] = [];
  if (!text) return candidates;

  let inString = false;
  let escape = false;
  let depth = 0;
  let startIdx: number | null = null;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === '\\') {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      // 字符串中不处理花括号
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === '{') {
      if (depth === 0) {
        startIdx = i;
      }
      depth++;
    } else if (ch === '}') {
      if (depth > 0) {
        depth--;
        if (depth === 0 && startIdx !== null) {
          candidates.push({
            content: text.substring(startIdx, i + 1),
            startIndex: startIdx,
            endIndex: i + 1
          });
          startIdx = null;
        }
      }
    }
  }

  return candidates;
}

/**
 * 高鲁棒性 JSON 解析器类。
 *
 * 负责从 LLM 响应中提取 JSON 部分并转换为结构化数据。
 * 使用智能候选识别和评分机制，确保在各种情况下都能正确解析。
 */
export class JsonParserService {
  private logger: any;

  /**
   * 初始化 JSON 解析器。
   */
  constructor() {
    // 使用传入的 logger 或默认的 logger
    try {
      // 尝试使用导入的 logger
      this.logger = logger;
      // 检查 logger 是否有 debug 方法
      if (!this.logger || typeof this.logger.debug !== 'function') {
        this.logger = defaultLogger;
      }
    } catch (e) {
      // 如果导入失败，使用默认 logger
      this.logger = defaultLogger;
    }
  }

  /**
   * 从 LLM 响应文本中解析出 feedback_data 字典。
   *
   * 使用高鲁棒性解析策略：
   * - 智能识别所有可能的JSON候选
   * - 根据字段完整性评分选择最佳候选
   * - 支持部分字段缺失的情况
   *
   * @param responseText LLM 的原始响应文本
   * @returns 解析后的 feedback_data 字典，失败时返回 null
   */
  parseLlmResponse(responseText: string): Record<string, any> | null {
    // 尝试提取JSON数据
    const result = this.extractJson(responseText);

    if (result === null) {
      this.logger.warn('JsonParser: 未能从响应中提取有效的 JSON');
      return null;
    }

    const jsonData = result.json;

    // 从 JSON 中提取 feedback_data
    if ('feedback_data' in jsonData) {
      let feedbackData = jsonData.feedback_data;

      // 如果 feedback_data 是字符串，尝试再次解析
      if (typeof feedbackData === 'string') {
        try {
          feedbackData = JSON.parse(feedbackData);
          this.logger.debug('JsonParser: feedback_data 是字符串，已重新解析为字典');
        } catch (error) {
          this.logger.warn('JsonParser: feedback_data 是字符串但无法解析为 JSON');
          return null;
        }
      }

      return feedbackData as Record<string, any>;
    } else {
      // 如果没有 feedback_data 包装，直接返回整个 JSON
      this.logger.debug('JsonParser: JSON 中未找到 \'feedback_data\' 字段，返回整个 JSON');
      return jsonData;
    }
  }

  /**
   * 从可能包含其他文本的字符串中，智能地提取最符合条件的单个JSON对象。
   *
   * 公共方法，用于从LLM响应中提取JSON数据。
   *
   * 提取策略:
   * 1.  **分割**: 如果存在分隔符，则优先处理分隔符之后的内容。
   * 2.  **清理**: 自动去除常见的Markdown代码块围栏。
   * 3.  **扫描**: 通过"平衡大括号"算法，找出所有结构上闭合的JSON候选片段。
   * 4.  **筛选**: (如果提供了`requiredFields`) 只保留那些包含所有必须字段的JSON对象。
   * 5.  **评分**: (如果提供了`optionalFields`) 根据包含的可选字段数量为每个合格的JSON对象打分。
   * 6.  **决策**: 返回分数最高的对象。如果分数相同，则选择在原文中位置最靠后的那一个。
   * 7.  **回退**: 如果上述策略找不到，则尝试一次"从第一个'{'到最后一个'}'"的大包围策略。
   *
   * @param text 包含JSON的模型原始输出字符串。
   * @param separator 用于分割内容的分隔符。
   * @param requiredFields 一个列表，JSON对象必须包含其中所有的字段才算合格。
   * @param optionalFields 一个列表，用于对合格的JSON对象进行评分，包含的可选字段越多，分数越高。
   * @return 最符合条件的JSON对象及其位置信息，如果找不到则返回null。
   */
  extractJson(
    text: string,
    separator: string = '---JSON---',
    requiredFields: string[] | null = null,
    optionalFields: string[] | null = null
  ): ExtractionResult | null {
    if (typeof text !== 'string') {
      this.logger.warn(`JsonParser: 输入不是字符串，而是 ${typeof text} 类型，无法解析`);
      return null;
    }

    if (!text.trim()) {
      this.logger.debug('JsonParser: 输入为空字符串');
      return null;
    }

    this.logger.log(`[JsonParser] 开始提取JSON，输入文本长度: ${text.length}`);

    // 1) 分隔符处理
    let jsonPart = text;
    let offset = 0; // 记录相对于原文的偏移量

    if (text.includes(separator)) {
      this.logger.debug(`JsonParser: 找到分隔符 '${separator}' 进行分割`);
      const parts = text.split(separator);
      if (parts.length > 1) {
        jsonPart = parts[1].trim();
        offset = text.indexOf(jsonPart); // 计算偏移量
      } else {
        this.logger.warn('JsonParser: 分隔符后无内容');
        return null;
      }
    } else {
      this.logger.debug(`JsonParser: 未找到分隔符 '${separator}'，将处理整个文本`);
      offset = 0;
    }

    // 在去除围栏前记录偏移量
    const preStripOffset = offset;

    // 2) 去掉代码围栏
    jsonPart = stripCodeFences(jsonPart);

    // 使用分隔符处理后的偏移量，如果找不到则使用原始偏移量
    const adjustedOffset = jsonPart ? text.indexOf(jsonPart) : preStripOffset;

    // 3) 扫描所有平衡的大括号候选
    const candidates = findJsonCandidates(jsonPart);
    this.logger.debug(`JsonParser: 扫描到可能的 JSON 候选数量: ${candidates.length}`);

    // 4) 筛选与评分
    const qualifiedJsons: JsonCandidate[] = [];
    for (const candidate of candidates) {
      try {
        const parsedJson = JSON.parse(candidate.content);
        if (typeof parsedJson !== 'object' || parsedJson === null || Array.isArray(parsedJson)) {
          continue; // 只处理对象类型的JSON
        }

        // 硬性条件：检查是否为工具调用JSON
        if (!parsedJson.tool_call) {
          this.logger.debug(`候选JSON不是tool_call格式，跳过: ${candidate.content.substring(0, 100)}...`);
          continue;
        }

        // 验证工具调用格式
        const toolCall = parsedJson.tool_call;
        if (!toolCall.name || !toolCall.arguments) {
          this.logger.debug(`tool_call缺少必要字段，跳过: ${candidate.content.substring(0, 100)}...`);
          continue;
        }

        // 验证工具名称是否在有效列表中
        const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask'];
        if (!VALID_TOOLS.includes(toolCall.name)) {
          this.logger.debug(`工具名称无效，跳过: ${toolCall.name}`);
          continue;
        }

        // 硬性条件：检查必须字段
        if (requiredFields) {
          if (!requiredFields.every(field => field in parsedJson)) {
            this.logger.debug(`候选JSON缺少必须字段，跳过: ${candidate.content.substring(0, 100)}...`);
            continue;
          }
        }

        // 计算分数
        let score = 0;
        if (optionalFields) {
          score = optionalFields.filter(field => field in parsedJson).length;
        }

        qualifiedJsons.push({
          json: parsedJson,
          score,
          startIndex: adjustedOffset + candidate.startIndex,
          endIndex: adjustedOffset + candidate.endIndex,
          original: candidate.content
        });
        this.logger.debug(`一个候选JSON合格，得分: ${score}`);

      } catch (error) {
        continue; // 解析失败，不是有效的JSON，跳过
      }
    }

    if (qualifiedJsons.length === 0) {
      this.logger.warn('JsonParser: 所有候选均不满足要求（或解析失败）。');
      return null;
    }

    // 5) 决策：选择分数最高的，同分则取第一个（AI不会连续发送多个工具调用）
    // 先按分数排序（稳定排序，降序），然后取第一个，这样就能保证在分数相同时，选择原文中位置更靠前的
    qualifiedJsons.sort((a, b) => b.score - a.score);
    const bestJsonItem = qualifiedJsons[0];

    this.logger.info(`JsonParser: 提取成功，选择了得分最高的JSON（得分: ${bestJsonItem.score}）。`);
    this.logger.log(`[JsonParser] 返回的JSON内容:`, bestJsonItem.json);

    return {
      json: bestJsonItem.json,
      startIndex: bestJsonItem.startIndex,
      endIndex: bestJsonItem.endIndex,
      original: bestJsonItem.original
    };
  }
}

export default new JsonParserService();