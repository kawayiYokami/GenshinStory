import { ref, watch } from 'vue';
import { useAppStore } from '@/stores/app';
import { useDataStore } from '@/stores/data';
import { storeToRefs } from 'pinia';

// --- 响应式状态 ---
const appStore = useAppStore();
const dataStore = useDataStore();
const { isLoading, error } = storeToRefs(dataStore); // Removed unused catalogIndex
const searchQuery = ref('');
const isSearching = ref(false);
const results = ref([]);
const hasSearched = ref(false);

// --- 搜索逻辑 (现在代理到 dataStore) ---
async function performSearch() {
    hasSearched.value = true;
    if (!searchQuery.value.trim()) {
        results.value = [];
        return;
    }

    isSearching.value = true;
    error.value = null; // Clear previous errors
    
    try {
        results.value = await dataStore.searchCatalog(searchQuery.value);
    } catch (e) {
        // The error is already set inside the store, but we can log it here if needed
        console.error("Search failed in view:", e);
        results.value = [];
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