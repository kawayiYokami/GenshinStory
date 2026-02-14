import logger from '../../../app/services/loggerService';
import { useDataStore } from '@/features/app/stores/data';
import { useAppStore } from '@/features/app/stores/app';
import type { IndexItem } from '@/features/app/stores/data';
import pathService from '../../../app/services/pathService';
import filePathService from '../../../app/services/filePathService';
import tokenizerService from '@/lib/tokenizer/tokenizerService';
import { stripMarkdown } from '@/lib/markdown/markdownStripper';

// --- 类型定义 ---
export interface DocRequest {
    path: string;
    lineRanges?: string[];
    preserveMarkdown?: boolean; // 新增：是否保留 Markdown 格式
}

interface SearchResult {
    path: string;
    line: number;
    snippet: string;
    totalLines?: number;
    totalTokens?: number;
    hitCount?: number;  // 该文件的实际命中次数
}

interface DocMetadata {
    totalTokens: number;
    totalLines: number;
}

/**
 * 将字符串切分为二字词组 (bigrams)
 * @param text 输入的文本
 * @returns 二字词组数组
 */
function getBigrams(text: string): string[] {
  const cleanedText = text.replace(/\s+/g, '').toLowerCase();
  if (cleanedText.length <= 1) {
    return [cleanedText];
  }
  const bigrams = new Set<string>();
  for (let i = 0; i < cleanedText.length - 1; i++) {
    bigrams.add(cleanedText.substring(i, i + 2));
  }
  return Array.from(bigrams);
}

/**
 * 通过修剪、转为小写并将全角字符替换为半角字符来规范化搜索查询。
 * @param query 输入的查询字符串
 * @returns 规范化后的查询字符串
 */
function _normalizeQuery(query: string): string {
  if (typeof query !== 'string') return '';
  return query
    .trim()
    .toLowerCase()
    .replace(/[\uff01-\uff5e]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xfee0))
    .replace(/\u3000/g, ' ') // 全角空格
    .replace(/"|"|'|'/g, '"') // 中文引号转标准引号
    .replace(/^"+|"+$/g, '') // 移除首尾引号
    .trim();
}

/**
 * 格式化搜索结果的代码片段：截断、突出显示查询词、清洗 Markdown
 * @param text 原始文本
 * @param query 搜索查询词
 * @param maxLength 最大长度（默认 50）
 * @returns 格式化后的片段
 */
function formatSearchSnippet(text: string, query: string, maxLength: number = 50): string {
  let snippet = text.trim();

  // 截断
  if (snippet.length > maxLength) {
    snippet = snippet.substring(0, maxLength) + '...';
  }

  // 突出显示查询词
  const regex = new RegExp(query.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'gi');
  snippet = snippet.replace(regex, `**${query}**`);

  // 清洗 Markdown 格式
  snippet = stripMarkdown(snippet);

  return snippet;
}

class LocalToolsService {
  // --- 路径助手函数 ---

  private _getPhysicalPathFromLogicalPath(logicalPath: string): string {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return '';
    return filePathService.toPhysicalDocPath(logicalPath, currentDomain);
  }

  private _getLogicalPathFromFrontendPath(frontendPath: string): string {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    return filePathService.fromFrontendCategoryPath(frontendPath, {
      domain: currentDomain || undefined,
      ensureMdExtension: true,
    });
  }

  // --- 工具函数 ---


  private _applyLineRanges(content: string, lineRanges?: string[]): string {
    if (!lineRanges || lineRanges.length === 0) {
      return content;
    }

    const lines = content.split('\n');
    const selectedLines = new Set<number>();

    for (const range of lineRanges) {
      const parts = range.split('-').map(Number);
      if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        const [start, end] = parts;

        if (start > lines.length) {
            continue;
        }

        for (let i = Math.max(1, start); i <= Math.min(lines.length, end); i++) {
          selectedLines.add(i);
        }
      }
    }

    if (selectedLines.size === 0) {
      return "[通知] 指定的行号范围无效或完全超出文件范围。";
    }

