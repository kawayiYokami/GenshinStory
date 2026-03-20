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
          <select
            :value="activeConfigId || ''"
            @change="handleSelectConfig"
            class="select select-bordered flex-1"
            :disabled="isFetchingModels"
          >
            <option value="" disabled>选择配置</option>
            <option v-for="config in configs" :key="config.id" :value="config.id">
              {{ config.name }}
            </option>
          </select>

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
      <div v-if="activeConfig && draftConfig" class="space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-sm font-bold" :class="isDirty ? 'text-warning' : 'text-success'">
            {{ isDirty ? '检测到未保存更改' : '当前配置已保存' }}
          </span>
          <div class="flex gap-2">
            <button
              class="btn btn-sm btn-secondary"
              :disabled="!isDirty"
              @click="resetDraft"
            >
              还原
            </button>
            <button
              class="btn btn-sm btn-primary"
              :disabled="!isDirty || !activeConfig"
              @click="saveConfig"
            >
              保存配置
            </button>
          </div>
        </div>
        <div v-if="saveMessages.length > 0" role="alert" class="alert alert-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="h-6 w-6 shrink-0 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span class="whitespace-pre-line">{{ saveMessages.join('\n') }}</span>
        </div>

        <div class="space-y-4">
          <div>
            <label class="label label-text" for="api-url">
              API URL
              <span class="text-xs text-base-content/60 ml-2">
                (自动识别: gemini → Gemini, deepseek/kimi → DeepSeek, 其他 → OpenAI Compatible)
              </span>
            </label>
            <input
              id="api-url"
              type="text"
              v-model="draftConfig.apiUrl"
              placeholder="例如: https://api.openai.com/v1"
              class="input input-bordered w-full"
            />
          </div>

          <div>
            <label class="label label-text" for="api-key">API Key</label>
            <input
              id="api-key"
              type="password"
              v-model="draftConfig.apiKey"
              placeholder="请输入您的 API Key"
              class="input input-bordered w-full"
            />
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label class="label label-text" for="model-select">Model</label>
            <div class="flex gap-2">
              <!-- 文本输入框 -->
              <input
                type="text"
                :value="draftConfig.modelName"
                @input="handleModelInput"
                placeholder="输入模型名称"
                class="input input-bordered flex-1"
              />

              <!-- 下拉选择按钮 -->
              <div ref="modelDropdownRef" class="relative">
                <button
                  class="btn btn-square"
                  :disabled="!activeConfig.availableModels?.length"
                  title="从列表选择"
                  @click.stop="toggleModelDropdown"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m6 9 6 6 6-6"/>
                  </svg>
                </button>
                <div
                  v-if="isModelDropdownOpen"
                  class="absolute right-0 top-full mt-2 z-30 flex flex-col shadow bg-base-100 rounded-box w-80 max-h-80 overflow-hidden border border-base-300"
                  @click.stop
                >
                  <input
                    v-model="modelSearch"
                    type="text"
                    placeholder="搜索模型..."
                    class="input input-bordered min-h-24 text-base w-full border-x-0 border-t-0 focus:outline-none"
                    @click.stop
                    @keydown.esc="isModelDropdownOpen = false"
                  />
                  <ul class="menu flex-col flex-nowrap flex-1 overflow-auto p-1">
                    <li v-for="model in filteredModels" :key="model">
                      <button class="whitespace-normal wrap-break-word text-left" @click="selectModel(model)">{{ model }}</button>
                    </li>
                    <li v-if="filteredModels.length === 0" class="text-center text-sm opacity-50 py-2">
                      {{ activeConfig.availableModels?.length ? '无匹配结果' : '暂无模型列表' }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- 刷新按钮 -->
              <button
                @click="fetchModels"
                class="btn btn-square"
                :disabled="isFetchingModels"
                :class="{ 'loading': isFetchingModels }"
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
            <div class="flex items-center justify-between">
              <label class="label label-text py-0">上下文上限 (Max Context)</label>
              <span class="text-sm opacity-70">{{ formatContextLength(draftConfig.maxContextLength) }}</span>
            </div>
            <input
              type="range"
              v-model.number="draftConfig.maxContextLength"
              min="4096"
              max="1048576"
              step="4096"
              class="range range-sm w-full"
            />
            <div class="flex justify-between text-xs opacity-60 mt-1">
              <span>4K</span>
              <span>512K</span>
              <span>1024K</span>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div class="text-sm font-medium">
            温度 (Temperature): {{ draftConfig.temperature.toFixed(1) }}
          </div>
          <div>
            <input
              id="temperature-range"
              type="range"
              v-model.number="draftConfig.temperature"
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
            v-model.number="draftConfig.requestInterval"
            min="0"
            step="100"
            class="input input-bordered w-full"
          />
        </div>

        <div>
          <label class="label label-text" for="max-iterations">最大迭代次数 (Max Iterations)</label>
          <input
            id="max-iterations"
            type="number"
            v-model.number="draftConfig.maxIterations"
            min="0"
            step="1"
            class="input input-bordered w-full"
          />
          <label class="label label-text-alt text-base-content/70">
            设置为 0 表示无限制
          </label>
        </div>

        <div class="form-control">
          <label class="label cursor-pointer" for="stream-checkbox">
            <span class="label-text">启用流式输出</span>
            <input
              id="stream-checkbox"
              type="checkbox"
              v-model="draftConfig.stream"
              class="checkbox"
            />
          </label>
        </div>

        <!-- 自定义参数 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">自定义参数</label>
            <button
              @click="addCustomParam"
              class="btn btn-sm btn-ghost"
              title="添加自定义参数"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/><path d="M12 5v14"/>
              </svg>
              添加参数
            </button>
          </div>

          <div v-for="(param, index) in draftConfig.customParams" :key="index" class="flex gap-2 items-center">
            <input
              type="text"
              v-model="param.key"
              placeholder="参数名 (如: top_k)"
              class="input input-bordered input-sm flex-1"
            />
            <input
              type="text"
              v-model="param.value"
              placeholder="参数值 (如: 50)"
              class="input input-bordered input-sm flex-1"
            />
            <button
              @click="removeCustomParam(index)"
              class="btn btn-sm btn-ghost btn-square text-error"
              title="删除参数"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
              </svg>
            </button>
          </div>

          <div class="text-xs text-base-content/70 bg-base-200 p-3 rounded-md">
            <div class="font-medium mb-1">常见的格式（如果不知道什么是标头请不要修改）：</div>
            <div class="space-y-1">
              <div>• <code class="bg-base-300 px-1 rounded">enable_thinking</code> - 启用思考模式 (true/false)</div>
            </div>
          </div>
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/features/app/stores/config';
import logger from '@/features/app/services/loggerService';
import type { Config, CustomParam } from '@/features/app/stores/config';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '/api';
const METADATA_TIMEOUT_MS = 8000;
const DEFAULT_MAX_CONTEXT_LENGTH = 262144; // 256K
const DEFAULT_MAX_ITERATIONS = 100;

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

// Local state
const modelSearch = ref('');
const isModelDropdownOpen = ref(false);
const modelDropdownRef = ref<HTMLElement | null>(null);
const draftConfig = ref<Config | null>(null);
const originalSnapshot = ref('');
const saveMessages = ref<string[]>([]);

const cloneCustomParams = (params?: CustomParam[]): CustomParam[] => {
  return (params || []).map(param => ({ key: param.key, value: param.value }));
};

const normalizeForCompare = (config: Config) => {
  return {
    apiUrl: config.apiUrl ?? '',
    apiKey: config.apiKey ?? '',
    modelName: config.modelName ?? '',
    temperature: config.temperature ?? 0.7,
    stream: config.stream ?? true,
    maxContextLength: config.maxContextLength ?? DEFAULT_MAX_CONTEXT_LENGTH,
    requestInterval: config.requestInterval ?? 1000,
    maxIterations: config.maxIterations ?? DEFAULT_MAX_ITERATIONS,
    customParams: cloneCustomParams(config.customParams),
  };
};

const snapshotConfig = (config: Config): string => {
  return JSON.stringify(normalizeForCompare(config));
};

watch(
  activeConfig,
  (config: Config | null) => {
    if (!config) {
      isModelDropdownOpen.value = false;
      modelSearch.value = '';
      draftConfig.value = null;
      originalSnapshot.value = '';
      saveMessages.value = [];
      return;
    }
    draftConfig.value = {
      ...config,
      customParams: cloneCustomParams(config.customParams),
    };
    originalSnapshot.value = snapshotConfig(draftConfig.value);
  },
  { immediate: true }
);

// Computed properties
const filteredModels = computed(() => {
  const models = activeConfig.value?.availableModels || [];
  const search = modelSearch.value.toLowerCase().trim();
  if (!search) return models;
  return models.filter((model: string) => model.toLowerCase().includes(search));
});

const isDirty = computed(() => {
  if (!draftConfig.value || !originalSnapshot.value) return false;
  return snapshotConfig(draftConfig.value) !== originalSnapshot.value;
});

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

const handleSelectConfig = (event: Event) => {
  const id = (event.target as HTMLSelectElement).value;
  logger.log(`--- UI: Config <select> changed. New ID selected: ${id}. Calling setActiveConfig. ---`);
  if (id) {
    setActiveConfig(id);
  }
};

const handleModelInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const value = target.value;
  if (draftConfig.value) {
    draftConfig.value.modelName = value;
  }
};

