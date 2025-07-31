import { get_encoding } from "tiktoken";
import logger from './loggerService.js';

// According to the tiktoken docs, the get_encoding() function will load the
// tokenizer model from the network the first time it's called. To avoid
// this happening in the middle of a user request, we initialize it once here
// when the module is first loaded.

let encoding;
try {
  // "cl100k_base" is the encoding used by gpt-4, gpt-3.5-turbo, and text-embedding-ada-002
  encoding = get_encoding("cl100k_base");
  logger.log("Tokenizer Service: tiktoken 'cl100k_base' encoding loaded successfully.");
} catch (e) {
  logger.error("Failed to load tiktoken encoding.", e);
  // Fallback to a simple length-based calculation if tiktoken fails to initialize.
  encoding = null;
}


class TokenizerService {
  /**
   * Calculates the number of tokens in a given text using the tiktoken library.
   * Falls back to a simple character count if the tokenizer failed to initialize.
   * @param {string} text - The text to count tokens for.
   * @returns {number} The number of tokens.
   */
  countTokens(text) {
    if (!text) return 0;

    if (encoding) {
      try {
        return encoding.encode(text).length;
      } catch (e) {
        logger.error("tiktoken encoding failed for a specific text, falling back to length.", { text, error: e });
        return text.length;
      }
    } else {
      // Fallback if the initial get_encoding failed.
      return text.length;
    }
  }

  /**
   * Frees the tokenizer model from memory.
   * Call this if you need to manage memory explicitly.
   */
  cleanup() {
    if (encoding) {
      encoding.free();
      logger.log("Tokenizer Service: tiktoken encoding freed from memory.");
    }
  }
}

const tokenizerService = new TokenizerService();
export default tokenizerService;