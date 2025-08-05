<template>
  <div class="detail-view">
    <div v-if="error" class="error-state">{{ error }}</div>
    <template v-else>
      <div class="markdown-body" v-html="contentHtml"></div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import 'github-markdown-css/github-markdown-light.css';
import { useDataStore } from '@/stores/data';
import MarkdownWorker from '@/workers/markdown.worker.ts?worker';


const route = useRoute();
const dataStore = useDataStore();

const contentHtml = ref('');
const isLoading = ref(false);
const error = ref<string | null>(null);

let markdownWorker: Worker | null = new MarkdownWorker();

async function loadContent() {
  const { domain } = route.params;
  if (!domain) {
    error.value = '无效的领域参数。';
    return;
  }

  isLoading.value = true;
  error.value = null;
  contentHtml.value = '';

  try {
    const urlPath = route.path;
    // Example: /domain/gi/category/Book/some-book -> /domains/gi/docs/Book/some-book.md
    const mdPath = urlPath.replace(`/domain/${domain}/category`, `/domains/${domain}/docs`) + '.md';
    
    // Fetch markdown from dataStore (which handles caching)
    const markdownText = await dataStore.fetchMarkdownContent(mdPath);

    if (!markdownWorker) {
      throw new Error('Markdown parser worker is not available.');
    }

    // Post the markdown text to the worker for parsing
    markdownWorker.postMessage({ markdownText: markdownText, originalId: urlPath });

    markdownWorker.onmessage = (event) => {
      if (event.data.originalId !== route.path) {
        return; // Stale message, ignore.
      }
      if (event.data.error) {
        throw new Error(event.data.error);
      }
      contentHtml.value = event.data.html;
      isLoading.value = false;
    };

    markdownWorker.onerror = (event) => {
        throw new Error(`Markdown worker error: ${event.message}`);
    }

  } catch (e) {
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
</script>

<style scoped>
.detail-view {
  width: 100%;
}
.markdown-body {
  max-width: 800px;
  margin: 0 auto;
}
.loading-state, .error-state {
  padding: 24px;
  color: var(--m3-on-surface);
}
</style>

<style>
/* Global style override to make markdown background transparent and adjust line-height */
.markdown-body {
  background-color: transparent !important;
  line-height: 1.7;
}
</style>