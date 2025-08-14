import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import linkProcessorService from '@/services/linkProcessorService';
import logger from '@/services/loggerService';

// --- Shared Logic ---

/**
 * Helper function to process a single [[...]] link text.
 * This is a synchronous version that returns a placeholder.
 * The actual link processing will happen later.
 * @param linkText The full link text, e.g., '[[Document Name]]' or '[[Display Text|path:some/path]]'.
 * @returns A placeholder string.
 */
export function createLinkPlaceholder(linkText: string): string {
  // Escape the link text for HTML attribute
  const escapedLinkText = linkText
    .replace(/&/g, "&")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, "\"")
    .replace(/'/g, "\'");
  return `{{INTERNAL_LINK_PLACEHOLDER:${escapedLinkText}}}`;
}

/**
 * Helper function to process a single [[...]] link text asynchronously.
 * @param linkText The full link text, e.g., '[[Document Name]]' or '[[Display Text|path:some/path]]'.
 * @returns A promise that resolves to the processed HTML anchor tag string.
 */
export async function processSingleLinkText(linkText: string): Promise<string> {
  // This regex should match the one in the markdown-it plugin
  const linkRegex = /^\[\[([^\]|]+)(?:\|([^\]]+))?\]\]$/;
  const match = linkText.match(linkRegex);

  if (!match) {
    // This should not happen if the function is called correctly.
    logger.warn(`Invalid link format passed to processSingleLinkText: ${linkText}`);
    return linkText;
  }

  const rawLink = linkText;
  const group1 = match[1];
  const group2 = match[2];

  const baseText = group1;
  let basePath = group2 !== undefined ? group2 : group1;

  // Handle 'path:' prefix if present in basePath
  if (basePath.startsWith('path:')) {
    basePath = basePath.substring(5); // Remove 'path:' prefix
  }

  let pathForValidation = basePath;
  let anchor = '';
  const anchorMatch = basePath.match(/^(.*?)#(.+)$/);
  if (anchorMatch) {
      pathForValidation = anchorMatch[1];
      anchor = anchorMatch[2];
  }

  const textForValidation = baseText.replace(/#.*$/, '');
  const finalDisplayText = anchor ? `${textForValidation} #${anchor}` : textForValidation;
  // The linkProcessorService expects the format [[text|path:...]]
  const linkToProcess = `[[${textForValidation}|path:${pathForValidation}]]`;

  try {
      const result = await linkProcessorService.resolveLink(linkToProcess);
      const isValid = result.isValid;
      const validityClass = isValid ? '' : 'invalid-link';
      
      // Return the HTML string.
      return `<a href="#" class="internal-doc-link ${validityClass}" data-is-valid="${isValid}" data-raw-link="${rawLink}" data-path="${pathForValidation}" data-anchor="${anchor}">${finalDisplayText}</a>`;

  } catch (error) {
    logger.error(`处理链接时出错: ${rawLink}`, error);
    return rawLink; // 回退到原始文本
  }
}

// --- markdown-it Plugin ---

/**
 * A markdown-it plugin to process [[...]] internal links.
 * @param md The markdown-it instance.
 */
function internalLinkPlugin(md: MarkdownIt) {
  // Define the regex to match [[...]] links
  const linkRegex = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/;

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
    
    // Return a placeholder. We will replace this later.
    return createLinkPlaceholder(linkText);
  };
}

// --- Public API ---

/**
 * Synchronously renders Markdown text to HTML and processes internal links.
 * Internal links are replaced with placeholders.
 * @param markdownText The Markdown text to render.
 * @returns The rendered HTML string with placeholders for internal links.
 */
export function renderMarkdownSync(markdownText: string): string {
  if (!markdownText) {
    return '';
  }

  try {
    // Initialize markdown-it with the internal link plugin
    const md = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
    });
    
    md.use(internalLinkPlugin);

    // Render the Markdown to HTML
    const rawHtml = md.render(markdownText);
    
    // Note: Placeholders are already inserted by the renderer.
    // The caller is responsible for replacing placeholders if needed.
    // For synchronous rendering, we return the HTML with placeholders.
    // DOMPurify cannot be used here in a Worker context for final sanitization
    // as it requires a DOM. Sanitization must be done by the caller in the main thread.
    
    return rawHtml;
  } catch (error) {
    logger.error('同步渲染 Markdown 时出错:', error);
    return `<p>渲染 Markdown 时出错: ${(error as Error).message}</p>`;
  }
}

