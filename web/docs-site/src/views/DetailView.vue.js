import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';
import 'github-markdown-css/github-markdown-light.css';
const route = useRoute();
const contentHtml = ref('');
const isLoading = ref(false);
const error = ref(null);
async function loadContent() {
    // 从路由中解构出 game 参数
    const { game } = route.params;
    if (!game) {
        error.value = '无效的游戏参数。';
        return;
    }
    isLoading.value = true;
    error.value = null;
    try {
        // 1. 从 route.path 获取当前页面的完整 URL 路径
        // 例如: /v2/gi/category/weapon/单手剑/西风剑-11401
        const urlPath = route.path;
        // 2. 将 URL 路径转换为实际的 Markdown 文件路径
        // 将 /v2/gi/category/ 替换为 /gi_md/
        const mdPath = urlPath.replace(`/v2/${game}/category`, `/${game}_md`) + '.md';
        // 3. 发起 fetch 请求
        const mdResponse = await fetch(mdPath);
        if (!mdResponse.ok) {
            if (mdResponse.status === 404) {
                throw new Error(`文件未找到: ${mdPath}`);
            }
            throw new Error(`Markdown 文件加载失败: ${mdResponse.statusText}`);
        }
        const markdownText = await mdResponse.text();
        contentHtml.value = await marked(markdownText);
    }
    catch (e) {
        error.value = e instanceof Error ? e.message : '加载内容时发生未知错误。';
        contentHtml.value = ''; // 清空旧内容
        console.error(e);
    }
    finally {
        isLoading.value = false;
    }
}
watch(() => route.path, loadContent, { immediate: true });
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