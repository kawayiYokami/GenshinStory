import logger from '../../app/services/loggerService';
import { useDataStore } from '@/features/app/stores/data';
import { useAppStore } from '@/features/app/stores/app';
import type { IndexItem } from '@/features/app/stores/data';
import pathService from '../../app/services/pathService';
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
    const cleanLogicalPath = logicalPath.startsWith('/') ? logicalPath.substring(1) : logicalPath;

    // 对路径的每一部分进行编码，以处理中文和特殊字符
    const encodedPath = cleanLogicalPath.split('/').map(part => encodeURIComponent(part)).join('/');

    return `/domains/${currentDomain}/docs/${encodedPath}`;
  }

  private _getLogicalPathFromFrontendPath(frontendPath: string): string {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return '';
    const logical = frontendPath.replace(`/v2/${currentDomain}/category/`, '');
    return `${logical}.md`;
  }

  // --- 工具函数 ---

  public async listDocs(path: string = '/'): Promise<string> {
    const jsonResult = await pathService.listDocs(path);

    // 检查是否是错误信息
    if (jsonResult.startsWith("错误：")) {
      // 将错误信息包装在 XML 中
      return `<directory_listing path="${path}"><error><![CDATA[${jsonResult}]]></error></directory_listing>`;
    }

    try {
      // 解析 JSON 结果
      const results: { path: string; type: string }[] = JSON.parse(jsonResult);

      // 递归函数，将扁平的路径列表转换为嵌套的 XML 结构
      const buildXmlTree = (items: { path: string; type: string }[], basePath: string = ''): string => {
        // 创建一个映射，将路径的第一部分映射到其子项
        const rootMap = new Map<string, { path: string; type: string }[]>();

        for (const item of items) {
          // 计算相对于 basePath 的相对路径
          const relativePath = item.path.startsWith(basePath) ? item.path.substring(basePath.length) : item.path;
          const cleanPath = relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
          const pathParts = cleanPath.split('/').filter(p => p);

          if (pathParts.length > 0) {
            const firstPart = pathParts[0];
            if (!rootMap.has(firstPart)) {
              rootMap.set(firstPart, []);
            }

            // 如果是文件或目录且没有更多层级，则直接添加
            if (pathParts.length === 1) {
              rootMap.get(firstPart)!.push(item);
            } else {
              // 如果还有更多层级，我们需要创建一个虚拟的目录条目
              // 但实际上我们不需要在这里做任何事情，因为我们会递归处理
              // 只需要确保父目录存在即可
              const parentPath = [basePath, firstPart].filter(Boolean).join('/');
              // 我们需要检查是否已经有一个条目代表这个父目录
              const existingParent = rootMap.get(firstPart)!.find(i => i.path === parentPath && i.type === 'directory');
              if (!existingParent) {
                // 如果没有，我们创建一个虚拟条目
                rootMap.get(firstPart)!.push({ path: parentPath, type: 'directory' });
              }
            }
          }
        }

        let xml = '';
        for (const [name, childItems] of rootMap.entries()) {
          const directItem = childItems.find(i => {
            const itemPath = i.path.startsWith('/') ? i.path.substring(1) : i.path;
            const itemParts = itemPath.split('/').filter(p => p);
            return itemParts.length === 1 && itemParts[0] === name;
          });

          if (directItem) {
            if (directItem.type === 'file') {
              xml += `<file name="${name}" />`;
            } else {
              // 这是一个目录，需要递归处理其子项
              const children = items.filter(i => i.path.startsWith(directItem.path + '/'));
              const childrenXml = buildXmlTree(children, directItem.path);
              xml += `<directory name="${name}">${childrenXml}</directory>`;
            }
          } else {
            // 这是一个中间目录，没有直接对应的条目，但仍需要处理其子项
            const children = items.filter(i => i.path.startsWith([basePath, name].filter(Boolean).join('/') + '/'));
            const childrenXml = buildXmlTree(children, [basePath, name].filter(Boolean).join('/'));
            xml += `<directory name="${name}">${childrenXml}</directory>`;
          }
        }

        return xml;
      };

      // 构建 XML 内容
      const xmlContent = buildXmlTree(results, path);

      // 返回完整的 XML 结构
      return `<directory_listing path="${path}">${xmlContent}</directory_listing>`;
    } catch (e) {
      // 如果解析 JSON 或构建 XML 时出错，返回错误信息
      return `<directory_listing path="${path}"><error><![CDATA[解析目录列表结果时出错: ${(e as Error).message}]]></error></directory_listing>`;
    }
  }

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

    logger.log(`执行文档读取...`, { requests: docRequests });
    const dataStore = useDataStore();

    if (!docRequests || docRequests.length === 0) {
      return JSON.stringify({
        error: "错误：未提供任何文档读取请求"
      });
    }

    const contentPromises = docRequests.map(async (request) => {
        let { path, lineRanges, preserveMarkdown = false } = request;

        // 修复: 增强 lineRanges 的健壮性
        if (typeof lineRanges === 'string') {
            lineRanges = [lineRanges];
        } else if (!Array.isArray(lineRanges)) {
            lineRanges = [];
        }

        const originalPath = path;
        let physicalPath: string;
        let fullContent: string;

        try {
            physicalPath = this._getPhysicalPathFromLogicalPath(path);
            fullContent = await dataStore.fetchMarkdownContent(physicalPath);

        } catch (initialError) {
            logger.log(`读取文档 '${path}' 首次尝试失败，将尝试路径解析...`);

            try {
                const justTheFileName = path.split('/').pop()?.split('\\').pop();
                if (!justTheFileName) throw initialError;

                const resolvedPath = await pathService.resolveLogicalPath(justTheFileName);

                // 如果解析到了路径，即使它和原始路径看起来一样（可能是编码差异或就是同一个文件但之前读取失败），
                // 我们也应该尝试用新的 _getPhysicalPathFromLogicalPath (它现在会进行正确的编码) 再试一次。
                if (resolvedPath) {
                    if (resolvedPath !== path) {
                        logger.log(`路径解析成功 (重定向): '${path}' -> '${resolvedPath}'。正在重试...`);
                        path = resolvedPath;
                    } else {
                        logger.log(`路径确认存在 (原路径): '${path}'。正在重试读取...`);
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
        logger.log(`文档读取成功: ${path}`, { lineRanges, originalPath });

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

   private async _performSingleSearch(query: string): Promise<SearchResult[]> {
       query = _normalizeQuery(query);
       if (!query) return [];

       const dataStore = useDataStore();
       const appStore = useAppStore();
       const currentDomain = appStore.currentDomain;
       if (!currentDomain) return [];

       const queryBigrams = getBigrams(query);
       if (queryBigrams.length === 0) return [];

       // 使用新的单文件搜索索引
       const searchIndex = await dataStore.loadSearchIndex(currentDomain);

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

       // 用于缓存每个文档的元数据，避免重复计算
       const metadataCache = new Map<string, { totalLines: number, totalTokens: number }>();

       for (const item of initialResults) {
           try {
               const logicalPath = this._getLogicalPathFromFrontendPath(item.path);

               if ((fileSnippetCount.get(logicalPath) || 0) >= 3) {
                   continue;
               }

               const physicalPath = this._getPhysicalPathFromLogicalPath(logicalPath);
               const content = await dataStore.fetchMarkdownContent(physicalPath);
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
                   if ((fileSnippetCount.get(logicalPath) || 0) >= 3) {
                       break;
                   }

                   if (lines[i].toLowerCase().includes(query.toLowerCase())) {
                       const foundLine = i + 1;
                       const snippet = formatSearchSnippet(lines[i], query);

                       results.push({
                           path: logicalPath,
                           line: foundLine,
                           snippet: snippet,
                           totalLines: metadata.totalLines,
                           totalTokens: metadata.totalTokens
                       });
                       const currentCount = fileSnippetCount.get(logicalPath) || 0;
                       fileSnippetCount.set(logicalPath, currentCount + 1);

                       i += 2;
                   }
               }
           } catch (e) {
               logger.error(`为 ${item.path} 生成摘要失败:`, e);
           }
       }
       return results;
   }

   private async _searchInSpecificPath(query: string, docPath: string, currentDomain: string, dataStore: any): Promise<string> {
     try {
       // 执行搜索获取所有匹配结果
       const terms = query.split(/\s+/).map(t => t.trim()).filter(t => t);
       const termResults = await Promise.all(terms.map(term => this._performSingleSearch(term)));

       // 统计每个文档的命中次数
       const docHitCount = new Map<string, number>();
       const allResults: SearchResult[] = [];

       // 收集所有搜索结果并统计命中次数
       termResults.forEach(results => {
         results.forEach(result => {
           const key = result.path;
           docHitCount.set(key, (docHitCount.get(key) || 0) + 1);
           allResults.push(result);
         });
       });

       // 按路径匹配度排序
       const scoredResults = allResults.map(result => {
         const path = result.path;

         // 计算路径匹配分数
         let pathScore = 0;

         // 1. 精确匹配（完整路径）
         if (path === docPath) {
           pathScore = 100;
         }
         // 2. 路径前缀匹配（docPath 是目录）
         else if (path.startsWith(docPath)) {
           // 计算匹配深度，越深分数越高
           const remainingPath = path.substring(docPath.length);
           const depth = remainingPath.split('/').filter(p => p).length;
           pathScore = Math.max(50 - depth * 5, 10);
         }
         // 3. 路径包含关键字匹配
         else if (path.toLowerCase().includes(docPath.toLowerCase())) {
           // 根据关键字在路径中的位置给分
           const parts = path.toLowerCase().split('/');
           const queryParts = docPath.toLowerCase().split('/');
           let matchScore = 0;

           queryParts.forEach(queryPart => {
             parts.forEach((part, index) => {
               if (part.includes(queryPart)) {
                 // 越靠前的路径部分匹配，分数越高
                 matchScore += Math.max(10 - index * 2, 1);
               }
             });
           });
           pathScore = Math.min(matchScore, 40);
         }

         return {
           ...result,
           pathScore
         };
       });

       // 过滤结果：只保留路径匹配分数大于 0 的结果
       const filteredResults = scoredResults.filter(r => r.pathScore > 0);

       // 按命中次数排序，命中次数相同的按路径匹配分数排序
       filteredResults.sort((a, b) => {
         const aHits = docHitCount.get(a.path) || 0;
         const bHits = docHitCount.get(b.path) || 0;

         if (aHits !== bHits) {
           return bHits - aHits; // 命中次数多的在前
         }

         // 相同命中次数按路径匹配分数排序
         return b.pathScore - a.pathScore;
       });

       // 限制结果数量
       const finalResults = filteredResults.slice(0, 20).map(r => ({
         path: r.path,
         line: r.line,
         snippet: r.snippet,
         totalLines: r.totalLines || 0,
         totalTokens: r.totalTokens || 0
       }));

       if (finalResults.length === 0) {
         return JSON.stringify({
           tool: 'search_docs',
           query,
           docPath,
           message: "在指定路径中未找到相关内容"
         });
       }

       return JSON.stringify({
         tool: 'search_docs',
         query,
         docPath,
         results: finalResults
       });

     } catch (error) {
       logger.error("指定路径搜索时发生异常:", error);
       return JSON.stringify({
         tool: 'search_docs',
         query,
         docPath,
         error: `错误：在指定路径搜索时发生异常: ${error.message}`
       });
     }
   }

    public async searchDocs(query: string, docPath?: string): Promise<string> {
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

     logger.log(`执行高级搜索...`, { query, docPath });
     const dataStore = useDataStore();
     const appStore = useAppStore();
     const currentDomain = appStore.currentDomain;

     if (!currentDomain) {
         return JSON.stringify({
           tool: 'search_docs',
           query,
           docPath,
           error: "错误：当前域未设置"
         });
     }

     // 如果指定了文档路径，进行指定文档搜索
     if (docPath && docPath.trim()) {
       return this._searchInSpecificPath(query.trim(), docPath.trim(), currentDomain, dataStore);
     }

     if (!dataStore.indexData || dataStore.indexData.length === 0) {
       logger.log(`LocalTools: 索引数据缺失，为 '${currentDomain}' 重新加载...`);
       try {
         await dataStore.fetchIndex(currentDomain);
       } catch (e) {
         logger.error(`错误：为域 '${currentDomain}' 自动加载知识库索引失败:`, e);
         return JSON.stringify({
           tool: 'search_docs',
           query,
           error: "错误: 无法加载知识库索引"
         });
       }
     }

     try {
        // 将查询按空格分割为多个关键词
        const terms = query.split(/\s+/).map(t => t.trim()).filter(t => t);
        if (terms.length === 0) return JSON.stringify({
           tool: 'search_docs',
           query,
           message: "请输入有效的查询词"
         });

        // 对每个关键词执行独立搜索
        const termResults = await Promise.all(terms.map(term => this._performSingleSearch(term)));

        // 统计每个文档的命中次数
        const docHitCount = new Map<string, number>();
        const allResults: SearchResult[] = [];

        // 收集所有搜索结果并统计命中次数
        termResults.forEach(results => {
          results.forEach(result => {
            const key = result.path;
            docHitCount.set(key, (docHitCount.get(key) || 0) + 1);
            allResults.push(result);
          });
        });

        // 去重（基于路径和行号）
        const uniqueResults = new Map<string, SearchResult>();
        for (const result of allResults) {
            const key = `${result.path}:${result.line}`;
            if (!uniqueResults.has(key)) {
                uniqueResults.set(key, result);
            }
        }
        let finalResults = Array.from(uniqueResults.values());

        // 限制结果数量
        if (finalResults.length > 20) {
          finalResults = finalResults.slice(0, 20);
        }

        logger.log("高级搜索成功。", { count: finalResults.length });

        if (finalResults.length === 0) {
          return JSON.stringify({
            tool: 'search_docs',
            query,
            message: "未找到相关文档"
          });
        }

        // 按命中次数降序排序，相同命中数按路径排序
        finalResults.sort((a, b) => {
          const aHits = docHitCount.get(a.path) || 0;
          const bHits = docHitCount.get(b.path) || 0;
          if (aHits !== bHits) {
            return bHits - aHits; // 命中次数多的在前
          }
          // 相同命中次数按路径和行号排序
          if (a.path < b.path) return -1;
          if (a.path > b.path) return 1;
          return a.line - b.line;
        });

       // 由于 SearchResult 已经包含了元数据，直接使用即可，无需重新获取
       // 确保所有结果都有元数据，如果没有则设置默认值
       const resultsWithMetadata = finalResults.map(r => ({
         path: r.path,
         line: r.line,
         snippet: r.snippet,
         totalLines: r.totalLines || 0,
         totalTokens: r.totalTokens || 0
       }));

       return JSON.stringify({
         tool: 'search_docs',
         query,
         results: resultsWithMetadata
       });

     } catch (e: any) {
       logger.error("高级搜索时发生异常:", e);
       return JSON.stringify({
         tool: 'search_docs',
         query,
         error: `错误：在执行高级搜索时发生异常: ${e.message}`
       });
     }
    }

   public async getDocMetadata(logicalPath: string): Promise<DocMetadata | null> {
     logger.log(`获取文档元数据...`, { path: logicalPath });
     const dataStore = useDataStore();
     const tokenizer = tokenizerService;

     try {
       const physicalPath = this._getPhysicalPathFromLogicalPath(logicalPath);
       const content = await dataStore.fetchMarkdownContent(physicalPath);
       const lines = content.split('\n');
       const totalLines = lines.length;
       const totalTokens = tokenizer.countTokens(content);

       logger.log(`元数据获取成功: ${logicalPath}`, { totalTokens, totalLines });
       return { totalTokens, totalLines };
     } catch (error) {
       logger.error(`获取元数据失败: ${logicalPath}`, error);
       return null;
     }
   }
}

const localToolsService = new LocalToolsService();
export default localToolsService;