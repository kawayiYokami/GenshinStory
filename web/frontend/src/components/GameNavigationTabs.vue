<template>
  <div class="pinned-items-bar">
    <div
      v-for="item in pinnedItems"
      :key="`${item.type}-${item.id}`"
      class="pin-tag"
      @click="selectItem(item)"
    >
      <el-icon class="pin-icon"><StarFilled /></el-icon>
      <span class="pin-label">{{ item.name }}</span>
      <el-icon class="close-icon" @click.stop="unpinItem(item)">
        <Close />
      </el-icon>
    </div>
    <div v-if="pinnedItems.length === 0" class="placeholder">
      点击详情卡片右上角的星星以钉选项目
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useContentStore, type PinnedItem } from '@/stores/content';
import { StarFilled, Close } from '@element-plus/icons-vue';

const contentStore = useContentStore();
const { togglePin } = contentStore;

const emit = defineEmits<{
  'select-pinned-item': [item: PinnedItem]
}>();

const pinnedItems = computed(() => contentStore.pinnedItems);

const selectItem = (item: PinnedItem) => {
  emit('select-pinned-item', item);
};

const unpinItem = (item: PinnedItem) => {
  togglePin(item);
};
</script>

<style scoped>
.pinned-items-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: 100%;
  overflow-x: auto; /* 如果图钉太多，可以滚动 */
}

.pin-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 16px;
  background-color: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap; /* 防止文字换行 */
}

.pin-tag:hover {
  background-color: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary-light-3);
}

.pin-icon {
  font-size: 14px;
}

.pin-label {
  font-size: 14px;
  font-weight: 500;
}

.close-icon {
  font-size: 12px;
  color: var(--el-color-primary-light-3);
  border-radius: 50%;
  padding: 2px;
  margin-left: 4px; /* 与文字拉开距离 */
  transition: all 0.2s ease;
}

.close-icon:hover {
  background-color: var(--el-color-primary);
  color: white;
}

.placeholder {
  color: var(--m3-on-surface-variant);
  font-size: 14px;
  margin-left: 8px;
}
</style>