<template>
  <div class="document-viewer-sidebar">
    <div class="header">
      <span class="path" :title="docViewerStore.documentPath">{{ formattedTitle }}</span>
      <button class="close-btn" @click="docViewerStore.close()">×</button>
    </div>
    <div class="content">
      <div v-if="docViewerStore.isLoading" class="loading-overlay">
        <p>正在加载...</p>
      </div>
      <div v-else-if="docViewerStore.errorMessage" class="error-message">
        <p>{{ docViewerStore.errorMessage }}</p>
      </div>
      <div v-else class="markdown-body" v-html="renderedMarkdown"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useDocumentViewerStore } from '@/stores/documentViewer';
import MarkdownIt from 'markdown-it';
import 'github-markdown-css/github-markdown-light.css';

const docViewerStore = useDocumentViewerStore();

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

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
});

const renderedMarkdown = computed(() => {
  if (docViewerStore.documentContent) {
    return md.render(docViewerStore.documentContent);
  }
  return '';
});
</script>

<style scoped>
.document-viewer-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent; /* Inherit background from parent */
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: transparent; /* Inherit background from parent */
}

.path {
  font-weight: 600;
  font-size: 1em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 0.5rem;
}

.content {
  flex: 1;
  overflow-y: auto;
  position: relative;
}
/* 针对 Webkit 浏览器 (Chrome, Safari) 的悬停隐藏效果 */
.content::-webkit-scrollbar-thumb {
  background-color: transparent;
  transition: background-color 0.3s ease;
}
.content:hover::-webkit-scrollbar-thumb {
  background-color: #c1c1c1; /* 恢复默认或原有颜色 */
}
/* Firefox 的滚动条通常较细且半透明，悬停时可以变得更明显一些 */
.content {
  scrollbar-color: transparent transparent; /* thumb track */
  transition: scrollbar-color 0.3s ease;
}
.content:hover {
  scrollbar-color: #c1c1c1 transparent; /* thumb track */
}

.loading-overlay, .error-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #777;
  font-style: italic;
}

.markdown-body {
  padding: 1rem 2.5rem;
  max-width: 1000px;
  margin: 0 auto;
}
</style>

<style>
/* Global style override to make markdown background transparent */
.markdown-body {
  background-color: transparent !important;
}
</style>