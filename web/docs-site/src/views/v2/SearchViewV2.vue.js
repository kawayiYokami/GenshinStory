import { ref, watch, onMounted, computed } from 'vue';
import { useAppStore } from '@/stores/app';
// --- 响应式状态 ---
const appStore = useAppStore();
const searchQuery = ref('');
const isLoading = ref(true); // 初始加载目录
const isSearching = ref(false); // 搜索过程状态
const error = ref(null);
const results = ref([]); // 结果现在是完整的目录条目
const hasSearched = ref(false);
// --- 索引数据存储 ---
let catalogIndex = [];
// 缓存已加载的分片，key是分片名(如'旅'), value是分片内容
let chunkCache = {};
// 将目录索引转换为以ID为键的Map，以便快速查找
const catalogMap = computed(() => {
    return new Map(catalogIndex.map(item => [item.id, item]));
});
// --- 数据加载 ---
async function loadCatalogIndex(game) {
    isLoading.value = true;
    error.value = null;
    results.value = [];
    searchQuery.value = '';
    hasSearched.value = false;
    catalogIndex = [];
    chunkCache = {}; // 切换游戏时清空所有缓存
    try {
        const response = await fetch(`/index_${game}.json`);
        if (!response.ok)
            throw new Error(`无法加载 ${game} 的目录索引文件。`);
        catalogIndex = await response.json();
    }
    catch (e) {
        error.value = e instanceof Error ? e.message : '未知错误';
        console.error(e);
    }
    finally {
        isLoading.value = false;
    }
}
// --- 搜索逻辑 ---
/**
 * 将字符串切分为二字词组 (bigrams)
 */
function getBigrams(text) {
    const cleanedText = text.replace(/\s+/g, '').toLowerCase();
    if (cleanedText.length <= 1) {
        return [cleanedText];
    }
    const bigrams = new Set();
    for (let i = 0; i < cleanedText.length - 1; i++) {
        bigrams.add(cleanedText.substring(i, i + 2));
    }
    return Array.from(bigrams);
}
/**
 * 根据搜索词，按需、并行地加载所需的分片文件
 */
async function fetchSearchChunks(terms) {
    const game = appStore.currentGame;
    const requiredChars = new Set();
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
        const promises = Array.from(requiredChars).map(char => fetch(`/${searchDir}/${char}.json`).then(res => {
            if (res.ok)
                return res.json();
            // 如果文件不存在（例如搜索了一个罕见的字），则返回一个空对象，而不是抛出错误
            if (res.status === 404)
                return {};
            throw new Error(`无法加载分片 ${char}.json`);
        }));
        const settledResults = await Promise.allSettled(promises);
        settledResults.forEach((result, index) => {
            const char = Array.from(requiredChars)[index];
            if (result.status === 'fulfilled') {
                chunkCache[char] = result.value; // 缓存加载到的分片
            }
            else {
                console.error(`加载分片 ${char} 失败:`, result.reason);
                chunkCache[char] = {}; // 即使失败也缓存空对象，避免重试
            }
        });
    }
    catch (e) {
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
        const idSets = [];
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
        const finalResults = [];
        intersection.forEach(id => {
            const item = catalogMap.value.get(id);
            if (item) {
                finalResults.push(item);
            }
        });
        results.value = finalResults;
    }
    catch (e) {
        error.value = e instanceof Error ? e.message : '搜索时发生未知错误';
    }
    finally {
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
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['result-item']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "search-view-v2" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "search-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onKeyup: (__VLS_ctx.performSearch) },
    type: "text",
    value: (__VLS_ctx.searchQuery),
    placeholder: "在当前游戏内搜索...",
    ...{ class: "search-input" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.performSearch) },
    ...{ class: "search-button" },
});
if (__VLS_ctx.isLoading) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "results-area" },
    });
}
else if (__VLS_ctx.isSearching) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "results-area" },
    });
}
else if (__VLS_ctx.error) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "results-area error" },
    });
    (__VLS_ctx.error);
}
else if (__VLS_ctx.hasSearched && __VLS_ctx.results.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "results-area" },
    });
    (__VLS_ctx.searchQuery);
}
else if (__VLS_ctx.results.length > 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "results-area" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({
        ...{ class: "search-results" },
    });
    for (const [item] of __VLS_getVForSourceType((__VLS_ctx.results))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
            key: (item.id),
        });
        const __VLS_0 = {}.RouterLink;
        /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
        // @ts-ignore
        const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
            to: ({ path: item.path, query: { from: 'search' } }),
            ...{ class: "result-item" },
        }));
        const __VLS_2 = __VLS_1({
            to: ({ path: item.path, query: { from: 'search' } }),
            ...{ class: "result-item" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_1));
        __VLS_3.slots.default;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "result-type" },
        });
        (item.type);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "result-name" },
        });
        (item.name);
        var __VLS_3;
    }
}
/** @type {__VLS_StyleScopedClasses['search-view-v2']} */ ;
/** @type {__VLS_StyleScopedClasses['search-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['search-button']} */ ;
/** @type {__VLS_StyleScopedClasses['results-area']} */ ;
/** @type {__VLS_StyleScopedClasses['results-area']} */ ;
/** @type {__VLS_StyleScopedClasses['results-area']} */ ;
/** @type {__VLS_StyleScopedClasses['error']} */ ;
/** @type {__VLS_StyleScopedClasses['results-area']} */ ;
/** @type {__VLS_StyleScopedClasses['results-area']} */ ;
/** @type {__VLS_StyleScopedClasses['search-results']} */ ;
/** @type {__VLS_StyleScopedClasses['result-item']} */ ;
/** @type {__VLS_StyleScopedClasses['result-type']} */ ;
/** @type {__VLS_StyleScopedClasses['result-name']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            searchQuery: searchQuery,
            isLoading: isLoading,
            isSearching: isSearching,
            error: error,
            results: results,
            hasSearched: hasSearched,
            performSearch: performSearch,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=SearchViewV2.vue.js.map