<template>
  <div class="max-w-3xl h-full w-full mx-auto p-4">
    <Teleport to="#navbar-content-target" v-if="isNavbarContentTargetAvailable">
      <div class="form-control h-full w-full max-w-xs relative">
        <input
          type="text"
          placeholder="在当前结果中过滤..."
          class="input input-bordered input-sm h-full w-full bg-base-300 border-none"
          v-model="filterKeyword"
        />
      </div>
    </Teleport>
    <!-- 加载状态 -->
    <div v-if="isLoading" class="p-5 text-function-pane">正在加载...</div>
    <div v-else-if="error" class="p-5 text-error">{{ error }}</div>

    <!-- Tabs 组件 -->
    <div v-else>
      <!-- 手风琴列表 -->
      <div class="space-y-2">
        <div
          v-for="subCategory in subCategories"
          :key="subCategory"
          class="collapse collapse-arrow bg-base-300 border border-base-300"
        >
          <input type="checkbox" />
          <div class="collapse-title font-semibold text-base-content">
            {{ subCategory }}
            <span class="text-xs text-base-content/70 ml-2">({{ getSubCategoryItemsSync(subCategory).length }})</span>
          </div>
          <div class="collapse-content">
            <!-- 页码导航 -->
            <div v-if="getTotalPages(subCategory) > 1" class="mb-6 flex flex-col items-center gap-4">
              <!-- 当前页码信息（调试用） -->
              <div class="text-xs text-base-content/50">
                当前页: {{ getCurrentPage(subCategory) }}
              </div>
              <!-- 页码按钮 -->
              <div class="join">
                <template v-for="page in getPageNumbers(subCategory)" :key="page">
                  <button
                    class="join-item btn btn-sm bg-base-100 hover:bg-base-200 border-base-300"
                    :class="{
                      'bg-base-200 hover:bg-base-300 border-base-400': page === getCurrentPage(subCategory),
                      'btn-disabled': page === '...'
                    }"
                    @click="typeof page === 'number' && changePage(subCategory, page)"
                  >
                    {{ page }}
                  </button>
                </template>
              </div>

              <!-- 页面信息 -->
              <div class="text-sm text-base-content/70">
                第 {{ getCurrentPage(subCategory) }} 页，共 {{ getTotalPages(subCategory) }} 页
                ({{ getSubCategoryItemsSync(subCategory).length }} 项)
              </div>
            </div>

            <!-- 分页显示内容 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <div
                v-for="item in getPaginatedItems(subCategory)"
                :key="item.path"
                @click="docViewerStore.open(filePathService.fromFrontendCategoryPath(item.path, { domain: appStore.currentDomain || undefined, ensureMdExtension: true }))"
                class="card card-compact bg-base-100 shadow cursor-pointer hover:shadow-md transition-shadow"
              >
                <div class="card-body relative">
                  <div
                    v-if="typeof item.score === 'number' && Number.isFinite(item.score)"
                    class="absolute top-2 right-2 text-[10px] leading-none px-2 py-1 rounded-full bg-primary/10 text-primary font-semibold"
                    title="搜索分数"
                  >
                    {{ Number(item.score).toFixed(3) }}
                  </div>
                  <h3 class="card-title text-sm">{{ item.name }}</h3>
                  <p class="text-xs text-base-content/70 mt-1">{{ item.type }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, computed, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '@/features/app/stores/app';
import { useDataStore } from '@/features/app/stores/data';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import filePathService from '@/features/app/services/filePathService';
import { storeToRefs } from 'pinia';

interface IndexItem {
  id?: number | string;
  name: string;
  path: string;
  type: string;
  category?: string;
  score?: number;
}

const route = useRoute();
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();

const { isLoading, error, indexData: fullIndex } = storeToRefs(dataStore);

// --- State ---
const containerRef = ref<HTMLElement>();
const pageSize = ref(16); // 每页显示16个
const expandedCategories = ref<Record<string, number>>({}); // 记录每个分类展开的页数
const currentPage = ref<Record<string, number>>({}); // 记录每个分类的当前页码
const isMounted = ref(false); // 用于标记组件是否挂载
const filterKeyword = ref(''); // 过滤关键字

// 搜索结果缓存
const searchResultsCache = ref<Record<string, IndexItem[]>>({});

const isSearching = ref(false);
let activeSearchToken = 0;

// 同步版本，供模板使用
const getSubCategoryItemsSync = (subCategory: string): any[] => {
  if (!filterKeyword.value) {
    return subCategoryIndex.value.get(subCategory) || [];
  }
  return searchResultsCache.value[subCategory] || [];
};

const normalizePathKey = (rawPath: string): string => {
  const normalized = filePathService.normalizeLogicalPath(rawPath || '', {
    domain: appStore.currentDomain || undefined,
    ensureMdExtension: false,
  });
  return normalized.toLowerCase();
};

// 获取特定子分类的当前页码
const getCurrentPage = (subCategory: string) => {
  return currentPage.value[subCategory] || 1;
};

// 检查navbar-content-target元素是否可用
const isNavbarContentTargetAvailable = computed(() => {
  return isMounted.value && typeof document !== 'undefined' && document.getElementById('navbar-content-target') !== null;
});

// --- Computed ---
const category = computed(() => {
  return Array.isArray(route.params.categoryName)
    ? route.params.categoryName[0]
    : route.params.categoryName;
});

const categoryTypeMap: Record<string, string> = {
  quest: 'questchapter',
};

// 获取当前分类下的所有文档（包括子目录）
const categoryItems = computed(() => {
  if (!category.value || fullIndex.value.length === 0) {
    return [];
  }

  const categoryId = category.value.toLowerCase();
  const targetType = categoryTypeMap[categoryId] || categoryId;

  return fullIndex.value.filter(item =>
    item.type.toLowerCase() === targetType
  );
});

// 创建子分类索引（优化性能）
const subCategoryIndex = computed(() => {
  const index = new Map<string, any[]>();

  categoryItems.value.forEach(item => {
    if (item && typeof item === 'object' && 'category' in item && item.category) {
      if (!index.has(item.category)) {
        index.set(item.category, []);
      }
      index.get(item.category)!.push(item);
    }
  });

  return index;
});

// 提取子分类（使用 category 字段）
const subCategories = computed(() => {
  if (!category.value) return [];

  // 直接从索引中获取所有子分类名称
  return Array.from(subCategoryIndex.value.keys()).sort();
});

watch(
  [filterKeyword, () => categoryItems.value, () => appStore.currentDomain],
  async () => {
    const keyword = filterKeyword.value.trim();
    if (!keyword) {
      searchResultsCache.value = {};
      return;
    }

    const token = ++activeSearchToken;
    isSearching.value = true;
    try {
      const catalogResults = await dataStore.searchCatalog(keyword);
      if (token !== activeSearchToken) return;

      const matchedIds = new Set(
        catalogResults
          .map(item => item.id)
          .filter(id => id !== undefined && id !== null)
          .map(id => String(id))
      );
      const matchedPaths = new Set(catalogResults.map(item => normalizePathKey(item.path)));
      const scoreById = new Map(
        catalogResults
          .filter(item => item.id !== undefined && item.id !== null && typeof item.score === 'number')
          .map(item => [String(item.id), Number(item.score)])
      );
      const scoreByPath = new Map(
        catalogResults
          .filter(item => typeof item.score === 'number')
          .map(item => [normalizePathKey(item.path), Number(item.score)])
      );
      const newResults: Record<string, IndexItem[]> = {};
      for (const subCategory of subCategories.value) {
        const items = (subCategoryIndex.value.get(subCategory) || []) as IndexItem[];
        newResults[subCategory] = items
          .filter(item => {
            const itemId = item.id !== undefined && item.id !== null ? String(item.id) : '';
            if (itemId && matchedIds.has(itemId)) return true;
            return matchedPaths.has(normalizePathKey(item.path));
          })
          .map(item => {
            const itemId = item.id !== undefined && item.id !== null ? String(item.id) : '';
            const pathKey = normalizePathKey(item.path);
            const score = itemId ? scoreById.get(itemId) : scoreByPath.get(pathKey);
            return typeof score === 'number' ? { ...item, score } : item;
          });
      }
      searchResultsCache.value = newResults;
    } catch (searchErr) {
      console.error('过滤搜索失败:', searchErr);
      if (token === activeSearchToken) {
        searchResultsCache.value = {};
      }
    } finally {
      if (token === activeSearchToken) {
        isSearching.value = false;
      }
    }
  },
  { immediate: true }
);


// 获取分页后的项目
const getPaginatedItems = (subCategory: string) => {
  const items = getSubCategoryItemsSync(subCategory);
  const page = currentPage.value[subCategory] || 1;
  const start = (page - 1) * pageSize.value;
  const end = start + pageSize.value;
  return items.slice(start, end);
};

// 获取总页数
const getTotalPages = (subCategory: string) => {
  const items = getSubCategoryItemsSync(subCategory);
  return Math.ceil(items.length / pageSize.value);
};

// 生成页码数组
const getPageNumbers = (subCategory: string) => {
  const totalPages = getTotalPages(subCategory);
  const current = currentPage.value[subCategory] || 1;
  const pages: (number | string)[] = [];

  if (totalPages <= 7) {
    // 如果页数少于7页，全部显示
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    // 总是显示第一页
    pages.push(1);

    if (current <= 4) {
      // 当前页在前4页时
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(totalPages);
    } else if (current >= totalPages - 3) {
      // 当前页在后4页时
      pages.push('...');
      for (let i = totalPages - 4; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 当前页在中间时
      pages.push('...');
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(totalPages);
    }
  }

  return pages;
};

// 切换页码
const changePage = (subCategory: string, page: number) => {
  if (!currentPage.value) {
    currentPage.value = {};
  }
  currentPage.value[subCategory] = page;
};

// --- Watchers ---
onMounted(() => {
  isMounted.value = true;
});

watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    dataStore.fetchIndex(newDomain);
  }
}, { immediate: true });

</script>
