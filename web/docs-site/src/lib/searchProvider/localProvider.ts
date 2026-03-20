/**
 * LocalSearchProvider: 保留原有的前端本地搜索逻辑
 * 将 data.ts 和 localToolsService.ts 中的搜索逻辑包装为 SearchProvider 接口
 */
import type { IndexItem } from '@/features/app/stores/data';
import { useDataStore } from '@/features/app/stores/data';
import { useAppStore } from '@/features/app/stores/app';
import localToolsService from '@/features/agent/tools/implementations/localToolsService';
import type { SearchProvider, DocReadRequest } from './types';

/**
 * LocalSearchProvider 委托给现有的 store 和 service
 * 这是一个瘦包装层，实际逻辑仍在 data.ts 和 localToolsService.ts 中
 */
class LocalSearchProvider implements SearchProvider {
  constructor(
    private readonly getDataStore = useDataStore,
    private readonly getAppStore = useAppStore,
    private readonly toolsService = localToolsService
  ) {}

  private _ensureDomain(domain: string): void {
    const appStore = this.getAppStore();
    if (appStore.currentDomain !== domain) {
      appStore.currentDomain = domain;
    }
  }

  async searchCatalog(domain: string, query: string): Promise<IndexItem[]> {
    this._ensureDomain(domain);
    const dataStore = this.getDataStore();
    return dataStore.searchCatalog(query);
  }

  async searchDocs(
    domain: string,
    query: string,
    docPath?: string,
    options?: { maxResults?: number; generateSummary?: boolean }
  ): Promise<string> {
    this._ensureDomain(domain);
    return this.toolsService.searchDocs(query, docPath, options);
  }

  async readDoc(domain: string, rawRequests: string | string[] | DocReadRequest[]): Promise<string> {
    this._ensureDomain(domain);
    return this.toolsService.readDoc(rawRequests);
  }

  async fetchIndex(domain: string): Promise<IndexItem[]> {
    this._ensureDomain(domain);
    const dataStore = this.getDataStore();
    await dataStore.fetchIndex(domain);
    return dataStore.indexData;
  }

  async fetchMarkdownContent(domain: string, physicalPath: string): Promise<string> {
    this._ensureDomain(domain);
    const dataStore = this.getDataStore();
    return dataStore.fetchMarkdownContent(physicalPath);
  }

  async loadSearchIndex(domain: string): Promise<Map<string, number[]>> {
    this._ensureDomain(domain);
    const dataStore = this.getDataStore();
    return dataStore.loadSearchIndex(domain);
  }
}

export const localSearchProvider = new LocalSearchProvider();
