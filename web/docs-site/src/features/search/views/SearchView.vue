<template>
  <div class="search-view w-full h-full flex flex-col">
    <!-- 搜索结果区域 - 可滚动，隐藏滚动条 -->
    <div class="flex-1 overflow-y-auto scrollbar-hide" ref="resultsPanel">
      <div class="max-w-3xl mx-auto px-4 pt-4">
        <!-- 状态显示 -->
        <div v-if="isLoading" class="flex items-center justify-center py-8">
          <span class="loading loading-spinner loading-md"></span>
          <span class="ml-2">正在加载...</span>
        </div>

        <div v-else-if="isSearching" class="flex items-center justify-center py-8">
          <span class="loading loading-spinner loading-md"></span>
          <span class="ml-2">正在搜索...</span>
        </div>

        <div v-else-if="error" class="alert alert-error">
          <ExclamationTriangleIcon class="w-5 h-5" />
          <span>{{ error }}</span>
        </div>

        <div v-else-if="hasSearched && results.length === 0" class="flex flex-col items-center justify-center py-12 text-base-content/60">
          <MagnifyingGlassIcon class="w-16 h-16 mb-4 opacity-30" />
          <p class="text-lg font-medium mb-2">未找到相关内容</p>
          <p class="text-sm">未找到与 "{{ searchQuery }}" 相关的内容</p>
        </div>

        <div v-else-if="results.length > 0">
          <CategoryAccordion
            :items="results"
            :group-by="'type'"
            :page-size="16"
            @item-click="handleItemClick"
          />
        </div>

        <div v-else class="flex flex-col items-center justify-center py-12 text-base-content/60">
          <MagnifyingGlassIcon class="w-16 h-16 mb-4 opacity-30" />
          <p class="text-lg font-medium mb-2">开始搜索</p>
          <p class="text-sm">在下方输入框中输入关键词开始搜索</p>
        </div>
      </div>
    </div>

    <!-- 搜索栏 - 固定在底部 -->
    <div class="flex-shrink-0">
      <div class="max-w-3xl mx-auto px-4 py-3">
        <div class="flex flex-col gap-2 p-3 card bg-base-200 shadow-lg">
          <!-- 移动端搜索栏 -->
          <div v-if="isMobile" class="flex items-center gap-3">
            <input
              type="text"
              v-model="searchQuery"
              placeholder="在当前游戏内搜索..."
              class="input input-bordered flex-1"
              @keyup.enter="performSearch"
            />
            <button @click="performSearch" class="btn btn-primary btn-square">
              <MagnifyingGlassIcon class="w-5 h-5" />
            </button>
          </div>

        <!-- 桌面端搜索栏 -->
        <div v-else class="flex gap-3">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="在当前游戏内搜索..."
            class="input input-bordered flex-1"
            @keyup.enter="performSearch"
          />
          <button @click="performSearch" class="btn btn-primary gap-2">
            <MagnifyingGlassIcon class="w-5 h-5" />
            搜索
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useAppStore } from "@/features/app/stores/app";
import { useDataStore } from "@/features/app/stores/data";
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import { storeToRefs } from 'pinia';
import { useResponsive } from '@/composables/useResponsive';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline';
import { CategoryAccordion } from '@/components/shared';

// --- 类型定义 ---
// 目录索引中的条目
interface CatalogItem {
  id: number | string;
  name: string;
  type: string;
  path: string;
  rarity?: number; // Rarity is optional
}

// 搜索索引中的搜索结果
interface SearchResult {
  id: number;
  name: string;
  type: string;
  match_source: string;
}

// 分片式倒排索引的结构 (内存中)
// key 是二元词组，value 是包含该词组的ID列表
type SearchChunk = Record<string, number[]>;

// --- 响应式状态 ---
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();
const { isLoading, error, indexData: catalogIndex } = storeToRefs(dataStore);

// --- Responsive ---
const { isMobile } = useResponsive();

// --- 本地状态 ---
const resultsPanel = ref<HTMLElement | null>(null);
const searchPanelContainer = ref<HTMLElement | null>(null);
let resizeObserver: ResizeObserver | null = null;


const searchQuery = ref('');
const isSearching = ref(false); // 搜索过程状态
const results = ref<CatalogItem[]>([]); // 结果现在是完整的目录条目
const hasSearched = ref(false);

// --- 索引数据存储 ---
// 搜索分片缓存现在由 dataStore 管理

// 将目录索引转换为以ID为键的Map，以便快速查找
const catalogMap = computed(() => {
  return new Map(catalogIndex.value.map(item => [item.id, item]));
});

// --- 搜索逻辑 ---

/**
 * 将字符串切分为二字词组 (bigrams)
 */
