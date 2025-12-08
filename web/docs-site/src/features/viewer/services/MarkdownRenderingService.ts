import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import logger from '@/features/app/services/loggerService';

// --- 共享逻辑 ---

/**
 * 处理单个 [[...]] 链接文本的辅助函数。
 * 这是一个同步版本，返回一个占位符。
 * 实际的链接处理将在稍后进行。
 * @param linkText 完整的链接文本，例如 '[[Document Name]]' 或 '[[Display Text|path:some/path]]'。
 * @returns 占位符字符串。
 */
export function createLinkPlaceholder(linkText: string): string {
  // 为 HTML 属性转义链接文本
  const escapedLinkText = linkText
    .replace(/&/g, "&")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, "\"")
    .replace(/'/g, "\'");
  return `{{INTERNAL_LINK_PLACEHOLDER:${escapedLinkText}}}`;
}

/**
 * 异步处理单个 [[...]] 链接文本的辅助函数。
 * @param linkText 完整的链接文本，例如 '[[Document Name]]' 或 '[[Display Text|path:some/path]]'。
 * @returns 解析为已处理的 HTML 锚点标签字符串的 Promise。
 */
export async function processSingleLinkText(linkText: string): Promise<string> {
  // 此正则表达式应与 markdown-it 插件中的正则表达式匹配
  // 使用非贪婪匹配来更稳健地处理包含特殊字符的链接
  const linkRegex = /^\[\[(.+?)(?:\|(.+?))?\]\]$/;
  const match = linkText.match(linkRegex);

  if (!match) {
    // 如果函数被正确调用，则不应发生这种情况。
    logger.warn(`传递给 processSingleLinkText 的链接格式无效: ${linkText}`);
    return linkText;
  }

  const rawLink = linkText;
  const group1 = match[1];
  const group2 = match[2];

  const baseText = group1;
  let basePath = group2 !== undefined ? group2 : group1;

  // 处理 basePath 中存在的 'path:' 前缀
  if (basePath.startsWith('path:')) {
    basePath = basePath.substring(5); // 移除 'path:' 前缀
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
  // linkProcessorService 期望的格式是 [[text|path:...]]
  const linkToProcess = `[[${textForValidation}|path:${pathForValidation}]]`;

  try {
      const result = await linkProcessorService.resolveLink(linkToProcess);
      const isValid = result.isValid;
      const validityClass = isValid ? '' : 'invalid-link';

      // 返回 HTML 字符串。
      const returnHtml = `<a href="#" class="internal-doc-link ${validityClass}" data-is-valid="${isValid}" data-raw-link="${rawLink}" data-path="${pathForValidation}" data-anchor="${anchor}">${finalDisplayText}</a>`;
      return returnHtml;

  } catch (error) {
    logger.error(`处理链接时出错: ${rawLink}`, error);
    return rawLink; // 回退到原始文本
  }
}

// --- markdown-it 插件 ---

/**
 * 用于处理 [[...]] 内部链接的 markdown-it 插件。
 * @param md markdown-it 实例。
 */
function internalLinkPlugin(md: MarkdownIt) {
  // 定义用于匹配 [[...]] 链接的正则表达式
  // 使用非贪婪匹配来更稳健地处理包含特殊字符的链接
  const linkRegex = /\[\[(.+?)(?:\|(.+?))?\]\]/;

  // 查找下一个潜在的 '[' 字符的函数
  function locator(state: any, start: number, end: number): number {
    for (let pos = start; pos < end; pos++) {
      if (state.src.charCodeAt(pos) === 0x5B /* [ */) {
        return pos;
      }
    }
    return -1;
  }

  // 解析 [[...]] 链接的主要规则函数
  function internal_link(state: any, silent: boolean): boolean {
    const start = state.pos;

    // 检查当前字符是否为 '['
    if (state.src.charCodeAt(start) !== 0x5B /* [ */) { return false; }

    // 使用正则表达式测试从 'start' 开始的子字符串
    const match = state.src.slice(start).match(linkRegex);

    if (!match) { return false; }

    const fullMatch = match[0];
    const linkText = fullMatch;
    const matchEnd = start + fullMatch.length;

    // 如果是静默模式，则只报告成功
    if (silent) { return true; }

    // 为内部链接创建一个新令牌
    const token = state.push('internal_link', '', 0);
    token.content = linkText; // 存储完整的链接文本以供后续处理

    // 更新位置
    state.pos = matchEnd;
    return true;
  }

  // 将定位器函数分配给规则函数本身
  (internal_link as any).locator = locator;

  // 在内联解析器中添加规则，优先级较高，在内置的 'link' 规则之前
  md.inline.ruler.before('link', 'internal_link', internal_link);

  // 为 'internal_link' 令牌类型添加渲染器
  md.renderer.rules.internal_link = function (tokens: any[], idx: number) {
    const token = tokens[idx];
    const linkText = token.content; // 这是完整的 [[...]] 文本

    // 返回一个占位符。我们稍后会替换它。
    return createLinkPlaceholder(linkText);
  };
}

// 用于添加行号属性的插件
function lineNumbersPlugin(md: MarkdownIt) {
  // 保存原始的渲染器规则
  const defaultRender = md.renderer.render;

  // 重写渲染器以添加行号
  md.renderer.render = function(tokens: any[], options: any, env: any) {
    let lineNum = 1;

    // 为每个块级令牌添加行号
    const addLineNumbers = (tokens: any[], isRootLevel: boolean = true) => {
      tokens.forEach((token, index) => {
        // 处理子令牌（先处理子令牌，再处理父令牌）
        if (token.children && token.children.length > 0) {
          addLineNumbers(token.children, false);
        }

        // 检查是否是块级元素开始
        if (token.type === 'paragraph_open' || token.type === 'heading_open' ||
            token.type === 'list_item_open' || token.type === 'blockquote_open' ||
            token.type === 'code_block' || token.type === 'fence' ||
            token.type === 'table_open' || token.type === 'hr') {
          // 为块级元素的开始添加行号
          if (!token.attrs) token.attrs = [];
          token.attrs.push(['data-line', lineNum.toString()]);
        }

        // 根据令牌类型计算行号增量
        if (token.type === 'paragraph_open' || token.type === 'heading_open' ||
            token.type === 'list_item_open' || token.type === 'blockquote_open') {
          // 对于列表项，需要特殊处理
          if (token.type === 'list_item_open') {
            // 优先使用 token.map 属性获取源代码行范围
            if (token.map && Array.isArray(token.map) && token.map.length >= 2) {
              // token.map 包含 [startLine, endLine]（从0开始计数）
              const lines = token.map[1] - token.map[0] + 1;
              lineNum += lines;
            } else if (isRootLevel) {
              // 如果没有 token.map 且是根级别，则遍历兄弟令牌直到找到匹配的 list_item_close
              let lines = 1; // 至少有一行（当前行）
              for (let i = index + 1; i < tokens.length; i++) {
                if (tokens[i].type === 'list_item_close') {
                  break;
                }
                if (tokens[i].content) {
                  lines += Math.max(0, tokens[i].content.split('\n').length - 1);
                }
              }
              lineNum += lines;
            } else {
              // 如果是嵌套的列表项且没有 token.map，使用默认值
              lineNum += 1;
            }
          } else {
            // 其他块级元素至少增加1行
            lineNum += 1;
          }
        } else if (token.type === 'code_block' || token.type === 'fence') {
          // 代码块按实际行数计算
          const lines = token.content ? token.content.split('\n').length : 1;
          lineNum += lines;
          console.log(`[lineNumbersPlugin] 代码块增加 ${lines} 行，当前行号: ${lineNum}`);
        } else if (token.content) {
          // 其他有内容的令牌
          const lines = token.content.split('\n').length - 1;
          lineNum += Math.max(0, lines);
        }
      });
    };

    addLineNumbers(tokens, true);

    const result = defaultRender.call(md.renderer, tokens, options, env);
    return result;
  };
}

// --- 公共 API ---

/**
 * 同步将 Markdown 文本渲染为 HTML 并处理内部链接。
 * 内部链接将被替换为占位符。
 * @param markdownText 要渲染的 Markdown 文本。
 * @returns 包含内部链接占位符的已渲染 HTML 字符串。
 */
export function renderMarkdownSync(markdownText: string): string {
  if (!markdownText) {
    return '';
  }

  try {
    // 使用内部链接插件初始化 markdown-it
    const md = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      breaks: true,
    });

    // Disable fuzzy link detection to prevent filenames (e.g., "file.md")
    // from being interpreted as domains. Only URLs with protocols will be linked.
    md.linkify.set({ fuzzyLink: false });

    md.use(internalLinkPlugin);
    md.use(lineNumbersPlugin); // 添加行号插件

    // 将 Markdown 渲染为 HTML
    const rawHtml = md.render(markdownText);

    // 注意：占位符已由渲染器插入。
    // 调用者负责在需要时替换占位符。
    // 对于同步渲染，我们返回带有占位符的 HTML。
    // DOMPurify 无法在此处的 Worker 环境中用于最终清理
    // 因为它需要 DOM。清理必须由调用者在主线程中完成。

    return rawHtml;
  } catch (error) {
    logger.error('同步渲染 Markdown 时出错:', error);
    return `<p>渲染 Markdown 时出错: ${(error as Error).message}</p>`;
  }
}

