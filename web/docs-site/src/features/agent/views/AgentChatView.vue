<template>
  <div class="agent-chat-view w-full h-full relative">
    <!-- 对话历史区域 - 留出输入面板空间 -->
    <div class="history-panel w-full px-4 pt-4" ref="historyPanel" style="padding-bottom: calc(var(--input-panel-height, 120px) + 1rem);">
      <div class="max-w-4xl mx-auto space-y-4">
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
    </div>

    <!-- 固定在屏幕底部的输入面板 -->
    <div class="input-panel-fixed max-w-4xl mx-auto px-4 py-3" ref="inputPanelContainer">
      <ChatInputPanel
        ref="inputPanelRef"
        v-model="userInput"
        :is-loading="isLoading || isProcessing"
        :error="error"
        :is-processing="isProcessing"
        :active-agent-name="activeAgentName"
        :thinking-time="thinkingTime"
        :show-history-panel="isHistoryPanelVisible"
        :show-raw-content="showRawContent"
        @update:show-history-panel="isHistoryPanelVisible = $event"
        @update:show-raw-content="showRawContent = $event"
        @send="handleSend"
        @stop="stopAgent"
      />
    </div>

    <!-- 模态框组件 -->
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
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useConfigStore } from '@/features/app/stores/config';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import { useAppStore } from '@/features/app/stores/app';
import 'github-markdown-css/github-markdown-light.css';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import logger from '@/features/app/services/loggerService';

// Import components
import ChatInputPanel from '@/features/agent/components/ChatInputPanel.vue';
import AgentSelectorModal from '@/features/agent/components/AgentSelectorModal.vue';
import MessageBubble from '@/features/agent/components/MessageBubble.vue';
import SessionHistoryPanel from '@/features/agent/components/SessionHistoryPanel.vue';

// Import composables
import { useResponsive } from '@/composables/useResponsive';

// --- Stores ---
const appStore = useAppStore();
const { currentDomain } = storeToRefs(appStore);

// --- Responsive ---
const { isMobile } = useResponsive();


const agentStore = useAgentStore();
const { isLoading, isProcessing, error, activeAgentName, availableAgents, currentRoleId } = storeToRefs(agentStore);
const { sendMessage, stopAgent, resetAgent, fetchAvailableAgents, switchAgent, initializeStoreFromCache, retryLastTurn, updateActiveAgentName } = agentStore;

const configStore = useConfigStore();
const { activeConfig } = storeToRefs(configStore);

// --- Local UI State ---
const userInput = ref('');
const historyPanel = ref(null);
const inputPanelRef = ref(null);
const inputPanelContainer = ref(null);
const isAgentSelectorVisible = ref(false);
const isHistoryPanelVisible = ref(false);
const thinkingTime = ref(0);
const showRawContent = ref(false);
let timerInterval = null;
let resizeObserver = null;

// --- Computed Properties ---
const visibleMessages = computed(() => {
  return agentStore.orderedMessages.filter(m => {
    // 过滤掉所有 is_hidden 的消息，以及所有纯粹的系统/工具消息
    return !m.is_hidden && m.role !== 'system' && m.role !== 'tool';
  });
});

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

// 更新输入面板高度（添加防抖优化）
let updateHeightTimeout = null;
const updateInputPanelHeight = () => {
  if (updateHeightTimeout) {
    clearTimeout(updateHeightTimeout);
  }

  updateHeightTimeout = setTimeout(() => {
    if (inputPanelContainer.value) {
      const height = inputPanelContainer.value.offsetHeight;
      document.documentElement.style.setProperty('--input-panel-height', `${height}px`);
    }
  }, 16); // 约60fps的更新频率
};

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
      alert(`链接指向的路径 "${result.originalPath}" 无法被解析或找到。`);
    }
  }
}


// --- Lifecycle & Watchers ---

let mutationObserver = null;

onMounted(() => {
  // fetchAvailableAgents(currentDomain.value); // This is now handled by MainLayout's orchestrator
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);

  const scrollToBottom = () => {
    // 滚动由master容器（SmartLayout的master区域）处理
    // 找到真正的滚动容器
    const scrollContainer = historyPanel.value?.closest('.master-scrollbar') ||
                          historyPanel.value?.closest('[class*="overflow-y-auto"]');
    if (scrollContainer) {
      scrollContainer.scrollTo({ top: scrollContainer.scrollHeight, behavior: 'smooth' });
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

  // 设置ResizeObserver来监控输入面板高度变化
  if (inputPanelContainer.value) {
    updateInputPanelHeight(); // 初始化高度

    resizeObserver = new ResizeObserver(() => {
      updateInputPanelHeight();
    });

    resizeObserver.observe(inputPanelContainer.value);
  }
});

// This watcher is redundant and was causing race conditions.
// The MainLayout component is now the single source of truth for orchestrating domain changes.
// watch(currentDomain, (newDomain) => {
//   fetchAvailableAgents(newDomain);
// });

watch([isLoading, isProcessing], ([newIsLoading, newIsProcessing]) => {
  const newValue = newIsLoading || newIsProcessing;
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
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  if (timerInterval) {
    clearInterval(timerInterval);
  }
  if (updateHeightTimeout) {
    clearTimeout(updateHeightTimeout);
  }
});
</script>

<style scoped lang="postcss">
/* 输入面板固定定位（仅负责定位，不添加装饰样式） */
.input-panel-fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 20;
}

/* 历史面板调整 */
.history-panel {
  min-height: 100vh;
}
</style>