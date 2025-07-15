<template>
  <TransitionGroup name="pin-list" tag="div" class="pin-bar">
    <div
      v-for="item in pinnedItems"
      :key="`${item.type}-${item.id}`"
      class="pinned-item"
      :class="{ 'is-active': isActive(item) }"
      @mouseenter="setHovering(item, true)"
      @mouseleave="setHovering(item, false)"
    >
      <div class="pinned-item__icon-wrapper" @click="handleIconClick(item)">
        <el-icon class="item-icon" :class="{ 'is-hidden': hoveringStates[`${item.type}-${item.id}`] }">
          <component :is="getIcon(item.navigationType)" />
        </el-icon>
        <el-icon class="close-icon" :class="{ 'is-visible': hoveringStates[`${item.type}-${item.id}`] }">
          <Close />
        </el-icon>
      </div>
      <span class="pinned-item__name" @click="contentStore.notifyPinClicked(item)">{{ item.name.length > 5 ? `${item.name.slice(0, 5)}...` : item.name }}</span>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useContentStore, type PinnedItem } from '@/stores/content';
import {
  Document,
  Reading,
  MagicStick,
  Trophy,
  Collection,
  Folder,
  Box,
  Star,
  Close
} from '@element-plus/icons-vue';

const contentStore = useContentStore();
const { pinnedItems, activePinnedItem } = storeToRefs(contentStore);
const { togglePin, setActivePinnedItem } = contentStore;

const hoveringStates = ref<Record<string, boolean>>({});
const setHovering = (item: PinnedItem, state: boolean) => {
  hoveringStates.value[`${item.type}-${item.id}`] = state;
};

// 图标映射
const iconMap: Record<string, any> = {
  quest: Document,
  weapon: MagicStick,
  character: Trophy,
  book: Collection,
  material: Folder,
  relicset: Box,
  default: Star, // 保留一个默认图标以防万一
};

const getIcon = (type: string) => {
  return iconMap[type] || iconMap.default;
};

const isActive = (item: PinnedItem) => {
  if (!activePinnedItem.value) return false;
  return activePinnedItem.value.type === item.type && activePinnedItem.value.id === item.id;
};

const handleIconClick = (item: PinnedItem) => {
  const itemKey = `${item.type}-${item.id}`;
  if (hoveringStates.value[itemKey]) {
    // 图标是关闭，执行关闭逻辑
    if (isActive(item)) {
      setActivePinnedItem(null);
    }
    togglePin(item);
  } else {
    // 图标是项目图标，执行选择逻辑
    contentStore.notifyPinClicked(item);
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