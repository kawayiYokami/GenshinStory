import logger from '../../app/services/loggerService';
import { useDataStore } from '@/features/app/stores/data';
import { useAppStore } from '@/features/app/stores/app';
import type { IndexItem } from '@/features/app/stores/data';
import pathService from '../../app/services/pathService';
import tokenizerService from '@/lib/tokenizer/tokenizerService';

// --- 类型定义 ---
export interface DocRequest {
    path: string;
    lineRanges?: string[];
}

interface SearchResult {
    path: string;
    line: number;
    snippet: string;
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
    .replace(/“|”|‘|’/g, '"') // 中文引号转标准引号
    .replace(/^"+|"+$/g, '') // 移除首尾引号
    .trim();
}

class LocalToolsService {
  // --- 路径助手函数 ---

  private _getPhysicalPathFromLogicalPath(logicalPath: string): string {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return '';
    const cleanLogicalPath = logicalPath.startsWith('/') ? logicalPath.substring(1) : logicalPath;
    return `/domains/${currentDomain}/docs/${cleanLogicalPath}`;
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
      docRequests = [{ path: rawRequests, lineRanges: [] }];
    } else if (Array.isArray(rawRequests) && rawRequests.every(item => typeof item === 'string')) {
      docRequests = (rawRequests as string[]).map(path => ({ path, lineRanges: [] }));
    } else {
      docRequests = rawRequests as DocRequest[];
    }

    logger.log(`执行文档读取...`, { requests: docRequests });
    const dataStore = useDataStore();
    
    if (!docRequests || docRequests.length === 0) {
      return '<docs><error><![CDATA[错误：未提供任何文档读取请求。]]></error></docs>';
    }

