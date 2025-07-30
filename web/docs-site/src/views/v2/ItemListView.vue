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
              <router-link :to="`${filteredItems[index].path}?from=category`" class="item-link" active-class="router-link-exact-active">
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
import { ref, watch, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '@/stores/app';
import { ElAutoResizer } from 'element-plus/es/components/table-v2/index.mjs';
import { FixedSizeList as ElVirtualList } from 'element-plus/es/components/virtual-list/index.mjs';
import 'element-plus/es/components/virtual-list/style/css';

interface IndexItem {
  id: number | string;
  name: string;
  type: string;
  path: string;
  text: string;
}

const route = useRoute();
const appStore = useAppStore();

const isLoading = ref(false);
const error = ref<string | null>(null);
const fullIndex = ref<IndexItem[]>([]);

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

async function loadIndex(game: string) {
  isLoading.value = true;
  error.value = null;
  try {
    // 修正：加载正确的、用于列表展示的目录索引文件
    const response = await fetch(`/index_${game}.json`);
    if (!response.ok) throw new Error(`索引文件加载失败: ${response.statusText}`);
    fullIndex.value = await response.json();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '未知错误';
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

// Watch for game changes from the store.
// When the game changes, reload the index.
// immediate: true ensures it runs once on component creation.
watch(() => appStore.currentGame, (newGame, oldGame) => {
    // Only reload if the game actually changes or if it's the first load (oldGame is undefined)
    if (newGame && newGame !== oldGame) {
        loadIndex(newGame);
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