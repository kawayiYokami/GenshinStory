<template>
  <div class="agent-chat-view">
    <!-- Config Section -->
    <div class="config-section">
      <div class="config-header">
        <button class="model-display-button" @click="isConfigVisible = !isConfigVisible">
          <span v-if="activeConfig">{{ activeConfig.name || '选择配置' }}</span>
          <span v-else>请先创建配置</span>
          <svg :class="{ 'is-expanded': isConfigVisible }" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        <div class="button-group">
           <button @click.stop="handleHistoryButtonClick" title="历史会话">
             <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 6H3"/><path d="M21 12H3"/><path d="M21 18H3"/></svg>
           </button>
          <button @click.stop="resetAgentAndStableList" title="新对话">
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
                <label for="show-raw">显示源码 (Debug)</label>
                <label class="switch">
                  <input id="show-raw" type="checkbox" v-model="showRawContent">
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

    <!-- Conversation History -->
    <div class="history-panel" ref="historyPanel">
      <!-- New Rendering Pipeline -->
      <MessageBubble
        v-for="message in visibleMessages"
        :key="message.id"
        :message="message"
        :show-raw-content="showRawContent"
        @select-suggestion="handleSuggestionSelected"
        @send-suggestion="handleSendSuggestionSelected"
        @delete-from-here="handleDeleteFrom"
      />
    </div>

    <div v-if="error" class="status-panel error">
      发生错误: {{ error.message }}
    </div>
    
    <div v-if="isLoading || !error"
         class="status-panel thinking-indicator"
         :class="{ 'clickable': !isLoading }"
         @click="toggleAgentSelector">
      <span v-if="isLoading">{{ activeAgentName }} 正在思考中...</span>
      <span v-else>{{ activeAgentName }} ，期待与您对话。</span>
    </div>

    <!-- Agent Selector Modal -->
    <div v-if="isAgentSelectorVisible" class="agent-selector-modal">
      <div class="modal-overlay" @click="toggleAgentSelector"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>选择一个角色</h3>
          <button @click="toggleAgentSelector" class="close-button">&times;</button>
        </div>
        <ul class="agent-list">
          <li v-for="agent in availableAgents[currentGame]" :key="agent.id">
            <button @click="handleSelectAgent(agent.id)" :class="{ active: agent.id === currentRoleId }">
              {{ agent.name }}
            </button>
          </li>
        </ul>
      </div>
    </div>

    <SessionHistoryPanel
      :visible="isHistoryPanelVisible"
      @close="isHistoryPanelVisible = false"
    />

    <!-- User Input -->
    <div class="input-panel">
      <div class="input-wrapper">
        <textarea
          ref="textareaRef"
          v-model="userInput"
          placeholder="请输入您的问题或指令... (Enter 发送)"
          @keydown.enter.exact.prevent="handleSend"
          @input="adjustTextareaHeight"
          :disabled="isLoading"
        ></textarea>
        <button
          @click="isLoading ? stopAgent() : handleSend()"
          :disabled="!isLoading && !userInput.trim()"
          :class="['send-button', { 'stop-button': isLoading }]"
          :title="isLoading ? '打断' : '发送'"
        >
          <svg v-if="isLoading" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 11L12 6L17 11M12 18V6"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/stores/agent';
import { useConfigStore } from '@/stores/config';
import { useDocumentViewerStore } from '@/stores/documentViewer';
import { useAppStore } from '@/stores/app';
import 'github-markdown-css/github-markdown-light.css';
import linkProcessorService from '@/services/linkProcessorService';
import logger from '@/services/loggerService';
import MessageBubble from '@/components/MessageBubble.vue';
import SessionHistoryPanel from '@/components/SessionHistoryPanel.vue';

// --- Stores ---
const appStore = useAppStore();
const { currentGame } = storeToRefs(appStore);

const agentStore = useAgentStore();
const { orderedMessages, isLoading, error, activeAgentName, availableAgents, currentRoleId } = storeToRefs(agentStore);
const { sendMessage, stopAgent, resetAgent, fetchAvailableAgents, switchAgent, initializeStoreFromCache } = agentStore;

const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, addConfig, updateConfig, deleteConfig, setActiveConfig } = configStore;


// --- Local UI State ---
const userInput = ref('');
const historyPanel = ref(null);
const textareaRef = ref(null);
const isConfigVisible = ref(false);
const isAgentSelectorVisible = ref(false);
const isHistoryPanelVisible = ref(false);
const showRawContent = ref(false); // DEBUG: Raw content toggle

// --- Computed Properties ---
const visibleMessages = computed(() =>
  orderedMessages.value.filter(m => m.role !== 'system' && m.role !== 'tool')
);

