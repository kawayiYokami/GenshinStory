<template>
  <div class="config-section">
    <div class="config-header">
      <button class="model-display-button" @click="isConfigVisible = !isConfigVisible">
        <span v-if="activeConfig">{{ activeConfig.name || '选择配置' }}</span>
        <span v-else>请先创建配置</span>
        <svg :class="{ 'is-expanded': isConfigVisible }" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div class="button-group">
          <button @click.stop="$emit('history-click')" title="历史会话">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 6H3"/><path d="M21 12H3"/><path d="M21 18H3"/></svg>
          </button>
        <button @click.stop="$emit('new-chat-click')" title="新对话">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>
    </div>
    <transition name="slide-fade">
      <div v-if="isConfigVisible" class="config-panel">
        <div v-if="configs.length > 0" class="config-item config-management-row">
            <label for="config-selector">当前配置</label>
            <div class="config-selector-wrapper">
            <select
              id="config-selector"
              :value="activeConfigId"
              @change="handleSelectConfig($event.target.value)"
              :disabled="isFetchingModels"
            >
              <option v-for="config in configs" :key="config.id" :value="config.id">
                {{ config.name }}
              </option>
            </select>
            <div class="config-actions">
              <button @click="handleAddNewConfig" :disabled="configs.length >= 13" title="新建配置">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              </button>
              <button @click="handleRenameConfig" :disabled="!activeConfig" title="重命名">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
              </button>
              <button @click="handleDeleteConfig" :disabled="!activeConfig" title="删除">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
              </button>
            </div>
          </div>
      </div>

      <div v-if="activeConfig" class="config-details">
        <div class="config-item">
          <label for="api-url">API URL</label>
          <input id="api-url" type="text" v-model="activeConfig.apiUrl" placeholder="例如: https://api.openai.com/v1" />
        </div>
        <div class="config-item">
          <label for="api-key">API Key</label>
          <input id="api-key" type="password" v-model="activeConfig.apiKey" placeholder="请输入您的 API Key" />
        </div>
        <div class="config-item">
          <label for="model-name">Model</label>
          <div class="model-selector-wrapper">
            <select id="model-name" v-model="activeConfig.modelName" :disabled="isFetchingModels">
              <option v-if="!activeConfig.availableModels || activeConfig.availableModels.length === 0" disabled value="">
                请先设置有效的 API Key 并刷新
              </option>
              <option v-for="model in activeConfig.availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
            <button @click.stop="fetchModels" class="refresh-button" :disabled="!activeConfig.apiKey || isFetchingModels" title="刷新模型列表">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
            </button>
          </div>
        </div>
        <div class="config-grid">
            <div class="config-item">
              <label for="max-tokens">上下文上限 (Max Tokens)</label>
              <select id="max-tokens" v-model.number="activeConfig.maxTokens">
                <option value="4096">4K</option>
                <option value="8192">8K</option>
                <option value="16384">16K</option>
                <option value="32768">32K</option>
                <option value="65536">64K</option>
                <option value="131072">128K</option>
                <option value="262144">256K</option>
              </select>
            </div>
            <div class="config-item">
              <label for="temperature">温度 (Temperature): {{ activeConfig.temperature.toFixed(1) }}</label>
              <input id="temperature" type="range" v-model.number="activeConfig.temperature" min="0" max="2" step="0.1" />
            </div>
            <div class="config-item">
              <label for="request-interval">请求间隔 (毫秒)</label>
              <input id="request-interval" type="number" v-model.number="activeConfig.requestInterval" min="0" step="100" />
            </div>
              <div class="config-item switch-item">
              <label for="stream-output">启用流式输出</label>
              <label class="switch">
                <input id="stream-output" type="checkbox" v-model="activeConfig.stream">
                <span class="slider round"></span>
              </label>
            </div>
            <div v-if="isDevMode" class="config-item switch-item">
              <label for="show-raw">显示源码 (Debug)</label>
              <label class="switch">
                <input id="show-raw" type="checkbox" v-model="localShowRawContent">
                <span class="slider round"></span>
              </label>
            </div>
        </div>
      </div>
      
      <div v-if="configs.length === 0" class="empty-config-state">
        <p>您还没有任何AI配置。</p>
        <button @click="handleAddNewConfig" class="button-primary">立即创建第一个</button>
      </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/stores/config';
import logger from '@/services/loggerService';

// This component now encapsulates all logic for configuration.

// --- Stores ---
const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, addConfig, updateConfig, deleteConfig, setActiveConfig } = configStore;

// --- Emits & Props ---
const emit = defineEmits(['update:showRawContent', 'history-click', 'new-chat-click']);
const props = defineProps({
  showRawContent: {
    type: Boolean,
    required: true,
  }
});

// --- Local UI State ---
const isConfigVisible = ref(false);
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
}
</script>

<style scoped>
/* --- Configuration Section --- */
.config-section {
  padding-bottom: 10px;
  border-bottom: 1px solid var(--m3-outline);
}
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
  border: 1px solid var(--m3-outline);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.9em;
  color: var(--m3-on-surface);
  cursor: pointer;
  transition: background-color 0.2s;
}
.model-display-button:hover {
  background-color: var(--m3-surface-variant);
}
.model-display-button svg {
  transition: transform 0.2s;
}
.model-display-button svg.is-expanded {
  transform: rotate(180deg);
}
.config-header button {
  background: none;
  border: none;
  color: var(--m3-primary);
  cursor: pointer;
  font-weight: 500;
}
.config-panel {
  padding: 16px 4px 0;
  overflow: hidden;
}

/* --- Transition Animation --- */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
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
  border-bottom: 1px solid var(--m3-outline);
}
.config-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
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
    color: var(--m3-on-surface-variant);
    flex-shrink: 0; /* Prevent button from shrinking */
}
.config-actions button:hover, .refresh-button:hover {
    background-color: var(--m3-surface-variant);
    color: var(--m3-primary);
}
.config-actions button:disabled, .refresh-button:disabled {
  color: var(--m3-outline);
  cursor: not-allowed;
  background-color: transparent;
}
.empty-config-state {
  text-align: center;
  padding: 20px;
}
.empty-config-state .button-primary {
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
}
.config-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}
.config-item label {
  font-size: 0.8rem;
  margin-bottom: 4px;
  color: var(--m3-on-surface-variant);
}
.config-item input, .config-item select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid var(--m3-outline);
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  width: 100%;
}
.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  align-items: center;
}
.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.button-group button {
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s, color 0.2s;
  background-color: transparent;
  color: var(--m3-on-surface-variant);
  border: none;
}
.button-group button:hover {
  color: var(--m3-primary);
}
.button-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border-color: var(--m3-outline);
}
.button-group button svg {
  width: 20px;
  height: 20px;
}

/* --- Switch (Toggle) --- */
.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 28px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--m3-surface-variant);
  transition: .4s;
}
.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 4px;
  bottom: 4px;
  background-color: var(--m3-outline);
  transition: .4s;
}
input:checked + .slider {
  background-color: var(--m3-primary);
}
input:checked + .slider:before {
  background-color: white;
  transform: translateX(20px);
}
.slider.round {
  border-radius: 28px;
}
.slider.round:before {
  border-radius: 50%;
}
</style>