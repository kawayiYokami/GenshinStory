<template>
  <div class="flex-1 overflow-hidden">
    <SmartLayout
      v-model:show-detail="docViewerStore.isVisible"
      detail-aria-label="文档详情"
      @close="docViewerStore.close"
    >
      <template #function>
        <component :is="functionComponent" />
      </template>
      <template #detail>
        <DocumentViewer />
      </template>
    </SmartLayout>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import SmartLayout from '@/components/SmartLayout.vue';
import DocumentViewer from '@/features/docs/components/DocumentViewer.vue';
import ItemListView from '@/features/docs/views/ItemListView.vue';
import SearchView from '@/features/search/views/SearchView.vue';
import AgentChatView from '@/features/agent/views/AgentChatView.vue';
import SettingsView from '@/features/settings/views/SettingsView.vue';

interface ComponentMap {
  [key: string]: any;
}

// Component Mapping for Main View
const componentMap: ComponentMap = {
  'ItemListView': ItemListView,
  'SearchView': SearchView,
  'AgentChatView': AgentChatView,
  'SettingsView': SettingsView
};

const route = useRoute();
const docViewerStore = useDocumentViewerStore();

const functionComponent = computed(() => {
  const componentName = route.meta.functionPane as keyof ComponentMap;
  return componentMap[componentName] || ItemListView;
});
</script>