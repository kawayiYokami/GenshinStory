<template>
  <div class="border-b border-outline">
    <div class="flex justify-between items-center p-1">
      <button class="btn btn-ghost btn-sm flex items-center gap-2" @click="isConfigVisible = !isConfigVisible">
        <span v-if="activeConfig">{{ activeConfig.name || '选择配置' }}</span>
        <span v-else>请先创建配置</span>
        <svg :class="isConfigVisible ? 'rotate-180' : ''" class="transition-transform duration-200" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div class="flex justify-end gap-2.5">
        <button @click.stop="$emit('history-click')" title="历史会话" class="btn-header-action">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16.5 12"/><line x1="12" y1="12" x2="12" y2="16.5"/></svg>
        </button>

        <DropdownMenu v-model:open="isNewChatMenuOpen">
          <template #trigger>
            <button title="新对话" class="btn-header-action">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
            </button>
          </template>
          <DropdownMenuItem
            v-for="agent in availableAgents[currentDomain]"
            :key="agent.id"
            @click="handleNewChatWithAgent(agent.id)"
          >
            {{ agent.name }}
          </DropdownMenuItem>
        </DropdownMenu>
      </div>
    </div>
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-300 cubic-bezier(1, 0.5, 0.8, 1)"
      enter-from-class="transform -translate-y-2.5 opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-[600px]"
      leave-from-class="opacity-100 max-h-[600px]"
      leave-to-class="transform -translate-y-2.5 opacity-0 max-h-0"
    >
      <div v-if="isConfigVisible" class="pt-4 px-1 overflow-hidden">
        <div>
          <div v-if="configs.length > 0" class="flex flex-col mb-3">
            <label for="config-selector" class="text-xs mb-1 text-(--m3-on-surface)">当前配置</label>
            <div class="flex items-center gap-2">
              <FormSelect
                id="config-selector"
                :modelValue="activeConfigId"
                @update:modelValue="handleSelectConfig"
                :disabled="isFetchingModels"
              >
                <option v-for="config in configs" :key="config.id" :value="config.id">
                  {{ config.name }}
                </option>
              </FormSelect>
              <div class="flex">
                <button @click="handleAddNewConfig" :disabled="configs.length >= 13" title="新建配置" class="flex items-center justify-center w-7 h-7 bg-transparent border-none rounded-full cursor-pointer text-(--m3-on-surface-variant) hover:bg-(--m3-surface-variant) hover:text-(--m3-primary)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                </button>
                <button @click="handleRenameConfig" :disabled="!activeConfig" title="重命名" class="flex items-center justify-center w-7 h-7 bg-transparent border-none rounded-full cursor-pointer text-(--m3-on-surface-variant) hover:bg-(--m3-surface-variant) hover:text-(--m3-primary)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                </button>
                <button @click="handleDeleteConfig" :disabled="!activeConfig" title="删除" class="flex items-center justify-center w-7 h-7 bg-transparent border-none rounded-full cursor-pointer text-(--m3-on-surface-variant) hover:bg-(--m3-surface-variant) hover:text-(--m3-primary)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
        <hr class="border-0 h-px bg-(--m3-outline) my-4">
        <div v-if="activeConfig" class="flex flex-col">
          <div class="max-h-[300px] overflow-y-auto pr-2 mb-4">
            <div class="flex flex-col mb-3">
              <label for="api-url" class="text-xs mb-1 text-(--m3-on-surface)">API URL</label>
              <FormInput id="api-url" type="text" v-model="activeConfig.apiUrl" placeholder="例如: https://api.openai.com/v1" />
            </div>
            <div class="flex flex-col mb-3">
              <label for="api-key" class="text-xs mb-1 text-(--m3-on-surface)">API Key</label>
              <FormInput id="api-key" type="password" v-model="activeConfig.apiKey" placeholder="请输入您的 API Key" />
            </div>
            <div class="flex flex-col mb-3">
              <label for="model-name" class="text-xs mb-1 text-(--m3-on-surface)">Model</label>
              <div class="flex items-center gap-2">
                <FormSelect id="model-name" v-model="activeConfig.modelName" :disabled="isFetchingModels">
                  <option v-if="!activeConfig.availableModels || activeConfig.availableModels.length === 0" disabled value="">
                    请先设置有效的 API Key 并刷新
                  </option>
                  <option v-for="model in activeConfig.availableModels" :key="model" :value="model">
                    {{ model }}
                  </option>
                </FormSelect>
                <button @click.stop="fetchModels" class="flex items-center justify-center w-7 h-7 bg-transparent border-none rounded-full cursor-pointer text-(--m3-on-surface-variant) hover:bg-(--m3-surface-variant) hover:text-(--m3-primary)" :disabled="!activeConfig.apiKey || isFetchingModels" title="刷新模型列表">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
                </button>
              </div>
            </div>
            <div class="grid grid-cols-1 gap-3">
              <div class="flex flex-col mb-3">
                <label for="max-tokens" class="text-xs mb-1 text-(--m3-on-surface)">上下文上限 (Max Tokens)</label>
                <FormSelect id="max-tokens" v-model.number="activeConfig.maxTokens">
                  <option value="4096">4K</option>
                  <option value="8192">8K</option>
                  <option value="16384">16K</option>
                  <option value="32768">32K</option>
                  <option value="65536">64K</option>
                  <option value="131072">128K</option>
                  <option value="262144">256K</option>
                </FormSelect>
              </div>
              <div class="flex flex-col mb-3">
                <label for="temperature" class="text-xs mb-1 text-(--m3-on-surface)">温度 (Temperature): {{ activeConfig.temperature.toFixed(1) }}</label>
                <input id="temperature" type="range" v-model.number="activeConfig.temperature" min="0" max="2" step="0.1" class="w-full" />
              </div>
              <div class="flex flex-col mb-3">
                <label for="request-interval" class="text-xs mb-1 text-(--m3-on-surface)">请求间隔 (毫秒)</label>
                <FormInput id="request-interval" type="number" v-model.number="activeConfig.requestInterval" min="0" step="100" />
              </div>
              <div class="flex items-center mb-3">
                <label class="flex items-center cursor-pointer gap-2">
                  <input id="stream-output" type="checkbox" v-model="activeConfig.stream" class="sr-only" />
                  <span class="w-5 h-5 bg-(--m3-surface) border border-(--m3-outline) rounded flex items-center justify-center">
                    <svg v-if="activeConfig.stream" class="w-3 h-3 text-(--m3-on-surface)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                  </span>
                  <span class="text-sm text-(--m3-on-surface)">启用流式输出</span>
                </label>
              </div>
              <div v-if="isDevMode" class="flex items-center mb-3">
                <label class="flex items-center cursor-pointer gap-2">
                  <input id="show-raw" type="checkbox" v-model="localShowRawContent" class="sr-only" />
                  <span class="w-5 h-5 bg-(--m3-surface) border border-(--m3-outline) rounded flex items-center justify-center">
                    <svg v-if="localShowRawContent" class="w-3 h-3 text-(--m3-on-surface)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                  </span>
                  <span class="text-sm text-(--m3-on-surface)">显示源码 (Debug)</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div v-if="configs.length === 0" class="text-center p-5">
          <p>您还没有任何AI配置。</p>
          <button @click="handleAddNewConfig" class="bg-(--m3-primary) text-(--m3-on-primary) py-2 px-4 rounded-lg border-none cursor-pointer mt-2.5">立即创建第一个</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import FormInput from '@/components/forms/FormInput.vue';
