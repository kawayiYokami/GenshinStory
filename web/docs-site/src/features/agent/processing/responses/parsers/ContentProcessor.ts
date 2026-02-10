/**
 * @fileoverview 内容处理器
 * @description 处理 AI 响应中的简化语法（表情和问题）
 *
 * 已移除 JSON 工具调用解析，完全使用简化语法
 */

import { simpleSyntaxParser, type ParsedEmote, type ParsedAsk, type ParseResult } from './SimpleSyntaxParser';

export interface ProcessedContent {
  cleanedContent: string;
  originalContent: string;
  hasAsk: boolean;
  askData: ParsedAsk | null;
  emotes: ParsedEmote[];
}

/**
 * 统一的内容处理包装层
 * 处理 AI 响应中的表情和问题语法
 */
export class ContentProcessor {
  /**
   * 从原始内容中提取表情和问题语法
   * @param originalContent 原始内容
   * @returns 处理结果
   */
  static extract(originalContent: string): ProcessedContent {
    const result = simpleSyntaxParser.parse(originalContent);

    return {
      cleanedContent: result.cleanedContent,
      originalContent,
      hasAsk: result.hasAsk,
      askData: result.askData,
      emotes: result.emotes,
    };
  }

  /**
   * 检查内容是否包含问题语法
   */
  static hasAsk(content: string): boolean {
    return simpleSyntaxParser.extractAsk(content) !== null;
  }

  /**
   * 检查内容是否包含表情或问题语法
   */
  static hasSimpleSyntax(content: string): boolean {
    return simpleSyntaxParser.hasSimpleSyntax(content);
  }

  /**
   * 将内容中的表情语法替换为图片标签
   * 用于最终渲染
   * @param content 原始内容
   * @param seed 可选的随机种子，用于确定性选择表情图片
   */
  static renderWithEmotes(content: string, seed?: number): string {
    return simpleSyntaxParser.replaceEmotesWithImages(content, seed);
  }

  /**
   * 移除内容中的问题语法
   */
  static removeAskSyntax(content: string): string {
    return simpleSyntaxParser.removeAskSyntax(content);
  }
}

export { type ParsedEmote, type ParsedAsk, type ParseResult };
