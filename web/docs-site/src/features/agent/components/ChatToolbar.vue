<template>
  <div class="flex justify-between items-center px-4 pb-3">
    <!-- 左侧工具组 -->
    <div class="flex gap-1">
      <!-- AI 供应商选择 -->
      <DaisyDropdown
        :model-value="activeConfigId || undefined"
        :options="configOptions"
        placeholder="选择配置"
        @update:modelValue="value => handleConfigChange(value as string)"
      />

      <!-- 模型选择 -->
      <DaisyDropdown
        :model-value="currentModel || undefined"
        :options="modelOptions"
        placeholder="选择模型"
        @update:modelValue="value => handleModelChange(value as string)"
      />
    </div>

    <!-- 右侧工具组 -->
    <div class="flex gap-1">
      <!-- 调试按钮 (仅在开发模式下显示) -->
      <button
        v-if="isDevMode"
        @click="toggleDebugPanel"
        class="debug-panel-btn"
        title="调试面板"
      >
        <Wrench class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { storeToRefs } from 'pinia';
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue';
import { Wrench } from 'lucide-vue-next';

// Stores
const configStore = useConfigStore();
const agentStore = useAgentStore();

const { configs, activeConfigId, activeConfig } = storeToRefs(configStore);
const { fetchModels, setActiveConfig } = configStore;
const { resetAgent } = agentStore;

// Props
const props = defineProps({
  showRawContent: {
    type: Boolean,
    default: false,
  },
  currentModel: {
    type: String,
    default: ''
  }
});

// Emits
const emit = defineEmits(['update:showRawContent', 'update:currentModel']);

// Local state
const isDevMode = import.meta.env.DEV;

// Methods
const toggleDebugPanel = () => {
  emit('update:showRawContent', !props.showRawContent);
};

// 下拉框选项
const configOptions = computed(() => {
  return configs.value.map(config => ({
    value: config.id,
    label: config.name
  }));
});

const modelOptions = computed(() => {
  if (!activeConfig.value?.availableModels) return []
  return activeConfig.value.availableModels.map(model => ({
    value: model,
    label: model
  }))
});

// Toolbar actions
const handleConfigChange = (configId: string) => {
  if (configId) {
    setActiveConfig(configId);
  }
};

const handleModelChange = (model: string) => {
  emit('update:currentModel', model);
  // 保存到配置中
  if (activeConfig.value && activeConfigId.value) {
    configStore.updateConfig(activeConfigId.value, { modelName: model });
  }
};

const handleNewChat = () => {
  resetAgent();
};
</script>