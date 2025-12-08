<template>
  <!-- 智能体聊天视图组件：负责协调聊天界面的各个部分 -->
  <div class="agent-chat-view w-full h-full flex flex-col">
    <Teleport to="#navbar-content-target" v-if="isNavbarContentTargetAvailable">
      <AgentNavbarContent
        :active-agent-name="activeAgentName"
        @new-session="handleNewSession"
      />
    </Teleport>

    <!-- 对话历史区域 - 可滚动，隐藏滚动条 -->
    <ChatHistoryPanel
      :show-raw-content="showRawContent"
      :visible-messages="visibleMessages"
      @select-suggestion="handleSuggestionSelected"
      @send-suggestion="handleSendSuggestionSelected"
      @delete-from="handleDeleteFrom"
      @retry="handleRetry"
      @message-rendered="handleMessageRendered"
      ref="historyPanelRef"
    />

    <!-- 输入面板容器 -->
    <div class="shrink-0 pt-0 pb-4 relative">
      <div class="max-w-4xl mx-auto">
        <ChatInputPanel
          ref="inputPanelRef"
          v-model="userInput"
          :is-loading="isLoading || isProcessing"
          :error="error as any"
          :is-processing="isProcessing"
          :active-agent-name="activeAgentName"
          :thinking-time="thinkingTime"
          :show-raw-content="showRawContent"
          @update:show-raw-content="showRawContent = $event"
          @send="handleSend"
          @stop="stopAgent"
        />

        <!-- 滚动到底部按钮 -->
        <ScrollToBottomButton
          :visible="scrollManager.showScrollToBottomButton.value"
          @click="scrollManager.scrollToBottom"
        />
      </div>
    </div>

    <!-- 模态框组件 -->
    <AgentChatModals
      :is-agent-selector-visible="isAgentSelectorVisible"
      :available-agents="availableAgents"
      :current-role-id="currentRoleId || ''"
      :current-domain="currentDomain || ''"
      @toggle-agent-selector="toggleAgentSelector"
      @select-agent="handleSelectAgent"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 智能体聊天视图组件
 * @description 这是智能体聊天界面的主要视图组件，负责协调聊天界面的各个部分
 * @author yokami
 *
 * 主要功能：
 * - 顶部导航栏内容
 * - 聊天历史记录面板
 * - 聊天输入面板
 * - 相关模态框
 *
 * 使用组合式API (Composition API) 和 Pinia 状态管理
 */

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
import AgentNavbarContent from '@/features/agent/components/AgentNavbarContent.vue';
import ChatHistoryPanel from '@/features/agent/components/ChatHistoryPanel.vue';
import AgentChatModals from '@/features/agent/components/AgentChatModals.vue';
import ScrollToBottomButton from '@/features/agent/components/ScrollToBottomButton.vue';

// Import icons
import { Plus } from 'lucide-vue-next';

// Import composables
import { useResponsive } from '@/composables/useResponsive';
import useScrollManager from '@/features/agent/composables/useScrollManager';

// --- Stores ---
/**
 * 应用状态存储
 * 用于获取当前域信息
 */
const appStore = useAppStore();
const { currentDomain } = storeToRefs(appStore);

// --- Responsive ---
/**
 * 响应式工具
 * 用于检测设备是否为移动设备
 */
const { isMobile } = useResponsive();

/**
 * 智能体状态存储
 * 包含聊天消息、加载状态、错误信息等
 */
const agentStore = useAgentStore();
const { isLoading, isProcessing, error, activeAgentName, availableAgents, currentRoleId } = storeToRefs(agentStore);
const { sendMessage, stopAgent, resetAgent, fetchAvailableAgents, switchAgent, initializeStoreFromCache, retryLastTurn } = agentStore;

/**
 * 配置状态存储
 * 用于获取当前AI配置信息
 */
const configStore = useConfigStore();
const { activeConfig } = storeToRefs(configStore);