    const sortedLines = Array.from(selectedLines).sort((a, b) => a - b);
    return sortedLines.map(lineNumber => `${lineNumber} | ${lines[lineNumber - 1]}`).join('\n');
  }

  public async readDoc(rawRequests: string | string[] | DocRequest[]): Promise<string> {
    let docRequests: DocRequest[];
    if (typeof rawRequests === 'string') {
      docRequests = [{ path: rawRequests, lineRanges: [], preserveMarkdown: false }];
    } else if (Array.isArray(rawRequests) && rawRequests.every(item => typeof item === 'string')) {
      docRequests = (rawRequests as string[]).map(path => ({ path, lineRanges: [], preserveMarkdown: false }));
    } else {
      docRequests = rawRequests as DocRequest[];
    }

    const dataStore = useDataStore();

    if (!docRequests || docRequests.length === 0) {
      return JSON.stringify({
        error: "错误：未提供任何文档读取请求"
      });
    }

    const contentPromises = docRequests.map(async (request) => {
        let { path, lineRanges, preserveMarkdown = false } = request;
        const appStore = useAppStore();
        const currentDomain = appStore.currentDomain || undefined;
        path = filePathService.normalizeLogicalPath(path, {
          domain: currentDomain,
          ensureMdExtension: true,
        });

        // 修复: 增强 lineRanges 的健壮性
        if (typeof lineRanges === 'string') {
            lineRanges = [lineRanges];
        } else if (!Array.isArray(lineRanges)) {
            lineRanges = [];
        }

        const originalPath = request.path;
        let physicalPath: string;
        let fullContent: string;

        try {
            physicalPath = this._getPhysicalPathFromLogicalPath(path);
            fullContent = await dataStore.fetchMarkdownContent(physicalPath);

        } catch (initialError) {

            try {
                const justTheFileName = filePathService.normalizeLogicalPath(path, {
                  domain: currentDomain,
                  ensureMdExtension: true,
                }).split('/').pop();
                if (!justTheFileName) throw initialError;

                const resolvedPath = await pathService.resolveLogicalPath(justTheFileName);

                // 如果解析到了路径，即使它和原始路径看起来一样（可能是编码差异或就是同一个文件但之前读取失败），
                // 我们也应该尝试用新的 _getPhysicalPathFromLogicalPath (它现在会进行正确的编码) 再试一次。
                if (resolvedPath) {
                    if (resolvedPath !== path) {
                        path = resolvedPath;
                    }

                    physicalPath = this._getPhysicalPathFromLogicalPath(path);
                    fullContent = await dataStore.fetchMarkdownContent(physicalPath);
                } else {
                    throw initialError;
                }
            } catch (secondaryError) {
                logger.error(`读取文档失败，最终放弃: ${originalPath}`, { initialError, secondaryError });
                const finalErrorMessage = `错误：无法找到文档 '${originalPath}'。系统已尝试在所有已知目录中搜索，但未找到匹配项。`;
                return { path: originalPath, error: finalErrorMessage };
            }
        }

        const content = this._applyLineRanges(fullContent, lineRanges);

        // 获取文档元数据
        const lines = fullContent.split('\n');
        const totalLines = lines.length;
        const totalTokens = tokenizerService.countTokens(fullContent);

        // 使用 JSON 格式返回文档内容
        const hasLineRanges = lineRanges && lineRanges.length > 0;
        const docResult: any = {
          path,
          totalLines,
          totalTokens
        };

        if (hasLineRanges) {
          docResult.content = content;
          // 计算单一连续的行号范围
          const actualLines = content.split('\n').filter(line => line.trim());
          if (actualLines.length > 0) {
            const firstLineMatch = actualLines[0].match(/^(\d+)\s*\|/);
            const lastLineMatch = actualLines[actualLines.length - 1].match(/^(\d+)\s*\|/);
            if (firstLineMatch && lastLineMatch) {
              docResult.lineRange = `${firstLineMatch[1]}-${lastLineMatch[1]}`;
            }
          }
          // 计算本次调用返回内容的字数
          docResult.returnedTokens = tokenizerService.countTokens(content);
          // 计算剩余字数
          docResult.remainingTokens = totalTokens - docResult.returnedTokens;
        } else {
          // 根据 preserveMarkdown 参数决定是否保留 Markdown 格式
          if (preserveMarkdown) {
            docResult.content = content; // 保留完整的 Markdown 格式
          } else {
            const strippedContent = stripMarkdown(content);
            docResult.content = strippedContent;
          }
          // 计算实际返回内容的 token 数
          docResult.returnedTokens = tokenizerService.countTokens(docResult.content);
          // 计算剩余 token 数，确保不为负数
          docResult.remainingTokens = Math.max(0, totalTokens - docResult.returnedTokens);
        }

        return JSON.stringify(docResult);
    });

    const results = await Promise.allSettled(contentPromises);

    const docElements: any[] = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
          if (typeof result.value === 'string') {
              // 解析 JSON 格式的结果
              try {
                const docResult = JSON.parse(result.value);
                docElements.push(docResult);
              } catch (parseError) {
                // 如果解析失败，作为错误处理
                docElements.push({
                  path: docRequests[index].path,
                  error: "返回格式解析失败"
                });
              }
          } else if (result.value && (result.value as any).error) {
              const { path: failedPath, error: errorMessage } = result.value as any;
              logger.error(`读取文档失败 (settled): ${failedPath}`, { reason: errorMessage });
              docElements.push({
                path: failedPath,
                error: errorMessage
              });
          }
      } else {
          const failedPath = docRequests[index].path;
          logger.error(`读取文档时发生意外的Promise拒绝: ${failedPath}`, { reason: result.reason });
          docElements.push({
            path: failedPath,
            error: "处理文档时发生意外错误"
          });
      }
    });

    // 构建最终的 JSON 结构
    return JSON.stringify({
      docs: docElements.map(element => {
        // 解析 XML 元素，提取数据
        if (typeof element === 'object' && element.path) {
          return element; // 已经是 JSON 对象
        }

        // 兼容旧的 XML 字符串格式
        const docMatch = element.match(/<doc><path>(.*?)<\/path>(?:<content[^>]*>(.*?)<\/content>)?(?:<error><!\[CDATA\[(.*?)\]\]><\/error>)?<\/doc>/);
        if (docMatch) {
          const [, path, content, error] = docMatch;
          return {
            path,
            ...(content && { content }),
            ...(error && { error })
          };
        }
        return { error: "解析文档元素失败" };
      }).filter(doc => doc.path || doc.error)
    });
  }

   private async _performSingleSearch(query: string, _signal?: AbortSignal): Promise<SearchResult[]> {
       query = _normalizeQuery(query);
       if (!query) return [];

       if (_signal?.aborted) {
         throw new DOMException('搜索被中止', 'AbortError');
       }

       const dataStore = useDataStore();
       const appStore = useAppStore();
       const currentDomain = appStore.currentDomain;
       if (!currentDomain) return [];

       const searchIndex = await dataStore.loadSearchIndex(currentDomain);

       const queryBigrams = getBigrams(query);
       if (queryBigrams.length === 0) return [];

       const idSets: Set<number>[] = [];
       queryBigrams.forEach(bigram => {
           if (searchIndex.has(bigram)) {
               const ids = searchIndex.get(bigram)!;
               if (ids.length > 0) {
                   idSets.push(new Set(ids));
               }
           }
       });

       if (idSets.length === 0) return [];

       const intersectionSet = idSets.reduce((acc, set) => new Set([...acc].filter(id => set.has(id))));
       if (intersectionSet.size === 0) return [];

       // Use the cached catalogMap from dataStore instead of creating a new one
       const catalogMap = dataStore.catalogMap;
       const initialResults = Array.from(intersectionSet).map(id => catalogMap.get(id)).filter(Boolean) as IndexItem[];

       if (initialResults.length === 0) return [];

       const results: SearchResult[] = [];
       const fileSnippetCount = new Map<string, number>();
       const fileHitCount = new Map<string, number>();  // 记录每个文件的实际命中次数

       // 用于缓存每个文档的元数据，避免重复计算
       const metadataCache = new Map<string, { totalLines: number, totalTokens: number }>();

       for (const item of initialResults) {
           try {
               const logicalPath = this._getLogicalPathFromFrontendPath(item.path);

               const content = await dataStore.fetchMarkdownContent(this._getPhysicalPathFromLogicalPath(logicalPath));
               const lines = content.split('\n');

               // 计算并缓存元数据
               let metadata = metadataCache.get(logicalPath);
               if (!metadata) {
                   metadata = {
                       totalLines: lines.length,
                       totalTokens: tokenizerService.countTokens(content)
                   };
                   metadataCache.set(logicalPath, metadata);
               }

               for (let i = 0; i < lines.length; i++) {
                   if (lines[i].toLowerCase().includes(query.toLowerCase())) {
                       // 记录实际命中次数
                       const currentHitCount = fileHitCount.get(logicalPath) || 0;
                       fileHitCount.set(logicalPath, currentHitCount + 1);

                       // 检查是否已经显示够了snippet
                       const currentSnippetCount = fileSnippetCount.get(logicalPath) || 0;
                       if (currentSnippetCount >= 3) {
                           continue; // 继续计数但不显示更多snippet
                       }

                       const foundLine = i + 1;
                       const snippet = formatSearchSnippet(lines[i], query);

                       // 先添加结果，稍后统一更新hitCount
                       results.push({
                           path: logicalPath,
                           line: foundLine,
                           snippet: snippet,
                           totalLines: metadata.totalLines,
                           totalTokens: metadata.totalTokens,
                           hitCount: undefined // 稍后更新
                       });
                       fileSnippetCount.set(logicalPath, currentSnippetCount + 1);

                       i += 2;
                   }
               }

           } catch (e) {
               // 静默处理错误，AI看到没有结果会知道出了问题
           }
       }

       // 所有文件扫描完成后，统一更新所有结果的hitCount
       results.forEach(result => {
           const finalHitCount = fileHitCount.get(result.path);
           if (finalHitCount !== undefined) {
               result.hitCount = finalHitCount;
           }
       });

       return results;
   }


    public async searchDocs(
      query: string,
      docPath?: string,
      options?: {
        maxResults?: number,        // 最大返回结果数，默认50
        generateSummary?: boolean    // 是否生成摘要，默认false
      }
    ): Promise<string> {
      if (typeof query !== 'string' || !query.trim()) {
        const errorMsg = "错误：查询工具收到了无效或缺失的查询参数。";
        logger.error(errorMsg, { query, docPath });
        return JSON.stringify({
          tool: 'search_docs',
          query,
          docPath,
          error: errorMsg
        });
      }

      return this._searchDocsInternal(query, docPath, undefined, options);
    }

    private async _searchDocsInternal(
      query: string,
      docPath: string | undefined,
      _signal: AbortSignal | undefined,
      options?: {
        maxResults?: number,
        generateSummary?: boolean
      }
    ): Promise<string> {
      const dataStore = useDataStore();
      const appStore = useAppStore();
      const currentDomain = appStore.currentDomain;

      if (!currentDomain) {
        return JSON.stringify({
          tool: 'search_docs',
          query,
          docPath,
          message: "当前域未设置"
        });
      }

      // 1. 预处理：分割查询词
      const terms = query.split(/\s+/).map(t => t.trim()).filter(t => t);
      if (terms.length === 0) return JSON.stringify({
        tool: 'search_docs',
        query,
        docPath,
        message: "请输入有效的查询词"
      });

      // 2. 执行搜索
      const allResults = await this._performSearch(terms, _signal || new AbortController().signal);

      // 3. 路径过滤（包含关系）
      const normalizedDocPath = docPath && docPath.trim()
        ? filePathService.normalizeLogicalPath(docPath.trim(), {
            domain: currentDomain,
            ensureMdExtension: false,
          })
        : '';
      const filteredResults = normalizedDocPath
        ? allResults.filter(r => this._pathContains(r.path, normalizedDocPath))
        : allResults;

      // 4. 分组并排序
      const sortedResults = this._groupAndSortResults(filteredResults);

      // 5. 应用结果数量限制
      const maxResults = options?.maxResults ?? 50;
      const limitedResults = sortedResults.slice(0, maxResults);

      // 6. 生成摘要
      const summary = (options?.generateSummary === true && limitedResults.length > 0)
        ? this._generateSummary(limitedResults, query)
        : undefined;

      // 7. 格式化输出
      return this._formatOutput(limitedResults, query, normalizedDocPath || docPath, summary);
    }

    private async _performSearch(terms: string[], _signal: AbortSignal): Promise<SearchResult[]> {
      const dataStore = useDataStore();

      // 对每个关键词执行独立搜索
      const termResults = await Promise.all(terms.map(term => {
        return this._performSingleSearch(term, _signal || new AbortController().signal);
      }));

      // 收集所有搜索结果
      const allResults: SearchResult[] = [];
      termResults.forEach(results => {
        allResults.push(...results);
      });

      return allResults;
    }

    private _pathContains(fullPath: string, filterPath: string): boolean {
      const fullLower = fullPath.toLowerCase();
      const filterLower = filterPath.toLowerCase();
      return fullLower.includes(filterLower);
    }

    private _groupAndSortResults(results: SearchResult[]): any[] {
      if (results.length === 0) return [];

      // 去重（基于路径和行号）
      const uniqueResults = new Map<string, SearchResult>();
      for (const result of results) {
        const key = `${result.path}:${result.line}`;
        if (!uniqueResults.has(key)) {
          uniqueResults.set(key, result);
        }
      }
      const finalResults = Array.from(uniqueResults.values());

      // 按文件分组结果
      const groupedResults = new Map<string, any>();
      for (const result of finalResults) {
        if (!groupedResults.has(result.path)) {
          groupedResults.set(result.path, {
            path: result.path,
            totalLines: result.totalLines,
            totalTokens: result.totalTokens,
            hits: []
          });
        }

        groupedResults.get(result.path).hits.push({
          line: result.line,
          snippet: result.snippet
        });
      }

      // 转换为数组并使用实际命中次数
      const groupedArray = Array.from(groupedResults.values()).map(group => {
        // 获取该文件第一个结果的 hitCount（因为每个相同路径的结果都有相同的 hitCount）
        const firstResult = finalResults.find(r => r.path === group.path);
        return {
          ...group,
          hitCount: firstResult?.hitCount || group.hits.length
        };
      });

      // 按命中次数降序排序，然后按路径排序
      groupedArray.sort((a, b) => {
        if (b.hitCount !== a.hitCount) {
          return b.hitCount - a.hitCount;
        }
        return a.path.localeCompare(b.path);
      });

      return groupedArray;
    }

    private _generateSummary(results: any[], query: string): string {
      const fileCount = results.length;
      const topFiles = results.slice(0, 3).map(r => r.path.split('/').pop()).join('、');

      return `找到 ${fileCount} 个相关文件，主要包括：${topFiles}等。`;
    }

    private _formatOutput(results: any[], query: string, docPath?: string, summary?: string): string {
      if (results.length === 0) {
        return JSON.stringify({
          tool: 'search_docs',
          query,
          docPath,
          message: docPath ? "在指定路径中未找到相关内容" : "未找到相关文档"
        });
      }

      const response: any = {
        tool: 'search_docs',
        query,
        results,
        grouped: true  // 添加 grouped 字段标识这是分组后的结果
      };

      if (docPath) response.docPath = docPath;
      if (summary) response.message = summary;  // 使用 message 字段而不是 summary

      return JSON.stringify(response);
    }


   public async getDocMetadata(logicalPath: string): Promise<DocMetadata | null> {
     const dataStore = useDataStore();
     const tokenizer = tokenizerService;

     try {
       const physicalPath = this._getPhysicalPathFromLogicalPath(logicalPath);
       const content = await dataStore.fetchMarkdownContent(physicalPath);
       const lines = content.split('\n');
       const totalLines = lines.length;
       const totalTokens = tokenizer.countTokens(content);

       return { totalTokens, totalLines };
     } catch (error) {
       logger.error(`获取元数据失败: ${logicalPath}`, error);
       return null;
     }
   }
}

const localToolsService = new LocalToolsService();
export default localToolsService;
