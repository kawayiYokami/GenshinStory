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
          <!-- User message, renders instantly -->
          <div v-if="message.role === 'user'">{{ message.content }}</div>
  
          <!-- Assistant message lifecycle -->
          <template v-if="message.role === 'assistant'">
            <!-- State 1 & 2 are now merged. We either show the streaming text or the final markdown. -->
            <template v-if="message.type === 'text'">
              <StreamingMarkdownRenderer
                v-if="!finalContent"
                :raw-content="message.content"
                :is-stream-complete="!!message.streamCompleted"
              />
              <MarkdownRenderer
                v-else
                :content="finalContent"
                @click="handleContentClick"
              />
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
import { ref, watch } from 'vue';
import StreamingMarkdownRenderer from './StreamingMarkdownRenderer.vue';
import MarkdownRenderer from './MarkdownRenderer.vue';
import markdownPostprocessorService from '@/services/MarkdownPostprocessorService';
import { useToast } from 'vue-toastification';

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
const finalContent = ref(null);

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

const handleContentClick = (event) => {
  const target = event.target.closest('.internal-doc-link');
  if (!target) return;

  event.preventDefault();

  const isValid = target.dataset.isValid === 'true';
  const rawLink = target.dataset.rawLink;

  if (isValid) {
    toast.success(`即将跳转到有效链接: ${rawLink}`);
    console.log("TODO: Implement navigation for valid link:", rawLink);
  } else {
    toast.error("该链接为无效链接，可能是AI的幻觉。", {
      timeout: 5000
    });
  }
};

// This watcher is now the single source of truth for transitioning
// from a streaming view to the final, post-processed Markdown view.
watch(
  () => props.message.streamCompleted,
  async (isComplete) => {
    if (isComplete && props.message.type === 'text') {
      const processedContent = await markdownPostprocessorService.process(props.message.content);
      finalContent.value = processedContent;
    }
  },
  { immediate: true } // immediate: true ensures it runs once on mount
);
</script>

<style scoped>
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
  max-width: 100%; /* message now takes full width of the padded wrapper */
  width: fit-content; /* But only as wide as its content */
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

/* Add styles for the final rendered markdown body */
:deep(.markdown-body) {
  background-color: transparent !important;
  padding: 0;
  color: var(--m3-on-surface-variant);
}
:deep(.markdown-body pre) {
  background-color: transparent !important;
}

:deep(.invalid-link) {
  color: var(--m3-error);
  text-decoration: underline dashed;
  text-underline-offset: 2px;
}

.question-container {
  margin-top: 16px;
  /* Removed background and border for a cleaner look */
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
  align-items: flex-start; /* Align items to the left */
}

.suggestion-item {
  display: flex;
  align-items: center; /* Center items vertically */
  justify-content: space-between; /* Push content and button to edges */
  padding: 0; /* Remove padding from container */
  border-radius: 20px; /* More rounded pill shape */
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border: 1px solid var(--m3-outline);
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
  font-size: 0.9rem;
  text-align: left; /* Ensure text inside button is left-aligned */
  width: auto; /* Allow button to size to its content */
  max-width: 100%; /* Prevent overflow */
  overflow: hidden; /* Hide overflowing content */
}

.suggestion-content {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  flex-grow: 1; /* Allow content to take up available space */
  transition: background-color 0.2s;
}

.suggestion-content:hover {
    background-color: rgba(0,0,0,0.1);
}

.add-button {
  background: transparent;
  border: none;
  /* border-left: 1px solid var(--m3-outline); */ /* Removed */
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: stretch; /* Make button height of parent */
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
  color: inherit; /* Inherit color from parent button */
}

.suggestion-text {
  white-space: normal; /* Allow text to wrap */
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
  opacity: 0; /* Hidden by default */
  pointer-events: none; /* Not clickable when hidden */
  transition: opacity 0.2s, background-color 0.2s;
  flex-shrink: 0; /* Prevent button from shrinking */
}

.message-wrapper:hover .delete-from-here-button {
  opacity: 0.8; /* Show on hover */
  pointer-events: auto; /* Clickable on hover */
}

.delete-from-here-button:hover {
  opacity: 1;
  background-color: var(--m3-error-container);
  color: var(--m3-on-error-container);
}
</style>