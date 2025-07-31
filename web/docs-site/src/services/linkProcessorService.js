import logger from './loggerService.js';
import localTools from './localToolsService.js';

class LinkProcessorService {
  /**
   * Parses a raw wiki-style link, resolves its path, and returns a structured object.
   * This is the single source of truth for handling inline links.
   * @param {string} rawLinkText - The raw link text, e.g., "[[Display Text|path:some/path.md]]".
   * @returns {Promise<{isValid: boolean, displayText: string, originalPath: string, resolvedPath: string|null, rawLink: string}>}
   */
  async resolveLink(rawLinkText) {
    const baseResult = {
      isValid: false,
      displayText: rawLinkText,
      originalPath: rawLinkText,
      resolvedPath: null,
      rawLink: rawLinkText
    };

    if (typeof rawLinkText !== 'string') {
      return baseResult;
    }

    // Enhanced Regex to handle both official and raw formats
    const genericLinkRegex = /\[\[([^|\]]+)(?:\|path:([^\]]+))?(?:\|([^\]]+))?\]\]/;
    const match = rawLinkText.match(genericLinkRegex);

    if (!match) {
        return baseResult;
    }

    const group1 = match[1]; // Always display text or the full path
    const group2 = match[2]; // Path from "path:" syntax
    const group3 = match[3]; // Path from raw syntax

    const displayText = group1.trim();
    // The path could be in group2 (official format) or group3 (raw format) or group1 (path-only format)
    const originalPath = (group2 || group3 || group1).trim();

    baseResult.displayText = displayText;
    baseResult.originalPath = originalPath;

    try {
      const resolvedPath = await localTools.resolveLogicalPath(originalPath);
      
      if (resolvedPath) {
        return {
          ...baseResult,
          isValid: true,
          resolvedPath
        };
      } else {
        return {
          ...baseResult,
          isValid: false,
        };
      }
    } catch (error) {
      return {
        ...baseResult,
        isValid: false,
      };
    }
  }
}

const linkProcessorService = new LinkProcessorService();
export default linkProcessorService;