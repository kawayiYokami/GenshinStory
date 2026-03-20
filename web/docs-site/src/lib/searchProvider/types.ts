/**
 * SearchProvider 接口定义
 * 统一前端本地搜索和后端 API 搜索的接口
 */
import type { IndexItem } from '@/features/app/stores/data';

export interface CatalogSearchResult {
  items: IndexItem[];
}

export interface DocSearchResult {
  tool: string;
  query: string;
  results?: DocSearchHit[];
  grouped?: boolean;
  docPath?: string;
  message?: string;
  error?: string;
}

export interface DocSearchHit {
  path: string;
  totalLines?: number;
  totalTokens?: number;
  hits: { line: number; snippet: string }[];
  hitCount: number;
}

export interface DocReadResult {
  path: string;
  content?: string;
  totalLines?: number;
  totalTokens?: number;
  returnedTokens?: number;
  remainingTokens?: number;
  lineRange?: string;
  error?: string;
}

export interface DocReadRequest {
  path: string;
  lineRanges?: string[];
  preserveMarkdown?: boolean;
}

/**
 * SearchProvider 接口
 * 所有搜索和文档读取操作通过此接口抽象
 */
export interface SearchProvider {
  /** 目录搜索（SearchView UI 使用） */
  searchCatalog(domain: string, query: string): Promise<IndexItem[]>;

  /** 深度文档搜索（Agent search_docs 工具使用） */
  searchDocs(
    domain: string,
    query: string,
    docPath?: string,
    options?: { maxResults?: number; generateSummary?: boolean }
  ): Promise<string>;

  /** 读取文档 */
  readDoc(domain: string, rawRequests: string | string[] | DocReadRequest[]): Promise<string>;

  /** 获取目录索引 */
  fetchIndex(domain: string): Promise<IndexItem[]>;

  /** 获取 Markdown 原始内容 */
  fetchMarkdownContent(domain: string, physicalPath: string): Promise<string>;

  /** 加载搜索索引（仅 local 模式需要，backend 模式返回空 Map） */
  loadSearchIndex(domain: string): Promise<Map<string, number[]>>;
}
