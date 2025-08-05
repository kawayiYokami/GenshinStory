<template>
  <div class="layout-v2">
    <router-view name="nav" class="nav-pane" />
    <splitpanes class="content-panel" @resized="savePaneSizes">
      <pane :size="paneSizes[0]">
        <div class="function-pane">
          <component :is="functionComponent" />
        </div>
      </pane>
      <pane :size="paneSizes[1]">
        <div class="detail-pane">
          <DocumentViewer v-if="docViewerStore.isVisible" />
          <div v-if="!docViewerStore.isVisible">
            <router-view name="detail" />
          </div>
        </div>
      </pane>
    </splitpanes>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useAgentStore } from '@/stores/agentStore';
import { useAppStore, Game } from '@/stores/app';
import { useDataStore } from '@/stores/data';
import { useDocumentViewerStore } from '@/stores/documentViewer';
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';

import DocumentViewer from '@/components/DocumentViewer.vue';
import ItemListView from '@/views/v2/ItemListView.vue';
import SearchViewV2 from '@/views/v2/SearchViewV2.vue';
import AgentChatView from '@/views/v2/AgentChatView.vue';

const route = useRoute();
const agentStore = useAgentStore();
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();

// --- Pane Size Management ---
const PANE_SIZES_KEY = 'pane-sizes-v2';
const getDefaultPaneSizes = () => (route.name === 'v2-agent' ? [65, 35] : [30, 70]);

const getValidPaneSizes = () => {
  try {
    const storedValue = localStorage.getItem(PANE_SIZES_KEY);
    if (storedValue) {
      const parsed = JSON.parse(storedValue);
      // Validate that it's an array of two numbers
      if (Array.isArray(parsed) && parsed.length === 2 && parsed.every(item => typeof item === 'number')) {
        return parsed;
      }
    }
  } catch (error) {
    console.error("Error parsing pane sizes from localStorage:", error);
  }
  // If anything fails, return the default
  return getDefaultPaneSizes();
};

const paneSizes = ref(getValidPaneSizes());

const savePaneSizes = (panes: unknown) => {
  // Type guard to ensure we have a valid array of panes
  if (Array.isArray(panes) && panes.every(p => typeof p.size === 'number')) {
    const sizes = panes.map(p => p.size);
    paneSizes.value = sizes;
    localStorage.setItem(PANE_SIZES_KEY, JSON.stringify(sizes));
  }
};

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

<style scoped>
.layout-v2 {
  display: grid;
  grid-template-columns: 120px 1fr;
  height: 100vh;
  width: 100vw;
  background-color: var(--genshin-bg-secondary);
}

.nav-pane {
  color: var(--genshin-text-secondary);
  overflow-y: auto;
}

.content-panel {
  background-color: var(--genshin-bg-primary);
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  overflow: hidden;
}

.function-pane,
.detail-pane {
  color: var(--genshin-text-primary);
  padding: 16px;
  overflow-y: auto;
  height: 100%;
}

</style>

<style>
/* Global styles for the splitter */
.splitpanes__splitter {
  background-color: transparent !important; /* Make the wide area invisible */
  position: relative;
  width: 9px !important; /* Increase clickable area */
  border: none !important;
  cursor: col-resize;
}

/* The visible line, which also acts as the hover/drag indicator */
.splitpanes__splitter:before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 1px; /* Default state: thin line */
  height: 100%; /* Default state: full height */
  background-color: var(--m3-border-color-soft);
  opacity: 1; /* Always visible */
  transition: all 0.2s ease-in-out;
}

.splitpanes--dragging .splitpanes__splitter:before,
.splitpanes__splitter:hover:before {
  width: 2px; /* Hover/drag state: thicker */
  height: 40px; /* Hover/drag state: shorter indicator */
  background-color: var(--genshin-accent-gold);
}

/* Prevent text selection while dragging */
.splitpanes--dragging {
  user-select: none;
}
</style>