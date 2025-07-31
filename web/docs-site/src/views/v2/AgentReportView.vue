<template>
  <div class="agent-report-container">
    <div class="main-content" :class="{ 'sidebar-visible': docViewerStore.isVisible }">
      <h4>最近一次请求 Body</h4>
      <div v-if="lastRequest" class="request-panel">
        <pre>{{ formattedRequest }}</pre>
      </div>
      <div v-else class="no-request-panel">
        <p>尚未发送任何请求。</p>
      </div>
    </div>
    
    <DocumentViewer v-if="docViewerStore.isVisible" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { lastRequest } from '@/services/loggerService';
import { useDocumentViewerStore } from '@/stores/documentViewer';
import DocumentViewer from '@/components/DocumentViewer.vue';

const docViewerStore = useDocumentViewerStore();

const formattedRequest = computed(() => {
  if (lastRequest.value) {
    return JSON.stringify(lastRequest.value, null, 2);
  }
  return '';
});
</script>

<style scoped>
.agent-report-container {
  display: flex;
  height: 100%;
}

.main-content {
  flex: 1;
  padding: 1rem;
  transition: width 0.3s ease-in-out;
  width: 100%;
  height: 100%;
}

.main-content.sidebar-visible {
  width: 60%; /* Adjust as needed */
}

h4 {
  margin-top: 0;
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.5rem;
}

.request-panel {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
  height: calc(100% - 50px); /* Adjust height as needed */
}

.request-panel pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.no-request-panel {
  color: #777;
  font-style: italic;
}
</style>