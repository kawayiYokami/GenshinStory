/**
 * @fileoverview 简化语法解析器
 * @description 解析类 Discord 风格的表情和问题语法
 *
 * 语法格式：
 * - 表情：:happy: :meow: :confused:
 * - 问题：[?问题内容|选项A|选项B|选项C]
 * - 组合：:happy: 你好！[?想干嘛|聊天|退出]
 */

import emoteService from '@/features/agent/services/emoteService';

// ============== 类型定义 ==============

export interface ParsedEmote {
  type: 'emote';
  name: string;
  imagePath: string;
}

export interface ParsedAsk {
  type: 'ask';
  question: string;
  suggestions: string[];
}

export interface ParsedText {
  type: 'text';
  content: string;
}

export type ParsedSegment = ParsedEmote | ParsedAsk | ParsedText;

export interface ParseResult {
  segments: ParsedSegment[];
  cleanedContent: string;
  hasAsk: boolean;
  askData: ParsedAsk | null;
  emotes: ParsedEmote[];
}

export interface StreamParseResult {
  segments: ParsedSegment[];
  remaining: string;
}

// ============== 解析器实现 ==============

class SimpleSyntaxParser {
  // 匹配 :emoteName: 格式
  private readonly EMOTE_PATTERN = /:([a-z]+):/g;