import FormSelect from '@/components/forms/FormSelect.vue';
import DropdownMenu from '@/components/ui/DropdownMenu.vue';
import DropdownMenuItem from '@/components/ui/DropdownMenuItem.vue';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import logger from '@/features/app/services/loggerService';

// This component now encapsulates all logic for configuration.

// --- Stores ---
const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, addConfig, updateConfig, deleteConfig, setActiveConfig } = configStore;

const agentStore = useAgentStore();
const { availableAgents } = storeToRefs(agentStore);
const { startNewChatWithAgent } = agentStore;

const appStore = useAppStore();
const { currentDomain } = storeToRefs(appStore);

// --- Emits & Props ---
const emit = defineEmits(['update:showRawContent', 'history-click']);
const props = defineProps({
  showRawContent: {
    type: Boolean,
    required: true,
  }
});

// --- Local UI State ---
const isConfigVisible = ref(false);
const isNewChatMenuOpen = ref(false);
const isDevMode = import.meta.env.DEV;

// Create a local computed property to use with v-model on the input
const localShowRawContent = computed({
  get: () => props.showRawContent,
  set: (value) => emit('update:showRawContent', value),
});


// --- Config Management Methods ---
const handleAddNewConfig = () => {
  logger.log('--- UI: AddNewConfig button clicked. ---');
  if (configs.value.length >= 13) {
    alert("配置数量已达到13个的上限。");
    return;
  }
  const newConfig = addConfig();
  if (newConfig) {
    isConfigVisible.value = true;
  }
};

