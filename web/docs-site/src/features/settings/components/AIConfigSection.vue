<template>
  <div class="card card-border bg-base-100 shadow-md mb-6">
    <div class="card-body">
      <h2 class="card-title mb-6">AI 配置</h2>

      <!-- Config Management -->
      <div v-if="configs.length > 0" class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <label class="text-sm font-medium">当前配置</label>
          <div class="flex gap-2">
            <button
              @click="handleAddNewConfig"
              :disabled="configs.length >= 13"
              class="btn btn-sm btn-primary"
              title="新建配置"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/><path d="M12 5v14"/>
              </svg>
              新建
            </button>
            <button
              @click="openNoKeyModal"
              class="btn btn-sm btn-secondary"
              title="获取免费API Key"
            >
              我没有key
            </button>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <DaisyDropdown
            :model-value="activeConfigId || undefined"
            :options="configOptions"
            placeholder="选择配置"
            :disabled="isFetchingModels"
            @update:modelValue="handleSelectConfig"
            class="flex-1"
          />

          <button
            @click="handleRenameConfig"
            :disabled="!activeConfig"
            class="btn btn-sm btn-ghost"
            title="重命名"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              <path d="m15 5 4 4"/>
            </svg>
          </button>

          <button
            @click="handleDeleteConfig"
            :disabled="!activeConfig"
            class="btn btn-sm btn-ghost text-error"
            title="删除"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              <line x1="10" x2="10" y1="11" y2="17"/>
              <line x1="14" x2="14" y1="11" y2="17"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Configuration Form -->
      <div v-if="activeConfig" class="space-y-4">
        <div class="space-y-4">
          <div>
            <label class="label label-text" for="api-url">API URL</label>
            <input
              id="api-url"
              type="text"
              v-model="activeConfig.apiUrl"
              placeholder="例如: https://api.openai.com/v1"
              class="input input-bordered w-full"
            />
          </div>

          <div>
            <label class="label label-text" for="api-key">API Key</label>
            <input
              id="api-key"
              type="password"
              v-model="activeConfig.apiKey"
              placeholder="请输入您的 API Key"
              class="input input-bordered w-full"
            />
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label class="label label-text" for="model-select">Model</label>
            <div class="flex gap-2">
              <DaisyDropdown
                :model-value="activeConfig.modelName || undefined"
                :options="modelOptions"
                :placeholder="!activeConfig.availableModels || activeConfig.availableModels.length === 0 ? '请先设置有效的 API Key 并刷新' : undefined"
                :disabled="isFetchingModels || (!activeConfig.availableModels || activeConfig.availableModels.length === 0)"
                @update:model-value="value => { if (activeConfig) activeConfig.modelName = value as string }"
                class="flex-1"
              />
              <button
                @click="fetchModels"
                class="btn btn-square"
                :disabled="!activeConfig.apiKey || isFetchingModels"
                title="刷新模型列表"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                  <path d="M21 3v5h-5"/>
                  <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                  <path d="M3 21v-5h5"/>
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label class="label label-text" for="max-tokens">上下文上限 (Max Tokens)</label>
            <DaisyDropdown
              :model-value="activeConfig.maxTokens || undefined"
              :options="maxTokensOptions"
              @update:model-value="value => { if (activeConfig) activeConfig.maxTokens = Number(value) }"
              class="w-full"
            />
          </div>
        </div>

        <div class="space-y-3">
          <div class="text-sm font-medium">
            温度 (Temperature): {{ activeConfig.temperature.toFixed(1) }}
          </div>
          <div>
            <input
              id="temperature-range"
              type="range"
              v-model.number="activeConfig.temperature"
              min="0"
              max="2"
              step="0.1"
              class="range w-full"
              aria-label="温度设置"
            />
            <div class="flex justify-between text-xs text-base-content/70 mt-1">
              <span>保守</span>
              <span>平衡</span>
              <span>创新</span>
            </div>
          </div>
        </div>

        <div>
          <label class="label label-text" for="request-interval">请求间隔 (毫秒)</label>
          <input
            id="request-interval"
            type="number"
            v-model.number="activeConfig.requestInterval"
            min="0"
            step="100"
            class="input input-bordered w-full"
          />
        </div>

        <div class="form-control">
          <label class="label cursor-pointer" for="stream-checkbox">
            <span class="label-text">启用流式输出</span>
            <input
              id="stream-checkbox"
              type="checkbox"
              v-model="activeConfig.stream"
              class="checkbox"
            />
          </label>
        </div>

        <!-- Debug options can be added back when showRawContent is implemented in config store -->
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto mb-4 text-base-content/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
        </svg>
        <p class="text-base-content/70 mb-4">您还没有任何 AI 配置</p>
        <button @click="handleAddNewConfig" class="btn btn-primary">
          立即创建第一个配置
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/features/app/stores/config';
import logger from '@/features/app/services/loggerService';
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue';

// Stores
const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, addConfig, updateConfig, deleteConfig, setActiveConfig } = configStore;

// Props
const props = defineProps({
  domains: {
    type: Array,
    required: true
  }
});

// Emits
const emit = defineEmits(['switchDomain', 'openNoKeyModal']);

// Computed properties
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

const maxTokensOptions = [
  { value: 4096, label: '4K' },
  { value: 8192, label: '8K' },
  { value: 16384, label: '16K' },
  { value: 32768, label: '32K' },
  { value: 65536, label: '64K' },
  { value: 131072, label: '128K' },
  { value: 153600, label: '150K' },
  { value: 204800, label: '200K' },
  { value: 262144, label: '256K' },
  { value: 524288, label: '512K' },
  { value: 1048576, label: '1024K' }
];

// Methods
const handleAddNewConfig = () => {
  logger.log('--- UI: AddNewConfig button clicked. ---');
  if (configs.value.length >= 13) {
    alert("配置数量已达到13个的上限。");
    return;
  }
  addConfig();
};

const handleDeleteConfig = () => {
  if (!activeConfig.value || !activeConfigId.value) return;
  logger.log(`--- UI: DeleteConfig button clicked for config: ${activeConfig.value.name} (${activeConfigId.value}) ---`);
  if (confirm(`确定要删除配置 "${activeConfig.value.name}" 吗？此操作无法撤销。`)) {
    logger.log('--- UI: Deletion confirmed by user. ---');
    deleteConfig(activeConfigId.value);
  } else {
    logger.log('--- UI: Deletion cancelled by user. ---');
  }
};

const handleRenameConfig = () => {
  if (!activeConfig.value || !activeConfigId.value) return;
  logger.log(`--- UI: RenameConfig button clicked for config: ${activeConfig.value.name} (${activeConfigId.value}) ---`);
  const oldName = activeConfig.value.name;
  const newName = prompt("请输入新的配置名称：", oldName);
  if (newName && newName.trim() !== "" && newName.trim() !== oldName) {
    logger.log(`--- UI: New name "${newName}" provided. Calling updateConfig. ---`);
    updateConfig(activeConfigId.value, { name: newName.trim() });
  } else {
    logger.log(`--- UI: Rename cancelled or name unchanged. ---`);
  }
};

const handleSelectConfig = (value: string | number) => {
  const id = String(value);
  logger.log(`--- UI: Config <select> changed. New ID selected: ${id}. Calling setActiveConfig. ---`);
  if (id) {
    setActiveConfig(id);
  }
};

const switchDomain = (domain: string) => {
  emit('switchDomain', domain);
};

const openNoKeyModal = () => {
  emit('openNoKeyModal');
};
</script>