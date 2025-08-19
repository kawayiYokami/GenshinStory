<template>
  <div class="prose-styling-container" v-html="htmlContent"></div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import 'github-markdown-css/github-markdown-light.css';
import MarkdownWorker from '@/workers/markdown.worker.ts?worker';

const props = defineProps({
  markdownText: {
    type: String,
    required: true,
  },
  docId: {
    type: String,
    required: true,
  }
});

const htmlContent = ref('');
let markdownWorker: Worker | null = new MarkdownWorker();

watch(() => [props.markdownText, props.docId], ([newText, newId]) => {
  if (markdownWorker && newText) {
    markdownWorker.postMessage({ markdownText: newText, originalId: newId });
  }
}, { immediate: true });

if (markdownWorker) {
  markdownWorker.onmessage = (event) => {
    // Only update if the processed ID matches the current docId prop
    if (event.data.originalId === props.docId) {
      htmlContent.value = event.data.html;
    }
  };

  markdownWorker.onerror = (event) => {
    console.error(`Markdown worker error: ${event.message}`);
  };
}

onUnmounted(() => {
  if (markdownWorker) {
    markdownWorker.terminate();
    markdownWorker = null;
  }
});
</script>