import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Game } from './app';

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

// --- Store Definition ---
export const useDataStore = defineStore('data', () => {
  // --- State ---
  const isLoadingIndex = ref(false);
  const error = ref<string | null>(null);
  
  const indexData = ref<IndexItem[]>([]);
  const lastFetchedGame = ref<Game | null>(null);
  
  const searchChunkCache = ref<Record<string, SearchChunk>>({});
  const contentCache = ref<Record<string, string>>({}); // path -> markdown content

  // --- Actions ---
  
  /**
   * Fetches the index data for a specific game.
   * This action is idempotent: it only fetches data if it's not already loaded
   * for the current game, preventing multiple redundant requests.
   * @param game The game ('hsr' | 'gi') to load data for.
   */
  async function fetchIndex(game: Game) {
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

    } catch (e) {
      error.value = e instanceof Error ? e.message : '未知错误';
      console.error(e);
      // Clear old data on error
      indexData.value = [];
      lastFetchedGame.value = null;
    } finally {
      isLoadingIndex.value = false;
    }
  }

  async function fetchSearchChunk(game: Game, char: string): Promise<SearchChunk> {
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
    } catch(e) {
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
    } catch(e) {
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
  };
});