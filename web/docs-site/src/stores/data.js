import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAppStore } from './app'; // Import app store

// --- Private Helpers ---
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


// --- Store Definition ---
export const useDataStore = defineStore('data', () => {
    const appStore = useAppStore();

    // --- State ---
    const isLoadingIndex = ref(false);
    const error = ref(null);
    const indexData = ref([]);
    const lastFetchedGame = ref(null);
    const searchChunkCache = ref({});
    const contentCache = ref({}); // path -> markdown content

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
    async function searchCatalog(query) {
        if (!query.trim() || indexData.value.length === 0) {
            return [];
        }

        try {
            const queryBigrams = getBigrams(query);
            if (queryBigrams.length === 0) return [];

            // 1. Fetch all needed chunks in parallel
            const chunkPromises = queryBigrams.map(bigram => fetchSearchChunk(appStore.currentGame, bigram[0]));
            const chunks = await Promise.all(chunkPromises);

            // 2. Get ID sets for each bigram
            const idSets = [];
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
            const finalResults = [];
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
     * Fetches the index data for a specific game.
     * This action is idempotent: it only fetches data if it's not already loaded
     * for the current game, preventing multiple redundant requests.
     * @param game The game ('hsr' | 'gi') to load data for.
     */
    async function fetchIndex(game) {
        // 1. Do nothing if data for the current game is already loaded.
        if (lastFetchedGame.value === game && indexData.value.length > 0) {
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
            const response = await fetch(`/index_${game}.json`);
            if (!response.ok) {
                throw new Error(`索引文件 index_${game}.json 加载失败: ${response.statusText}`);
            }
            const data = await response.json();
            indexData.value = data;
            lastFetchedGame.value = game;
            // Clear caches when game changes
            searchChunkCache.value = {};
            contentCache.value = {};
        }
        catch (e) {
            error.value = e instanceof Error ? e.message : '未知错误';
            console.error(e);
            // Clear old data on error
            indexData.value = [];
            lastFetchedGame.value = null;
        }
        finally {
            isLoadingIndex.value = false;
        }
    }
    async function fetchSearchChunk(game, char) {
        const cacheKey = `${game}_${char}`;
        if (searchChunkCache.value[cacheKey]) {
            return searchChunkCache.value[cacheKey];
        }
        try {
            const searchDir = game === 'hsr' ? 'search_hsr' : 'search';
            const response = await fetch(`/${searchDir}/${char}.json`);
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
    async function fetchMarkdownContent(path) {
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
//# sourceMappingURL=data.js.map