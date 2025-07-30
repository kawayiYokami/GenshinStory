import { ref, watch, computed } from 'vue';
import { useAppStore } from '@/stores/app';
import { useDataStore } from '@/stores/data';
import { storeToRefs } from 'pinia';
// --- 响应式状态 ---
const appStore = useAppStore();
const dataStore = useDataStore();
const { isLoading, error, indexData: catalogIndex } = storeToRefs(dataStore);
const searchQuery = ref('');
const isSearching = ref(false); // 搜索过程状态
const results = ref([]); // 结果现在是完整的目录条目
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
        const chunkPromises = queryBigrams.map(bigram => dataStore.fetchSearchChunk(appStore.currentGame, bigram[0]));
        const chunks = await Promise.all(chunkPromises);
        // 2. 获取每个二元组对应的ID列表
        const idSets = [];
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
    if (newGame) {
        // Clear search results when game changes
        results.value = [];
        searchQuery.value = '';
        hasSearched.value = false;
        // The dataStore now handles clearing its own caches when the game changes.
        dataStore.fetchIndex(newGame);
    }
}, { immediate: true });
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
            isLoading: isLoading,
            error: error,
            searchQuery: searchQuery,
            isSearching: isSearching,
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