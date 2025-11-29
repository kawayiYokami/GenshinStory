/**
 * Token 计算服务
 * 使用字符估算法替代 tiktoken 库，减少依赖和初始化开销
 *
 * 估算规则：
 * - 1 个英文字符 ≈ 0.3 个 token
 * - 1 个中文字符 ≈ 0.6 个 token
 * - 标点符号、数字等按英文字符计算
 */

class TokenizerService {
  /**
   * 使用字符估算法计算给定文本中的 token 数量
   * @param text 要计算 token 的文本
   * @returns 估算的 token 数量
   */
  public countTokens(text: string): number {
    if (!text) return 0;

    let englishCharCount = 0;
    let chineseCharCount = 0;

    for (const char of text) {
      // 检测中文字符（包括中文标点）
      if (this.isChinese(char)) {
        chineseCharCount++;
      } else {
        englishCharCount++;
      }
    }

    // 按比例计算 token 数量
    const englishTokens = englishCharCount * 0.3;
    const chineseTokens = chineseCharCount * 0.6;

    // 四舍五入并取整数
    return Math.round(englishTokens + chineseTokens);
  }

  /**
   * 检测字符是否为中文字符
   * @param char 要检测的字符
   * @returns 是否为中文字符
   */
  private isChinese(char: string): boolean {
    // 中文字符的 Unicode 范围
    const chineseRanges = [
      [0x4E00, 0x9FFF],   // 基本汉字
      [0x3400, 0x4DBF],   // 扩展A
      [0x20000, 0x2A6DF], // 扩展B
      [0x2A700, 0x2B73F], // 扩展C
      [0x2B740, 0x2B81F], // 扩展D
      [0x2B820, 0x2CEAF], // 扩展E
      [0x3000, 0x303F],   // 中文标点
      [0xFF00, 0xFFEF]    // 全角字符（包括中文标点）
    ];

    const code = char.codePointAt(0);
    if (code === undefined) return false;

    return chineseRanges.some(([start, end]) => code >= start && code <= end);
  }

  /**
   * 清理方法（为保持兼容性保留）
   */
  public cleanup(): void {
    // 估算法不需要内存清理，保留方法以维持API兼容性
  }
}

const tokenizerService = new TokenizerService();
export default tokenizerService;