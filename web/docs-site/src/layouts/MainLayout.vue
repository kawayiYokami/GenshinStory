<template>
  <div class="grid grid-cols-[120px_1fr] h-screen w-screen">
      <router-view name="nav" class="relative z-10 bg-background text-on-background overflow-y-auto" />
      <ResizablePanes class="overflow-hidden">
        <template #left>
          <div class="p-4 overflow-y-auto h-full bg-surface shadow-md">
            <component :is="functionComponent" />
          </div>
        </template>
        <template #right>
          <div class="p-4 overflow-y-auto h-full bg-background">
            <DocumentViewer v-if="docViewerStore.isVisible" />
            <div v-if="!docViewerStore.isVisible">
              <router-view name="detail" />
            </div>
          </div>
        </template>
      </ResizablePanes>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useTheme } from '@/composables/useTheme';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import type { Game } from '@/features/app/stores/app';
import { useDataStore } from '@/features/app/stores/data';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import ResizablePanes from '@/components/ResizablePanes.vue';

import DocumentViewer from '@/features/docs/components/DocumentViewer.vue';
import ItemListView from '@/features/docs/views/ItemListView.vue';
import SearchViewV2 from '@/features/search/views/SearchViewV2.vue';
import AgentChatView from '@/features/agent/views/AgentChatView.vue';

const route = useRoute();
const agentStore = useAgentStore();
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();

// Activate the global theme service
useTheme();


const componentMap = {
  'ItemListView': ItemListView,
  'SearchViewV2': SearchViewV2,
  'AgentChatView': AgentChatView
};

const functionComponent = computed(() => {
  const componentName = route.meta.functionPane as keyof typeof componentMap;
  if (componentName && componentMap[componentName]) {
    return componentMap[componentName];
  }
  return ItemListView;
});

// Watch for game changes in the route and update all relevant stores
// --- Application Initialization Orchestrator ---
async function initializeApplication(domain: string) {
  if (!domain) return;

  appStore.isCoreDataReady = false;
  
  // The order is critical here
  await dataStore.fetchIndex(domain);
  await agentStore.switchDomainContext(domain);

  appStore.isCoreDataReady = true;
}

watch(() => appStore.currentDomain, (newDomain, oldDomain) => {
  if (newDomain && newDomain !== oldDomain) {
    initializeApplication(newDomain);
  }
}, { immediate: true });


onMounted(async () => {
  // 1. Load domain list first
  await appStore.loadDomains();
  // 2. Initialize agent store from cache
  await agentStore.initializeStoreFromCache();
  // 3. Trigger the initial application setup based on the current domain
  // The watcher above will handle the first initialization.
});
</script>
