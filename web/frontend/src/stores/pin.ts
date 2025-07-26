import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export interface PinnedItem {
  itemType: string;
  id: string;
  name: string;
  // The target URL, which contains all context needed to restore the view.
  // e.g., '/item/quest/12345?highlight=keyword'
  targetUrl: string; 
}

export const usePinStore = defineStore('pin', () => {
  // --- State ---
  const pinnedItems = ref<PinnedItem[]>(JSON.parse(localStorage.getItem('pinnedItems') || '[]'));

  // --- Getters ---
  const isPinned = computed(() => {
    return (itemType: string, itemId: string) =>
      pinnedItems.value.some(p => p.itemType === itemType && p.id === itemId);
  });

  // --- Actions ---
  function addPin(item: PinnedItem) {
    if (!isPinned.value(item.itemType, item.id)) {
      pinnedItems.value.push(item);
      _persist();
    }
  }

  function removePin(itemType: string, itemId: string) {
    const index = pinnedItems.value.findIndex(p => p.itemType === itemType && p.id === itemId);
    if (index > -1) {
      pinnedItems.value.splice(index, 1);
      _persist();
    }
  }

  function togglePin(item: PinnedItem) {
    if (isPinned.value(item.itemType, item.id)) {
      removePin(item.itemType, item.id);
    } else {
      addPin(item);
    }
  }

  function _persist() {
    localStorage.setItem('pinnedItems', JSON.stringify(pinnedItems.value));
  }

  return {
    pinnedItems,
    isPinned,
    addPin,
    removePin,
    togglePin,
  };
});