<template>
  <div class="h-full overflow-y-auto">
    <el-auto-resizer>
      <template #default="{ height }">
        <div v-if="isLoading" class="p-5 text-app-function-pane-text">正在加载...</div>
        <div v-else-if="error" class="p-5 text-m3-error">{{ error }}</div>
        <el-virtual-list
          v-else
          :data="filteredItems"
          :total="filteredItems.length"
          :item-size="45"
          :height="height"
          class="p-0 m-0"
        >
          <template #default="{ index, style }">
            <div :key="filteredItems[index].id" :style="style">
              <div
                @click="docViewerStore.open(filteredItems[index].path.replace(/\/v2\/[^/]+\/category\/(.+?)(?:-尾声)?(-\d+)?$/, '$1$2.md'))"
                class="flex items-center h-full px-4 no-underline text-on-surface-variant rounded-lg transition-colors duration-200 hover:bg-primary-container [&.router-link-exact-active]:bg-primary [&.router-link-exact-active]:text-on-primary [&.router-link-exact-active]:font-medium cursor-pointer"
              >
                {{ filteredItems[index].name }}
              </div>
            </div>
          </template>
        </el-virtual-list>
      </template>
    </el-auto-resizer>
  </div>
</template>

<script setup lang="ts">
import { watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '@/features/app/stores/app';
import { useDataStore } from '@/features/app/stores/data';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import { storeToRefs } from 'pinia';
import { ElAutoResizer } from 'element-plus/es/components/table-v2/index.mjs';
import { FixedSizeList as ElVirtualList } from 'element-plus/es/components/virtual-list/index.mjs';

const route = useRoute();
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();

const { isLoading, error, indexData: fullIndex } = storeToRefs(dataStore);

const category = computed(() => {
  return Array.isArray(route.params.categoryName)
    ? route.params.categoryName[0]
    : route.params.categoryName;
});

const filteredItems = computed(() => {
  if (!category.value || fullIndex.value.length === 0) {
    return [];
  }
  // Use startsWith for broader category matching (e.g., "Weapon" should match "Weapon/Sword")
  return fullIndex.value.filter(item =>
    item.type.toLowerCase().startsWith(category.value.toLowerCase())
  );
});

// Watch for domain changes from the store.
// When the domain changes, trigger the fetch action in the data store.
// immediate: true ensures it runs once on component creation.
watch(() => appStore.currentDomain, (newDomain) => {
    if (newDomain) {
        dataStore.fetchIndex(newDomain);
    }
}, { immediate: true });

</script>

<style scoped>
/* Styles are now handled by utility classes and the active-class prop. */
</style>