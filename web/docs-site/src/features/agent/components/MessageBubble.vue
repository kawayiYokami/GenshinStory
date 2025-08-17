<template>
  <div :class="['message-wrapper', message.role === 'user' ? 'user-wrapper' : 'assistant-wrapper']">
    <button v-if="message.role === 'user'" class="delete-from-here-button" @click="handleDeleteFromHere" title="从此处删除后续对话">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
    </button>
    <div :class="['message', message.role]">
      <div class="content">
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
                <div v-if="renderedHtml" v-html="renderedHtml"></div>
                <!-- Independently render the tool call cards -->
                <template v-if="message.tool_calls && message.tool_calls.length > 0">
                  <ToolCallCard v-for="toolCall in message.tool_calls" :key="toolCall.xml" :tool-call="toolCall" />
                </template>
              </div>
              <!-- Question/Suggestion Rendering -->
              <div v-if="message.question" class="question-container">
                <p class="question-text">{{ message.question.text }}</p>
                <div class="suggestions-list">
                  <div
                    v-for="(suggestion, index) in message.question.suggestions"
                    :key="index"
                    class="suggestion-item"
                  >
                    <span class="suggestion-content" @click="handleSendSuggestion(suggestion)">
                      <span class="suggestion-index">{{ index + 1 }}.</span>
                      <span class="suggestion-text">{{ suggestion }}</span>
                    </span>
                    <button class="add-button" @click="handleSuggestionClick(suggestion)" title="添加到输入框">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="7" x2="7" y2="17"></line><polyline points="17 17 7 17 7 7"></polyline></svg>
                    </button>
                  </div>
                </div>
              </div>
            </template>
  
            <!-- Other message types (no animation) -->
            <div v-else-if="message.type === 'tool_status'" class="tool-status">{{ message.content }}</div>
            <div v-else-if="message.type === 'tool_result'" class="tool-result">
              <details>
                <summary>研究记录</summary>
                <pre v-if="message.content" class="tool-result-pre">{{ message.content }}</pre>
              </details>
            </div>
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

<style scoped>
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
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-wrapper.assistant-wrapper {
  justify-content: flex-start;
}

.message-wrapper.user-wrapper {
  justify-content: flex-end;
}

.message {
  border-radius: 12px;
  max-width: 100%;
  width: fit-content;
}
.message .content {
  word-wrap: break-word;
  font-size: 1rem;
  padding: 10px 16px;
  border-radius: 12px;
}
.message.user .content {
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
  border-bottom-right-radius: 2px;
}
.message.assistant .content {
  background-color: transparent;
  color: var(--m3-on-surface-variant);
}

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
  overflow: hidden;
}
.tool-result summary {
  cursor: pointer;
  font-weight: bold;
  padding: 8px 12px 8px 32px;
  outline: none;
  color: var(--genshin-accent-gold);
  position: relative;
  list-style: none;
}
.tool-result summary::-webkit-details-marker {
  display: none;
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
.tool-result-pre {
  white-space: pre-wrap;
  word-break: break-all;
}
.error-container {
  display: flex;
  align-items: center;
  gap: 12px;
}
.error-text {
  color: var(--m3-error);
  font-style: italic;
  flex-grow: 1;
}
.retry-button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid var(--m3-outline);
  color: var(--m3-on-surface-variant);
  padding: 4px 10px;
  border-radius: 16px;
  cursor: pointer;
  font-size: 0.85em;
  transition: background-color 0.2s, color 0.2s;
}
.retry-button:hover {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  border-color: var(--m3-primary);
}

.raw-content-debug {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  font-size: 0.8rem;
  color: #c5c8c6;
  background-color: #1e1e1e;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
}

:deep(.markdown-body) {
  background-color: transparent !important;
  padding: 0;
  color: var(--m3-on-surface-variant);
}
:deep(.markdown-body pre) {
  background-color: transparent !important;
}

.assistant-content {
  /* Inherit styles from the parent .content */
}

:deep(.internal-doc-link) {
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
  color: var(--m3-primary);
}

:deep(.internal-doc-link:hover) {
    text-decoration: none;
}

.question-container {
  margin-top: 16px;
}

.question-text {
  margin: 0 0 12px 0;
  font-weight: 500;
  color: var(--m3-on-surface);
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.suggestion-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
  border-radius: 20px;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border: 1px solid var(--m3-outline);
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
  font-size: 0.9rem;
  text-align: left;
  width: auto;
  max-width: 100%;
  overflow: hidden;
}

.suggestion-content {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  flex-grow: 1;
  transition: background-color 0.2s;
}

.suggestion-content:hover {
    background-color: rgba(0,0,0,0.1);
}

.add-button {
  background: transparent;
  border: none;
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: stretch;
  transition: background-color 0.2s, color 0.2s;
}

.add-button:hover {
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
}

.suggestion-item:hover {
  border-color: var(--m3-primary);
}

.suggestion-index {
  font-weight: 600;
  color: inherit;
}

.suggestion-text {
  white-space: normal;
  word-break: break-word;
}

.delete-from-here-button {
  background-color: var(--m3-surface);
  border: 1px solid var(--m3-outline);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--m3-on-surface-variant);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s, background-color 0.2s;
  flex-shrink: 0;
}

.message-wrapper:hover .delete-from-here-button {
  opacity: 0.8;
  pointer-events: auto;
}

.delete-from-here-button:hover {
  opacity: 1;
  background-color: var(--m3-error-container);
  color: var(--m3-on-error-container);
}
</style>