// --- Local UI State ---
/**
 * 本地UI状态变量
 * 用于管理组件内部的状态
 */
const userInput = ref(''); // 用户输入的内容
const historyPanelRef = ref<{ historyPanel: HTMLElement } | null>(null); // 聊天历史面板的引用
const inputPanelRef = ref<{
  $el: HTMLElement;
  focus: () => void;
  adjustTextareaHeight: () => void
} | null>(null); // 输入面板的引用
const isAgentSelectorVisible = ref(false); // 智能体选择器是否可见
const thinkingTime = ref(0); // 思考时间计数器
const showRawContent = ref(false); // 是否显示原始内容
const isMounted = ref(false); // 用于跟踪组件是否挂载
let timerInterval: ReturnType<typeof setInterval> | null = null; // 计时器间隔引用

// --- Scroll Management ---
/**
 * 滚动管理状态
 * 用于控制自动滚动行为
 */
const autoScroll = ref(true); // 默认启用自动滚动

/**
 * 初始化滚动管理器 - 使用简化版
 */
const scrollManager = useScrollManager({
  scrollElement: computed(() => historyPanelRef.value?.historyPanel || null),
  autoScroll
});

// --- Computed Properties ---
/**
 * 计算属性：可见消息列表
 * 过滤掉隐藏的消息和系统/工具消息，只显示用户和智能体的对话
 */
const visibleMessages = computed(() => {
  return agentStore.orderedMessages.filter(m => {
    // 过滤掉所有 is_hidden 的消息，以及所有纯粹的系统/工具消息
    return !m.is_hidden && m.role !== 'system' && m.role !== 'tool';
  });
});

// --- Event Handlers from Child Components ---
/**
 * 事件处理函数：处理建议选择
 * 当用户点击建议问题时，将建议文本添加到输入框中
 * @param {string} suggestionText - 建议的文本内容
 */
const handleSuggestionSelected = (suggestionText: string) => {
  if (userInput.value.trim() !== '') {
    userInput.value += '\n';
  }
  userInput.value += suggestionText;

  nextTick(() => {
    inputPanelRef.value?.focus();
    inputPanelRef.value?.adjustTextareaHeight();
  });
};

/**
 * 事件处理函数：处理建议发送
 * 当用户点击建议问题的发送按钮时，直接发送建议文本
 * @param {string} suggestionText - 建议的文本内容
 */
const handleSendSuggestionSelected = (suggestionText: string) => {
  sendMessage(suggestionText);
};

/**
 * 事件处理函数：删除消息
 * 从指定消息开始删除后续所有消息
 * @param {string} messageId - 消息ID
 */
const handleDeleteFrom = (messageId: string) => {
  agentStore.deleteMessagesFrom(messageId);
};

/**
 * 事件处理函数：重试
 * 重新发送最后一条消息
 */
const handleRetry = () => {
  retryLastTurn();
};

/**
 * 事件处理函数：处理消息渲染完成
 * @param {string} messageId - 消息ID
 */
const handleMessageRendered = (messageId: string) => {
  // 可以在这里添加消息渲染完成后的处理逻辑
  // 目前为空实现，保留接口以备将来扩展
};

/**
 * 事件处理函数：选择智能体
 * 切换当前使用的智能体
 * @param {string} roleId - 智能体ID
 */
const handleSelectAgent = (roleId: string) => {
  switchAgent(roleId);
  isAgentSelectorVisible.value = false;
};

// --- Agent & Message Methods ---
/**
 * 方法：切换智能体选择器
 * 控制智能体选择器模态框的显示/隐藏
 */
const toggleAgentSelector = () => {
  // This is no longer needed as primary way to switch agents.
  // Kept for modal's close button functionality if reused.
  isAgentSelectorVisible.value = !isAgentSelectorVisible.value;
};

