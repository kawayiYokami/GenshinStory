import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAppStore } from './app'; // Import app store
import type { Domain } from './app';
import { isBackendMode, backendSearchProvider } from '@/lib/searchProvider';

// 仅在 local 模式下需要 msgpack
let msgpack: typeof import('msgpack-lite') | null = null;
if (!isBackendMode()) {
    import('msgpack-lite').then(m => { msgpack = m; });
}

// --- Type Definitions ---
export interface IndexItem {
  id: number;
  name: string;
  type: string;
  path: string;
  score?: number;
  rarity?: number; // Make rarity optional to handle all cases
  // Add other potential fields if they exist in your index
  [key: string]: any;
}

export type SearchChunk = Record<string, number[]>;

// --- 差值解码函数 (仅 local 模式使用) ---
function deltaDecode(deltas: number[]): number[] {
    if (!deltas.length) return [];
    const sortedIds = [deltas[0]];
    for (let i = 1; i < deltas.length; i++) {
        sortedIds.push(sortedIds[i-1] + deltas[i]);
    }
    return sortedIds;
}

// --- Private Helpers (仅 local 模式使用) ---
/**
 * 将字符串切分为二字词组 (bigrams)
 * @param {string} text - The input text.
 * @returns {string[]} An array of bigrams.
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


// --- Store Definition ---
export const useDataStore = defineStore('data', () => {
    const appStore = useAppStore();

    // --- State ---
    const isLoadingIndex = ref(false);
    const error = ref<string | null>(null);
    const indexData = ref<IndexItem[]>([]);
    const lastFetchedDomain = ref<string | null>(null);
    const searchIndexCache = ref<Map<string, number[]> | null>(null); // 全局搜索索引缓存 (仅 local 模式)
    const contentCache = ref<Record<string, string>>({}); // path -> markdown content

    const catalogMap = computed(() => {
        return new Map(indexData.value.map(item => [item.id, item]));
    });

    // --- Actions ---
    /**
     * 一次性加载搜索索引（差值编码+MessagePack格式）
     * 仅在 local 模式下使用
     */
    async function loadSearchIndex(domain: string): Promise<Map<string, number[]>> {
        if (isBackendMode()) {
            return new Map();
        }

        if (searchIndexCache.value) {
            return searchIndexCache.value;
        }

        try {
            // 1. 加载索引文件
            const response = await fetch(`/domains/${domain}/metadata/search/index.msg`);
            if (!response.ok) {
                throw new Error(`Failed to load search index: ${response.status} ${response.statusText}`);
            }

            const arrayBuffer = await response.arrayBuffer();

            // 2. 直接MessagePack解码
            if (!msgpack) {
                msgpack = await import('msgpack-lite');
            }
            const uint8Array = new Uint8Array(arrayBuffer);
            const chunkedData = msgpack.decode(uint8Array) as Record<string, Record<string, number[]>>;

            // 3. 差值解码并合并所有分片
            searchIndexCache.value = new Map();
            for (const chunk of Object.values(chunkedData)) {
                for (const [keyword, deltas] of Object.entries(chunk)) {
                    const ids = deltaDecode(deltas);
                    searchIndexCache.value.set(keyword, ids);
                }
            }

            return searchIndexCache.value;

        } catch (e) {
            console.error('搜索索引加载失败:', e);
            return new Map();
        }
    }

    /**
     * 在内存中执行搜索（基于已加载的完整索引）
     * 仅在 local 模式下使用
     */
    function searchInMemory(query: string, searchIndex: Map<string, number[]>): number[] {
        const bigrams = getBigrams(query);

        if (bigrams.length === 0) return [];

        const idSets: Set<number>[] = [];

        // 获取每个bigram的ID集合
        for (const bigram of bigrams) {
            const ids = searchIndex.get(bigram);
            if (ids && ids.length > 0) {
                idSets.push(new Set(ids));
            }
        }

        if (idSets.length === 0) return [];

        const intersectionSet = idSets.reduce((acc, set) =>
            new Set([...acc].filter(id => set.has(id)))
        );

        return Array.from(intersectionSet);
    }

    /**
     * Searches the catalog index based on a query.
     * Backend 模式调用后端 API，Local 模式使用内存搜索。
     */
    async function searchCatalog(query: string): Promise<IndexItem[]> {
        if (!query.trim()) {
            return [];
        }

        try {
            if (!appStore.currentDomain) {
                throw new Error("Current domain is not set.");
            }

            // ===== Backend 模式 =====
            if (isBackendMode()) {
                return await backendSearchProvider.searchCatalog(appStore.currentDomain, query);
            }

            // ===== Local 模式 =====
            if (indexData.value.length === 0) {
                return [];
            }

            const searchIndex = await loadSearchIndex(appStore.currentDomain);
            const intersectionIds = searchInMemory(query, searchIndex);

            const finalResults: IndexItem[] = [];
            intersectionIds.forEach(id => {
                const item = catalogMap.value.get(id);
                if (item) {
                    finalResults.push(item);
                }
            });

            return finalResults;

        } catch (e) {
            error.value = e instanceof Error ? e.message : '搜索时发生未知错误';
            console.error("Search catalog error:", e);
            return [];
        }
    }


    /**
     * Fetches the index data for a specific domain.
     * Backend 模式从后端 API 加载，Local 模式从静态文件加载。
     */
    async function fetchIndex(domain: string) {
        // 1. Do nothing if data for the current domain is already loaded.
        if (lastFetchedDomain.value === domain && indexData.value.length > 0) {
            return;
        }
        // 2. Do nothing if a fetch is already in progress.
        if (isLoadingIndex.value) {
            return;
        }
        // 3. Start fetching
        isLoadingIndex.value = true;
        error.value = null;
        try {
            let normalizedData: IndexItem[];

            if (isBackendMode()) {
                // ===== Backend 模式 =====
                normalizedData = await backendSearchProvider.fetchIndex(domain);
            } else {
                // ===== Local 模式 =====
                const url = `/domains/${domain}/metadata/index.json`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Failed to load index.json: ${response.status} ${response.statusText}`);
                }
                const data = await response.json();
                normalizedData = data.map((item: any) => ({
                    ...item,
                    id: typeof item.id === 'string' ? parseInt(item.id, 10) : item.id
                }));
            }

            indexData.value = normalizedData;
            lastFetchedDomain.value = domain;

            // Clear caches when domain changes
            searchIndexCache.value = null;
            contentCache.value = {};

        }
        catch (e) {
            error.value = e instanceof Error ? e.message : 'Unknown error';
            console.error(`[DataStore] Failed to fetch index for domain '${domain}':`, e);
            indexData.value = [];
            lastFetchedDomain.value = null;
            searchIndexCache.value = null;
            contentCache.value = {};
        }
        finally {
            isLoadingIndex.value = false;
        }
    }

    async function fetchMarkdownContent(path: string): Promise<string> {
        if (contentCache.value[path]) {
            return contentCache.value[path];
        }
        try {
            // ===== Backend 模式 =====
            if (isBackendMode() && appStore.currentDomain) {
                const content = await backendSearchProvider.fetchMarkdownContent(appStore.currentDomain, path);
                contentCache.value[path] = content;
                return content;
            }

            // ===== Local 模式 =====
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(response.status === 404 ? `文件未找到: ${path}` : `Markdown 文件加载失败: ${response.statusText}`);
            }
            const contentType = (response.headers.get('content-type') || '').toLowerCase();
            const markdown = await response.text();

            const looksLikeHtmlShell = /^\s*<!doctype html>/i.test(markdown) || /^\s*<html/i.test(markdown);
            if (contentType.includes('text/html') || looksLikeHtmlShell) {
                throw new Error(`读取文档失败：路径 '${path}' 返回了 HTML 页面，请检查文档路径是否被错误拼接或被路由回退。`);
            }

            contentCache.value[path] = markdown;
            return markdown;
        }
        catch (e) {
            console.error(e);
            throw e;
        }
    }
    return {
        isLoading: isLoadingIndex,
        error,
        indexData,
        fetchIndex,
        fetchMarkdownContent,
        searchCatalog,
        loadSearchIndex,
        catalogMap,
    };
});
