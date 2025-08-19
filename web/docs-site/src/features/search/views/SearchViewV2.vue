<template>
  <div class="flex flex-col h-full">
    <div class="flex flex-col gap-3 pb-4 border-b border-m3-border-soft">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="在当前游戏内搜索..."
        class="w-full h-12 px-4 text-base bg-m3-surface-variant text-m3-on-surface-variant border border-transparent rounded-lg focus:outline-none focus:border-m3-primary"
        @keyup.enter="performSearch"
      />
      <button @click="performSearch" class="h-12 border-none rounded-lg bg-m3-primary text-m3-on-primary text-base cursor-pointer">搜索</button>
    </div>

    <div v-if="isLoading" class="pt-4 overflow-y-auto grow">正在加载...</div>
    <div v-else-if="isSearching" class="pt-4 overflow-y-auto grow">正在搜索...</div>
    <div v-else-if="error" class="pt-4 overflow-y-auto grow text-m3-error">{{ error }}</div>
    <div v-else-if="hasSearched && results.length === 0" class="pt-4 overflow-y-auto grow">
      未找到与 "{{ searchQuery }}" 相关的内容。
    </div>
    <div v-else-if="results.length > 0" class="pt-4 overflow-y-auto grow">
      <ul class="list-none p-0 m-0">
        <li v-for="item in results" :key="item.id">
          <div @click="docViewerStore.open(item.path.replace(/\/v2\/[^/]+\/category\/(.+?)(?:-尾声)?(-\d+)?$/, '$1$2.md'))" class="block py-3 px-2 my-1 no-underline text-m3-on-surface rounded-lg transition-colors duration-200 hover:bg-m3-surface-variant cursor-pointer">
            <span class="text-sm text-m3-on-surface-variant mr-2">[{{ item.type }}]</span>
            <span class="font-medium">{{ item.name }}</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useAppStore } from "@/features/app/stores/app";
import { useDataStore } from "@/features/app/stores/data";
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import { storeToRefs } from 'pinia';

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
</script>
