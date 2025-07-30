import { ref, watch, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import 'github-markdown-css/github-markdown-light.css';
import { useDataStore } from '@/stores/data';
import MarkdownWorker from '@/workers/markdown.worker.ts?worker';
const route = useRoute();
const dataStore = useDataStore();
const contentHtml = ref('');
const isLoading = ref(false);
const error = ref(null);
let markdownWorker = new MarkdownWorker();
async function loadContent() {
    const { game } = route.params;
    if (!game) {
        error.value = '无效的游戏参数。';
        return;
    }
    isLoading.value = true;
    error.value = null;
    contentHtml.value = '';
    try {
        const urlPath = route.path;
        const mdPath = urlPath.replace(`/v2/${game}/category`, `/${game}_md`) + '.md';
        // Fetch markdown from dataStore (which handles caching)
        const markdownText = await dataStore.fetchMarkdownContent(mdPath);
        if (!markdownWorker) {
            throw new Error('Markdown parser worker is not available.');
        }
        // Post the markdown text to the worker for parsing
        markdownWorker.postMessage(markdownText);
        markdownWorker.onmessage = (event) => {
            if (event.data.error) {
                throw new Error(event.data.error);
            }
            contentHtml.value = event.data.html;
            isLoading.value = false;
        };
        markdownWorker.onerror = (event) => {
            throw new Error(`Markdown worker error: ${event.message}`);
        };
    }
    catch (e) {
        error.value = e instanceof Error ? e.message : '加载内容时发生未知错误。';
        isLoading.value = false;
        console.error(e);
    }
}
watch(() => route.path, loadContent, { immediate: true });
onUnmounted(() => {
    if (markdownWorker) {
        markdownWorker.terminate();
        markdownWorker = null;
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "detail-view" },
});
if (__VLS_ctx.error) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "error-state" },
    });
    (__VLS_ctx.error);
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "markdown-body" },
    });
    __VLS_asFunctionalDirective(__VLS_directives.vHtml)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.contentHtml) }, null, null);
}
/** @type {__VLS_StyleScopedClasses['detail-view']} */ ;
/** @type {__VLS_StyleScopedClasses['error-state']} */ ;
/** @type {__VLS_StyleScopedClasses['markdown-body']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            contentHtml: contentHtml,
            error: error,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=DetailView.vue.js.map