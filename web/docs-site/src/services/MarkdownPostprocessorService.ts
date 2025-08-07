import linkProcessorService from '@/services/linkProcessorService';
import logger from './loggerService';

class MarkdownPostprocessorService {
  private buffer = '';
  private readonly linkRegex = /\[\[([^|\]]+)(?:\|([^\]]+))?\]\]/g;

  /**
   * 处理一个文本块，解析其中完整的链接，并缓冲不完整的链接。
   * @param chunk 流式传入的文本块。
   * @returns 一个 Promise，解析为已处理的、可立即渲染的 HTML 字符串。
   */
  public async processStream(chunk: string): Promise<string> {
    this.buffer += chunk;

    const matches = [...this.buffer.matchAll(this.linkRegex)];
    if (matches.length === 0) {
      // 如果没有找到链接，检查缓冲区是否可能包含一个未闭合的链接的开头。
      const lastOpenBracket = this.buffer.lastIndexOf('[[');
      if (lastOpenBracket !== -1 && this.buffer.lastIndexOf(']]') < lastOpenBracket) {
        // 看起来有一个未完成的链接，所以我们返回缓冲区开头到这个链接之前的部分。
        const contentToOutput = this.buffer.substring(0, lastOpenBracket);
        this.buffer = this.buffer.substring(lastOpenBracket);
        return contentToOutput;
      } else {
        // 没有发现链接，清空缓冲区并返回所有内容。
        const contentToOutput = this.buffer;
        this.buffer = '';
        return contentToOutput;
      }
    }

    const parts: string[] = [];
    let lastIndex = 0;

    for (const match of matches) {
      // 将上一个匹配项到当前匹配项之间的文本添加到 parts 中。
      parts.push(this.buffer.substring(lastIndex, match.index));
      
      const processedLink = await this.processSingleLink(match);
      parts.push(processedLink);

      lastIndex = (match.index ?? 0) + match.length;
    }

    // 更新缓冲区，只保留最后一个匹配项之后的部分。
    this.buffer = this.buffer.substring(lastIndex);

    // 检查新的缓冲区是否以一个未闭合的链接开头。
    // 这很重要，因为正则表达式只会找到完整的匹配项。
    const lastOpenBracket = this.buffer.lastIndexOf('[[');
    if (lastOpenBracket > -1 && this.buffer.lastIndexOf(']]') < lastOpenBracket) {
      const contentToKeep = this.buffer.substring(lastOpenBracket);
      const contentToOutput = this.buffer.substring(0, lastOpenBracket);
      this.buffer = contentToKeep;
      parts.push(contentToOutput);
    } else {
      // 否则，所有内容都已处理，将其追加并清空缓冲区。
      parts.push(this.buffer);
      this.buffer = '';
    }

    return parts.join('');
  }

  /**
   * 清空缓冲区中所有剩余的内容。
   * @returns 一个 Promise，解析为缓冲区中剩余部分的已处理 HTML。
   */
  public async flush(): Promise<string> {
    const remainingContent = this.buffer;
    this.buffer = '';
    // 使用原始的 process 方法来处理任何剩余的、可能格式不正确的片段。
    return await this.process(remainingContent);
  }

  /**
   * 为不同的格式的内部链接提供健壮的解析。
   * 这是一个非流式的完整处理方法，为了向后兼容而保留。
   * @param text 包含潜在自定义链接的原始文本。
   * @returns 一个解析为已处理文本的 Promise。
   */
  public async process(text: string): Promise<string> {
    if (!text || !text.includes('[[')) {
      return text;
    }

    const matches = [...text.matchAll(this.linkRegex)];
    if (matches.length === 0) return text;
    
    const replacements = await Promise.all(matches.map(match => this.processSingleLink(match)));

    let lastIndex = 0;
    const parts: string[] = [];
    matches.forEach((match, index) => {
      parts.push(text.substring(lastIndex, match.index));
      parts.push(replacements[index]);
      lastIndex = (match.index ?? 0) + match[0].length;
    });
    parts.push(text.substring(lastIndex));

    return parts.join('');
  }

  /**
   * Helper method to process a single link match.
   * @param match A single regex match object.
   * @returns A promise that resolves to the processed HTML anchor tag.
   */
  private async processSingleLink(match: RegExpMatchArray): Promise<string> {
    const rawLink = match[0];
    const group1 = match[1];
    const group2 = match[2];

    const baseText = group1;
    const basePath = group2 !== undefined ? group2 : group1;

    let pathForValidation = basePath;
    let anchor = '';
    const anchorMatch = basePath.match(/^(.*?)#(.+)$/);
    if (anchorMatch) {
        pathForValidation = anchorMatch[1];
        anchor = anchorMatch[2];
    }

    const textForValidation = baseText.replace(/#.*$/, '');
    const finalDisplayText = anchor ? `${textForValidation} #${anchor}` : textForValidation;
    const linkToProcess = `[[${textForValidation}|path:${pathForValidation}]]`;

    try {
        const result = await linkProcessorService.resolveLink(linkToProcess);
        const isValid = result.isValid;
        const validityClass = isValid ? '' : 'invalid-link';
        
        return `<a href="#" class="internal-doc-link ${validityClass}" data-is-valid="${isValid}" data-raw-link="${rawLink}" data-path="${pathForValidation}" data-anchor="${anchor}">${finalDisplayText}</a>`;

    } catch (error) {
      logger.error(`处理链接时出错: ${rawLink}`, error);
      return rawLink; // 回退到原始文本
    }
  }
}

const markdownPostprocessorService = new MarkdownPostprocessorService();
export default markdownPostprocessorService;