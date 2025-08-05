import linkProcessorService from '@/services/linkProcessorService';
import logger from './loggerService';

class MarkdownPostprocessorService {
  /**
   * 为不同格式的内部链接提供健壮的解析。
   * @param text 包含潜在自定义链接的原始文本。
   * @returns 一个解析为已处理文本的 Promise。
   */
  public async process(text: string): Promise<string> {
    if (!text || !text.includes('[[')) {
      return text;
    }

    // 正则表达式处理两种格式: [[text|path]] 和 [[path]]
    const linkRegex = /\[\[([^|\]]+)(?:\|([^\]]+))?\]\]/g;
    const matches = [...text.matchAll(linkRegex)];

    if (matches.length === 0) {
      return text;
    }

    const replacements = await Promise.all(
      matches.map(async (match) => {
        const rawLink = match[0];
        const group1 = match[1];
        const group2 = match[2];

        const baseText = group2 !== undefined ? group1 : group1;
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
            
            const template = `<a href="#" class="internal-doc-link ${validityClass}" data-is-valid="${isValid}" data-raw-link="${rawLink}" data-path="${pathForValidation}" data-anchor="${anchor}">${finalDisplayText}</a>`;
            return template;

        } catch (error) {
          logger.error(`处理链接时出错: ${rawLink}`, error);
          return rawLink; // 出错时回退到原始文本
        }
      })
    );

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
}

const markdownPostprocessorService = new MarkdownPostprocessorService();
export default markdownPostprocessorService;