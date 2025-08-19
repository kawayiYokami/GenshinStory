<template>
  <div :class="['message-wrapper', message.role === 'user' ? 'user-wrapper' : 'assistant-wrapper']">
      <button v-if="message.role === 'user'" class="delete-from-here-button" @click="handleDeleteFromHere" title="从此处删除后续对话">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
      </button>
      <div :class="[
        'message',
        message.role,
        'message-bubble',
        {
          'bg-primary-container text-on-primary-container': message.role === 'user',
        }
      ]">
        <div :class="['content', { 'tool-content': message.tool_calls || message.type === 'tool_result' }]">
        <!-- DEBUG: Raw Content View -->
        <pre v-if="showRawContent" class="raw-content-debug">{{ message }}</pre>
        
        <!-- Simplified Rendering Pipeline -->
        <template v-else>
          <!-- User message, now handles text, images, or both -->
          <div v-if="message.role === 'user'" class="user-content-wrapper">
            <template v-if="Array.isArray(message.content)">
              <div v-for="(item, index) in message.content" :key="index" class="content-part">
                <p v-if="item.type === 'text'" class="text-part">{{ item.text }}</p>
                <img v-if="item.type === 'image_url'" :src="item.image_url.url" class="image-part" alt="User uploaded content"/>
                <!-- Render 'doc' as a standard internal link, mimicking the postprocessor -->
                <a v-if="item.type === 'doc'"
                   :href="item.path"
                   @click.prevent="handleDocClick(item.path)"
                   class="internal-doc-link"
                   :data-is-valid="!item.error"
                   :data-raw-link="`[[${item.name}|path:${item.path}]]`"
                >
                  {{ item.name }}
                </a>
              </div>
            </template>
            <template v-else>
              {{ message.content }}
            </template>
          </div>
  
          <!-- Assistant message lifecycle -->
          <template v-if="message.role === 'assistant'">
            <!-- State 1 & 2 are now merged. We either show the streaming text or the final markdown. -->
            <template v-if="message.type === 'text'">
              <div ref="contentContainer" class="assistant-content">
                <!-- Render the cleaned text content -->
                <div v-if="renderedHtml" class="prose-styling-container" v-html="renderedHtml"></div>
                <!-- Independently render the tool call cards -->
                <template v-if="message.tool_calls && message.tool_calls.length > 0">
                  <ToolCallCard v-for="toolCall in message.tool_calls" :key="toolCall.xml" :tool-call="toolCall" />
                </template>
              </div>
              <!-- Question/Suggestion Rendering -->
              <div class="w-full">
                <QuestionSuggestions
                  v-if="message.question"
                  :question="message.question"
                  @select-suggestion="handleSuggestionClick"
                  @send-suggestion="handleSendSuggestion"
                />
              </div>
            </template>
  
            <!-- Other message types (no animation) -->
            <div v-else-if="message.type === 'tool_status'" class="tool-status">{{ message.content }}</div>
            <ToolResultCard v-else-if="message.type === 'tool_result'" :content="message.content" />
            <div v-else-if="message.type === 'error'" class="error-container">
              <span class="error-text">{{ message.content }}</span>
              <button v-if="isLastMessage" @click="$emit('retry')" class="retry-button">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                重试
              </button>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick, onMounted, watchEffect } from 'vue';
import { useToast } from 'vue-toastification';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useSmartBuffer } from '@/composables/useSmartBuffer';
import ToolCallCard from './ToolCallCard.vue';
import ToolResultCard from './ToolResultCard.vue';
import QuestionSuggestions from './QuestionSuggestions.vue';

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  showRawContent: {
    type: Boolean,
    default: false,
  },
  isLastMessage: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits(['select-suggestion', 'send-suggestion', 'delete-from-here', 'retry']);

const toast = useToast();
const agentStore = useAgentStore();

// 标志位，确保渲染完成信号只发送一次
const hasSignaledRenderComplete = ref(false);

// 内容容器引用
const contentContainer = ref(null);

// 创建本地 refs 来驱动 useSmartBuffer
const localContent = ref(props.message.content);
const renderCompleted = ref(props.message.streamCompleted);

// 当 props 变化时，更新本地 refs
watch(() => props.message.content, (newContent) => {
  localContent.value = newContent;
});
watch(() => props.message.streamCompleted, (newValue) => {
  renderCompleted.value = newValue;
});

// 在 onMounted 中，对于已完成的消息，强制重新执行一次“流式”渲染
onMounted(() => {
  if (props.message.streamCompleted) {
    renderCompleted.value = false; // 强制进入“流式”状态
    nextTick(() => {
      renderCompleted.value = true; // 在下一个 tick 立即“完成”流
    });
  }
});