/**
 * 异步将 HTML 中的占位符替换为已处理的内部链接。
 * @param htmlWithPlaceholders 包含占位符的 HTML 字符串。
 * @returns 解析为已将占位符替换为实际链接的 HTML 字符串的 Promise。
 */
export async function replaceLinkPlaceholders(htmlWithPlaceholders: string): Promise<string> {
  if (!htmlWithPlaceholders) {
    return '';
  }

  try {
    // 检查 DOMParser 是否可用（浏览器环境）
    if (typeof DOMParser === 'undefined') {
      // 如果不可用，则无法在此处处理占位符。
      // 这在 Web Worker 中是这种情况。我们应该记录文档说明
      // Worker 环境中的调用者需要以不同方式处理占位符替换
      // 或将 HTML 传递回主线程进行处理。
      // 现在，我们将记录警告并按原样返回 HTML。
      // 对于 Worker，更健壮的解决方案是使用字符串替换。

      // 对于没有 DOMParser 的环境（例如 Web Workers），回退到字符串替换
      logger.warn('DOMParser 不可用，使用字符串替换处理链接占位符。');

      // 用于查找占位符的正则表达式
      const placeholderRegex = /\{\{INTERNAL_LINK_PLACEHOLDER:([^\}]+)\}\}/g;
      let match;
      let newHtml = htmlWithPlaceholders;
      const replacements: { [key: string]: string } = {};

      // 查找所有唯一的占位符
      while ((match = placeholderRegex.exec(htmlWithPlaceholders)) !== null) {
        const placeholder = match[0];
        const encodedLinkText = match[1];
        // 解码链接文本
        const linkText = encodedLinkText
          .replace(/&/g, "&")
          .replace(/</g, "<")
          .replace(/>/g, ">")
          .replace(/"/g, '"')
          .replace(/'/g, "'");

        if (!replacements[placeholder]) {
          // 处理链接文本并存储结果
          const replacement = await processSingleLinkText(linkText);
          replacements[placeholder] = replacement;
        }
      }

      // 替换所有占位符
      for (const [placeholder, replacement] of Object.entries(replacements)) {
        // 修复：确保 | 字符也被正确转义，防止正则表达式解析错误
        const escapedPlaceholder = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedPlaceholder, 'g');
        newHtml = newHtml.replace(regex, replacement);
        }

        return newHtml;
    }

    // 将 HTML 字符串解析为 DOM 文档
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlWithPlaceholders, 'text/html');

    // 查找所有占位符跨度
    // 注意：渲染器现在创建的是文本占位符，而不是跨度。
    // 我们需要调整选择器或渲染器。
    // 让我们调整渲染器以创建一个特定的类以便于选择（如果需要），
    // 但现在，我们将坚持使用上面回退中显示的文本替换。
    // 当前渲染器创建 `{{INTERNAL_LINK_PLACEHOLDER:...}}` 文本节点。
    // 在 DOM 中查找和替换这些节点很棘手。
    // 字符串替换更可靠。

    // 重用回退中的字符串替换逻辑
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
        const replacement = await processSingleLinkText(linkText);
        replacements[placeholder] = replacement;
      }
    }

    for (const [placeholder, replacement] of Object.entries(replacements)) {
      // 修复：确保 | 字符也被正确转义，防止正则表达式解析错误
      const escapedPlaceholder = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escapedPlaceholder, 'g');
      newHtml = newHtml.replace(regex, replacement);
      }

      return newHtml;

  } catch (error) {
    logger.error('替换链接占位符时出错:', error);
    return htmlWithPlaceholders; // 出错时返回原始 HTML
  }
}