// --- Config Management Methods ---
const handleAddNewConfig = () => {
  logger.log('--- UI: AddNewConfig button clicked. ---');
  if (configs.value.length >= 13) {
    alert("配置数量已达到13个的上限。");
    return;
  }
  // 简化：直接调用 action，将命名逻辑完全交给 store
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

const handleSuggestionSelected = (suggestionText) => {
  if (userInput.value.trim() !== '') {
    userInput.value += '\n';
  }
  userInput.value += suggestionText;
  
  nextTick(() => {
    textareaRef.value?.focus();
    adjustTextareaHeight();
  });
};

const handleSendSuggestionSelected = (suggestionText) => {
  // Directly call the existing sendMessage logic
  sendMessage(suggestionText);
};

const handleDeleteFrom = (messageId) => {
  agentStore.deleteMessagesFrom(messageId);
};

const handleSelectConfig = (id) => {
  logger.log(`--- UI: Config <select> changed. New ID selected: ${id}. Calling setActiveConfig. ---`);
  setActiveConfig(id);
}

// --- Agent Selection Methods ---
const toggleAgentSelector = () => {
  if (!isLoading.value) {
    isAgentSelectorVisible.value = !isAgentSelectorVisible.value;
  }
};

const handleSelectAgent = (roleId) => {
  switchAgent(roleId);
  isAgentSelectorVisible.value = false;
};


// --- Methods ---
const handleHistoryPanelClick = async (event) => {
  const target = event.target.closest('.internal-doc-link');
  if (target && target.dataset.rawLink) {
    event.preventDefault();
    const rawLink = target.dataset.rawLink;
    const result = await linkProcessorService.resolveLink(rawLink);
    if (result.isValid) {
      const docViewerStore = useDocumentViewerStore();
      docViewerStore.open(result.resolvedPath);
    } else {
      alert(`链接指向的路径 "${result.resolvedPath}" 无法被解析或找到。`);
    }
  }
}

const handleSend = async () => {
  const messageToSend = userInput.value.trim();
  if (!messageToSend) return;

  if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
    isConfigVisible.value = true;
    alert("请先完成当前AI配置，API URL 和 API Key 不能为空。");
    return;
  }

  if (isLoading.value) {
    logger.log("--- UI: Sending message while loading. Stopping agent first. ---");
    stopAgent();
    // Give a very short moment for the stop signal to propagate,
    // ensuring the new message is processed in a cleaner state.
    await nextTick();
  }
  
  sendMessage(messageToSend);
  userInput.value = '';
  await nextTick();
  adjustTextareaHeight();
};

// Override the original resetAgent to also clear our stable message list
const originalResetAgent = resetAgent;
const resetAgentAndStableList = () => {
  // stableVisibleMessages will now automatically clear when orderedMessages resets.
  originalResetAgent();
};

const adjustTextareaHeight = () => {
  const textarea = textareaRef.value;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
};

// --- Lifecycle & Watchers ---

// This watcher is no longer needed. The v-for with visibleMessages is sufficient.
// The complexity was only required because of the broken renderer logic.

let mutationObserver = null;

onMounted(() => {
  fetchAvailableAgents(currentGame.value);
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);
  
  const scrollToBottom = () => {
    if (historyPanel.value) {
      historyPanel.value.scrollTo({ top: historyPanel.value.scrollHeight, behavior: 'smooth' });
    }
  };

  // MutationObserver is the correct and robust way to detect content changes
  // inside a scrolling container, which ResizeObserver cannot do.
  mutationObserver = new MutationObserver((mutations) => {
    // We don't need to inspect the mutations, any change should trigger a scroll check.
    scrollToBottom();
  });

  if (historyPanel.value) {
    mutationObserver.observe(historyPanel.value, {
      childList: true, // observes direct children being added or removed
      subtree: true,   // observes all descendants
      characterData: true, // observes text changes
    });
  }
});

watch(currentGame, (newGame) => {
  fetchAvailableAgents(newGame);
});

onUnmounted(() => {
  historyPanel.value?.removeEventListener('click', handleHistoryPanelClick);
  if (mutationObserver) {
    mutationObserver.disconnect();
  }
});

const handleHistoryButtonClick = async () => {
  await initializeStoreFromCache();
  isHistoryPanelVisible.value = true;
};
</script>

<style scoped>
/* Base styling for the view */
.agent-chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: var(--m3-on-surface);
}

