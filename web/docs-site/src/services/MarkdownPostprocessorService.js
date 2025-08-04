import linkProcessorService from '@/services/linkProcessorService';
import logger from './loggerService';

class MarkdownPostprocessorService {
  /**
   * Processes internal links with robust parsing for different formats.
   * @param {string} text - The raw text containing potential custom links.
   * @returns {Promise<string>} A promise that resolves to the processed text.
   */
  async process(text) {
    if (!text || !text.includes('[[')) {
      return text;
    }

    // Regex to handle both formats: [[text|path]] and [[path]]
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

        // Determine the base text and path from the regex groups.
        const baseText = group2 !== undefined ? group1 : group1;
        const basePath = group2 !== undefined ? group2 : group1;

        // Extract anchor and clean the path for validation.
        let pathForValidation = basePath;
        let anchor = '';
        const anchorMatch = basePath.match(/^(.*?)#(.+)$/);
        if (anchorMatch) {
            pathForValidation = anchorMatch[1];
            anchor = anchorMatch[2];
        }

        // The text for validation should also be clean of any anchor.
        const textForValidation = baseText.replace(/#.*$/, '');

        // The final display text should include the anchor if it exists.
        const finalDisplayText = anchor ? `${textForValidation} #${anchor}` : textForValidation;

        // Construct the link in the official format for the validation service.
        const linkToProcess = `[[${textForValidation}|path:${pathForValidation}]]`;

        try {
            const result = await linkProcessorService.resolveLink(linkToProcess);
            const isValid = result.isValid;
            const validityClass = isValid ? '' : 'invalid-link';
            
            // The final template uses the processed display text.
            const template = `<a href="#" class="internal-doc-link ${validityClass}" data-is-valid="${isValid}" data-raw-link="${rawLink}" data-path="${pathForValidation}" data-anchor="${anchor}">${finalDisplayText}</a>`;
            // logger.log(`[MarkdownPostprocessor] 生成链接模板`, { rawLink, finalDisplayText, pathForValidation, isValid });
          return template;

        } catch (error) {
          logger.error(`Error processing link: ${rawLink}`, error);
          return rawLink; // Fallback to raw text on error
        }
      })
    );

    // Replace all matches in the original text
    let lastIndex = 0;
    const parts = [];
    matches.forEach((match, index) => {
      parts.push(text.substring(lastIndex, match.index));
      parts.push(replacements[index]);
      lastIndex = match.index + match[0].length;
    });
    parts.push(text.substring(lastIndex));

    return parts.join('');
  }
}

const markdownPostprocessorService = new MarkdownPostprocessorService();
export default markdownPostprocessorService;