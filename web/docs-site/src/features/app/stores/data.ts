import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAppStore } from './app'; // Import app store
import type { Domain } from './app';

// --- Type Definitions ---
export interface IndexItem {
  id: number | string;
  name: string;
  type: string;
  path: string;
  rarity?: number; // Make rarity optional to handle all cases
  // Add other potential fields if they exist in your index
  [key: string]: any;
}

export type SearchChunk = Record<string, number[]>;

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
    const searchChunkCache = ref<Record<string, SearchChunk>>({});
    const contentCache = ref<Record<string, string>>({}); // path -> markdown content

    const catalogMap = computed(() => {
        return new Map(indexData.value.map(item => [item.id, item]));
    });

    // --- Actions ---
    /**
     * Searches the catalog index based on a query.
     * This is the centralized search logic for the entire app.
     * @param {string} query - The search query.
     * @returns {Promise<Array>} A promise that resolves to an array of result items.
     */
    async function searchCatalog(query: string): Promise<IndexItem[]> {
        if (!query.trim() || indexData.value.length === 0) {
            return [];
        }

        try {
            const queryBigrams = getBigrams(query);
            if (queryBigrams.length === 0) return [];

            // 1. Fetch all needed chunks in parallel
            if (!appStore.currentDomain) {
                throw new Error("Current domain is not set.");
            }
            const chunkPromises = queryBigrams.map(bigram => fetchSearchChunk(appStore.currentDomain!, bigram[0]));
            const chunks = await Promise.all(chunkPromises);

            // 2. Get ID sets for each bigram
            const idSets: Set<number>[] = [];
            queryBigrams.forEach((bigram, index) => {
                const chunk = chunks[index];
                if (chunk && chunk[bigram]) {
                    idSets.push(new Set(chunk[bigram]));
                }
            });

            if (idSets.length === 0) {
                return [];
            }

            // 3. Find the intersection of all ID sets (AND logic)
            const intersection = idSets.reduce((acc, set) => new Set([...acc].filter(id => set.has(id))));

            // 4. Map IDs to full catalog items
            const finalResults: IndexItem[] = [];
            intersection.forEach(id => {
                const item = catalogMap.value.get(id);
                if (item) {
                    finalResults.push(item);
                }
            });
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

            console.log(`[DataStore] 📦 加载了 ${data.length} 个条目`);

            console.time(`[DataStore] 状态更新-${domain}`);
            indexData.value = data;
            lastFetchedDomain.value = domain;
            console.timeEnd(`[DataStore] 状态更新-${domain}`);

            // Clear caches when domain changes
            searchChunkCache.value = {};
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
    async function fetchSearchChunk(domain: string, char: string): Promise<SearchChunk> {
        const cacheKey = `${domain}_${char}`;
        if (searchChunkCache.value[cacheKey]) {
            return searchChunkCache.value[cacheKey];
        }
        try {
            const response = await fetch(`/domains/${domain}/metadata/search/${char}.json`);
            if (response.ok) {
                const chunk = await response.json();
                searchChunkCache.value[cacheKey] = chunk;
                return chunk;
            }
            if (response.status === 404) {
                searchChunkCache.value[cacheKey] = {}; // Cache empty object for 404s
                return {};
            }
            throw new Error(`无法加载分片 ${char}.json`);
        }
        catch (e) {
            console.error(e);
            searchChunkCache.value[cacheKey] = {}; // Cache empty on error
            return {};
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
        fetchSearchChunk,
        fetchMarkdownContent,
        searchCatalog, // Expose the new search action
    };
});