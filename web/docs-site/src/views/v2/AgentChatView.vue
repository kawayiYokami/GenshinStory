<template>
  <div class="agent-chat-view">
    <AgentConfigPanel
      v-model:show-raw-content="showRawContent"
      @history-click="handleHistoryButtonClick"
    />

    <!-- Conversation History -->
    <div class="history-panel" ref="historyPanel">
      <MessageBubble
        v-for="(message, index) in visibleMessages"
        :key="message.id"
        :message="message"
        :show-raw-content="showRawContent"
        :is-last-message="index === visibleMessages.length - 1"
        @select-suggestion="handleSuggestionSelected"
        @send-suggestion="handleSendSuggestionSelected"
        @delete-from-here="handleDeleteFrom"
        @retry="handleRetry"
      />
    </div>

    <!-- Status Indicator: Mutually Exclusive States -->
    <div v-if="error" class="status-panel error">
      发生错误: {{ error.message }}
    </div>
    <div v-else-if="isLoading" class="status-panel thinking-indicator">
      <span>{{ activeAgentName }} 正在思考中... ({{ thinkingTime }}s)</span>
    </div>
    <div v-else class="status-panel">
      <span>{{ activeAgentName }} ，期待与您对话。</span>
    </div>

    <AgentSelectorModal
      :visible="isAgentSelectorVisible"
      :agents="availableAgents[currentDomain] || []"
      :selected-agent-id="currentRoleId"
      @close="toggleAgentSelector"
      @select-agent="handleSelectAgent"
    />

    <SessionHistoryPanel
      :visible="isHistoryPanelVisible"
      @close="isHistoryPanelVisible = false"
    />

    <ChatInputPanel
      ref="inputPanelRef"
      v-model="userInput"
      :is-loading="isLoading"
      @send="handleSend"
      @stop="stopAgent"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/stores/agentStore';
import { useConfigStore } from '@/stores/config';
import { useDocumentViewerStore } from '@/stores/documentViewer';
import { useAppStore } from '@/stores/app';
import 'github-markdown-css/github-markdown-light.css';
import linkProcessorService from '@/services/linkProcessorService';
import logger from '@/services/loggerService';

// Import newly created components
import AgentConfigPanel from '@/components/AgentConfigPanel.vue';
import ChatInputPanel from '@/components/ChatInputPanel.vue';
import AgentSelectorModal from '@/components/AgentSelectorModal.vue';
import MessageBubble from '@/components/MessageBubble.vue';
import SessionHistoryPanel from '@/components/SessionHistoryPanel.vue';

// --- Stores ---
const appStore = useAppStore();
const { currentDomain } = storeToRefs(appStore);

const agentStore = useAgentStore();
const { orderedMessages, isLoading, error, activeAgentName, availableAgents, currentRoleId } = storeToRefs(agentStore);
const { sendMessage, stopAgent, resetAgent, fetchAvailableAgents, switchAgent, initializeStoreFromCache, retryLastTurn } = agentStore;

const configStore = useConfigStore();
const { activeConfig } = storeToRefs(configStore);

// --- Local UI State ---
const userInput = ref('');
const historyPanel = ref(null);
const inputPanelRef = ref(null);
const isAgentSelectorVisible = ref(false);
const isHistoryPanelVisible = ref(false);
const showRawContent = ref(false); // DEBUG: Raw content toggle
const thinkingTime = ref(0);
let timerInterval = null;

// --- Computed Properties ---
const visibleMessages = computed(() =>
  orderedMessages.value.filter(m => m.role !== 'system' && m.role !== 'tool')
);

// --- Event Handlers from Child Components ---

const handleSuggestionSelected = (suggestionText) => {
  if (userInput.value.trim() !== '') {
    userInput.value += '\n';
  }
  userInput.value += suggestionText;
  
  nextTick(() => {
    inputPanelRef.value?.focus();
    inputPanelRef.value?.adjustTextareaHeight();
  });
};

const handleSendSuggestionSelected = (suggestionText) => {
  sendMessage(suggestionText);
};

const handleDeleteFrom = (messageId) => {
  agentStore.deleteMessagesFrom(messageId);
};

const handleRetry = () => {
  retryLastTurn();
};

const handleSelectAgent = (roleId) => {
  switchAgent(roleId);
  isAgentSelectorVisible.value = false;
};