const toggleModelDropdown = () => {
  if (!activeConfig.value?.availableModels?.length) return;
  isModelDropdownOpen.value = !isModelDropdownOpen.value;
  if (!isModelDropdownOpen.value) {
    modelSearch.value = '';
  }
};

const selectModel = (modelName: string) => {
  if (draftConfig.value) {
    draftConfig.value.modelName = modelName;
    modelSearch.value = '';
    isModelDropdownOpen.value = false;
  }
};

const handleDocumentClick = (event: MouseEvent) => {
  const root = modelDropdownRef.value;
  if (!root) return;
  if (!root.contains(event.target as Node)) {
    isModelDropdownOpen.value = false;
    modelSearch.value = '';
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleDocumentClick);
});

const formatContextLength = (value: number): string => {
  if (value >= 1024) {
    return `${value / 1024}K`;
  }
  return String(value);
};

const switchDomain = (domain: string) => {
  emit('switchDomain', domain);
};

const openNoKeyModal = () => {
  emit('openNoKeyModal');
};

// 自定义参数相关方法
const addCustomParam = () => {
  if (!draftConfig.value) return;

  if (!draftConfig.value.customParams) {
    draftConfig.value.customParams = [];
  }

  draftConfig.value.customParams.push({
    key: '',
    value: ''
  });

  logger.log('--- UI: Added new custom parameter ---');
};

