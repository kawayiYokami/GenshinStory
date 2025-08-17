import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

// Define the interface for a pinned item
export interface PinnedItem {
  path: string;
  name: string;
  type: string;
}

export const usePinStore = defineStore('pin', () => {
  // --- State ---
  // Load initial state from localStorage
  const pinnedItems = ref<PinnedItem[]>(
    JSON.parse(localStorage.getItem('pinnedItems') || '[]')
  );

  // --- Actions ---
  function addPin(item: PinnedItem) {
    if (!isPinned(item.path)) {
      pinnedItems.value.push(item);
    }
  }

  function removePin(itemPath: string) {
    pinnedItems.value = pinnedItems.value.filter(p => p.path !== itemPath);
  }

  function togglePin(item: PinnedItem) {
    if (isPinned(item.path)) {
      removePin(item.path);
    } else {
      addPin(item);
    }
  }

  // --- Getters (as functions) ---
  function isPinned(itemPath: string): boolean {
    return pinnedItems.value.some(p => p.path === itemPath);
  }

  // --- Watcher for localStorage persistence ---
  watch(
    pinnedItems,
    (newValue) => {
      localStorage.setItem('pinnedItems', JSON.stringify(newValue));
    },
    { deep: true }
  );

  return {
    pinnedItems,
    addPin,
    removePin,
    togglePin,
    isPinned,
  };
});