// --- Agent & Message Methods ---

const toggleAgentSelector = () => {
  // This is no longer needed as the primary way to switch agents.
  // Kept for the modal's close button functionality if reused.
  isAgentSelectorVisible.value = !isAgentSelectorVisible.value;
};

const handleSend = async (payload) => {
  // The payload from ChatInputPanel is now an object: { text, images }
  const messageToSend = payload;

  if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
    alert("请先完成当前AI配置，API URL 和 API Key 不能为空。");
    // Future improvement: emit an event to the config panel to make it visible
    return;
  }

  if (isLoading.value) {
    logger.log("--- UI: Sending message while loading. Stopping agent first. ---");
    stopAgent();
    // 关键修改：在调用 stopAgent 后直接返回，不再执行后续代码
    return;
  }
  
  // Pass the entire payload object to the store
  sendMessage(messageToSend);

  // userInput is now cleared inside the ChatInputPanel itself upon sending.
  // We just need to ensure the textarea height is adjusted.
  await nextTick();
  inputPanelRef.value?.adjustTextareaHeight();
};

const resetAgentAndStableList = () => {
  // This function is now handled by the new-chat-dropdown in AgentConfigPanel
  // Kept here for now to avoid breaking changes if called elsewhere, but can be removed.
  // agentStore.startNewChatWithAgent(currentRoleId.value);
};

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

const handleHistoryButtonClick = async () => {
  await initializeStoreFromCache();
  isHistoryPanelVisible.value = true;
};

// --- Lifecycle & Watchers ---

let mutationObserver = null;

onMounted(() => {
  // fetchAvailableAgents(currentDomain.value); // This is now handled by MainLayoutV2's orchestrator
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);
  
  const scrollToBottom = () => {
    if (historyPanel.value) {
      historyPanel.value.scrollTo({ top: historyPanel.value.scrollHeight, behavior: 'smooth' });
    }
  };

  mutationObserver = new MutationObserver(() => {
    scrollToBottom();
  });

  if (historyPanel.value) {
    mutationObserver.observe(historyPanel.value, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }
});

// This watcher is redundant and was causing race conditions.
// The MainLayoutV2 component is now the single source of truth for orchestrating domain changes.
// watch(currentDomain, (newDomain) => {
//   fetchAvailableAgents(newDomain);
// });

watch(isLoading, (newValue) => {
  if (newValue) {
    // Start timer when loading begins
    thinkingTime.value = 0;
    timerInterval = setInterval(() => {
      thinkingTime.value++;
    }, 1000);
  } else {
    // Stop timer when loading ends
    clearInterval(timerInterval);
    timerInterval = null;
  }
});

onUnmounted(() => {
  historyPanel.value?.removeEventListener('click', handleHistoryPanelClick);
  if (mutationObserver) {
    mutationObserver.disconnect();
  }
  if (timerInterval) {
    clearInterval(timerInterval);
  }
});
</script>

<style scoped>
/* Base styling for the view */
.agent-chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: var(--m3-on-surface);
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
/* 针对 Webkit 浏览器 (Chrome, Safari) 的悬停隐藏效果 */
.history-panel::-webkit-scrollbar-thumb {
  background-color: transparent;
  transition: background-color 0.3s ease;
}
.history-panel:hover::-webkit-scrollbar-thumb {
  background-color: #c1c1c1; /* 恢复默认或原有颜色 */
}
/* Firefox 的滚动条通常较细且半透明，悬停时可以变得更明显一些 */
.history-panel {
  scrollbar-color: transparent transparent; /* thumb track */
  transition: scrollbar-color 0.3s ease;
}
.history-panel:hover {
  scrollbar-color: #c1c1c1 transparent; /* thumb track */
}

/* --- Status Indicators --- */
.status-panel {
  padding: 8px 12px;
  margin: 0 8px;
  border-radius: 8px;
  font-size: 0.9em;
  color: var(--m3-on-surface-variant);
  text-align: center;
  min-height: 38px;
  box-sizing: border-box;
  transition: background-color 0.2s;
}
/* .clickable class and its hover effect are no longer needed */
.status-panel.error {
  color: var(--m3-error);
}

/* --- Tool & Markdown Styles (kept for MessageBubble) --- */
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
</style>