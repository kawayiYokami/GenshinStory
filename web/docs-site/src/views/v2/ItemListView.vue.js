import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '@/stores/app';
import { ElAutoResizer } from 'element-plus/es/components/table-v2/index.mjs';
import { FixedSizeList as ElVirtualList } from 'element-plus/es/components/virtual-list/index.mjs';
import 'element-plus/es/components/virtual-list/style/css';
const route = useRoute();
const appStore = useAppStore();
const isLoading = ref(false);
const error = ref(null);
const fullIndex = ref([]);
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
    return fullIndex.value.filter(item => item.type.toLowerCase().startsWith(category.value.toLowerCase()));
});
async function loadIndex(game) {
    isLoading.value = true;
    error.value = null;
    try {
        // 修正：加载正确的、用于列表展示的目录索引文件
        const response = await fetch(`/index_${game}.json`);
        if (!response.ok)
            throw new Error(`索引文件加载失败: ${response.statusText}`);
        fullIndex.value = await response.json();
    }
    catch (e) {
        error.value = e instanceof Error ? e.message : '未知错误';
        console.error(e);
    }
    finally {
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
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['item-link']} */ ;
/** @type {__VLS_StyleScopedClasses['item-link']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "item-list-view" },
});
const __VLS_0 = {}.ElAutoResizer;
/** @type {[typeof __VLS_components.ElAutoResizer, typeof __VLS_components.elAutoResizer, typeof __VLS_components.ElAutoResizer, typeof __VLS_components.elAutoResizer, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({}));
const __VLS_2 = __VLS_1({}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
{
    const { default: __VLS_thisSlot } = __VLS_3.slots;
    const [{ height }] = __VLS_getSlotParams(__VLS_thisSlot);
    if (__VLS_ctx.isLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "status-info" },
        });
    }
    else if (__VLS_ctx.error) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "status-info error" },
        });
        (__VLS_ctx.error);
    }
    else {
        const __VLS_4 = {}.ElVirtualList;
        /** @type {[typeof __VLS_components.ElVirtualList, typeof __VLS_components.elVirtualList, typeof __VLS_components.ElVirtualList, typeof __VLS_components.elVirtualList, ]} */ ;
        // @ts-ignore
        const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
            data: (__VLS_ctx.filteredItems),
            total: (__VLS_ctx.filteredItems.length),
            itemSize: (45),
            height: (height),
            ...{ class: "item-list" },
        }));
        const __VLS_6 = __VLS_5({
            data: (__VLS_ctx.filteredItems),
            total: (__VLS_ctx.filteredItems.length),
            itemSize: (45),
            height: (height),
            ...{ class: "item-list" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_5));
        __VLS_7.slots.default;
        {
            const { default: __VLS_thisSlot } = __VLS_7.slots;
            const [{ index, style }] = __VLS_getSlotParams(__VLS_thisSlot);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (__VLS_ctx.filteredItems[index].id),
                ...{ style: (style) },
            });
            const __VLS_8 = {}.RouterLink;
            /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
            // @ts-ignore
            const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
                to: (`${__VLS_ctx.filteredItems[index].path}?from=category`),
                ...{ class: "item-link" },
                activeClass: "router-link-exact-active",
            }));
            const __VLS_10 = __VLS_9({
                to: (`${__VLS_ctx.filteredItems[index].path}?from=category`),
                ...{ class: "item-link" },
                activeClass: "router-link-exact-active",
            }, ...__VLS_functionalComponentArgsRest(__VLS_9));
            __VLS_11.slots.default;
            (__VLS_ctx.filteredItems[index].name);
            var __VLS_11;
        }
        var __VLS_7;
    }
}
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['item-list-view']} */ ;
/** @type {__VLS_StyleScopedClasses['status-info']} */ ;
/** @type {__VLS_StyleScopedClasses['status-info']} */ ;
/** @type {__VLS_StyleScopedClasses['error']} */ ;
/** @type {__VLS_StyleScopedClasses['item-list']} */ ;
/** @type {__VLS_StyleScopedClasses['item-link']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            ElAutoResizer: ElAutoResizer,
            ElVirtualList: ElVirtualList,
            isLoading: isLoading,
            error: error,
            filteredItems: filteredItems,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=ItemListView.vue.js.map