    const contentPromises = docRequests.map(async (request) => {
        let { path, lineRanges } = request;
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

                if (resolvedPath && resolvedPath !== path) {
                    logger.log(`路径解析成功: '${path}' -> '${resolvedPath}'。正在重试...`);
                    path = resolvedPath;
                    
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
        
        // 构建 <content> 标签，如果指定了行号范围，则添加 lines 属性
        let contentTag = '<content';
        if (lineRanges && lineRanges.length > 0) {
            // 将行号范围数组 join 成字符串，例如 "1-10, 20-30"
            const linesAttrValue = lineRanges.join(', ');
            contentTag += ` lines="${linesAttrValue}"`;
        }
        contentTag += '>';
        
        // 使用 CDATA 包裹内容以处理特殊字符
        return `<doc><path>${path}</path>${contentTag}<![CDATA[${content}]]></content></doc>`;
    });

    const results = await Promise.allSettled(contentPromises);
    
    const docElements: string[] = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
          if (typeof result.value === 'string') {
              docElements.push(result.value);
          } else if (result.value && (result.value as any).error) {
              const { path: failedPath, error: errorMessage } = result.value as any;
              logger.error(`读取文档失败 (settled): ${failedPath}`, { reason: errorMessage });
              // 错误信息也使用 CDATA 包裹以防特殊字符
              docElements.push(`<doc><path>${failedPath}</path><error><![CDATA[${errorMessage}]]></error></doc>`);
          }
      } else {
          const failedPath = docRequests[index].path;
          logger.error(`读取文档时发生意外的Promise拒绝: ${failedPath}`, { reason: result.reason });
          const errorMessage = `错误：处理文档 '${failedPath}' 时发生意外错误。`;
          docElements.push(`<doc><path>${failedPath}</path><error><![CDATA[${errorMessage}]]></error></doc>`);
      }
    });

    // 构建最终的 XML 结构
    const xmlContent = docElements.join('');
    return `<docs>${xmlContent}</docs>`;
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

       const chunkPromises = queryBigrams.map(bigram => dataStore.fetchSearchChunk(currentDomain, bigram[0]));
       const chunks = await Promise.all(chunkPromises);
       
       const idSets: Set<number>[] = [];
       queryBigrams.forEach((bigram, index) => {
           const chunk = chunks[index];
           if (chunk && chunk[bigram] && chunk[bigram].length > 0) {
               idSets.push(new Set(chunk[bigram]));
           }
       });

       if (idSets.length === 0) return [];
       
       const intersection = idSets.reduce((acc, set) => new Set([...acc].filter(id => set.has(id))));
       if (intersection.size === 0) return [];

       const catalogMap = new Map<string | number, IndexItem>(dataStore.indexData.map(item => [item.id, item]));
       const initialResults = Array.from(intersection).map(id => catalogMap.get(id)).filter(Boolean) as IndexItem[];

       if (initialResults.length === 0) return [];

       const results: SearchResult[] = [];
       const fileSnippetCount = new Map<string, number>();

       for (const item of initialResults) {
           try {
               const logicalPath = this._getLogicalPathFromFrontendPath(item.path);
               
               if ((fileSnippetCount.get(logicalPath) || 0) >= 3) {
                   continue;
               }

               const physicalPath = this._getPhysicalPathFromLogicalPath(logicalPath);
               const content = await dataStore.fetchMarkdownContent(physicalPath);
               const lines = content.split('\n');
               
               for (let i = 0; i < lines.length; i++) {
                   if ((fileSnippetCount.get(logicalPath) || 0) >= 3) {
                       break;
                   }

                   if (lines[i].toLowerCase().includes(query.toLowerCase())) {
                       const foundLine = i + 1;
                       let snippet = lines[i].trim();
                       
                       if (snippet.length > 50) {
                           snippet = snippet.substring(0, 50) + '...';
                       }
                       
                       const regex = new RegExp(query.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'gi');
                       snippet = snippet.replace(regex, `**${query}**`);

                       results.push({ path: logicalPath, line: foundLine, snippet: snippet });
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

    public async searchDocs(query: string): Promise<string> {
     if (typeof query !== 'string' || !query.trim()) {
       const errorMsg = "错误：查询工具收到了无效或缺失的查询参数。";
       logger.error(errorMsg, { query });
       return `<search_results query="${query}"><error><![CDATA[${errorMsg}]]></error></search_results>`;
     }

     logger.log(`执行高级搜索...`, { query });
     const dataStore = useDataStore();
     const appStore = useAppStore();
     const currentDomain = appStore.currentDomain;

     if (!currentDomain) {
         return `<search_results query="${query}"><error><![CDATA[错误：当前域未设置。]]></error></search_results>`;
     }

     if (!dataStore.indexData || dataStore.indexData.length === 0) {
       logger.log(`LocalTools: 索引数据缺失，为 '${currentDomain}' 重新加载...`);
       try {
         await dataStore.fetchIndex(currentDomain);
       } catch (e) {
         logger.error(`错误：为域 '${currentDomain}' 自动加载知识库索引失败:`, e);
         return `<search_results query="${query}"><error><![CDATA[错误: 无法加载知识库索引。]]></error></search_results>`;
       }
     }

     try {
        const orGroups = query.split('|').map(g => g.trim()).filter(g => g);
        if (orGroups.length === 0) return `<search_results query="${query}"><message><![CDATA[请输入有效的查询词。]]></message></search_results>`;

        const allGroupResults = await Promise.all(orGroups.map(async (group) => {
            const andTerms = group.split(/\s+/).map(t => t.trim()).filter(t => t);
            if (andTerms.length === 0) return [];

            const termResults = await Promise.all(andTerms.map(term => this._performSingleSearch(term)));

            if (termResults.some(res => res.length === 0)) {
                return [];
            }
            
            const docMap = new Map<string, { snippets: SearchResult[], firstResult: SearchResult }>();
            
            for (const result of termResults[0]) {
                docMap.set(result.path, { snippets: [result], firstResult: result });
            }

            for (let i = 1; i < termResults.length; i++) {
                const currentResults = termResults[i];
                const currentPaths = new Set(currentResults.map(r => r.path));
                for (const path of docMap.keys()) {
                    if (!currentPaths.has(path)) {
                        docMap.delete(path);
                    } else {
                        const existing = docMap.get(path);
                        if (existing) {
                            const newSnippets = currentResults.filter(r => r.path === path);
                            existing.snippets.push(...newSnippets);
                        }
                    }
                }
            }
            
            return Array.from(docMap.values()).flatMap(val => val.snippets);
        }));

        const allResults = allGroupResults.flat();

        const uniqueResults = new Map<string, SearchResult>();
        for (const result of allResults) {
            const key = `${result.path}:${result.line}`;
            if (!uniqueResults.has(key)) {
                uniqueResults.set(key, result);
            }
        }
        let finalResults = Array.from(uniqueResults.values());

       if (finalResults.length > 20) {
         finalResults = finalResults.slice(0, 20);
       }

       logger.log("高级搜索成功。", { count: finalResults.length });
       
       if (finalResults.length === 0) {
         return `<search_results query="${query}"><message><![CDATA[未找到相关文档。]]></message></search_results>`;
       }
       
       finalResults.sort((a, b) => {
         if (a.path < b.path) return -1;
         if (a.path > b.path) return 1;
         return a.line - b.line;
       });
       
       // 构建 XML 结果
       let resultElements = '';
       for (const result of finalResults) {
         // 使用 CDATA 包裹代码片段以处理特殊字符
         resultElements += `<result><path>${result.path}</path><line>${result.line}</line><snippet><![CDATA[${result.snippet}]]></snippet></result>`;
       }
       
       return `<search_results query="${query}">${resultElements}</search_results>`;

     } catch (e: any) {
       logger.error("高级搜索时发生异常:", e);
       return `<search_results query="${query}"><error><![CDATA[错误：在执行高级搜索时发生异常: ${e.message}]]></error></search_results>`;
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