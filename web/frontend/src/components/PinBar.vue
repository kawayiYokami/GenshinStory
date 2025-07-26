<template>
  <TransitionGroup name="pin-list" tag="div" class="pin-bar">
    <div
      v-for="item in pinStore.pinnedItems"
      :key="item.targetUrl"
      class="pinned-item"
      :class="{ 'is-active': isActive(item) }"
      @mouseenter="setHovering(item, true)"
      @mouseleave="setHovering(item, false)"
    >
      <div class="pinned-item__icon-wrapper" @click="handleIconClick(item)">
        <el-icon class="item-icon" :class="{ 'is-hidden': hoveringStates[item.targetUrl] }">
          <component :is="getIcon(item.itemType)" />
        </el-icon>
        <el-icon class="close-icon" :class="{ 'is-visible': hoveringStates[item.targetUrl] }">
          <Close />
        </el-icon>
      </div>
      <span class="pinned-item__name" @click="handlePinContentClick(item)">{{ item.name.length > 5 ? `${item.name.slice(0, 5)}...` : item.name }}</span>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { usePinStore, type PinnedItem } from '@/stores/pin';
import { useEventBusStore } from '@/stores/eventBus';
import {
  Document,
  MagicStick,
  Trophy,
  Collection,
  Folder,
  Box,
  Star,
  Close,
  Search
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const pinStore = usePinStore();
const eventBus = useEventBusStore();

const hoveringStates = ref<Record<string, boolean>>({});
const setHovering = (item: PinnedItem, state: boolean) => {
  hoveringStates.value[item.targetUrl] = state;
};

// 图标映射
const iconMap: Record<string, any> = {
  quest: Document,
  weapon: MagicStick,
  character: Trophy,
  book: Collection,
  material: Folder,
  relicset: Box,
  search: Search,
  default: Star,
};

const getIcon = (type: string) => {
  return iconMap[type] || iconMap.default;
};

const isActive = (item: PinnedItem) => {
  return route.fullPath === item.targetUrl;
};

const handlePinContentClick = (item: PinnedItem) => {
  // If the target is a category list, we need to emit an event
  // so the list view can highlight the item after navigation.
  const isCategoryNav = item.targetUrl.startsWith('/category');
  if (isCategoryNav) {
    eventBus.emit('highlight-item-in-list', { itemType: item.itemType, id: item.id });
  }
  router.push(item.targetUrl);
};

const handleIconClick = (item: PinnedItem) => {
  if (hoveringStates.value[item.targetUrl]) {
    pinStore.removePin(item.itemType, item.id);
  } else {
    handlePinContentClick(item);
  }
};
</script>

<style scoped>
.pin-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  height: fit-content; /* 高度由内容决定 */
  padding: 4px; /* 统一内边距 */
  margin-left: auto; /* 将整个容器推到右边 */
  background-color: var(--m3-surface-container); /* 卡片背景色 */
  border-radius: 12px; /* 卡片圆角 */
  overflow: visible; /* 允许放大效果溢出 */
}

.pinned-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  height: 32px;
  border-radius: 8px;
  color: var(--m3-on-surface-variant);
  cursor: pointer;
  transition: transform 0.2s ease, color 0.2s ease, font-weight 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.pinned-item:hover {
  transform: scale(1.3);
  color: var(--m3-on-surface);
}

.pinned-item.is-active {
  transform: scale(1.2);
  color: var(--m3-on-surface);
  font-weight: bold;
}

.pinned-item__icon-wrapper {
  position: relative;
  width: 16px;
  height: 16px;
  font-size: 16px;
}

.pinned-item__icon-wrapper .item-icon,
.pinned-item__icon-wrapper .close-icon {
  position: absolute;
  top: 0;
  left: 0;
  transition: opacity 0.2s ease;
}

.item-icon.is-hidden,
.close-icon:not(.is-visible) {
  opacity: 0;
  pointer-events: none;
}

.close-icon.is-visible {
  opacity: 1;
}

.pinned-item__name {
  font-size: 14px;
}

/* TransitionGroup Animations */
.pin-list-enter-active,
.pin-list-leave-active {
  transition: all 0.3s ease;
}
.pin-list-enter-from,
.pin-list-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.pin-list-move {
  transition: transform 0.3s ease;
}

/* Custom Scrollbar for Pin Bar */
.pin-bar::-webkit-scrollbar {
  height: 6px; /* 滚动条高度 */
}

.pin-bar::-webkit-scrollbar-track {
  background: transparent; /* 轨道背景 */
}

.pin-bar::-webkit-scrollbar-thumb {
  background-color: var(--m3-outline-variant); /* 滑块颜色 */
  border-radius: 3px; /* 滑块圆角 */
}

.pin-bar::-webkit-scrollbar-thumb:hover {
  background-color: var(--m3-outline); /* 悬停时滑块颜色 */
}
</style>