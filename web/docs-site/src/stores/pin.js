import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
export const usePinStore = defineStore('pin', () => {
    // --- State ---
    // Load initial state from localStorage
    const pinnedItems = ref(JSON.parse(localStorage.getItem('pinnedItems') || '[]'));
    // --- Actions ---
    function addPin(item) {
        if (!isPinned(item.path)) {
            pinnedItems.value.push(item);
        }
    }
    function removePin(itemPath) {
        pinnedItems.value = pinnedItems.value.filter(p => p.path !== itemPath);
    }
    function togglePin(item) {
        if (isPinned(item.path)) {
            removePin(item.path);
        }
        else {
            addPin(item);
        }
    }
    // --- Getters (as functions) ---
    function isPinned(itemPath) {
        return pinnedItems.value.some(p => p.path === itemPath);
    }
    // --- Watcher for localStorage persistence ---
    watch(pinnedItems, (newValue) => {
        localStorage.setItem('pinnedItems', JSON.stringify(newValue));
    }, { deep: true });
    return {
        pinnedItems,
        addPin,
        removePin,
        togglePin,
        isPinned,
    };
});
//# sourceMappingURL=pin.js.map