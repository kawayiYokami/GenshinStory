<template>
  <div class="detail-pane">
    <!-- 仅在有选中项时显示星星 -->
    <el-icon
      v-if="selectedItemId && selectedItemType"
      class="pin-button"
      :class="{ 'is-pinned': isPinned(selectedItemType, selectedItemId) }"
      @click="handlePinClick"
    >
      <component :is="isPinned(selectedItemType, selectedItemId) ? 'StarFilled' : 'Star'" />
    </el-icon>
    
    <ItemDetailView
      v-if="selectedItemId && selectedItemType"
      :item-id="selectedItemId"
      :item-type="selectedItemType"
    />
    
    <div v-else class="placeholder">
      <p>请在左侧选择一个项目以查看详情。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Star, StarFilled } from '@element-plus/icons-vue';
import { useRoute } from 'vue-router';
import ItemDetailView from '@/views/ItemDetailView.vue';
import { useContentStore } from '@/stores/content';

// This component now acts as a host for ItemDetailView.
// It receives the selected item's identity and passes it down.
const props = defineProps<{
  selectedItemType: string | null; // This is the REAL type, e.g., 'chapter' or 'series'
  selectedItemId: string | null;
  selectedItemName: string | null;
}>();

const route = useRoute();
const contentStore = useContentStore();
const { isPinned, togglePin } = contentStore;

function handlePinClick() {
  if (props.selectedItemType && props.selectedItemId && props.selectedItemName) {
    togglePin({
      type: props.selectedItemType, // The real type
      id: props.selectedItemId,
      name: props.selectedItemName,
      // The navigation category, taken from the route
      navigationType: route.params.itemType as string,
    });
  }
}
</script>

<style scoped>
.detail-pane {
  position: relative;
  flex-grow: 1;
  display: flex; /* This is crucial for the child to fill the height */
  flex-direction: column;
  overflow-y: auto;
  background-color: var(--m3-card-color-visible);
  border-radius: 12px;
  border: 1px solid var(--m3-border-color-soft);
}

.pin-button {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 20px;
  color: var(--m3-on-surface-variant);
  cursor: pointer;
  z-index: 10; /* Ensure it's above the content */
}

.pin-button:hover {
  color: var(--m3-on-surface);
}

/* 新增：为已钉住的星星添加高亮样式 */
.pin-button.is-pinned {
  color: var(--el-color-warning); /* 使用Element Plus的警告色作为高亮 */
}

.placeholder {
  flex: 1; /* Make it fill the available space */
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: var(--m3-on-surface-variant);
}
</style>