const removeCustomParam = (index: number) => {
  if (!draftConfig.value?.customParams) return;

  const removed = draftConfig.value.customParams.splice(index, 1)[0];
  logger.log(`--- UI: Removed custom parameter: ${removed.key} ---`);
};

const saveConfig = async () => {
  if (!activeConfig.value || !draftConfig.value) return;
  if (!isDirty.value) return;
  const notices: string[] = [];
  saveMessages.value = [];

  // 先尝试获取模型元数据，自动设置上下文上限
  const modelName = draftConfig.value.modelName?.trim();
  if (modelName) {
    draftConfig.value.modelName = modelName;
    const requestedContext = draftConfig.value.maxContextLength;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), METADATA_TIMEOUT_MS);
    try {
      const response = await fetch(`${BACKEND_URL}/api/models/metadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName }),
        signal: controller.signal,
      });
      if (response.ok) {
        const data = await response.json() as { found?: boolean; context_window?: number | null };
        if (data.found && typeof data.context_window === 'number') {
          const modelLimit = Math.max(4096, Math.min(data.context_window, 1048576));
          if (requestedContext > modelLimit) {
            draftConfig.value.maxContextLength = modelLimit;
            notices.push(
              `你设置的上下文是 ${formatContextLength(requestedContext)}，超过该模型上限 ${formatContextLength(modelLimit)}，已自动调整为 ${formatContextLength(modelLimit)}。`
            );
            logger.log(`[Model Metadata] 上下文超限，自动调整: ${requestedContext} -> ${modelLimit}`);
          } else {
            notices.push(
              `该模型最大上下文约为 ${formatContextLength(modelLimit)}，你当前设置为 ${formatContextLength(requestedContext)}。`
            );
          }

          const recommendedAttentionWindow = 204800; // 200K
          if (modelLimit >= 1048576 && requestedContext > recommendedAttentionWindow) {
            notices.push(
              `提示：一般模型有效注意力大约在 200K 左右，即使支持 1M 上下文，也建议设置为 200K 以提升注意力利用率并降低费用。`
            );
          }
        }
      } else {
        logger.warn(`[Model Metadata] 请求失败: ${response.status}`);
      }
    } catch (error) {
      logger.warn('[Model Metadata] 获取模型元数据失败:', error);
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  updateConfig(activeConfig.value.id, {
    apiUrl: draftConfig.value.apiUrl,
    apiKey: draftConfig.value.apiKey,
    modelName: draftConfig.value.modelName,
    temperature: draftConfig.value.temperature,
    stream: draftConfig.value.stream,
    maxContextLength: draftConfig.value.maxContextLength,
    requestInterval: draftConfig.value.requestInterval,
    maxIterations: draftConfig.value.maxIterations,
    customParams: cloneCustomParams(draftConfig.value.customParams),
  });

  originalSnapshot.value = snapshotConfig(draftConfig.value);
  logger.log('--- UI: 配置已手动保存 ---');

  if (notices.length > 0) {
    saveMessages.value = notices;
  }
};

const resetDraft = () => {
  if (!activeConfig.value) return;
  draftConfig.value = {
    ...activeConfig.value,
    customParams: cloneCustomParams(activeConfig.value.customParams),
  };
  originalSnapshot.value = snapshotConfig(draftConfig.value);
  saveMessages.value = [];
  logger.log('--- UI: 草稿已还原 ---');
};
</script>

<style scoped>
/* Scrollbar hover effect - hide by default, show on hover */
:deep(.overflow-y-auto::-webkit-scrollbar) {
  width: 6px;
}

:deep(.overflow-y-auto::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.overflow-y-auto::-webkit-scrollbar-thumb) {
  background-color: transparent;
  border-radius: 3px;
  transition: background-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover::-webkit-scrollbar-thumb) {
  background-color: #c1c1c1;
}

/* Firefox scrollbar */
:deep(.overflow-y-auto) {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
  transition: scrollbar-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover) {
  scrollbar-color: #c1c1c1 transparent;
}
</style>
