<template>
  <div class="layout-v2">
    <router-view name="nav" class="nav-pane" />
    <div class="content-panel">
      <!-- The function pane is now a dynamic component controlled by this layout -->
      <div class="function-pane">
        <component :is="functionComponent" />
      </div>
      <router-view name="detail" class="detail-pane" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { shallowRef, watch } from 'vue';
import { useRoute } from 'vue-router';
import ItemListView from '@/views/v2/ItemListView.vue';
import SearchViewV2 from '@/views/v2/SearchViewV2.vue';

const route = useRoute();
const functionComponent = shallowRef(ItemListView); // Default component

const componentMap = {
  'ItemListView': ItemListView,
  'SearchViewV2': SearchViewV2
};

// Watch for route changes to decide which component to show in the function pane
watch(
  () => route.name,
  (toName) => {
    // When navigating to a detail view, we want to keep the function pane as it is.
    // The 'keepFunctionPane' meta field signals this intent.
    if (route.meta.keepFunctionPane) {
      return;
    }

    const componentName = route.meta.functionPane as keyof typeof componentMap;
    if (componentName && componentMap[componentName]) {
      functionComponent.value = componentMap[componentName];
    } else {
      // Fallback to a default if the meta field is not set or invalid
      functionComponent.value = ItemListView;
    }
  },
  { immediate: true } // Run on initial load
);
</script>

<style scoped>
.layout-v2 {
  display: grid;
  grid-template-columns: 120px 1fr; /* Nav pane and the rest of the content */
  height: 100vh;
  width: 100vw;
  background-color: var(--genshin-bg-secondary);
}

.nav-pane {
  color: var(--genshin-text-secondary);
  overflow-y: auto;
}

.content-panel {
  display: grid;
  grid-template-columns: 300px 1fr; /* Function pane and Detail pane */
  background-color: var(--genshin-bg-primary);
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  overflow: hidden;
}

.function-pane {
  color: var(--genshin-text-primary);
  border-right: 1px solid #D3CFC6;
  padding: 16px;
  overflow-y: auto;
}

.detail-pane {
  color: var(--genshin-text-primary);
  padding: 24px;
  overflow-y: auto;
}
</style>