function getBigrams(text: string): string[] {
  const cleanedText = text.replace(/\s+/g, '').toLowerCase();
  if (cleanedText.length <= 1) {
    return [cleanedText];
  }
  const bigrams = new Set<string>();
  for (let i = 0; i < cleanedText.length - 1; i++) {
    bigrams.add(cleanedText.substring(i, i + 2));
  }
  return Array.from(bigrams);
}

// fetchSearchChunks 逻辑已移至 dataStore

async function performSearch() {
  hasSearched.value = true;
  if (!searchQuery.value.trim() || catalogIndex.value.length === 0) {
    results.value = [];
    return;
  }

  isSearching.value = true;
  results.value = [];
  error.value = null;

  try {
    const queryBigrams = getBigrams(searchQuery.value);

    // 1. 并行从 dataStore 获取所有需要的分片
    const chunkPromises = queryBigrams.map(bigram => dataStore.fetchSearchChunk(appStore.currentDomain || '', bigram[0]));
    const chunks = await Promise.all(chunkPromises);

    // 2. 获取每个二元组对应的ID列表
    const idSets: Set<number>[] = [];
    queryBigrams.forEach((bigram, index) => {
      const chunk = chunks[index];
      if (chunk && chunk[bigram]) {
        idSets.push(new Set(chunk[bigram]));
      }
    });

    if (idSets.length === 0) {
      results.value = [];
      return;
    }

    // 3. 计算所有查询词组都匹配的ID交集 (AND logic)
    if (idSets.length === 0) {
      results.value = [];
      isSearching.value = false;
      return;
    }
    const intersection = idSets.reduce((acc, set) => new Set([...acc].filter(id => set.has(id))));

    // 4. 从目录索引中查找详细信息并构建最终结果
    const finalResults: CatalogItem[] = [];
    intersection.forEach(id => {
      const item = catalogMap.value.get(id);
      if (item) {
        finalResults.push(item);
      }
    });

    results.value = finalResults;
  } catch (e) {
    error.value = e instanceof Error ? e.message : '搜索时发生未知错误';
  } finally {
    isSearching.value = false;
  }
}

// --- 生命周期钩子 ---
watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    // Clear search results when domain changes
    results.value = [];
    searchQuery.value = '';
    hasSearched.value = false;
    // The dataStore now handles clearing its own caches when the domain changes.
    dataStore.fetchIndex(newDomain);
  }
}, { immediate: true });

// 处理条目点击
const handleItemClick = (item: CatalogItem) => {
  docViewerStore.open(item.path.replace(/\/v2\/[^/]+\/category\/(.+?)(?:-尾声)?(-\d+)?$/, '$1$2.md'));
};

// 更新搜索面板高度（添加防抖优化）
let updateHeightTimeout: ReturnType<typeof setTimeout> | null = null;
const updateSearchPanelHeight = () => {
  if (updateHeightTimeout) {
    clearTimeout(updateHeightTimeout);
  }

  updateHeightTimeout = setTimeout(() => {
    if (searchPanelContainer.value) {
      const height = (searchPanelContainer.value as HTMLElement).offsetHeight;
      document.documentElement.style.setProperty('--search-panel-height', `${height}px`);
    }
  }, 16); // 约60fps的更新频率
};

onMounted(() => {
  // 设置ResizeObserver来监控搜索面板高度变化
  if (searchPanelContainer.value) {
    updateSearchPanelHeight(); // 初始化高度

    resizeObserver = new ResizeObserver(() => {
      updateSearchPanelHeight();
    });

    resizeObserver.observe(searchPanelContainer.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  if (updateHeightTimeout) {
    clearTimeout(updateHeightTimeout);
  }
});

</script>

<style scoped>
/* 固定在屏幕底部的搜索面板 */
.search-panel-fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 20;
  background: transparent;
}

/* 移除搜索框激活时的边框 */
:deep(.input:focus) {
  outline: none;
  border-color: hsl(var(--bc) / 0.2);
  box-shadow: none;
}

/* 保留必要的滚动条样式（DaisyUI没有提供） */
:deep(.overflow-y-auto::-webkit-scrollbar) {
  width: 6px;
}

:deep(.overflow-y-auto::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.overflow-y-auto::-webkit-scrollbar-thumb) {
  background-color: transparent;
  border-radius: 3px;
  transition: background-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover::-webkit-scrollbar-thumb) {
  background-color: hsl(var(--bc) / 0.2);
}

/* Firefox scrollbar */
:deep(.overflow-y-auto) {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
  transition: scrollbar-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover) {
  scrollbar-color: hsl(var(--bc) / 0.2) transparent;
}
</style>
