import logger from '@/features/app/services/loggerService';
import jsonParserService from './JsonParserService';
import toolParserService from './toolParserService';
import type { ParsedToolCall } from './toolParserService';

/**
 * 计算字符串的简单哈希值（不用于安全目的，仅用于日志记录）
 */
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(16);
}

export interface ProcessedContent {
  cleanedContent: string;
  toolCalls: ParsedToolCall[];
  originalContent: string;
}

export interface ReconstructOptions {
  includeToolCalls?: boolean;
  toolCallFormat?: 'original' | 'formatted';
}

/**
 * 统一的内容处理包装层
 * 处理AI响应中的工具调用提取和重建
 */
export class ContentProcessor {
  /**
   * 从原始内容中提取工具调用，返回清理后的内容和工具调用
   */
  static extract(originalContent: string): ProcessedContent {
    // 使用 JsonParserService 解析LLM响应
    const result = jsonParserService.parseLlmResponse(originalContent);

    const toolCalls: ParsedToolCall[] = [];
    let cleanedContent = originalContent;

    // 处理解析到的结果
    if (result) {
      const parsedResult = result.toolCall;

      // 检查是否为工具调用
      if ('tool' in parsedResult && typeof parsedResult.tool === 'string') {
        // 修复：直接传递对象给toolParserService，避免不必要的字符串化
        const toolCall = toolParserService.parseToolCall(parsedResult);

        if (toolCall) {
          toolCalls.push(toolCall);

          // 使用 JsonParserService 返回的起始位置进行清理
          // 截断从 startIndex 开始的所有内容
          cleanedContent = originalContent.substring(0, result.startIndex);
        }
      }
    }

    // 清理多余的空白行
    cleanedContent = cleanedContent.replace(/\n\s*\n\s*\n/g, '\n\n').trim();

    return {
      cleanedContent,
      toolCalls,
      originalContent
    };
  }

  /**
   * 从清理后的内容和工具调用重建原始内容
   * 用于历史消息传递给LLM时，使用标准化的正确格式进行错误纠正学习
   */
  static reconstruct(processed: ProcessedContent, options: ReconstructOptions = {}): string {
    const { includeToolCalls = true, toolCallFormat = 'original' } = options;

    if (!includeToolCalls || processed.toolCalls.length === 0) {
      return processed.cleanedContent;
    }

    let reconstructed = processed.cleanedContent;

    // 修复：直接内嵌工具调用到内容末尾，避免视觉拆分
    for (const toolCall of processed.toolCalls) {
      let toolCallContent: string;

      if (toolCallFormat === 'original') {
        // 历史消息中总是使用标准化格式进行错误纠正学习
        // 这样LLM会在对话历史中看到正确的工具调用格式
        const standardizedFormat = {
          ...toolCall.params,
          tool: toolCall.name
        };
        toolCallContent = JSON.stringify(standardizedFormat);
      } else {
        toolCallContent = JSON.stringify(toolCall.params, null, 2);
      }

      // 内嵌到内容末尾，保留换行符确保解析一致性
      reconstructed += '\n' + toolCallContent;
    }

    return reconstructed;
  }

  /**
   * 检查内容是否包含工具调用
   */
  static hasToolCalls(content: string): boolean {
    const result = this.extract(content);
    return result.toolCalls.length > 0;
  }

  /**
   * 获取内容中的工具调用数量
   */
  static getToolCallCount(content: string): number {
    const result = this.extract(content);
    return result.toolCalls.length;
  }

  /**
   * 验证处理的一致性（extract -> reconstruct 应该得到原始内容）
   */
  static validateConsistency(originalContent: string): boolean {
    const extracted = this.extract(originalContent);
    const reconstructed = this.reconstruct(extracted, {
      includeToolCalls: true,
      toolCallFormat: 'original'
    });

    const isConsistent = reconstructed === originalContent;

    if (!isConsistent) {
      // 记录安全的元数据而非敏感内容
      const diffCount = this.getDifferencesCount(originalContent, reconstructed);
    }

    return isConsistent;
  }

  /**
   * 计算两个字符串的差异数量
   */
  private static getDifferencesCount(str1: string, str2: string): number {
    const lines1 = str1.split('\n');
    const lines2 = str2.split('\n');
    let count = 0;

    for (let i = 0; i < Math.max(lines1.length, lines2.length); i++) {
      if (lines1[i] !== lines2[i]) {
        count++;
      }
    }

    return count;
  }

  /**
   * 计算两个字符串的差异
   */
  private static getDifferences(str1: string, str2: string): string {
    const lines1 = str1.split('\n');
    const lines2 = str2.split('\n');

    const differences: string[] = [];

    for (let i = 0; i < Math.max(lines1.length, lines2.length); i++) {
      if (lines1[i] !== lines2[i]) {
        differences.push(`行${i + 1}: "${lines1[i]}" -> "${lines2[i]}"`);
      }
    }

    return differences.join('; ');
  }
}
