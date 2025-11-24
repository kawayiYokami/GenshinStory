import logger from '@/features/app/services/loggerService';
import jsonParserService, { ExtractionResult } from './JsonParserService';
import toolParserService from './toolParserService';
import type { ParsedToolCall } from './toolParserService';

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
    logger.log('[ContentProcessor] 开始处理内容:', originalContent.substring(0, 100) + '...');

    // 使用 JsonParserService 提取JSON（带位置信息）
    const extractedResult = jsonParserService.extractJson(originalContent);
    logger.log('[ContentProcessor] 提取到的JSON数量:', extractedResult ? 1 : 0);

    const toolCalls: ParsedToolCall[] = [];
    let cleanedContent = originalContent;

    // 处理提取到的JSON
    if (extractedResult) {
      // 尝试解析为工具调用
      const jsonString = JSON.stringify(extractedResult.json);
      const toolCall = toolParserService.parseToolCall(jsonString);

      if (toolCall) {
        toolCalls.push(toolCall);

        // 从JSON起点删除到末尾
        cleanedContent = originalContent.substring(0, extractedResult.startIndex);

        logger.log('[ContentProcessor] 成功提取并删除工具调用:', toolCall.name);
        logger.log('[ContentProcessor] 删除位置:', {
          startIndex: extractedResult.startIndex,
          endIndex: extractedResult.endIndex,
          deletedLength: extractedResult.endIndex - extractedResult.startIndex
        });
      } else {
        logger.log('[ContentProcessor] JSON不是工具调用，保留在内容中');
      }
    }

    // 清理多余的空白行
    cleanedContent = cleanedContent.replace(/\n\s*\n\s*\n/g, '\n\n').trim();

    logger.log('[ContentProcessor] 最终清理结果:', {
      hasToolCalls: toolCalls.length > 0,
      cleanedContentLength: cleanedContent.length,
      originalContentLength: originalContent.length
    });

    return {
      cleanedContent,
      toolCalls,
      originalContent
    };
  }

  /**
   * 从清理后的内容和工具调用重建原始内容
   */
  static reconstruct(processed: ProcessedContent, options: ReconstructOptions = {}): string {
    const { includeToolCalls = true, toolCallFormat = 'original' } = options;

    if (!includeToolCalls || processed.toolCalls.length === 0) {
      return processed.cleanedContent;
    }

    let reconstructed = processed.cleanedContent;

    // 在内容末尾添加工具调用
    for (const toolCall of processed.toolCalls) {
      const toolCallContent = toolCallFormat === 'original'
        ? toolCall.original
        : JSON.stringify(toolCall.params, null, 2);

      reconstructed += '\n\n' + toolCallContent;
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
      logger.warn('[ContentProcessor] 验证失败:', {
        original: originalContent,
        reconstructed,
        differences: this.getDifferences(originalContent, reconstructed)
      });
    }

    return isConsistent;
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

export default ContentProcessor;