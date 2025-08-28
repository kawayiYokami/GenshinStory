<template>
  <div class="overflow-y-auto scrollbar-hide h-full" ref="historyPanel">
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
</template>

<script setup lang="ts">
/**
 * ChatHistoryPanel 组件
 *
 * 这是聊天历史记录面板组件，负责显示聊天消息列表，
 * 处理用户交互事件，以及管理滚动行为。
 */

import { ref, onMounted, onUnmounted } from 'vue';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import MessageBubble from './MessageBubble.vue';

/**
 * 组件属性定义
 * @property {boolean} showRawContent - 是否显示原始内容
 * @property {Array} visibleMessages - 可见消息列表
 */
const props = defineProps<{
  showRawContent: boolean;
  visibleMessages: any[];
}>();

/**
 * 组件事件定义
 * @event select-suggestion - 当用户选择建议时触发
 * @event send-suggestion - 当用户发送建议时触发
 * @event delete-from - 当用户删除消息时触发
 * @event retry - 当用户重试时触发
 */
const emit = defineEmits<{
  (e: 'select-suggestion', suggestionText: string): void;
  (e: 'send-suggestion', suggestionText: string): void;
  (e: 'delete-from', messageId: string): void;
  (e: 'retry'): void;
}>();

/**
 * 智能体状态存储
 * 用于获取智能体相关信息
 */
const agentStore = useAgentStore();

/**
 * 组件引用和状态变量
 */
const historyPanel = ref<HTMLElement | null>(null);
let mutationObserver: MutationObserver | null = null;

/**
 * 事件处理函数：处理建议选择
 * @param {string} suggestionText - 建议文本
 */
const handleSuggestionSelected = (suggestionText: string) => {
  emit('select-suggestion', suggestionText);
};

/**
 * 事件处理函数：处理建议发送
 * @param {string} suggestionText - 建议文本
 */
const handleSendSuggestionSelected = (suggestionText: string) => {
  emit('send-suggestion', suggestionText);
};

/**
 * 事件处理函数：处理删除消息
 * @param {string} messageId - 消息ID
 */
const handleDeleteFrom = (messageId: string) => {
  emit('delete-from', messageId);
};

/**
 * 事件处理函数：处理重试
 */
const handleRetry = () => {
  emit('retry');
};

/**
 * 事件处理函数：处理历史面板点击事件
 * 主要用于处理文档链接点击
 * @param {Event} event - 点击事件
 */
const handleHistoryPanelClick = async (event: Event) => {
  const target = (event.target as HTMLElement).closest('.internal-doc-link');
  if (target && target instanceof HTMLElement && target.dataset.rawLink) {
    event.preventDefault();
    const rawLink = target.dataset.rawLink;
    const result = await linkProcessorService.resolveLink(rawLink);
    if (result.isValid && result.resolvedPath) {
      const docViewerStore = useDocumentViewerStore();
      docViewerStore.open(result.resolvedPath!);
    } else {
      alert(`链接指向的路径 "${result.originalPath}" 无法被解析或找到。`);
    }
  }
};

/**
 * 方法：滚动到底部
 * 确保最新的消息始终可见
 */
const scrollToBottom = () => {
  if (historyPanel.value) {
    historyPanel.value.scrollTo({ top: historyPanel.value.scrollHeight, behavior: 'smooth' });
  }
};

/**
 * 生命周期钩子：组件挂载时执行
 * 添加事件监听器和设置滚动观察器
 */
onMounted(() => {
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);

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

/**
 * 生命周期钩子：组件卸载时执行
 * 清理事件监听器和观察器
 */
onUnmounted(() => {
  historyPanel.value?.removeEventListener('click', handleHistoryPanelClick);
  if (mutationObserver) {
    mutationObserver.disconnect();
  }
});

/**
 * 暴露组件属性给父组件
 */
defineExpose({
  historyPanel
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