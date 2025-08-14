import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import linkProcessorService from '@/services/linkProcessorService';
import logger from '@/services/loggerService';
import { processSingleLinkText, createLinkPlaceholder, replaceLinkPlaceholders } from '@/services/MarkdownRenderingService';

/**
 * Helper function to process a single [[...]] link text.
 * @param linkText The full link text, e.g., '[[Document Name]]' or '[[Display Text|path:some/path]]'.
 * @returns A promise that resolves to the processed HTML anchor tag string.
 */

/**
 * A markdown-it plugin to process [[...]] internal links.
 * @param md The markdown-it instance.
 */
function internalLinkPlugin(md: MarkdownIt) {
  // Define the regex to match [[...]] links
  const linkRegex = /^\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/;

  // Function to find the next potential '[' character
  function locator(state: any, start: number, end: number): number {
    for (let pos = start; pos < end; pos++) {
      if (state.src.charCodeAt(pos) === 0x5B /* [ */) {
        return pos;
      }
    }
    return -1;
  }

  // The main rule function for parsing [[...]] links
  function internal_link(state: any, silent: boolean): boolean {
    const start = state.pos;
    
    // Check if the current character is '['
    if (state.src.charCodeAt(start) !== 0x5B /* [ */) { return false; }
    
    // Use the regex to test the substring starting at 'start'
    const match = state.src.slice(start).match(linkRegex);
    
    if (!match) { return false; }
    
    const fullMatch = match[0];
    const linkText = fullMatch;
    const matchEnd = start + fullMatch.length;
    
    // If silent mode, just report success
    if (silent) { return true; }
    
    // Create a new token for the internal link
    const token = state.push('internal_link', '', 0);
    token.content = linkText; // Store the full link text for later processing
    // token.info = 'internal_link'; // Optional: store additional info
    
    // Update the position
    state.pos = matchEnd;
    return true;
  }

  // Assign the locator function to the rule function itself
  (internal_link as any).locator = locator;
  
  // Add the rule to the inline parser
  md.inline.ruler.push('internal_link', internal_link);
  
  // Add the renderer for 'internal_link' token type
  md.renderer.rules.internal_link = function (tokens: any[], idx: number) {
    const token = tokens[idx];
    const linkText = token.content; // This is the full [[...]] text
    
    // Return a placeholder using the shared function for consistency.
    return createLinkPlaceholder(linkText);
  };
}

/**
 * 一个用于流式 Markdown 解析的服务。
 * 它接收文本块，维护内部缓冲区，并实时渲染为安全的 HTML。
 */
export class StreamingMarkdownParser {
  private buffer: string;
  private md: MarkdownIt;
  private placeholders: Map<string, string>;
  private askQuestionRegex = /<ask_question>[\s\S]*?<\/ask_question>/g;

  constructor() {
    this.buffer = '';
    this.placeholders = new Map();
    // 初始化 markdown-it 实例
    this.md = new MarkdownIt({
      html: true,        // 启用 HTML 标签
      linkify: true,     // 自动识别 URL 为链接
      typographer: true, // 启用语言学替换和引号美化
    });
    
    // Use the internal link plugin
    this.md.use(internalLinkPlugin);
  }

  /**
   * 处理一个新的文本块。
   * @param chunk - 新的文本块。
   * @returns 经过净化的安全 HTML 字符串。
   */
  public async processChunk(chunk: string): Promise<string> {
    this.buffer += chunk;

    // 1. 隐藏 <ask_question> 标签
    let tempBuffer = this.buffer;
    const matches = tempBuffer.match(this.askQuestionRegex);
    if (matches) {
      matches.forEach((match, index) => {
        const placeholder = `__ASK_QUESTION_PLACEHOLDER_${index}__`;
        this.placeholders.set(placeholder, match);
        tempBuffer = tempBuffer.replace(match, placeholder);
      });
    }

    // 2. 使用 markdown-it 渲染处理过的缓冲区
    const rawHtml = this.md.render(tempBuffer);

    // 3. 替换内部链接占位符
    const htmlWithLinks = await this._replaceInternalLinkPlaceholders(rawHtml);

    // 4. 使用 DOMPurify 净化 HTML
    let sanitizedHtml = DOMPurify.sanitize(htmlWithLinks);

    // 5. 恢复 <ask_question> 标签
    this.placeholders.forEach((original, placeholder) => {
      sanitizedHtml = sanitizedHtml.replace(placeholder, original);
    });

    return sanitizedHtml;
  }

  /**
   * 获取当前缓冲区的完整 HTML 渲染结果。
   * @returns 经过净化的安全 HTML 字符串。
   */
  public async getHtml(): Promise<string> {
    // 1. 隐藏 <ask_question> 标签
    let tempBuffer = this.buffer;
    const matches = tempBuffer.match(this.askQuestionRegex);
    if (matches) {
      matches.forEach((match, index) => {
        const placeholder = `__ASK_QUESTION_PLACEHOLDER_${index}__`;
        this.placeholders.set(placeholder, match);
        tempBuffer = tempBuffer.replace(match, placeholder);
      });
    }
    
    const rawHtml = this.md.render(tempBuffer);
    const htmlWithLinks = await this._replaceInternalLinkPlaceholders(rawHtml);
    let sanitizedHtml = DOMPurify.sanitize(htmlWithLinks);

    // 恢复 <ask_question> 标签
    this.placeholders.forEach((original, placeholder) => {
      sanitizedHtml = sanitizedHtml.replace(placeholder, original);
    });

    return sanitizedHtml;
  }

  /**
   * 重置解析器状态，清空缓冲区。
   * 通常在开始一条新消息时调用。
   */
  public reset(): void {
    this.buffer = '';
    this.placeholders.clear();
  }
  
  /**
   * Private method to replace internal link placeholders with actual HTML.
   * @param html The HTML string potentially containing placeholders.
   * @returns A promise that resolves to the HTML string with placeholders replaced.
   */
  private async _replaceInternalLinkPlaceholders(html: string): Promise<string> {
    // Use the shared function from MarkdownRenderingService
    return await replaceLinkPlaceholders(html);
  }
}