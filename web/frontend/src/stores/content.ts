import { defineStore } from 'pinia';
import { ref } from 'vue';

// This store is now solely responsible for fetching and caching raw content.
export const useContentStore = defineStore('content', () => {
  // --- State ---
  // A cache for already fetched markdown content to avoid redundant API calls.
  const contentCache = ref(new Map<string, string>());
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Actions ---

  /**
   * Fetches the markdown content for a specific item, using a cache.
   * @param {string} itemType - The type of the item (e.g., 'quest', 'weapon').
   * @param {string} itemId - The ID of the item.
   * @returns {Promise<string>} The raw markdown content.
   */
  async function fetchContent(itemType: string, itemId: string): Promise<string> {
    const cacheKey = `${itemType}-${itemId}`;
    if (contentCache.value.has(cacheKey)) {
      return contentCache.value.get(cacheKey)!;
    }

    if (!itemType || !itemId) {
      return Promise.reject('Invalid item type or ID.');
    }

    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/${itemType.toLowerCase()}/${itemId}/content`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const rawMarkdown = await response.text();
      contentCache.value.set(cacheKey, rawMarkdown); // Cache the result
      return rawMarkdown;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : `获取 ${itemType} 内容失败`;
      error.value = errorMessage;
      console.error(e);
      return Promise.reject(errorMessage);
    } finally {
      isLoading.value = false;
    }
  }

  return {
    isLoading,
    error,
    fetchContent,
  };
});