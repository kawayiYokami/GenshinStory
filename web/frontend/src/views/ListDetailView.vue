<template>
  <ListPane
    :list="filteredList"
    :is-loading="dataStore.isLoading.list"
    v-model:search-query="searchQuery"
    :expanded-groups="expandedGroups"
    :selected-item="selectedItem"
    @toggle-group="toggleGroup"
    @select-item="handleSelectItem"
  />
  <router-view />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDataStore, type ListItem } from '@/stores/data';
import { useEventBusStore, type AppEvent } from '@/stores/eventBus';
import ListPane from '@/components/ListPane.vue';

const route = useRoute();
const router = useRouter();
const dataStore = useDataStore();
const eventBus = useEventBusStore();

const searchQuery = ref('');
const expandedGroups = ref(new Set<string>());

const currentItemType = computed(() => route.params.itemType as string);
const selectedItemId = computed(() => {
  const id = route.params.id;
  return Array.isArray(id) ? id[0] : id;
});

const listData = computed(() => dataStore.lists[currentItemType.value] || []);

const selectedItem = computed(() => {
  if (!selectedItemId.value || !listData.value) return null;
  for (const group of listData.value) {
    const found = group.children.find(child => child.data.id.toString() === selectedItemId.value);
    if (found) return found;
  }
  return null;
});

const filteredList = computed(() => {
  if (!searchQuery.value) return listData.value;
  const lowerCaseQuery = searchQuery.value.toLowerCase();
  return listData.value.map(group => ({
    ...group,
    children: group.children.filter(item => item.name.toLowerCase().includes(lowerCaseQuery)),
  })).filter(group => group.children.length > 0);
});

const toggleGroup = (groupName: string) => {
  if (expandedGroups.value.has(groupName)) {
    expandedGroups.value.delete(groupName);
  } else {
    expandedGroups.value.add(groupName);
  }
};

const handleSelectItem = (item: ListItem) => {
  // The only source of truth for navigation is the item's own data.
  router.push({
    name: 'category-detail',
    params: {
      // This is the parent route's param, which should not change.
      itemType: currentItemType.value,
      // This is the new param for the detail view's type.
      detailItemType: item.data.type,
      id: item.data.id
    }
  });
};

const processHighlightEvent = (event: AppEvent) => {
  if (event.name === 'highlight-item-in-list' && event.payload.itemType === currentItemType.value) {
    for (const group of listData.value) {
      const found = group.children.some(child => child.data.id.toString() === event.payload.id);
      if (found) {
        if (!expandedGroups.value.has(group.groupName)) {
          toggleGroup(group.groupName);
        }
        break;
      }
    }
    eventBus.consume(event.id);
  }
};

watch(currentItemType, (newItemType) => {
  if (newItemType) {
    dataStore.fetchList(newItemType);
    expandedGroups.value.clear();
  }
}, { immediate: true });

// Process any pending highlight events when the component mounts or list data changes
watch(listData, () => {
  eventBus.events.forEach(processHighlightEvent);
}, { immediate: true });

let unsubscribe: (() => void) | undefined;
onMounted(() => {
  const cb = (event: AppEvent) => processHighlightEvent(event);
  eventBus.events.forEach(cb);
  // A simple way to subscribe to new events. In a real app, a more robust event bus would be better.
  const interval = setInterval(() => {
    eventBus.events.forEach(e => {
      if (!e.consumed) cb(e);
    });
  }, 200);
  unsubscribe = () => clearInterval(interval);
});

onUnmounted(() => {
  if (unsubscribe) unsubscribe();
});

</script>