<template>
  <div class="search-view w-full h-full flex flex-col bg-base-100">
    <Teleport to="#navbar-content-target" v-if="isNavbarContentTargetAvailable">
      <div class="relative h-full w-full max-w-md">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="在当前知识领域内搜索..."
          class="input input-sm h-full w-full bg-base-300 border-none pr-10"
          @keyup.enter="performSearch"
        />
        <div class="absolute right-2 top-1/2 transform -translate-y-1/2 z-10">
          <button
            @click="performSearch"
            class="btn btn-ghost btn-sm btn-circle"
            :disabled="isSearching || isLoading"
            title="搜索"
          >
            <Search class="w-4 h-4" />
          </button>
        </div>
      </div>
    </Teleport>
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
          <TriangleAlert class="w-5 h-5" />
          <span>{{ error }}</span>
        </div>

        <div v-else-if="hasSearched && results.length === 0" class="flex flex-col items-center justify-center py-12 text-base-content/60">
          <Search class="w-16 h-16 mb-4 opacity-30" />
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
          <Search class="w-16 h-16 mb-4 opacity-30" />
          <p class="text-lg font-medium mb-2">开始搜索</p>
          <p class="text-sm">在上方输入框中输入关键词开始搜索</p>
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
import filePathService from '@/features/app/services/filePathService';
import { storeToRefs } from 'pinia';
import { useResponsive } from '@/composables/useResponsive';
import {
  Search,
  TriangleAlert,
  ChevronRight
} from 'lucide-vue-next';
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
const isMounted = ref(false); // 添加isMounted变量定义

// --- 索引数据存储 ---
// 搜索分片缓存现在由 dataStore 管理

// 将目录索引转换为以ID为键的Map，以便快速查找
const catalogMap = computed(() => {
  return new Map(catalogIndex.value.map(item => [item.id, item]));
});

// --- 搜索逻辑 ---
// 搜索相关函数已移至 dataStore，这里直接使用 dataStore.searchCatalog

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
    // 使用 dataStore 的集中搜索功能
    const searchResults = await dataStore.searchCatalog(searchQuery.value);
    results.value = searchResults;

    console.log('SearchView: 搜索完成，查询:', searchQuery.value, '结果数量:', searchResults.length);
  } catch (e) {
    error.value = e instanceof Error ? e.message : '搜索时发生未知错误';
    console.error('SearchView: 搜索失败:', e);
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
  const logicalPath = filePathService.fromFrontendCategoryPath(item.path, {
    domain: appStore.currentDomain || undefined,
    ensureMdExtension: true,
  });
  docViewerStore.open(logicalPath);
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
  isMounted.value = true;
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

// 添加计算属性检查navbar-content-target元素是否可用
const isNavbarContentTargetAvailable = computed(() => {
  return isMounted.value && typeof document !== 'undefined' && document.getElementById('navbar-content-target') !== null;
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

/* 为内部按钮留出空间 */
:deep(.input) {
  padding-right: 2.5rem !important;
}

/* 确保内部按钮样式 */
:deep(.input-container button) {
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
  z-index: 10;
}

:deep(.input-container button:hover) {
  background-color: hsl(var(--bc) / 0.1);
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
le>
le>