import { renderMarkdownSync, replaceLinkPlaceholders } from '@/features/viewer/services/MarkdownRenderingService'; // 导入渲染函数

// useSmartBuffer 现在总是依赖于我们可控的本地状态
const { renderedHtml: smartBufferHtml, renderableContent } = useSmartBuffer(
  localContent, // 传递本地 content ref
  renderCompleted // 传递本地 stream completion ref
);

const renderedHtml = ref('');
watchEffect(async () => {
  // watchEffect 会自动追踪 localContent 和 renderCompleted 的变化
  if (renderCompleted.value) {
    const markdownHtml = renderMarkdownSync(localContent.value || '');
    renderedHtml.value = await replaceLinkPlaceholders(markdownHtml);
  } else if (!props.message.streamCompleted) {
    // 仅在真实流式传输期间使用 smartBuffer 的输出
    renderedHtml.value = smartBufferHtml.value;
  } else {
    // 在 onMounted 强制刷新期间，暂时清空内容
    renderedHtml.value = '';
  }
});



// 新增的 watch，用于在消息变化时重置状态
watch(() => props.message.id, () => {
  hasSignaledRenderComplete.value = false;
});

// 使用 watch 监听消息变化，替代 onUpdated 钩子
watch(() => props.message, (newMessage) => {
  // 检查消息是否为 tool_result 类型且状态为 rendering
  if (newMessage.type === 'tool_result' && newMessage.status === 'rendering') {
    // 确保信号只发送一次
    if (!hasSignaledRenderComplete.value) {
      // 调用 agentStore 中的 confirmMessageRendered 方法
      agentStore.confirmMessageRendered(newMessage.id);
      // 设置标志位为 true，防止重复发送信号
      hasSignaledRenderComplete.value = true;
    }
  }
}, { deep: true, immediate: true });

const handleSuggestionClick = (suggestionText) => {
  emit('select-suggestion', suggestionText);
};

const handleSendSuggestion = (suggestionText) => {
  emit('send-suggestion', suggestionText);
};

const handleDeleteFromHere = () => {
  if (confirm(`确定要删除从这条消息开始的所有后续对话吗？此操作无法撤销。`)) {
    emit('delete-from-here', props.message.id);
  }
};

const handleDocClick = (path) => {
  toast.info(`Clicked on doc: ${path}. Preview functionality to be implemented.`);
};
</script>

<style scoped lang="postcss">
.user-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.content-part .text-part {
  margin: 0;
  white-space: pre-wrap; /* Preserve line breaks in text */
}
.content-part .image-part {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  object-fit: contain;
}

.message-wrapper {
  position: relative;
  padding: 0 !important; /* EXPLICITLY SET to 0 */
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-wrapper.assistant-wrapper {
  justify-content: flex-start;
  align-self: flex-start;
}

.message-wrapper.user-wrapper {
  justify-content: flex-end;
  align-self: flex-end;
}

.message {
  border-radius: 12px;
  max-width: 100%;
  width: fit-content;
  padding: 8px 12px; /* ADDED - This is now the single source of padding */
}
.message .content {
  word-wrap: break-word;
  font-size: 1rem;
  padding: 0 !important; /* EXPLICITLY SET to 0 */
  border-radius: 12px;
}
.message .content.tool-content {
  padding: 4px;
}

.tool-status {
  font-style: italic;
  color: var(--color-on-surface-variant);
  padding: 8px 12px;
  background-color: var(--color-surface-variant);
  border-radius: 8px;
  margin: 4px 0;
}
.error-container {
  display: flex;
  align-items: center;
  gap: 12px;
}
.error-text {
  color: var(--color-error);
  font-style: italic;
  flex-grow: 1;
}

.raw-content-debug {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--color-on-surface);
  background-color: var(--color-surface-variant);
  padding: 10px;
  border-radius: 4px;
  margin: 0;
}

:deep(.markdown-body) {
  background-color: transparent !important;
  padding: 0;
  color: var(--color-on-surface-variant);
}
:deep(.markdown-body pre) {
  background-color: transparent !important;
}

:deep(.internal-doc-link) {
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
  color: var(--color-primary);
}

:deep(.internal-doc-link:hover) {
    text-decoration: none;
}


.delete-from-here-button {
  background-color: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease-in-out;
  flex-shrink: 0;
}

.message-wrapper:hover .delete-from-here-button {
  opacity: 0.8;
  pointer-events: auto;
}

.delete-from-here-button:hover {
  opacity: 1;
  background-color: var(--color-error-container);
  color: var(--color-on-error-container);
}
</style>