  // 匹配 [?问题|选项1|选项2|...] 格式
  private readonly ASK_PATTERN = /\[\?([^|\]]+)\|([^\]]+)\]/g;

  /**
   * 解析完整内容
   * @param content 原始内容
   * @returns 解析结果
   */
  public parse(content: string): ParseResult {
    const segments: ParsedSegment[] = [];
    const emotes: ParsedEmote[] = [];
    let hasAsk = false;
    let askData: ParsedAsk | null = null;
    let cleanedContent = content;

    // 1. 解析并替换表情
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    const emoteRegex = new RegExp(this.EMOTE_PATTERN);

    while ((match = emoteRegex.exec(content)) !== null) {
      const emoteName = match[1];
      if (emoteService.isValidEmote(emoteName)) {
        // 添加表情之前的文本
        if (match.index > lastIndex) {
          const textBefore = content.slice(lastIndex, match.index);
          if (textBefore.trim()) {
            segments.push({ type: 'text', content: textBefore });
          }
        }

        // 添加表情
        const imagePath = emoteService.getRandomEmoteSync(emoteName);
        if (imagePath) {
          const emote: ParsedEmote = { type: 'emote', name: emoteName, imagePath };
          segments.push(emote);
          emotes.push(emote);
        }

        lastIndex = match.index + match[0].length;

        // 从 cleanedContent 中移除表情语法
        cleanedContent = cleanedContent.replace(match[0], '');
      }
    }

    // 2. 解析问题语法
    const askRegex = new RegExp(this.ASK_PATTERN);
    match = askRegex.exec(content);

    if (match) {
      hasAsk = true;
      const question = match[1].trim();
      const optionsStr = match[2];
      const suggestions = optionsStr.split('|').map(s => s.trim()).filter(Boolean);

      askData = { type: 'ask', question, suggestions };

      // 从 cleanedContent 中移除问题语法
      cleanedContent = cleanedContent.replace(match[0], '');
    }

    // 3. 添加剩余的文本
    if (lastIndex < content.length) {
      let remaining = content.slice(lastIndex);
      // 移除问题语法
      if (askData) {
        remaining = remaining.replace(this.ASK_PATTERN, '');
      }
      if (remaining.trim()) {
        segments.push({ type: 'text', content: remaining.trim() });
      }
    }

    return {
      segments,
      cleanedContent: cleanedContent.trim(),
      hasAsk,
      askData,
      emotes,
    };
  }

  /**
   * 流式解析
   * @param chunk 新的文本块
   * @param buffer 之前未完成的缓冲区
   * @returns 解析结果和剩余缓冲区
   */
  public parseStreaming(chunk: string, buffer: string): StreamParseResult {
    const combined = buffer + chunk;
    const segments: ParsedSegment[] = [];
    let remaining = combined;

    // 1. 检查是否有完整的表情
    let emoteMatch: RegExpExecArray | null;
    const emoteRegex = new RegExp(this.EMOTE_PATTERN);
    let lastEmoteEnd = 0;

    while ((emoteMatch = emoteRegex.exec(combined)) !== null) {
      const emoteName = emoteMatch[1];
      if (emoteService.isValidEmote(emoteName)) {
        // 添加表情之前的文本
        if (emoteMatch.index > lastEmoteEnd) {
          const textBefore = combined.slice(lastEmoteEnd, emoteMatch.index);
          if (textBefore) {
            segments.push({ type: 'text', content: textBefore });
          }
        }

        // 添加表情
        const imagePath = emoteService.getRandomEmoteSync(emoteName);
        if (imagePath) {
          segments.push({ type: 'emote', name: emoteName, imagePath });
        }

        lastEmoteEnd = emoteMatch.index + emoteMatch[0].length;
      }
    }

    // 2. 检查是否有完整的问题语法
    const askMatch = this.ASK_PATTERN.exec(combined);
    if (askMatch) {
      // 添加问题之前的文本
      if (askMatch.index > lastEmoteEnd) {
        const textBefore = combined.slice(lastEmoteEnd, askMatch.index);
        if (textBefore) {
          segments.push({ type: 'text', content: textBefore });
        }
      }

      // 添加问题
      const question = askMatch[1].trim();
      const suggestions = askMatch[2].split('|').map(s => s.trim()).filter(Boolean);
      segments.push({ type: 'ask', question, suggestions });

      remaining = combined.slice(askMatch.index + askMatch[0].length);
    } else {
      // 检查是否有未完成的问题语法
      const incompleteAskIndex = combined.lastIndexOf('[?');
      if (incompleteAskIndex !== -1 && combined.indexOf(']', incompleteAskIndex) === -1) {
        // 有未完成的问题语法，保留在缓冲区
        if (incompleteAskIndex > lastEmoteEnd) {
          const textBefore = combined.slice(lastEmoteEnd, incompleteAskIndex);
          if (textBefore) {
            segments.push({ type: 'text', content: textBefore });
          }
        }
        remaining = combined.slice(incompleteAskIndex);
      } else if (lastEmoteEnd > 0) {
        // 有完整的表情，更新 remaining
        remaining = combined.slice(lastEmoteEnd);
      }
    }

    // 3. 检查是否有未完成的表情语法
    const lastColonIndex = remaining.lastIndexOf(':');
    if (lastColonIndex !== -1) {
      const afterColon = remaining.slice(lastColonIndex + 1);
      // 如果冒号后面是有效的表情名前缀，保留在缓冲区
      if (/^[a-z]*$/.test(afterColon) && afterColon.length < 15) {
        if (lastColonIndex > 0) {
          segments.push({ type: 'text', content: remaining.slice(0, lastColonIndex) });
        }
        remaining = remaining.slice(lastColonIndex);
      } else {
        // 不是未完成的表情，作为普通文本处理
        if (remaining && !remaining.startsWith('[?')) {
          segments.push({ type: 'text', content: remaining });
          remaining = '';
        }
      }
    } else if (remaining && !remaining.startsWith('[?')) {
      // 没有可能的未完成语法，直接输出
      segments.push({ type: 'text', content: remaining });
      remaining = '';
    }

    return { segments, remaining };
  }

  /**
   * 检查内容是否包含简化语法
   */
  public hasSimpleSyntax(content: string): boolean {
    return this.EMOTE_PATTERN.test(content) || this.ASK_PATTERN.test(content);
  }

  /**
   * 从内容中提取问题数据（如果有）
   */
  public extractAsk(content: string): ParsedAsk | null {
    const match = this.ASK_PATTERN.exec(content);
    if (!match) return null;

    return {
      type: 'ask',
      question: match[1].trim(),
      suggestions: match[2].split('|').map(s => s.trim()).filter(Boolean),
    };
  }

  /**
   * 将内容中的表情语法替换为图片标签
   * @param content 原始内容
   * @param seed 可选的随机种子，用于确定性选择表情图片
   */
  public replaceEmotesWithImages(content: string, seed?: number): string {
    return content.replace(this.EMOTE_PATTERN, (match, emoteName) => {
      if (emoteService.isValidEmote(emoteName)) {
        const imagePath = emoteService.getRandomEmoteSync(emoteName, seed);
        if (imagePath) {
          return `<img src="${imagePath}" alt=":${emoteName}:" class="inline-emote" />`;
        }
      }
      return match;
    });
  }

  /**
   * 移除内容中的问题语法
   */
  public removeAskSyntax(content: string): string {
    return content.replace(this.ASK_PATTERN, '').trim();
  }
}

export const simpleSyntaxParser = new SimpleSyntaxParser();
export default simpleSyntaxParser;
