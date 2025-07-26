<template>
  <div class="list-pane">
    <div class="search-bar">
      <input
        type="text"
        :value="searchQuery"
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        @keydown.enter="$emit('search-clicked')"
        placeholder="搜索..."
      />
      <button @click="$emit('search-clicked')" class="search-button">
        <el-icon><Search /></el-icon>
      </button>
    </div>
    <div class="horizontal-divider"></div>
    <div v-if="isLoading" class="loading-skeleton">
      <p>Loading list...</p>
    </div>
    <ul v-else class="list-container">
      <li v-for="group in list" :key="group.groupName" class="list-group">
        <div class="list-group-header" @click="$emit('toggleGroup', group.groupName)">
          <span class="group-name">{{ group.groupName }}</span>
          <span class="group-arrow" :class="{ 'is-expanded': expandedGroups.has(group.groupName) }">›</span>
        </div>
        <Transition name="list-expand">
          <ul v-if="expandedGroups.has(group.groupName)" class="list-sub-items">
            <li
              v-for="item in group.children"
            :key="item.id"
            class="list-item"
            :class="{ 'is-active': selectedItem?.id === item.id }"
            @click="$emit('selectItem', item)"
          >
            <el-icon v-if="item.icon" class="list-item__icon"><component :is="item.icon" /></el-icon>
            <span class="list-item__name">{{ item.name }}</span>
            </li>
          </ul>
        </Transition>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue';
import type { ListGroup, ListItem } from '@/stores/data';

defineProps<{
  list: ListGroup[];
  isLoading: boolean;
  searchQuery: string;
  expandedGroups: Set<string>;
  selectedItem: ListItem | null;
}>();

defineEmits<{
  (e: 'update:searchQuery', value: string): void;
  (e: 'toggleGroup', groupName: string): void;
  (e: 'selectItem', item: ListItem): void;
  (e: 'search-clicked'): void;
}>();
</script>

<style scoped>
.list-pane {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--m3-card-color-visible);
  border-radius: 12px; /* Add border-radius to make it a card */
  overflow: hidden; /* Ensure content respects the border radius */
  border: 1px solid var(--m3-border-color-soft);
}

.search-bar {
  margin: 16px;
  display: flex;
  gap: 8px;
}

.search-bar input {
  flex-grow: 1;
  padding: 8px 12px;
  border-radius: 16px;
  border: 1px solid var(--m3-outline);
  background-color: var(--m3-surface-1);
  min-width: 0; /* Fix for flexbox overflow */
}

.search-button {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.search-button:hover {
  background-color: var(--m3-primary);
}

.horizontal-divider {
  height: 1px;
  background-color: var(--m3-outline);
  margin: 0 16px; /* Add margin to match search padding */
}

.list-container {
  list-style: none;
  /* Apply consistent horizontal padding to match the search bar */
  padding: 8px 16px;
  margin: 0;
  overflow-y: auto;
  flex-grow: 1;
}

.list-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  font-weight: 500;
  color: var(--m3-on-surface-variant);
  border-radius: 8px;
}

.list-group-header:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.group-arrow {
  transition: transform 0.2s ease-in-out;
  font-size: 1.2em;
}

.group-arrow.is-expanded {
  transform: rotate(90deg);
}

.list-sub-items {
  list-style: none;
  /* Add padding-left to create visual indentation for child items */
  padding-left: 16px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  /* Adjust padding for a more compact look */
  padding: 10px 16px;
  cursor: pointer;
  border-radius: 8px;
  margin-top: 4px;
  position: relative;
  overflow: hidden;
}

.list-item__name {
  /* Slightly smaller font for child items */
  font-size: 0.95em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 400; /* Regular weight for non-selected items */
}

.list-item__icon {
  font-size: 18px;
  color: var(--m3-on-surface-variant);
}

.list-item.is-active .list-item__icon {
    color: var(--m3-on-primary-container);
}

.list-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--m3-state-layer-color);
  opacity: 0;
  transition: opacity var(--m3-transition-short);
}

.list-item:hover::before {
  opacity: var(--m3-state-layer-opacity-hover);
}

.list-item:active::before {
  opacity: var(--m3-state-layer-opacity-pressed);
}

.list-item.is-active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  font-weight: 700;
}

/* Ensure active state hover is stronger */
.list-item.is-active:hover::before {
    opacity: calc(var(--m3-state-layer-opacity-hover) + 0.04);
}

.loading-skeleton {
  padding: 24px;
  color: var(--m3-on-surface-variant);
}

/* Transition for list expand/collapse */
.list-expand-enter-active,
.list-expand-leave-active {
  transition: all 0.2s ease-out;
}
.list-expand-enter-from,
.list-expand-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>