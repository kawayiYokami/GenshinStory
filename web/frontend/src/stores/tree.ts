import { defineStore } from 'pinia';
import { ref } from 'vue';

// Corresponds to the structure returned by the backend's /api/.../tree endpoints
export interface TreeNode {
  key: string;
  label: string;
  isLeaf: boolean;
  children?: TreeNode[];
  data: {
    type: string;
    id: string | number;
  };
}

export const useTreeStore = defineStore('tree', () => {
  // --- State ---

  // Stores the fetched tree data, keyed by item type (e.g., 'quest', 'character')
  const trees = ref<{ [itemType: string]: TreeNode[] }>({});

  // Tracks loading state for different tree types
  const isLoading = ref<{ [key: string]: boolean }>({});

  // Tracks any errors that occur during fetching
  const error = ref<{ [key: string]: string | null }>({});


  // --- Actions ---

  /**
   * Fetches the tree structure for a given item type from the backend.
   * If the data is already in the cache, it will not fetch again.
   * @param {string} itemType - The type of item to fetch (e.g., 'quest', 'character').
   * @param {boolean} force - Whether to force a refetch even if data is cached.
   */
  async function fetchTree(itemType: string, force: boolean = false) {
    if (!itemType) return;
    if (trees.value[itemType] && !force) {
      return; // Already cached
    }

    isLoading.value[itemType] = true;
    error.value[itemType] = null;

    try {
      const response = await fetch(`/api/${itemType}/tree`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch ${itemType} tree`);
      }
      const data: TreeNode[] = await response.json();
      trees.value[itemType] = data;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : `An unknown error occurred.`;
      error.value[itemType] = errorMessage;
      console.error(`Failed to fetch tree for ${itemType}:`, e);
      trees.value[itemType] = []; // Clear or set to empty on error
    } finally {
      isLoading.value[itemType] = false;
    }
  }

  return {
    trees,
    isLoading,
    error,
    fetchTree,
  };
});