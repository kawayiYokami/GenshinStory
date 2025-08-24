<template>
  <div class="flex gap-2">
    <!-- API URL Selector -->
    <select
      :value="activeConfigId"
      @change="handleConfigChange(($event.target as HTMLSelectElement).value)"
      class="select select-bordered select-sm flex-1"
      :disabled="isFetchingModels"
    >
      <option v-for="config in configs" :key="config.id" :value="config.id">
        {{ config.name }}
      </option>
    </select>

    <!-- Model Selector -->
    <select
      v-model="currentModel"
      class="select select-bordered select-sm flex-1"
      :disabled="isFetchingModels || !activeConfig"
    >
      <option v-if="!activeConfig?.availableModels || activeConfig.availableModels.length === 0" disabled value="">
        请先设置有效的 API Key
      </option>
      <option v-for="model in activeConfig?.availableModels || []" :key="model" :value="model">
        {{ model }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/features/app/stores/config';

const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, setActiveConfig } = configStore;

// Current model for v-model
const currentModel = computed({
  get: () => activeConfig.value?.modelName || '',
  set: (value: string) => {
    if (activeConfig.value && value !== activeConfig.value.modelName) {
      configStore.updateConfig(activeConfigId.value!, { modelName: value });
    }
  }
});

// Handle config change
const handleConfigChange = (configId: string) => {
  if (configId) {
    setActiveConfig(configId);
  }
};

// Watch for active config changes and ensure model is synchronized
watch(() => activeConfig.value?.modelName, (newModelName) => {
  if (newModelName !== currentModel.value) {
    // This ensures the v-model stays in sync
    currentModel.value = newModelName || '';
  }
});
</script>

<style scoped>
/* No styles needed - clean appearance */
</style>