<template>
  <div class="overflow-y-auto scrollbar-hide flex-1" ref="historyPanel">
    <div class="max-w-4xl mx-auto space-y-1 px-4 pt-4 pb-4" ref="messageContainer">
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
        @rendered="handleMessageRendered"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import MessageBubble from './MessageBubble.vue';

const props = defineProps<{
  showRawContent: boolean;
  visibleMessages: any[];
}>();

const emit = defineEmits<{
  (e: 'select-suggestion', suggestionText: string): void;
  (e: 'send-suggestion', suggestionText: string): void;
  (e: 'delete-from', messageId: string): void;
  (e: 'retry'): void;
}>();

const agentStore = useAgentStore();
const historyPanel = ref<HTMLElement | null>(null);
const messageContainer = ref<HTMLElement | null>(null);
let mutationObserver: MutationObserver | null = null;

const handleSuggestionSelected = (suggestionText: string) => {
  emit('select-suggestion', suggestionText);
};

const handleSendSuggestionSelected = (suggestionText: string) => {
  emit('send-suggestion', suggestionText);
};

const handleDeleteFrom = (messageId: string) => {
  emit('delete-from', messageId);
};

const handleRetry = () => {
  emit('retry');
};

const handleMessageRendered = (messageId: string) => {
  const lastMessage = props.visibleMessages[props.visibleMessages.length - 1];
  if (lastMessage && lastMessage.id === messageId) {
    nextTick(() => {
      if (historyPanel.value) {
        const isNearBottom = historyPanel.value.scrollTop +
                          historyPanel.value.clientHeight >=
                          historyPanel.value.scrollHeight - 200;
        if (isNearBottom) {
          historyPanel.value.scrollTo({
            top: historyPanel.value.scrollHeight,
            behavior: 'smooth'
          });
        }
      }
    });
  }
};

/**
 * 检查面板是否接近底部（与 handleMessageRendered 使用相同的阈值）
 */
const isHistoryPanelNearBottom = (): boolean => {
  if (!historyPanel.value) return false;
  return historyPanel.value.scrollTop +
         historyPanel.value.clientHeight >=
         historyPanel.value.scrollHeight - 200;
};

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

onMounted(() => {
  historyPanel.value?.addEventListener('click', handleHistoryPanelClick);

  // 设置 MutationObserver 监听消息容器的变化
  if (messageContainer.value && historyPanel.value) {
    mutationObserver = new MutationObserver(() => {
      nextTick(() => {
        // 仅当面板接近底部时才自动滚动，避免打断用户阅读历史
        if (isHistoryPanelNearBottom()) {
          if (historyPanel.value) {
            historyPanel.value.scrollTo({
              top: historyPanel.value.scrollHeight,
              behavior: 'smooth'
            });
          }
        }
      });
    });

    mutationObserver.observe(messageContainer.value, {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: false
    });
  }
});

// 监听 visibleMessages 长度变化，确保用户消息也会触发滚动
watch(() => props.visibleMessages.length, (newLength, oldLength) => {
  if (newLength > oldLength) {
    nextTick(() => {
      if (historyPanel.value) {
        setTimeout(() => {
          if (historyPanel.value) {
            historyPanel.value.scrollTo({
              top: historyPanel.value.scrollHeight,
              behavior: 'smooth'
            });
          }
        }, 50);
      }
    });
  }
});

onUnmounted(() => {
  historyPanel.value?.removeEventListener('click', handleHistoryPanelClick);
  if (mutationObserver) {
    mutationObserver.disconnect();
  }
});

defineExpose({
  historyPanel
});
</script>

<style scoped lang="postcss">
.scrollbar-hide {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>