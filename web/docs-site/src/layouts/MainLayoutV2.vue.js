import { shallowRef, watch } from 'vue';
import { useRoute } from 'vue-router';
import ItemListView from '@/views/v2/ItemListView.vue';
import SearchViewV2 from '@/views/v2/SearchViewV2.vue';
import AgentChatView from '@/views/v2/AgentChatView.vue';
const route = useRoute();
const functionComponent = shallowRef(ItemListView); // Default component
const componentMap = {
    'ItemListView': ItemListView,
    'SearchViewV2': SearchViewV2,
    'AgentChatView': AgentChatView
};
// Watch for route changes to decide which component to show in the function pane
watch(() => route.name, (toName) => {
    console.log('--- Layout Watcher ---');
    console.log('Route Name:', toName);
    console.log('Route Meta:', route.meta);
    // When navigating to a detail view, we want to keep the function pane as it is.
    // The 'keepFunctionPane' meta field signals this intent.
    if (route.meta.keepFunctionPane) {
        console.log('Keeping function pane as is.');
        return;
    }
    const componentName = route.meta.functionPane;
    console.log('Target Component Name:', componentName);
    if (componentName && componentMap[componentName]) {
        functionComponent.value = componentMap[componentName];
        console.log('Switched to component:', componentName);
    }
    else {
        // Fallback to a default if the meta field is not set or invalid
        functionComponent.value = ItemListView;
        console.log('Fallback to default component: ItemListView');
    }
}, { immediate: true } // Run on initial load
);
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "layout-v2" },
});
const __VLS_0 = {}.RouterView;
/** @type {[typeof __VLS_components.RouterView, typeof __VLS_components.routerView, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    name: "nav",
    ...{ class: "nav-pane" },
}));
const __VLS_2 = __VLS_1({
    name: "nav",
    ...{ class: "nav-pane" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "content-panel" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "function-pane" },
});
const __VLS_4 = ((__VLS_ctx.functionComponent));
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({}));
const __VLS_6 = __VLS_5({}, ...__VLS_functionalComponentArgsRest(__VLS_5));
const __VLS_8 = {}.RouterView;
/** @type {[typeof __VLS_components.RouterView, typeof __VLS_components.routerView, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    name: "detail",
    ...{ class: "detail-pane" },
}));
const __VLS_10 = __VLS_9({
    name: "detail",
    ...{ class: "detail-pane" },
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
/** @type {__VLS_StyleScopedClasses['layout-v2']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['function-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['detail-pane']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            functionComponent: functionComponent,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=MainLayoutV2.vue.js.map