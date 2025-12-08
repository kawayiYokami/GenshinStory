<template>
  <div class="w-full h-full flex flex-col relative">
    <!-- 关闭按钮 -->
    <button
      class="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-base-300/50 hover:bg-base-300/80 backdrop-blur-sm border border-base-300 flex items-center justify-center text-base-content/70 hover:text-base-content transition-all duration-200"
      @click="docViewerStore.close()"
      title="关闭文档"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- 标题条 -->
    <div class="sticky top-0 z-10 h-0 overflow-hidden">
      <div class="absolute inset-x-0 top-0 h-12 bg-linear-to-b from-base-100/80 to-transparent backdrop-blur-sm">
        <span class="absolute left-4 top-3 font-semibold text-base whitespace-nowrap overflow-hidden text-ellipsis max-w-md" :title="docViewerStore.documentPath">
          {{ formattedTitle }}
        </span>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="flex-1 overflow-y-auto detail-scrollbar relative" ref="contentContainer">
      <div v-if="docViewerStore.isLoading" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>正在加载...</p>
      </div>
      <div v-else-if="docViewerStore.errorMessage" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>{{ docViewerStore.errorMessage }}</p>
      </div>
      <div v-else class="px-10 max-w-3xl mx-auto pb-20 pt-4">
        <!-- 直接传入原始 Markdown 内容，不再做正则处理 -->
        <MarkdownRenderer
          v-if="docViewerStore.documentContent"
          :markdownText="docViewerStore.documentContent"
          :docId="docViewerStore.documentPath"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, nextTick, ref, onUnmounted } from 'vue';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import MarkdownRenderer from '@/components/ui/MarkdownRenderer.vue';

const docViewerStore = useDocumentViewerStore();
const contentContainer = ref<HTMLElement | null>(null);

// ========================================================
// 核心逻辑：DOM 树遍历搜索 (TreeWalker)
// ========================================================
watch(() => [docViewerStore.highlightKeywords, docViewerStore.documentContent, docViewerStore.isLoading],
  async ([keywords, content, isLoading]) => {
    // 确保 keywords 是数组类型
    const keywordsArray = Array.isArray(keywords) ? keywords : [];

    // 确保内容已加载且有关键词
    if (!isLoading && content && keywordsArray.length > 0) {
      await nextTick(); // 等待 Vue 渲染完成

      // 给一点时间让浏览器布局完成 (保险起见)
      setTimeout(() => {
        // 取第一个关键词进行跳转
        findAndScrollToText(keywordsArray[0]);
      }, 100);
    }
  },
  { deep: true }
);

const findAndScrollToText = (searchText: string) => {
  if (!contentContainer.value || !searchText) return;

  const container = contentContainer.value;
  const searchLower = searchText.toLowerCase();

  // 清除旧的高亮边框
  clearHighlights();

  // --- 终极方案：TreeWalker ---
  // 它能遍历 DOM 中所有的“纯文本节点”，无视 div/span/p 的层级结构
  const walker = document.createTreeWalker(
    container,
    NodeFilter.SHOW_TEXT,
    null
  );

  let node: Node | null;
  let targetNode: Node | null = null;

  // 遍历所有文字
  while ((node = walker.nextNode())) {
    if (node.nodeValue && node.nodeValue.toLowerCase().includes(searchLower)) {
      targetNode = node;
      break; // 找到第一个匹配的就停止
    }
  }

  if (targetNode && targetNode.parentElement) {
    const parentEl = targetNode.parentElement;

    // 1. 滚动
    parentEl.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });

    // 2. 高亮 (画一个框)
    highlightElement(parentEl);
  } else {
    console.warn('[DocumentViewer] 未在 DOM 中找到文本:', searchText);
  }
};

// ========================================================
// 辅助函数：画框与样式管理
// ========================================================
const highlightElement = (el: HTMLElement) => {
  // 简单粗暴：直接给目标元素加一个 class
  // 注意：这里去掉了 setTimeout，高亮会一直存在直到下一次搜索
  el.classList.add('search-target-highlight');
};

const clearHighlights = () => {
  if (!contentContainer.value) return;
  // 移除所有旧的高亮类
  const old = contentContainer.value.querySelectorAll('.search-target-highlight');
  old.forEach(el => el.classList.remove('search-target-highlight'));
};

// 完整还原之前的标题格式化逻辑
const formattedTitle = computed(() => {
  const path = docViewerStore.documentPath;
  if (!path) return '';

  // 安全获取文件名
  const pathParts = path.split('/');
  const lastPart = pathParts[pathParts.length - 1];
  if (!lastPart) return '';

  const filename = lastPart.replace('.md', '');

  // Extracts "三月七" and "1001" from "三月七-1001"
  const match = filename.match(/^(.*?)-(\d+)$/);

  if (match) {
    const name = match[1];
    const id = match[2];
    return `${name} (ID: ${id})`;
  }

  // Fallback
  return filename;
});

// 组件卸载时清理
onUnmounted(() => {
  clearHighlights();
});
</script>

<style>
/* 详情区域滚动条样式 */
.detail-scrollbar {
  scrollbar-color: transparent transparent;
}

.detail-scrollbar:hover,
.detail-scrollbar:focus-within {
  scrollbar-color: hsl(var(--muted) / 0.3) transparent;
}

.detail-scrollbar::-webkit-scrollbar-thumb {
  background-color: transparent;
}

.detail-scrollbar:hover::-webkit-scrollbar-thumb,
.detail-scrollbar:focus-within::-webkit-scrollbar-thumb {
  background-color: hsl(var(--muted) / 0.3);
}

.detail-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--muted) / 0.5);
}

/*
  高亮样式
  position: relative 是为了让 ::after 伪元素定位
*/
.search-target-highlight {
  position: relative;
  /* 去掉了动画，使用固定背景色，永久显示 */
  background-color: rgba(250, 204, 21, 0.2);
  border-radius: 4px;
  transition: background-color 0.3s;
}

/* 使用伪元素画一个显眼的框，不影响原本布局 */
.search-target-highlight::after {
  content: '';
  position: absolute;
  inset: -4px; /* 向外扩一点，包住文字 */
  border: 2px solid #facc15; /* 黄色边框 */
  border-radius: 6px;
  pointer-events: none;
  z-index: 10;
}
</style>