/**
 * 方法：处理消息发送
 * 处理用户发送消息的逻辑，包括验证配置、停止当前加载等
 * @param {Object} payload - 发送的消息负载，包含文本和图片
 */
const handleSend = async (payload: string | { text: string; images?: string[]; references?: any[] }) => {
  // The payload from ChatInputPanel is now an object: { text, images }
  const messageToSend = payload;

  // 验证AI配置是否完整
  if (!activeConfig.value || !activeConfig.value.apiUrl || !activeConfig.value.apiKey) {
    alert("请先完成当前AI配置，API URL 和 API Key 不能为空。");
    // Future improvement: emit an event to config panel to make it visible
    return;
  }

  // 如果当前正在处理（加载或AI处理中），先停止智能体
  if (isLoading.value || isProcessing.value) {
    logger.log("--- UI: Sending message while processing. Stopping agent first. ---");

    // 等待停止完成
    await stopAgent();

    // 使用轮询方式检查状态，最多等待2秒
    const maxWaitTime = 2000; // 2秒超时
    const pollInterval = 50;  // 50ms轮询间隔
    let totalWaitTime = 0;

    while ((isLoading.value || isProcessing.value) && totalWaitTime < maxWaitTime) {
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      totalWaitTime += pollInterval;
    }

    // 如果仍然在处理中，显示取消提示并返回
    if (isLoading.value || isProcessing.value) {
      logger.log("--- UI: Agent still processing after stop, aborting send. ---");

      // 创建一个临时的用户提示消息
      await agentStore.addMessage({
        role: 'assistant',
        content: "*上一个请求仍在处理中，已取消发送新消息。*",
        type: 'text',
        is_hidden: false // 显示给用户
      });

      // 滚动到底部以显示提示消息
      await nextTick();
      scrollManager.scrollToBottom();

      return;
    }
  }

  // 发送消息到智能体
  await sendMessage(messageToSend);

  // 等待DOM更新后直接滚动到底部
  await nextTick(); // 确保 DOM 更新
  scrollManager.scrollToBottom(); // 直接滚动到底部

  // userInput is now cleared inside ChatInputPanel itself upon sending.
  // We just need to ensure textarea height is adjusted.
  await nextTick();
  inputPanelRef.value?.adjustTextareaHeight();
};

/**
 * 方法：重置智能体和稳定列表
 * 用于开始新的聊天会话
 */
const resetAgentAndStableList = () => {
  // This function is now handled by new-chat-dropdown in AgentConfigPanel
  // Kept here for now to avoid breaking changes if called elsewhere, but can be removed.
  // agentStore.startNewChatWithAgent(currentRoleId.value);
};

// --- Lifecycle & Watchers ---
/**
 * 生命周期钩子：组件挂载时执行
 * 初始化组件状态，滚动管理现在由useScrollManager处理
 */
onMounted(() => {
  isMounted.value = true; // 设置组件挂载状态
  // 滚动管理现在由useScrollManager自动处理
});

/**
 * 监听器：监听加载状态变化
 * 当加载状态改变时，控制思考时间计时器
 */
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
    if (timerInterval !== null) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }
});

/**
 * 计算属性：检查navbar-content-target元素是否可用
 * 用于确定是否可以将内容传送到导航栏
 */
const isNavbarContentTargetAvailable = computed(() => {
  return isMounted.value && typeof document !== 'undefined' && document.getElementById('navbar-content-target') !== null;
});

/**
 * 事件处理函数：处理新会话
 * 开始一个新的聊天会话
 */
const handleNewSession = async () => {
  if (currentRoleId.value) {
    await agentStore.startNewChatWithAgent(currentRoleId.value);
  }
};

/**
 * 生命周期钩子：组件卸载时执行
 * 清理计时器等资源
 */
onUnmounted(() => {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
  }
});
</script>

<style scoped lang="postcss">
/* 样式区域：负责组件样式 */
/* 隐藏滚动条的样式已在ChatHistoryPanel中定义 */
</style>