/* --- Configuration Section --- */
.config-section {
  padding-bottom: 10px;
  border-bottom: 1px solid var(--m3-outline);
}
.config-header {
  display: flex;
  justify-content: space-between; /* Align items to start and end */
  align-items: center;
  /* Removed cursor and padding as they are handled by child buttons */
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

/* --- History Panel & Messages --- */
.history-panel {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 1000px;
}

/* --- Input Panel --- */
.input-panel {
  display: flex;
  flex-direction: column;
  padding: 16px 8px 12px; /* Adjusted padding */
  border-top: 1px solid var(--m3-outline);
}
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.input-panel textarea {
  width: 100%;
  min-height: 52px; /* Increased height */
  max-height: 200px;
  padding: 14px 52px 14px 18px; /* Adjusted padding */
  border-radius: 26px; /* Rounded corners */
  border: 1px solid var(--m3-outline);
  background-color: var(--m3-surface);
  resize: none;
  overflow-y: auto;
  line-height: 1.6;
  font-family: inherit;
  color: var(--m3-on-surface);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-panel textarea:focus {
  outline: none;
  border-color: var(--m3-primary);
  box-shadow: 0 0 0 2px var(--m3-primary-container);
}

.send-button {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background-color 0.2s;
}
.send-button:hover {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
}
.send-button:disabled {
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  cursor: not-allowed;
}
.send-button svg {
  width: 20px;
  height: 20px;
  transform: rotate(90deg);
}
.send-button.stop-button {
  background-color: var(--m3-error);
  color: var(--m3-on-error);
}
.send-button.stop-button:hover {
  background-color: var(--m3-error-container);
  color: var(--m3-on-error-container);
}
.send-button.stop-button svg {
  transform: none; /* Reset rotation for the stop icon */
}

/* --- Buttons --- */
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
/* Disabled State */
.button-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border-color: var(--m3-outline);
}

/* --- Status Indicators --- */
.thinking-indicator {
  text-align: left;
  padding: 8px 12px;
  margin: 0 8px 0; /* Adjusted margin */
  background-color: transparent;
  border: none; /* Removed border */
  border-radius: 8px;
  font-size: 0.9em;
  color: var(--m3-on-surface-variant);
  display: flex;
  justify-content: center; /* Centered the content */
  align-items: center;
  min-height: 38px;
  box-sizing: border-box;
  transition: background-color 0.2s;
}
.thinking-indicator.clickable:hover {
  background-color: var(--m3-surface-variant);
  cursor: pointer;
}
.button-group button svg {
  width: 20px;
  height: 20px;
}
.button-group .stop-button {
  background-color: var(--m3-error) !important;
  color: var(--m3-on-error) !important;
  border-color: transparent !important;
}
.button-group .stop-button:hover {
  background-color: var(--m3-error-container) !important;
  color: var(--m3-on-error-container) !important;
}
.error-text {
  color: var(--m3-error);
  font-style: italic;
}
.status-panel.error {
  color: var(--m3-error);
}

/* --- Tool & Markdown Styles --- */
.tool-status {
  font-style: italic;
  color: var(--m3-on-surface-variant);
  padding: 8px 12px;
  background-color: var(--m3-surface-variant);
  border-radius: 8px;
  margin: 4px 0;
}
.tool-result {
  font-size: 0.9em;
  border-radius: 8px;
  margin-top: 8px;
  background-color: var(--genshin-bg-secondary);
  border: 1px solid var(--genshin-accent-gold);
  color: var(--genshin-text-secondary);
  overflow: hidden; /* Ensures child elements adhere to border-radius */
}
.tool-result summary {
  cursor: pointer;
  font-weight: bold;
  padding: 8px 12px 8px 32px;
  outline: none;
  color: var(--genshin-accent-gold);
  position: relative;
  list-style: none; /* Hide default marker */
}
.tool-result summary::-webkit-details-marker {
  display: none; /* Hide default marker for Safari */
}
.tool-result summary::before {
  content: '▶';
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  transition: transform 0.2s;
  color: var(--genshin-accent-gold);
}
.tool-result details[open] > summary::before {
  transform: translateY(-50%) rotate(90deg);
}
.tool-result details[open] > summary {
  border-bottom: 1px solid var(--genshin-accent-gold);
}
.tool-result pre {
  padding: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: rgba(0, 0, 0, 0.2);
  margin: 0;
  color: var(--genshin-text-secondary);
}
:deep(.markdown-body) {
  background-color: transparent !important;
  padding: 0;
  color: var(--m3-on-surface-variant);
}
:deep(.markdown-body pre) {
  background-color: transparent !important;
}
:deep(.internal-doc-link) {
  background-color: var(--m3-primary-container);
  border: 1px solid var(--m3-outline);
  color: var(--m3-primary);
  padding: 2px 6px;
  border-radius: 4px;
  text-decoration: none;
  cursor: pointer;
  font-weight: 500;
}
:deep(.internal-doc-link:hover) {
  border-color: var(--m3-primary);
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
/* --- Scrollbar Hiding --- */
.input-panel textarea::-webkit-scrollbar {
  display: none; /* For Webkit-based browsers (Chrome, Safari, Edge) */
}
.input-panel textarea {
  -ms-overflow-style: none;  /* For Internet Explorer and Edge */
  scrollbar-width: none;  /* For Firefox */
}

/* --- Agent Selector Modal --- */
.agent-selector-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}
.modal-content {
  background-color: var(--m3-surface);
  padding: 20px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  z-index: 1001;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--m3-outline);
  padding-bottom: 10px;
  margin-bottom: 15px;
}
.modal-header h3 {
  margin: 0;
  color: var(--m3-on-surface);
}
.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--m3-on-surface-variant);
}
.agent-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 60vh;
  overflow-y: auto;
}
.agent-list li button {
  width: 100%;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--m3-outline);
  border-radius: 8px;
  margin-bottom: 8px;
  text-align: left;
  font-size: 1em;
  cursor: pointer;
  color: var(--m3-on-surface);
  transition: background-color 0.2s, border-color 0.2s;
}
.agent-list li button:hover {
  background-color: var(--m3-surface-variant);
  border-color: var(--m3-primary);
}
.agent-list li button.active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  border-color: var(--m3-primary);
  font-weight: bold;
}
</style>