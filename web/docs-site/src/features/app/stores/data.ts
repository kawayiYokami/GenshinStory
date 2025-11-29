import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAppStore } from './app'; // Import app store
import type { Domain } from './app';
import * as msgpack from 'msgpack-lite';

// --- Type Definitions ---
export interface IndexItem {
  id: number;
  name: string;
  type: string;
  path: string;
  rarity?: number; // Make rarity optional to handle all cases
  // Add other potential fields if they exist in your index
  [key: string]: any;
}

export type SearchChunk = Record<string, number[]>;

// --- 差值解码函数 ---
function deltaDecode(deltas: number[]): number[] {
    if (!deltas.length) return [];
    const sortedIds = [deltas[0]];
    for (let i = 1; i < deltas.length; i++) {
        sortedIds.push(sortedIds[i-1] + deltas[i]);
    }
    return sortedIds;
}

// --- Private Helpers ---
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
    const searchIndexCache = ref<Map<string, number[]> | null>(null); // 全局搜索索引缓存
    const contentCache = ref<Record<string, string>>({}); // path -> markdown content

    const catalogMap = computed(() => {
        return new Map(indexData.value.map(item => [item.id, item]));
    });

    // --- Actions ---
    /**
     * 一次性加载搜索索引（差值编码+MessagePack格式）
     */
    async function loadSearchIndex(domain: string): Promise<Map<string, number[]>> {
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

            console.log(`搜索索引加载完成: ${domain}, 词条数量: ${searchIndexCache.value.size}`);
            return searchIndexCache.value;

        } catch (e) {
            console.error('搜索索引加载失败:', e);
            return new Map();
        }
    }

    /**
     * 在内存中执行搜索（基于已加载的完整索引）
     */
    function searchInMemory(query: string, searchIndex: Map<string, number[]>): number[] {
        const bigrams = getBigrams(query);
        console.log('Bigrams for query:', query, '=>', bigrams);

        if (bigrams.length === 0) return [];

        const idSets: Set<number>[] = [];

        // 获取每个bigram的ID集合
        for (const bigram of bigrams) {
            const ids = searchIndex.get(bigram);
            console.log(`Bigram "${bigram}":`, ids ? `${ids.length} IDs` : 'Not found');
            if (ids && ids.length > 0) {
                idSets.push(new Set(ids));
            }
        }

        console.log('Total idSets found:', idSets.length);

        if (idSets.length === 0) return [];

        const intersectionSet = idSets.reduce((acc, set) =>
            new Set([...acc].filter(id => set.has(id)))
        );

        const intersection = Array.from(intersectionSet);
        console.log('Intersection result:', intersection);
        return intersection;
    }
    /**
     * Searches the catalog index based on a query (using optimized in-memory search).
     * @param {string} query - The search query.
     * @returns {Promise<Array>} A promise that resolves to an array of result items.
     */
    async function searchCatalog(query: string): Promise<IndexItem[]> {
        if (!query.trim() || indexData.value.length === 0) {
            return [];
        }

        console.log('Starting search for query:', query);

        try {
            if (!appStore.currentDomain) {
                throw new Error("Current domain is not set.");
            }

            // 1. 确保搜索索引已加载
            console.log('Loading search index for domain:', appStore.currentDomain);
            const searchIndex = await loadSearchIndex(appStore.currentDomain);
            console.log('Search index loaded, size:', searchIndex.size);

            // 2. 在内存中执行搜索
            const intersectionIds = searchInMemory(query, searchIndex);
            console.log('Search completed, found IDs:', intersectionIds.length);

            // 3. 映射ID到完整的catalog条目
            const finalResults: IndexItem[] = [];
            intersectionIds.forEach(id => {
                const item = catalogMap.value.get(id);
                if (item) {
                    finalResults.push(item);
                } else {
                    console.log('ID', id, 'not found in catalog');
                }
            });

            console.log('Final results count:', finalResults.length);
            return finalResults;

        } catch (e) {
            error.value = e instanceof Error ? e.message : '搜索时发生未知错误';
            console.error("Search catalog error:", e);
            return []; // Return empty array on error
        }
    }


    /**
     * Fetches the index data for a specific domain.
     * This action is idempotent: it only fetches data if it's not already loaded
     * for the current domain, preventing multiple redundant requests.
     * @param domain The domain ('hsr' | 'gi') to load data for.
     */
    async function fetchIndex(domain: string) {
        // 1. Do nothing if data for the current domain is already loaded.
        if (lastFetchedDomain.value === domain && indexData.value.length > 0) {
            console.log(`[DataStore] Index for domain '${domain}' is already loaded.`);
            return;
        }
        // 2. Do nothing if a fetch is already in progress.
        if (isLoadingIndex.value) {
            console.log(`[DataStore] Index fetch for domain '${domain}' is already in progress.`);
            return;
        }
        // 3. Start fetching
        console.log(`[DataStore] 🔍 开始加载索引: ${domain}`);
        console.time(`[DataStore] 完整索引加载-${domain}`);
        isLoadingIndex.value = true;
        error.value = null;
        try {
            const url = `/domains/${domain}/metadata/index.json`;
            console.log(`[DataStore] 📡 请求URL: ${url}`);
            console.time(`[DataStore] 网络请求-${domain}`);

            const response = await fetch(url);
            console.timeEnd(`[DataStore] 网络请求-${domain}`);
            if (!response.ok) {
                throw new Error(`Failed to load index.json: ${response.status} ${response.statusText}`);
            }

            console.time(`[DataStore] JSON解析-${domain}`);
            const data = await response.json();
            console.timeEnd(`[DataStore] JSON解析-${domain}`);

            // Ensure all IDs are numbers for type consistency
            const normalizedData = data.map((item: any) => ({
                ...item,
                id: typeof item.id === 'string' ? parseInt(item.id, 10) : item.id
            }));

            console.log(`[DataStore] 📦 加载了 ${normalizedData.length} 个条目`);

            console.time(`[DataStore] 状态更新-${domain}`);
            indexData.value = normalizedData;
            lastFetchedDomain.value = domain;
            console.timeEnd(`[DataStore] 状态更新-${domain}`);

            // Clear caches when domain changes
            searchIndexCache.value = null;
            contentCache.value = {};

            console.log(`[DataStore] ✅ 索引加载成功: ${domain}`);
            console.timeEnd(`[DataStore] 完整索引加载-${domain}`);
        }
        catch (e) {
            error.value = e instanceof Error ? e.message : 'Unknown error';
            console.error(`[DataStore] Failed to fetch index for domain '${domain}':`, e);
            // Clear old data on error
            indexData.value = [];
            lastFetchedDomain.value = null;
        }
        finally {
            isLoadingIndex.value = false;
            console.log(`[DataStore] Finished fetching index for domain '${domain}'.`);
        }
    }

    async function fetchMarkdownContent(path: string): Promise<string> {
        if (contentCache.value[path]) {
            return contentCache.value[path];
        }
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(response.status === 404 ? `文件未找到: ${path}` : `Markdown 文件加载失败: ${response.statusText}`);
            }
            const markdown = await response.text();
            contentCache.value[path] = markdown;
            return markdown;
        }
        catch (e) {
            console.error(e);
            throw e; // Re-throw to be caught by the component
        }
    }
    return {
        isLoading: isLoadingIndex, // Keep original name for simplicity in components
        error,
        indexData,
        fetchIndex,
        fetchMarkdownContent,
        searchCatalog, // Expose the new search action
        loadSearchIndex, // Expose the new index loading function
        catalogMap, // Expose the catalog map for direct access
    };
});