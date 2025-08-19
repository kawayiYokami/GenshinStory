<template>
  <div class="w-full h-full flex flex-col bg-transparent">
    <div class="flex justify-between items-center py-2 px-4 bg-transparent">
      <span class="font-semibold text-base whitespace-nowrap overflow-hidden text-ellipsis" :title="docViewerStore.documentPath">{{ formattedTitle }}</span>
      <button class="bg-none border-none text-2xl cursor-pointer py-0 px-2" @click="docViewerStore.close()">×</button>
    </div>
    <div class="flex-1 overflow-y-auto relative">
      <div v-if="docViewerStore.isLoading" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>正在加载...</p>
      </div>
      <div v-else-if="docViewerStore.errorMessage" class="flex justify-center items-center h-full text-gray-500 italic">
        <p>{{ docViewerStore.errorMessage }}</p>
      </div>
      <div v-else class="py-4 px-10 max-w-4xl mx-auto">
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

  // Extracts "三月七-1001" from "characters/三月七-1001.md"
  const filename = path.split('/').pop().replace('.md', '');
  
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