const handleDeleteConfig = () => {
  if (!activeConfig.value) return;
  logger.log(`--- UI: DeleteConfig button clicked for config: ${activeConfig.value.name} (${activeConfigId.value}) ---`);
  if (confirm(`确定要删除配置 "${activeConfig.value.name}" 吗？此操作无法撤销。`)) {
    logger.log('--- UI: Deletion confirmed by user. ---');
    deleteConfig(activeConfigId.value);
  } else {
    logger.log('--- UI: Deletion cancelled by user. ---');
  }
};

const handleRenameConfig = () => {
  if (!activeConfig.value) return;
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

const handleSelectConfig = (id) => {
  logger.log(`--- UI: Config <select> changed. New ID selected: ${id}. Calling setActiveConfig. ---`);
  setActiveConfig(id);
};

const handleNewChatWithAgent = (roleId) => {
  startNewChatWithAgent(roleId);
  isNewChatMenuOpen.value = false; // Explicitly close the menu after an action
};
</script>

<style scoped lang="postcss">
/* All dropdown styles are now handled by the reusable DropdownMenu component. */

/* --- Configuration Section (styles are now applied directly in the template) --- */
.config-header {
  display: flex;
  justify-content: space-between; /* Align items to start and end */
  align-items: center;
}
.model-display-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: transparent;
  /* border: 1px solid var(--color-outline); REMOVED */
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.9em;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background-color 0.2s;
}
.model-display-button:hover {
  background-color: var(--color-surface-variant);
}
.model-display-button svg {
  transition: transform 0.2s;
}
.model-display-button svg.is-expanded {
  transform: rotate(180deg);
}
/* This overly broad rule has been removed and replaced by the .btn-header-action component class */
.config-panel {
  padding: 16px 4px 0;
  overflow: hidden;
}

/* --- Transition Animation --- */
.slide-fade-enter-active {
  transition: all 300ms ease-out;
  will-change: transform, opacity, max-height;
}
.slide-fade-leave-active {
  transition: all 300ms cubic-bezier(1, 0.5, 0.8, 1);
  will-change: transform, opacity, max-height;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
  max-height: 0;
}
.slide-fade-enter-to,
.slide-fade-leave-from {
  max-height: 600px; /* Adjust as needed */
  opacity: 1;
}

.config-management-row {
  margin-bottom: 16px;
  padding-bottom: 12px;
  /* border-bottom: 1px solid var(--color-outline); REMOVED */
}
.config-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
/* All form styles are now handled by reusable components */
.config-selector-wrapper select {
  flex-grow: 1;
}
.model-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.model-selector-wrapper select {
  flex-grow: 1;
}
/* --- New Icon Button Style --- */
.config-actions, .refresh-button {
    display: flex;
}
.config-actions button, .refresh-button {
    background: transparent;
    border: none;
    padding: 4px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    color: var(--color-on-surface-variant);
    flex-shrink: 0; /* Prevent button from shrinking */
}
.config-actions button:hover, .refresh-button:hover {
    background-color: var(--color-surface-variant);
    color: var(--color-primary);
}
.config-actions button:disabled, .refresh-button:disabled {
  color: var(--color-outline);
  cursor: not-allowed;
  background-color: transparent;
}
/* .empty-config-state styles are now applied directly in the template */

/* All form element styles are now encapsulated in their respective components */
/* in the @/components/forms/ directory. */

.config-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}
.config-item label {
  font-size: 0.8rem;
  margin-bottom: 4px;
  color: var(--color-on-surface);
}

.config-options-scroll-area {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding-right: 8px; /* 为滚动条留出一些空间 */
}

.config-panel-divider {
  border: 0;
  height: 1px;
  background-color: var(--color-outline);
  margin: 16px 0;
}
/* .button-group styles are now applied directly in the template */

/* --- Custom Checkbox --- */
.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  gap: 8px;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  height: 20px;
  width: 20px;
  background-color: var(--color-surface); /* 与面板背景一致 */
  border: 1px solid var(--color-outline); /* 减小边框宽度 */
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.checkbox-container input:checked ~ .checkmark {
  background-color: var(--color-surface); /* 选中时背景色保持不变 */
  border-color: var(--color-primary); /* 选中时边框变为主色 */
}

.checkmark::after {
  content: "";
  display: none;
  width: 6px;
  height: 12px;
  border: solid var(--color-on-surface); /* 与文本颜色一致 */
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(0, -1px);
}

.checkbox-container input:checked ~ .checkmark::after {
  display: block;
}

.label-text {
  font-size: 0.9rem;
  color: var(--color-on-surface);
}
</style>