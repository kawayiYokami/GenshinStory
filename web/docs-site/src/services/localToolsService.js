import logger from './loggerService.js';
import { useDataStore } from '@/stores/data';
import { useAppStore } from '@/stores/app';
import localforage from 'localforage';

const catalogStore = localforage.createInstance({
  name: "catalogTreeCache"
});

/**
 * 将字符串切分为二字词组 (bigrams)
 * @param {string} text - The input text.
 * @returns {string[]} An array of bigrams.
 */
function getBigrams(text) {
  const cleanedText = text.replace(/\s+/g, '').toLowerCase();
  if (cleanedText.length <= 1) {
    return [cleanedText];
  }
  const bigrams = new Set();
  for (let i = 0; i < cleanedText.length - 1; i++) {
    bigrams.add(cleanedText.substring(i, i + 2));
  }
  return Array.from(bigrams);
}

/**
 * Normalizes a search query by trimming, converting to lowercase, 
 * and replacing full-width characters with their half-width counterparts.
 * @param {string} query - The input query string.
 * @returns {string} The normalized query string.
 */
function _normalizeQuery(query) {
  if (typeof query !== 'string') return '';
  return query
    .trim()
    .toLowerCase()
    .replace(/[\uff01-\uff5e]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xfee0))
    .replace(/\u3000/g, ' ') // Full-width space
    .replace(/“|”|‘|’/g, '"') // Chinese quotes to standard quotes
    .replace(/^"+|"+$/g, '') // Remove leading/trailing quotes
    .trim();
}

class LocalToolsService {
  _catalogLoadingPromise = {}; // Cache for in-flight promises

  // --- REFACTORED PATH HELPERS ---

  /**
   * Converts a logical path (used by AI) to a physical path (used by fetch).
   * e.g., "characters/file.md" -> "/hsr_md/characters/file.md"
   * @private
   */
  _getPhysicalPathFromLogicalPath(logicalPath) {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return '';
    return `/domains/${currentDomain}/docs/${logicalPath}`;
  }