/**
 * Asynchronously replaces placeholders in HTML with processed internal links.
 * @param htmlWithPlaceholders The HTML string containing placeholders.
 * @returns A promise that resolves to the HTML string with placeholders replaced by actual links.
 */
export async function replaceLinkPlaceholders(htmlWithPlaceholders: string): Promise<string> {
  if (!htmlWithPlaceholders) {
    return '';
  }

  try {
    // Check if DOMParser is available (browser environment)
    if (typeof DOMParser === 'undefined') {
      // If not, we cannot process placeholders here.
      // This is the case in a Web Worker. We should document that
      // the caller in a Worker environment needs to handle placeholder replacement differently
      // or pass the HTML back to the main thread for processing.
      // For now, we'll log a warning and return the HTML as is.
      // A more robust solution for Worker would be to use string replacement.
      
      // Fallback to string replacement for environments without DOMParser (e.g., Web Workers)
      logger.warn('DOMParser is not available, using string replacement for link placeholders.');
      
      // Regex to find placeholders
      const placeholderRegex = /\{\{INTERNAL_LINK_PLACEHOLDER:([^\}]+)\}\}/g;
      let match;
      let newHtml = htmlWithPlaceholders;
      const replacements: { [key: string]: string } = {};

      // Find all unique placeholders
      while ((match = placeholderRegex.exec(htmlWithPlaceholders)) !== null) {
        const placeholder = match[0];
        const encodedLinkText = match[1];
        // Decode the link text
        const linkText = encodedLinkText
          .replace(/&/g, "&")
          .replace(/</g, "<")
          .replace(/>/g, ">")
          .replace(/"/g, '"')
          .replace(/'/g, "'");
        
        if (!replacements[placeholder]) {
          // Process the link text and store the result
          replacements[placeholder] = await processSingleLinkText(linkText);
        }
      }

      // Replace all placeholders
      for (const [placeholder, replacement] of Object.entries(replacements)) {
        newHtml = newHtml.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), replacement);
      }
      
      return newHtml;
    }

    // Parse the HTML string into a DOM document
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlWithPlaceholders, 'text/html');

    // Find all placeholder spans
    // Note: The renderer now creates text placeholders, not spans.
    // We need to adjust the selector or the renderer.
    // Let's adjust the renderer to create a specific class for easier selection if needed,
    // but for now, we'll stick with text replacement as shown in the fallback above.
    // The current renderer creates `{{INTERNAL_LINK_PLACEHOLDER:...}}` text nodes.
    // Finding and replacing these in the DOM is tricky.
    // String replacement is more reliable.
    
    // Re-use the string replacement logic from the fallback
    const placeholderRegex = /\{\{INTERNAL_LINK_PLACEHOLDER:([^\}]+)\}\}/g;
    let match;
    let newHtml = htmlWithPlaceholders;
    const replacements: { [key: string]: string } = {};

    while ((match = placeholderRegex.exec(htmlWithPlaceholders)) !== null) {
      const placeholder = match[0];
      const encodedLinkText = match[1];
      const linkText = encodedLinkText
        .replace(/&/g, "&")
        .replace(/</g, "<")
        .replace(/>/g, ">")
        .replace(/"/g, '"')
        .replace(/'/g, "'");
      
      if (!replacements[placeholder]) {
        replacements[placeholder] = await processSingleLinkText(linkText);
      }
    }

    for (const [placeholder, replacement] of Object.entries(replacements)) {
      newHtml = newHtml.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), replacement);
    }
    
    return newHtml;

  } catch (error) {
    logger.error('替换链接占位符时出错:', error);
    return htmlWithPlaceholders; // Return the original HTML on error
  }
}