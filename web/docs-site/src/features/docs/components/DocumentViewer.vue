<template>
  <div class="w-full h-full flex flex-col relative">
    <!-- 浮动关闭按钮 -->
    <button
      class="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-base-300/50 hover:bg-base-300/80 backdrop-blur-sm border border-base-300 flex items-center justify-center text-base-content/70 hover:text-base-content transition-all duration-200"
      @click="docViewerStore.close()"
      title="关闭文档"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- 可选：顶部标题条（仅在滚动时显示） -->
    <div class="sticky top-0 z-10 h-0 overflow-hidden">
      <div class="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-base-100/80 to-transparent backdrop-blur-sm">
        <span class="absolute left-4 top-3 font-semibold text-base whitespace-nowrap overflow-hidden text-ellipsis max-w-md" :title="docViewerStore.documentPath">
          {{ formattedTitle }}
        </span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto detail-scrollbar">
      <div v-if="docViewerStore.isLoading" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>正在加载...</p>
      </div>
      <div v-else-if="docViewerStore.errorMessage" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>{{ docViewerStore.errorMessage }}</p>
      </div>
      <div v-else class="px-10 max-w-3xl mx-auto">
        <MarkdownRenderer
          v-if="docViewerStore.documentContent"
          :markdownText="processedMarkdownText"
          :docId="docViewerStore.documentPath"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import MarkdownRenderer from '@/components/ui/MarkdownRenderer.vue';

const docViewerStore = useDocumentViewerStore();

// 转义正则表达式特殊字符
const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[$$\$$\\/]/g, '\\$&');
};

const formattedTitle = computed(() => {
  const path = docViewerStore.documentPath;
  if (!path) return '';

  // 安全获取文件名
  const pathParts = path.split('/');
  const lastPart = pathParts[pathParts.length - 1];
  if (!lastPart) return '';

  const filename = lastPart.replace('.md', '');

  // Extracts "三月七" and "1001"
  const match = filename.match(/^(.*?)-(\d+)$/);

  if (match) {
    const name = match[1];
    const id = match[2];
    return `${name} (ID: ${id})`;
  }

  // Fallback for other file formats
  return filename;
});

const processedMarkdownText = computed(() => {
  let content = docViewerStore.documentContent;
  const keywords = docViewerStore.highlightKeywords;

  if (!keywords || keywords.length === 0) {
    return content;
  }

  keywords.forEach(keyword => {
    if (keyword) {
      const escapedKeyword = escapeRegExp(keyword);
      // 使用 'gi' 标志进行全局、不区分大小写的匹配
      const regex = new RegExp(`(${escapedKeyword})`, 'gi');
      content = content.replace(regex, '<mark>$1</mark>');
    }
  });

  return content;
});
</script>

<style>
/* 详情区域滚动条样式 */
.detail-scrollbar {
  scrollbar-color: transparent transparent; /* Firefox: thumb track */
}

.detail-scrollbar:hover,
.detail-scrollbar:focus-within {
  scrollbar-color: hsl(var(--muted) / 0.3) transparent; /* Firefox: thumb track */
}

/* 针对 Webkit 浏览器 (Chrome, Safari) 的悬停隐藏效果 */
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
</style>
