/**
 * BackendSearchProvider: 通过后端 API 执行搜索和文档读取
 */
import type { IndexItem } from '@/features/app/stores/data';
import type { SearchProvider, DocReadRequest } from './types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '/api';
const API_BASE = BACKEND_URL.endsWith('/api') ? BACKEND_URL : `${BACKEND_URL}/api`;

class BackendSearchProvider implements SearchProvider {
  private indexCache: Map<string, IndexItem[]> = new Map();
  private contentCache: Map<string, string> = new Map();

  async searchCatalog(domain: string, query: string): Promise<IndexItem[]> {
    if (!query.trim()) return [];

    const params = new URLSearchParams({
      query,
      mode: 'catalog',
      maxResults: '100',
    });
    const resp = await fetch(`${API_BASE}/${domain}/search?${params}`);
    if (!resp.ok) return [];

    const data = await resp.json();
    // 后端返回的 results 字段需要映射成 IndexItem 格式
    return (data.results || []).map((r: any) => ({
      id: r.id,
      name: r.name,
      type: r.type,
      path: r.path,
      category: r.category,
      score: typeof r.score === 'number' ? r.score : undefined,
    }));
  }

  async searchDocs(
    domain: string,
    query: string,
    docPath?: string,
    options?: { maxResults?: number; generateSummary?: boolean }
  ): Promise<string> {
    if (!query.trim()) {
      return JSON.stringify({ tool: 'search_docs', query, message: '请输入有效的查询词' });
    }

    const params = new URLSearchParams({
      query,
      mode: 'docs',
      maxResults: String(options?.maxResults ?? 50),
      generateSummary: String(options?.generateSummary ?? true),
    });
    if (docPath) params.set('path', docPath);

    const resp = await fetch(`${API_BASE}/${domain}/search?${params}`);
    if (!resp.ok) {
      return JSON.stringify({ tool: 'search_docs', query, error: `后端请求失败: ${resp.status}` });
    }

    const data = await resp.json();
    return JSON.stringify(data);
  }

  async readDoc(domain: string, rawRequests: string | string[] | DocReadRequest[]): Promise<string> {
    let docRequests: DocReadRequest[];
    if (typeof rawRequests === 'string') {
      docRequests = [{ path: rawRequests, lineRanges: [], preserveMarkdown: false }];
    } else if (Array.isArray(rawRequests) && rawRequests.every(item => typeof item === 'string')) {
      docRequests = (rawRequests as string[]).map(path => ({ path, lineRanges: [], preserveMarkdown: false }));
    } else {
      docRequests = rawRequests as DocReadRequest[];
    }

    if (!docRequests || docRequests.length === 0) {
      return JSON.stringify({ error: '错误：未提供任何文档读取请求' });
    }

    const results = await Promise.allSettled(
      docRequests.map(async (req) => {
        const params = new URLSearchParams({ path: req.path });
        if (req.lineRanges && req.lineRanges.length > 0) {
          for (const range of req.lineRanges) {
            params.append('line_range', range);
          }
        }
        if (req.preserveMarkdown) {
          params.set('preserve_markdown', 'true');
        }

        const resp = await fetch(`${API_BASE}/${domain}/doc?${params}`);
        if (!resp.ok) {
          const detail = await resp.text();
          return { path: req.path, error: `读取失败: ${detail}` };
        }
        return await resp.json();
      })
    );

    const docs = results.map((r, i) => {
      if (r.status === 'fulfilled') return r.value;
      return { path: docRequests[i].path, error: '请求失败' };
    });

    return JSON.stringify({ docs });
  }

  async resolveSourceLink(
    domain: string,
    title: string,
    options?: { k?: number; minScore?: number }
  ): Promise<string> {
    const normalizedTitle = String(title || '').trim();
    if (!normalizedTitle) {
      return JSON.stringify({
        tool: 'resolve_source_link',
        found: false,
        message: '请输入有效的文件名或路径',
      });
    }

    const params = new URLSearchParams({
      title: normalizedTitle,
      k: String(options?.k ?? 3),
      minScore: String(options?.minScore ?? 100),
    });

    const resp = await fetch(`${API_BASE}/${domain}/resolve-link?${params}`);
    if (!resp.ok) {
      return JSON.stringify({
        tool: 'resolve_source_link',
        found: false,
        title: normalizedTitle,
        error: `后端请求失败: ${resp.status}`,
      });
    }

    const data = await resp.json();
    return JSON.stringify({
      tool: 'resolve_source_link',
      ...data,
    });
  }

  async fetchIndex(domain: string): Promise<IndexItem[]> {
    if (this.indexCache.has(domain)) {
      return this.indexCache.get(domain)!;
    }

    const resp = await fetch(`${API_BASE}/${domain}/index`);
    if (!resp.ok) throw new Error(`加载索引失败: ${resp.status}`);

    const data: IndexItem[] = await resp.json();
    const normalized = data.map((item: any) => ({
      ...item,
      id: (() => {
        const parsed = typeof item.id === 'string'
          ? parseInt(item.id, 10)
          : (typeof item.id === 'number' ? item.id : NaN);
        return Number.isNaN(parsed) ? 0 : parsed;
      })(),
    }));
    this.indexCache.set(domain, normalized);
    return normalized;
  }

  async fetchMarkdownContent(domain: string, physicalPath: string): Promise<string> {
    const cacheKey = `${domain}:${physicalPath}`;
    if (this.contentCache.has(cacheKey)) {
      return this.contentCache.get(cacheKey)!;
    }

    const params = new URLSearchParams({ path: physicalPath });
    const resp = await fetch(`${API_BASE}/${domain}/doc/raw?${params}`);
    if (!resp.ok) throw new Error(`文档加载失败: ${resp.status}`);

    const content = await resp.text();
    this.contentCache.set(cacheKey, content);
    return content;
  }

  async loadSearchIndex(_domain: string): Promise<Map<string, number[]>> {
    // 后端模式不需要加载搜索索引
    return new Map();
  }

  /** 切换域时清空缓存 */
  clearCache(): void {
    this.indexCache.clear();
    this.contentCache.clear();
  }
}

export const backendSearchProvider = new BackendSearchProvider();
