<template>
  <div class="search-view-v2">
    <div class="search-bar">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="在当前游戏内搜索..."
        class="search-input"
        @keyup.enter="performSearch"
      />
      <button @click="performSearch" class="search-button">搜索</button>
    </div>

    <div v-if="isLoading" class="results-area">正在加载...</div>
    <div v-else-if="isSearching" class="results-area">正在搜索...</div>
    <div v-else-if="error" class="results-area error">{{ error }}</div>
    <div v-else-if="hasSearched && results.length === 0" class="results-area">
      未找到与 "{{ searchQuery }}" 相关的内容。
    </div>
    <div v-else-if="results.length > 0" class="results-area">
      <ul class="search-results">
        <li v-for="item in results" :key="item.id">
          <router-link :to="{ path: item.path, query: { from: 'search' } }" class="result-item">
            <span class="result-type">[{{ item.type }}]</span>
            <span class="result-name">{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useAppStore } from '@/stores/app';

// --- 类型定义 ---
// 目录索引中的条目
interface CatalogItem {
  id: number | string;
  name: string;
  type: string;
  path: string;
  rarity: number;
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
const searchQuery = ref('');
const isLoading = ref(true); // 初始加载目录
const isSearching = ref(false); // 搜索过程状态
const error = ref<string | null>(null);
const results = ref<CatalogItem[]>([]); // 结果现在是完整的目录条目
const hasSearched = ref(false);

// --- 索引数据存储 ---
let catalogIndex: CatalogItem[] = [];
// 缓存已加载的分片，key是分片名(如'旅'), value是分片内容
let chunkCache: Record<string, SearchChunk> = {};

// 将目录索引转换为以ID为键的Map，以便快速查找
const catalogMap = computed(() => {
  return new Map(catalogIndex.map(item => [item.id, item]));
});


// --- 数据加载 ---
async function loadCatalogIndex(game: string) {
  isLoading.value = true;
  error.value = null;
  results.value = [];
  searchQuery.value = '';
  hasSearched.value = false;
  catalogIndex = [];
  chunkCache = {}; // 切换游戏时清空所有缓存

  try {
    const response = await fetch(`/index_${game}.json`);
    if (!response.ok) throw new Error(`无法加载 ${game} 的目录索引文件。`);
    catalogIndex = await response.json();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '未知错误';
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

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

/**
 * 根据搜索词，按需、并行地加载所需的分片文件
 */
async function fetchSearchChunks(terms: string[]): Promise<void> {
  const game = appStore.currentGame;
  const requiredChars = new Set<string>();
  
  // 确定需要哪些分片文件
  terms.forEach(term => {
    if (term.length > 0) {
      const firstChar = term[0];
      // 如果分片尚未被缓存，则加入请求列表
      if (!chunkCache[firstChar]) {
        requiredChars.add(firstChar);
      }
    }
  });

  if (requiredChars.size === 0) {
    return; // 所有需要的分片都已在缓存中
  }

  // 并行请求所有未缓存的分片
  try {
    const searchDir = game === 'hsr' ? 'search_hsr' : 'search';
    const promises = Array.from(requiredChars).map(char =>
      fetch(`/${searchDir}/${char}.json`).then(res => {
        if (res.ok) return res.json();
        // 如果文件不存在（例如搜索了一个罕见的字），则返回一个空对象，而不是抛出错误
        if (res.status === 404) return {};
        throw new Error(`无法加载分片 ${char}.json`);
      })
    );
    const settledResults = await Promise.allSettled(promises);
    
    settledResults.forEach((result, index) => {
      const char = Array.from(requiredChars)[index];
      if (result.status === 'fulfilled') {
        chunkCache[char] = result.value; // 缓存加载到的分片
      } else {
        console.error(`加载分片 ${char} 失败:`, result.reason);
        chunkCache[char] = {}; // 即使失败也缓存空对象，避免重试
      }
    });
  } catch (e) {
    // 这个 catch 块可能不会被执行，因为 Promise.allSettled 不会短路
    error.value = e instanceof Error ? e.message : '加载搜索分片时发生未知错误';
  }
}

async function performSearch() {
  hasSearched.value = true;
  if (!searchQuery.value.trim() || catalogIndex.length === 0) {
    results.value = [];
    return;
  }

  isSearching.value = true;
  results.value = [];
  error.value = null;

  try {
    const queryBigrams = getBigrams(searchQuery.value);
    
    // 1. 确保所有需要的分片都已加载
    await fetchSearchChunks(queryBigrams);

    // 2. 获取每个二元组对应的ID列表
    const idSets: Set<number>[] = [];
    queryBigrams.forEach(bigram => {
      const firstChar = bigram[0];
      const chunk = chunkCache[firstChar];
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
watch(() => appStore.currentGame, (newGame) => {
  loadCatalogIndex(newGame);
});

onMounted(() => {
  loadCatalogIndex(appStore.currentGame);
});
</script>

<style scoped>
.search-view-v2 {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.search-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--m3-border-color-soft);
}
.search-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  font-size: 16px;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border: 1px solid transparent;
  border-radius: 8px;
}
.search-input:focus {
  outline: none;
  border-color: var(--m3-primary);
}
.search-button {
  height: 48px;
  border: none;
  border-radius: 8px;
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
  font-size: 16px;
  cursor: pointer;
}
.results-area {
  padding-top: 16px;
  overflow-y: auto;
  flex-grow: 1;
}
.error {
  color: var(--m3-error);
}
.search-results {
  list-style: none;
  padding: 0;
  margin: 0;
}
.result-item {
  display: block;
  padding: 12px 8px;
  margin: 4px 0;
  text-decoration: none;
  color: var(--m3-on-surface);
  border-radius: 8px;
  transition: background-color 0.2s;
}
.result-item:hover {
  background-color: var(--m3-surface-variant);
}
.result-type {
  font-size: 0.9rem;
  color: var(--m3-on-surface-variant);
  margin-right: 0.5rem;
}
.result-name {
  font-weight: 500;
}
</style>