  /**
   * Converts a frontend router path (from index) to a logical path (for AI).
   * e.g., "/v2/hsr/category/characters/file" -> "characters/file.md"
   * @private
   */
  _getLogicalPathFromFrontendPath(frontendPath) {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!currentDomain) return '';
    // Removes the prefix and adds the .md extension
    const logical = frontendPath.replace(`/v2/${currentDomain}/category/`, '');
    return `${logical}.md`;
  }

  // --- END REFACTORED PATH HELPERS ---

  /**
   * Lists the content of a specific directory path from the catalog tree.
   * @param {string} path - The directory path to list. Defaults to '/'.
   */
  async listDocs(path = '/') {
    logger.log(`执行目录列表...`, { path });
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    
    try {
      await this.ensureCatalogReady();
      const catalogTree = this._catalogTreeCache[currentDomain];
      const pathParts = path.trim().replace(/^\/|\/$/g, '').split('/').filter(p => p);
      
      let currentLevel = catalogTree;
      for (const part of pathParts) {
        if (currentLevel && typeof currentLevel === 'object' && part in currentLevel) {
          currentLevel = currentLevel[part];
        } else {
          return `错误：路径 '${path}' 不存在。`;
        }
      }

      if (typeof currentLevel !== 'object' || currentLevel === null) {
        return `错误：路径 '${path}' 不是一个目录。`;
      }
      
      const normalizedBasePath = path.trim().replace(/\/$/, '');
      const finalPath = normalizedBasePath === '/' ? '' : normalizedBasePath;

      const results = Object.keys(currentLevel).map(key => {
        const fullPath = [finalPath, key].filter(Boolean).join('/');
        const type = currentLevel[key] === null ? 'file' : 'directory';
        return { path: fullPath, type: type };
      });

      logger.log(`目录列表成功: ${path}`, { count: results.length });
      return JSON.stringify(results, null, 2);

    } catch (error) {
      logger.error(`列出目录时失败: ${path}`, error);
      return `错误：无法列出目录 '${path}': ${error.message}`;
    }
  }
   /**
   * Resolves a partial file name to a full logical path by searching the catalog.
   * @private
   * @param {string} fileName - The file name (or partial path) to resolve.
   * @returns {Promise<string|null>} The full logical path, or null if not found.
   */
   async resolveLogicalPath(logicalPath) {
    try {
        await this.ensureCatalogReady();
    } catch (error) {
        logger.error(`[resolveLogicalPath] 无法加载目录树，路径解析中止:`, error);
        return null; // Cannot resolve if the catalog isn't loaded
    }

    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    const catalogTree = this._catalogTreeCache[currentDomain];
    if (!catalogTree) return null;

    const cleanPath = logicalPath.split('#')[0];
    const normalizedPath = cleanPath.trim().replace(/\\/g, '/');
    const pathParts = normalizedPath.split('/').filter(p => p);

    // --- 1. Attempt to resolve the full path directly ---
    let currentNode = catalogTree;
    let isValid = true;
    for (const part of pathParts) {
        if (currentNode && typeof currentNode === 'object' && part in currentNode) {
            currentNode = currentNode[part];
        } else {
            isValid = false;
            break;
        }
    }
    // If we reached the end and the final node is a file (null), the full path is valid.
    if (isValid && currentNode === null) {
        return normalizedPath;
    }

    // --- 2. Fallback: Search by filename only ---
    const justTheFileName = pathParts.length > 0 ? pathParts[pathParts.length - 1].toLowerCase() : null;
    if (!justTheFileName) return null; // No filename to search for

    const traverse = (node, currentPath) => {
        for (const key in node) {
            const newPath = currentPath ? `${currentPath}/${key}` : key;
            if (node[key] === null) { // It's a file
                if (key.toLowerCase() === justTheFileName || key.toLowerCase() === `${justTheFileName}.md`) {
                    return newPath;
                }
            } else if (typeof node[key] === 'object') { // It's a directory
                const found = traverse(node[key], newPath);
                if (found) return found;
            }
        }
        return null;
    };

    const foundPath = traverse(catalogTree, '');
    return foundPath;
}

  /**
   * Applies line range filtering to document content.
   * @private
   * @param {string} content - The full content of the document.
   * @param {string[]} lineRanges - An array of line ranges, e.g., ["10-20", "35-40"].
   * @returns {string} The filtered content with line numbers.
   */
  _applyLineRanges(content, lineRanges) {
    if (!lineRanges || lineRanges.length === 0) {
      return content;
    }

    const lines = content.split('\n');
    const selectedLines = new Set();
    
    for (const range of lineRanges) {
      const parts = range.split('-').map(Number);
      if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        const [start, end] = parts;
        
        // If the start of the range is already beyond the end of the file,
        // it's an invalid range, so we can just skip it.
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

  /**
   * Reads the content of one or more documents, with optional line range support.
   * @param {object[]} docRequests - An array of document request objects.
   * @param {string} docRequests[].path - The logical path to the document.
   * @param {string[]} [docRequests[].lineRanges] - Optional array of line ranges (e.g., ["10-20"]).
   */
  async readDoc(rawRequests) {
    // --- Compatibility Layer for backward compatibility ---
    let docRequests;
    if (typeof rawRequests === 'string') {
      // Handle single path string from legacy calls (e.g., DocViewer)
      docRequests = [{ path: rawRequests, lineRanges: [] }];
    } else if (Array.isArray(rawRequests) && rawRequests.every(item => typeof item === 'string')) {
      // Handle array of path strings from legacy calls
      docRequests = rawRequests.map(path => ({ path, lineRanges: [] }));
    } else {
      // Assume it's already in the new format: [{ path, lineRanges }]
      docRequests = rawRequests;
    }
    // --- End Compatibility Layer ---

    logger.log(`执行文档读取...`, { requests: docRequests });
    const dataStore = useDataStore();
    
    if (!docRequests || docRequests.length === 0) {
      return "错误：未提供任何文档读取请求。";
    }

    const contentPromises = docRequests.map(async (request) => {
        let { path, lineRanges } = request;
        const originalPath = path;
        let physicalPath;
        let fullContent;

        try {
            physicalPath = this._getPhysicalPathFromLogicalPath(path);
            fullContent = await dataStore.fetchMarkdownContent(physicalPath);

        } catch (initialError) {
            logger.log(`读取文档 '${path}' 首次尝试失败，将尝试路径解析...`);
            
            try {
                const justTheFileName = path.split('/').pop().split('\\').pop();
                if (!justTheFileName) throw initialError;

                const resolvedPath = await this.resolveLogicalPath(justTheFileName);

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
    
    const successfulContents = [];
    const failedPaths = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
          if (typeof result.value === 'string') {
              successfulContents.push(result.value);
          } else if (result.value && result.value.error) {
              // Handle our custom error object
              const { path: failedPath, error: errorMessage } = result.value;
              failedPaths.push(failedPath);
              logger.error(`读取文档失败 (settled): ${failedPath}`, { reason: errorMessage });
              successfulContents.push(`--- DOC START: ${failedPath} ---\n\n${errorMessage}\n\n--- DOC END: ${failedPath} ---`);
          }
      } else {
          // Handle unexpected rejections
          const failedPath = docRequests[index].path;
          failedPaths.push(failedPath);
          logger.error(`读取文档时发生意外的Promise拒绝: ${failedPath}`, { reason: result.reason });
          const errorMessage = `错误：处理文档 '${failedPath}' 时发生意外错误。`;
          successfulContents.push(`--- DOC START: ${failedPath} ---\n\n${errorMessage}\n\n--- DOC END: ${failedPath} ---`);
      }
    });

    return successfulContents.join('\n\n');
  }

  /**
    * Performs a single, non-OR search. Each file is processed independently.
    * @private
    */
   async _performSingleSearch(query) {
       query = _normalizeQuery(query);
       if (!query) return []; // Return empty if query becomes empty after normalization

       const dataStore = useDataStore();
       const appStore = useAppStore();
       const currentDomain = appStore.currentDomain;

       const queryBigrams = getBigrams(query);
       if (queryBigrams.length === 0) return [];

       const chunkPromises = queryBigrams.map(bigram => dataStore.fetchSearchChunk(currentDomain, bigram[0]));
       const chunks = await Promise.all(chunkPromises);
       
       const idSets = [];
       queryBigrams.forEach((bigram, index) => {
           const chunk = chunks[index];
           // Only add a set if it's valid and contains IDs
           if (chunk && chunk[bigram] && chunk[bigram].length > 0) {
               idSets.push(new Set(chunk[bigram]));
           }
       });

       // If no bigrams yielded any document IDs, there are no results.
       if (idSets.length === 0) return [];
       
       const intersection = idSets.reduce((acc, set) => new Set([...acc].filter(id => set.has(id))));
       if (intersection.size === 0) return [];

       const catalogMap = new Map(dataStore.indexData.map(item => [item.id, item]));
       const initialResults = Array.from(intersection).map(id => catalogMap.get(id)).filter(Boolean);

       if (initialResults.length === 0) return [];

       const results = [];
       const fileSnippetCount = new Map();

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

  /**
   * Performs an advanced search, supporting OR logic via '|'.
   * @param {string} query - The search query.
   */
   async searchDocs(query) {
    // 1. --- Validation and Initialization ---
    if (typeof query !== 'string' || !query.trim()) {
      const errorMsg = "错误：查询工具收到了无效或缺失的查询参数。";
      logger.error(errorMsg, { query });
      return errorMsg;
    }

    logger.log(`执行高级搜索...`, { query });
    const dataStore = useDataStore();
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;

    if (!dataStore.indexData || dataStore.indexData.length === 0 || dataStore.gameName !== currentDomain) {
      logger.log(`LocalTools: 索引数据缺失或域不匹配，为 '${currentDomain}' 重新加载...`);
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
               return []; // For an AND group, if one term fails, the group fails
           }
           
           // Intersect results within the AND group
           const docMap = new Map(); // path -> { snippets: [], firstResult: {} }
           
           // Initialize map with the first term's results
           for (const result of termResults[0]) {
               docMap.set(result.path, { snippets: [result], firstResult: result });
           }

           // Intersect with subsequent term results
           for (let i = 1; i < termResults.length; i++) {
               const currentResults = termResults[i];
               const currentPaths = new Set(currentResults.map(r => r.path));
               for (const path of docMap.keys()) {
                   if (!currentPaths.has(path)) {
                       docMap.delete(path);
                   } else {
                       // Add snippets from the current term's results for the intersecting path
                       const existing = docMap.get(path);
                       const newSnippets = currentResults.filter(r => r.path === path);
                       existing.snippets.push(...newSnippets);
                   }
               }
           }
           
           // Flatten the results from the map
           return Array.from(docMap.values()).flatMap(val => val.snippets);
       }));

       const allResults = allGroupResults.flat();

       const uniqueResults = new Map();
       for (const result of allResults) {
           const key = `${result.path}:${result.line}`;
           if (!uniqueResults.has(key)) {
               uniqueResults.set(key, result);
           }
       }
       let finalResults = Array.from(uniqueResults.values());

      // 3. --- Formatting and Return ---
      if (finalResults.length > 20) {
        finalResults = finalResults.slice(0, 20);
      }

      logger.log("高级搜索成功。", { count: finalResults.length });
      
      if (finalResults.length === 0) {
        return "未找到相关文档。";
      }
      
      // Sort results by path then by line number for consistent output
      finalResults.sort((a, b) => {
        if (a.path < b.path) return -1;
        if (a.path > b.path) return 1;
        return a.line - b.line;
      });
      
      return finalResults.map(r => `${r.path}\n  ${r.line}: ${r.snippet}`).join('\n\n');

    } catch (e) {
      logger.error("高级搜索时发生异常:", e);
      return `错误：在执行高级搜索时发生异常: ${e.message}`;
    }
   }

  /**
   * Retrieves metadata for a document, such as token count and line count.
   * @param {string} logicalPath - The logical path to the document.
   * @returns {Promise<{totalTokens: number, totalLines: number}|null>} Metadata object or null on error.
   */
  async getDocMetadata(logicalPath) {
    logger.log(`获取文档元数据...`, { path: logicalPath });
    const dataStore = useDataStore();
    // This needs the tokenizer, which is currently in agentService.
    // To avoid circular dependencies, we'll need to move the tokenizer to its own service.
    // For now, let's assume we have access to it.
    const tokenizer = (await import('./tokenizerService.js')).default;

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

  /**
   * Ensures the catalog tree for the current domain is loaded into the cache.
   * This method is idempotent and handles concurrent calls gracefully.
   * It uses a hybrid memory -> promise -> persistent cache strategy.
   * @private
   */
  async ensureCatalogReady() {
    const appStore = useAppStore();
    const currentDomain = appStore.currentDomain;
    if (!this._catalogTreeCache) this._catalogTreeCache = {};

    // 1. Check memory cache (fastest)
    if (this._catalogTreeCache[currentDomain]) {
      return;
    }

    // 2. Check for an in-flight promise to avoid race conditions
    if (this._catalogLoadingPromise[currentDomain]) {
      await this._catalogLoadingPromise[currentDomain];
      return;
    }

    // 3. Create a promise and store it. This is the core of the race condition prevention.
    const loadPromise = (async () => {
      try {
        // 3a. Check persistent cache (localforage)
        const cachedTree = await catalogStore.getItem(currentDomain);
        if (cachedTree) {
          logger.log(`目录树 for '${currentDomain}' 从持久化缓存中加载成功。`);
          this._catalogTreeCache[currentDomain] = cachedTree;
          return;
        }

        // 3b. If all caches miss, fetch from network
        const mapPath = `/domains/${currentDomain}/metadata/catalog.json`;
        logger.log(`目录树缓存未命中，正在为域 '${currentDomain}' 加载: ${mapPath}`);
        const response = await fetch(mapPath);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const tree = await response.json();

        // Store in both memory and persistent cache
        this._catalogTreeCache[currentDomain] = tree;
        await catalogStore.setItem(currentDomain, tree);

        logger.log(`目录树 for '${currentDomain}' 加载并缓存成功。`);
      } catch (error) {
        logger.error(`加载目录树失败 for '${currentDomain}':`, error);
        throw error; // Re-throw to let callers handle it
      } finally {
        // 4. Clean up the promise cache once loading is complete (or has failed)
        delete this._catalogLoadingPromise[currentDomain];
      }
    })();

    this._catalogLoadingPromise[currentDomain] = loadPromise;
    await loadPromise;
  }
}

const localToolsService = new LocalToolsService();
export default localToolsService;