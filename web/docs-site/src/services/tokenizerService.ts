import { get_encoding, Tiktoken } from "tiktoken";
import logger from './loggerService';

let encoding: Tiktoken | null;
try {
  // "cl100k_base" 是 gpt-4, gpt-3.5-turbo, 和 text-embedding-ada-002 使用的编码
  encoding = get_encoding("cl100k_base");
  logger.log("Tokenizer Service: tiktoken 'cl100k_base' 编码加载成功。");
} catch (e) {
  logger.error("加载 tiktoken 编码失败。", e);
  // 如果 tiktoken 初始化失败，回退到基于长度的简单计算。
  encoding = null;
}

class TokenizerService {
  /**
   * 使用 tiktoken 库计算给定文本中的 token 数量。
   * 如果 tokenizer 初始化失败，则回退到简单的字符计数。
   * @param text 要计算 token 的文本。
   * @returns token 的数量。
   */
  public countTokens(text: string): number {
    if (!text) return 0;

    if (encoding) {
      try {
        return encoding.encode(text).length;
      } catch (e) {
        logger.error("特定文本的 tiktoken 编码失败，回退到长度计算。", { text, error: e });
        return text.length;
      }
    } else {
      // 如果初始 get_encoding 失败，则回退。
      return text.length;
    }
  }

  /**
   * 从内存中释放 tokenizer 模型。
   * 如果需要显式管理内存，请调用此方法。
   */
  public cleanup(): void {
    if (encoding) {
      encoding.free();
      logger.log("Tokenizer Service: tiktoken 编码已从内存中释放。");
    }
  }
}

const tokenizerService = new TokenizerService();
export default tokenizerService;