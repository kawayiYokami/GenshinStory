<template>
  <div class="item-list-view">
    <el-auto-resizer>
      <template #default="{ height }">
        <div v-if="isLoading" class="status-info">正在加载...</div>
        <div v-else-if="error" class="status-info error">{{ error }}</div>
        <el-virtual-list
          v-else
          :data="filteredItems"
          :total="filteredItems.length"
          :item-size="45"
          :height="height"
          class="item-list"
        >
          <template #default="{ index, style }">
            <div :key="filteredItems[index].id" :style="style">
              <router-link :to="`${filteredItems[index].path.replace('/v2/', '/domain/')}?from=category`" class="item-link" active-class="router-link-exact-active">
                {{ filteredItems[index].name }}
              </router-link>
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
import { storeToRefs } from 'pinia';
import { ElAutoResizer } from 'element-plus/es/components/table-v2/index.mjs';
import { FixedSizeList as ElVirtualList } from 'element-plus/es/components/virtual-list/index.mjs';
import 'element-plus/es/components/virtual-list/style/css';

const route = useRoute();
const appStore = useAppStore();
const dataStore = useDataStore();

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
.item-list-view {
  height: 100%;
  overflow-y: auto;
}
.status-info {
  padding: 20px;
  color: var(--app-function-pane-text);
}
.error {
  color: var(--m3-error);
}
.item-list {
  padding: 0;
  margin: 0;
}
.item-link {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 16px;
  text-decoration: none;
  color: var(--genshin-text-primary);
  border-radius: 8px;
  transition: background-color 0.2s;
}
.item-link:hover {
  background-color: rgba(0,0,0,0.05);
}
.item-link.router-link-exact-active {
  background-color: var(--genshin-accent-gold);
  color: var(--genshin-text-secondary);
  font-weight: 500;
}
</style>