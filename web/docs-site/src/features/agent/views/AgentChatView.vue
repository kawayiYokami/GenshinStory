<template>
  <div class="agent-chat-view w-full h-full flex flex-col">
    <Teleport to="#navbar-content-target" v-if="isNavbarContentTargetAvailable">
      <div class="flex items-center gap-4">
        <span class="text-lg font-bold">{{ activeAgentName }}</span>
        <div class="h-4 border-l border-base-content/30"></div>
        <button @click="handleNewSession" class="btn btn-ghost btn-sm" title="新会话">
          <PlusIcon class="w-4 h-4" />
        </button>
      </div>
    </Teleport>
    <!-- 对话历史区域 - 可滚动，隐藏滚动条 -->
    <div class="flex-1 overflow-y-auto scrollbar-hide" ref="historyPanel">
      <div class="max-w-4xl mx-auto space-y-1 px-4 py-4">
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

    <!-- 输入面板 - 固定在底部 -->
    <div class="flex-shrink-0">
      <div class="max-w-4xl mx-auto">
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

// Import icons
import { PlusIcon } from '@heroicons/vue/24/outline';

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
const isAgentSelectorVisible = ref(false);
const isHistoryPanelVisible = ref(false);
const thinkingTime = ref(0);
const showRawContent = ref(false);
const isMounted = ref(false); // 用于跟踪组件是否挂载
let timerInterval = null;

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
  isMounted.value = true; // 设置组件挂载状态
  // fetchAvailableAgents(currentDomain.value); // This is now handled by MainLayout's orchestrator
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);

  const scrollToBottom = () => {
    // 滚动到底部 - 现在由历史面板自身处理
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

// 添加计算属性检查navbar-content-target元素是否可用
const isNavbarContentTargetAvailable = computed(() => {
  return isMounted.value && typeof document !== 'undefined' && document.getElementById('navbar-content-target') !== null;
});

// 添加新会话处理函数
const handleNewSession = async () => {
  if (currentRoleId.value) {
    await agentStore.startNewChatWithAgent(currentRoleId.value);
  }
};

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

<style scoped lang="postcss">
/* 隐藏滚动条的样式 */
.scrollbar-hide {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
}

.scrollbar-hide::-webkit-scrollbar {
  display: none; /* WebKit */
}
</style>