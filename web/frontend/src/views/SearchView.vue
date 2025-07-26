<template>
  <SearchPane
    :list="searchResults"
    :is-loading="isLoading"
    v-model:search-query="keyword"
    :expanded-groups="expandedGroups"
    :selected-item="selectedItem"
    @search-clicked="performSearch"
    @toggle-group="toggleGroup"
    @select-item="handleSelectItem"
  />
  <router-view />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import SearchPane from '@/components/SearchPane.vue';
import type { ListGroup, ListItem } from '@/stores/data';

// --- Component State ---
const route = useRoute();
const router = useRouter();
const keyword = ref('');
const searchResults = ref<ListGroup[]>([]);
const isLoading = ref(false);
const expandedGroups = ref<Set<string>>(new Set());

const selectedItemId = computed(() => {
  const id = route.params.id;
  return Array.isArray(id) ? id[0] : id;
});

const selectedItem = computed(() => {
  if (!selectedItemId.value || !searchResults.value) return null;
  for (const group of searchResults.value) {
    const found = group.children.find(child => child.id.toString() === selectedItemId.value);
    if (found) return found;
  }
  return null;
});

// --- Core Logic ---
const performSearch = async () => {
  if (!keyword.value) {
    searchResults.value = [];
    return;
  }
  isLoading.value = true;
  try {
    const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword.value)}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data: ListGroup[] = await response.json();
    searchResults.value = data;
    expandedGroups.value = new Set(data.map(g => g.groupName));
  } catch (error) {
    console.error("Search failed:", error);
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
};

// --- Event Handlers ---
const handleSelectItem = (item: ListItem) => {
  router.push({
    name: 'search-detail',
    params: { itemType: item.type, id: item.id },
    query: { highlight: keyword.value }
  });
};

const toggleGroup = (groupName: string) => {
  if (expandedGroups.value.has(groupName)) {
    expandedGroups.value.delete(groupName);
  } else {
    expandedGroups.value.add(groupName);
  }
};
</script>

<style scoped>
/* No specific styles needed here, parent layout controls flex */
</style>