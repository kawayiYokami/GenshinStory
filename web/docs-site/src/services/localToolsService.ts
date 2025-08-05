import logger from './loggerService';
import { useDataStore } from '@/stores/data';
import { useAppStore } from '@/stores/app';
import type { IndexItem } from '@/stores/data';
import pathService from './pathService';

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
    return pathService.listDocs(path);
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
      return "错误：未提供任何文档读取请求。";
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
        return `--- DOC START: ${path} ---\n\n${content}\n\n--- DOC END: ${path} ---`;
    });

    const results = await Promise.allSettled(contentPromises);
    
    const successfulContents: string[] = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
          if (typeof result.value === 'string') {
              successfulContents.push(result.value);
          } else if (result.value && (result.value as any).error) {
              const { path: failedPath, error: errorMessage } = result.value as any;
              logger.error(`读取文档失败 (settled): ${failedPath}`, { reason: errorMessage });
              successfulContents.push(`--- DOC START: ${failedPath} ---\n\n${errorMessage}\n\n--- DOC END: ${failedPath} ---`);
          }
      } else {
          const failedPath = docRequests[index].path;
          logger.error(`读取文档时发生意外的Promise拒绝: ${failedPath}`, { reason: result.reason });
          const errorMessage = `错误：处理文档 '${failedPath}' 时发生意外错误。`;
          successfulContents.push(`--- DOC START: ${failedPath} ---\n\n${errorMessage}\n\n--- DOC END: ${failedPath} ---`);
      }
    });

    return successfulContents.join('\n\n');
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
       return errorMsg;
     }

     logger.log(`执行高级搜索...`, { query });
     const dataStore = useDataStore();
     const appStore = useAppStore();
     const currentDomain = appStore.currentDomain;

     if (!currentDomain) {
         return "错误：当前域未设置。";
     }

     if (!dataStore.indexData || dataStore.indexData.length === 0) {
       logger.log(`LocalTools: 索引数据缺失，为 '${currentDomain}' 重新加载...`);
       try {
         await dataStore.fetchIndex(currentDomain);
       } catch (e) {
         logger.error(`错误：为域 '${currentDomain}' 自动加载知识库索引失败:`, e);
         return `错误: 无法加载知识库索引。`;
       }
     }

     try {
        const orGroups = query.split('|').map(g => g.trim()).filter(g => g);
        if (orGroups.length === 0) return "请输入有效的查询词。";

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
         return "未找到相关文档。";
       }
       
       finalResults.sort((a, b) => {
         if (a.path < b.path) return -1;
         if (a.path > b.path) return 1;
         return a.line - b.line;
       });
       
       return finalResults.map(r => `${r.path}\n  ${r.line}: ${r.snippet}`).join('\n\n');

     } catch (e: any) {
       logger.error("高级搜索时发生异常:", e);
       return `错误：在执行高级搜索时发生异常: ${e.message}`;
     }
    }

   public async getDocMetadata(logicalPath: string): Promise<DocMetadata | null> {
     logger.log(`获取文档元数据...`, { path: logicalPath });
     const dataStore = useDataStore();
     const tokenizer = (await import('./tokenizerService')).default;

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