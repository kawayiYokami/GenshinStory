<template>
  <!-- 用户消息：保持简单的气泡设计 -->
  <div v-if="message.role === 'user'" class="chat chat-end animate-slide-in-right" style="animation-duration: 0.3s;" :data-message-id="message.id" :data-message-role="message.role">
    <!-- 压缩摘要消息特殊样式 -->
    <div v-if="message.isCompressed" class="card bg-base-200 border border-base-300 shadow-xs">
      <div class="card-body p-0">
        <div class="collapse collapse-arrow bg-base-200/50 p-0">
          <!-- 直接绑定到 isCompressedExpanded 是合理的，因为每个消息气泡组件实例都有自己的状态 -->
          <input type="checkbox" v-model="isCompressedExpanded" />
          <div class="collapse-title compressed-message-card p-0">
            <div class="flex h-7 w-7 items-center justify-center rounded-full bg-primary/20">
              <Archive class="h-4 w-4 text-primary" />
            </div>
            <span class="font-medium text-sm">对话摘要</span>
          </div>
          <div class="collapse-content">
            <div class="divider mt-0 mb-3"></div>
            <div class="whitespace-pre-wrap text-sm bg-transparent p-0">{{ message.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 普通用户消息 -->
    <div v-else class="chat-bubble-container">
      <button class="delete-from-here-button" @click="handleDeleteFromHere" title="从此处删除后续对话">
        <Trash2 class="w-4 h-4" />
      </button>
      <div class="chat-bubble chat-bubble-primary">
        <div v-if="Array.isArray(message.content)" class="space-y-2">
          <div v-for="(item, index) in message.content" :key="index">
            <p v-if="item.type === 'text'" class="whitespace-pre-wrap text-sm">{{ item.text }}</p>
            <div v-if="item.type === 'image_url' && item.image_url" class="card bg-base-100 shadow-xl">
              <figure class="px-2 pt-2">
                <img :src="item.image_url.url" class="rounded-lg max-h-64 object-contain" alt="User uploaded content"/>
              </figure>
            </div>
            <div v-if="item.type === 'doc' && item.path" class="card card-compact bg-base-100 shadow-xl border-l-4 border-primary">
              <div class="card-body">
                <a :href="item.path"
                   @click.prevent="handleDocClick(item.path!)"
                   class="link link-primary font-medium"
                   :class="{ 'link-error': item.error }"
                   :data-raw-link="`[[${item.name}|path:${item.path}]]`"
                >
                  {{ item.name }}
                </a>
              </div>
            </div>
          </div>
        </div>
        <span v-else class="whitespace-pre-wrap text-sm">{{ message.content }}</span>
      </div>
    </div>

  </div>

  <!-- 助理消息：简化为直接内容展示，靠左对齐，右侧留空 -->
  <div v-else class="message-container animate-slide-in-left" :class="{ 'streaming-message': !message.streamCompleted && message.type === 'text', 'typing-indicator': !message.streamCompleted && message.type === 'text' }" style="animation-duration: 0.3s;" :data-message-id="message.id" :data-message-role="message.role">
    <!-- DEBUG: Raw Content View -->
    <pre v-if="showRawContent" class="raw-content-debug">{{ message }}</pre>

    <!-- 助理文本消息 -->
    <template v-else-if="message.type === 'text'">
      <div v-if="renderedHtml" class="prose-styling-container" v-html="renderedHtml"></div>

      <!-- 工具调用 -->
      <template v-if="message.tool_calls && message.tool_calls.length > 0">
        <div class="divider divider-start text-xs opacity-60">工具调用</div>
        <div class="flex flex-wrap gap-2">
          <ToolCallCard v-for="toolCall in message.tool_calls" :key="toolCall.name + JSON.stringify(toolCall.params)" :tool-call="toolCall" />
        </div>
      </template>

      <!-- 建议问题 -->
      <div v-if="message.question" class="">
        <QuestionSuggestions
          :question="message.question"
          @select-suggestion="handleSuggestionClick"
          @send-suggestion="handleSendSuggestion"
        />
      </div>
    </template>

    <!-- 其他消息类型 -->
    <div v-else-if="message.type === 'tool_status'" class="card bg-info text-info-content shadow-xl">
      <div class="card-body p-3">
        <div class="flex items-center gap-2">
          <span class="loading loading-spinner loading-xs"></span>
          <span class="text-sm font-medium">{{ message.content }}</span>
        </div>
      </div>
    </div>

    <ToolResultCard v-else-if="message.type === 'tool_result'" :content="typeof message.content === 'string' ? message.content : JSON.stringify(message.content, null, 2)" />

    <div v-else-if="message.type === 'error'" class="card bg-error text-error-content shadow-xl">
      <div class="card-body p-3">
        <div class="flex items-center justify-between gap-3">
          <span class="flex-1 text-sm">{{ message.content }}</span>
          <button v-if="isLastMessage" @click="$emit('retry')" class="btn btn-sm btn-ghost">
            <RefreshCw class="w-4 h-4" />
            重试
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted, watchEffect, type Ref } from 'vue';
import { useToast } from 'vue-toastification';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useSmartBuffer } from '@/composables/useSmartBuffer';
import { Trash2, RefreshCw, Archive } from 'lucide-vue-next';
import ToolCallCard from './ToolCallCard.vue';
import ToolResultCard from './ToolResultCard.vue';
import QuestionSuggestions from './QuestionSuggestions.vue';

// 类型定义
interface ContentPart {
  type: 'text' | 'image_url' | 'doc';
  text?: string;
  image_url?: {
    url: string;
  };
  name?: string;
  path?: string;
  error?: boolean;
}

import type { ToolCall } from '../utils/messageUtils';
// ToolCall 接口已从 messageUtils 导入

interface Question {
  text: string;
  suggestions: string[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  type?: 'text' | 'tool_status' | 'tool_result' | 'error' | 'compression_summary';
  content: string | ContentPart[];
  tool_calls?: ToolCall[];
  question?: Question;
  streamCompleted?: boolean;
  status?: string;
  isCompressed?: boolean;
}

interface Props {
  message: Message;
  showRawContent?: boolean;
  isLastMessage?: boolean;
}

interface Emits {
  (e: 'select-suggestion', suggestionText: string): void;
  (e: 'send-suggestion', suggestionText: string): void;
  (e: 'delete-from-here', messageId: string): void;
  (e: 'retry'): void;
  (e: 'rendered', messageId: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  showRawContent: false,
  isLastMessage: false
});

const emit = defineEmits<Emits>();

const toast = useToast();
const agentStore = useAgentStore();

// 标志位，确保渲染完成信号只发送一次
const hasSignaledRenderComplete = ref<boolean>(false);

// 内容容器引用
const contentContainer = ref<HTMLElement | null>(null);

// 压缩消息展开/折叠状态
// 注意：虽然这里使用了单一的 ref，但这是设计上合理的，因为：
// 1. 应用中同时只会存在一个压缩消息（对话摘要）
// 2. 每个消息气泡都是独立的组件实例，各自维护自己的状态
// 3. 不需要基于消息 ID 的状态管理，简化了实现
const isCompressedExpanded = ref<boolean>(false);

// 导入工具函数
import { cleanContentFromToolCalls } from '../utils/messageUtils';

// 创建本地 refs 来驱动 useSmartBuffer
const localContent = ref<string>(cleanContentFromToolCalls(props.message.content as string, props.message.tool_calls));
const renderCompleted = ref<boolean>(props.message.streamCompleted || false);

// 当 props 变化时，更新本地 refs
watch(() => props.message.content, (newContent) => {
  const contentStr = typeof newContent === 'string' ? newContent : JSON.stringify(newContent);
  localContent.value = cleanContentFromToolCalls(contentStr, props.message.tool_calls);
});

watch(() => props.message.streamCompleted, async (newValue) => {
  renderCompleted.value = newValue || false;

  // 当流式消息完成时（从 false 变为 true），等待 DOM 更新后发出 rendered 事件
  if (newValue === true && !hasSignaledRenderComplete.value) {
    await nextTick();
    emit('rendered', props.message.id);
    hasSignaledRenderComplete.value = true;
  }
});

// 监听 tool_calls 的变化
watch(() => props.message.tool_calls, (newToolCalls) => {
  const contentStr = typeof props.message.content === 'string' ? props.message.content : JSON.stringify(props.message.content);
  localContent.value = cleanContentFromToolCalls(contentStr, newToolCalls);
}, { deep: true });

// 在 onMounted 中，对于已完成的消息，强制重新执行一次"流式"渲染
onMounted(async () => {
  if (props.message.streamCompleted) {
    renderCompleted.value = false; // 强制进入"流式"状态
    await nextTick();
    renderCompleted.value = true; // 在下一个 tick 立即"完成"流
    // 等待 DOM 更新完成后再发出 rendered 事件
    await nextTick();
    emit('rendered', props.message.id);
  }
  // 如果消息正在流式传输，不在这里发出 rendered，等待 streamCompleted 变化
});

import { renderMarkdownSync, replaceLinkPlaceholders } from '@/features/viewer/services/MarkdownRenderingService'; // 导入渲染函数

// useSmartBuffer 现在总是依赖于我们可控的本地状态
const { renderedHtml: smartBufferHtml, renderableContent } = useSmartBuffer(
  localContent, // 传递本地 content ref
  renderCompleted // 传递本地 stream completion ref
);

const renderedHtml = ref<string>('');
watchEffect(async () => {
  // 始终使用 smartBuffer 的输出，让 useSmartBuffer 处理所有逻辑
  renderedHtml.value = smartBufferHtml.value;
});



// 新增的 watch，用于在消息变化时重置状态
watch(() => props.message.id, () => {
  hasSignaledRenderComplete.value = false;
  console.log(`Message ID changed, reset hasSignaledRenderComplete for ${props.message.id}`);
}, { immediate: false });

// 优化后的消息监听，只监听必要属性
watch([() => props.message.type, () => props.message.status], ([newType, newStatus]) => {
  // 检查消息是否为 tool_result 类型且状态为 rendering
  if (newType === 'tool_result' && newStatus === 'rendering') {
    // 确保信号只发送一次
    if (!hasSignaledRenderComplete.value) {
      // 调用 agentStore 中的 confirmMessageRendered 方法
      agentStore.confirmMessageRendered(props.message.id);
      // 设置标志位为 true，防止重复发送信号
      hasSignaledRenderComplete.value = true;
    }
  }

  // 添加调试日志
  if (newType === 'tool_result') {
    console.log(`ToolResultCard Status: ${props.message.id} - status: ${newStatus}, hasSignaled: ${hasSignaledRenderComplete.value}`);
  }
}, { immediate: true });

const handleSuggestionClick = (suggestionText: string): void => {
  emit('select-suggestion', suggestionText);
};

const handleSendSuggestion = (suggestionText: string): void => {
  emit('send-suggestion', suggestionText);
};

const handleDeleteFromHere = (): void => {
  if (confirm(`确定要删除从这条消息开始的所有后续对话吗？此操作无法撤销。`)) {
    emit('delete-from-here', props.message.id);
  }
};

const handleDocClick = (path: string): void => {
  try {
    // 这里可以添加实际的文档预览逻辑
    toast.info(`正在加载文档: ${path}`);
    // 模拟异步操作
    setTimeout(() => {
      toast.success(`文档加载完成: ${path}`);
    }, 1000);
  } catch (error) {
    toast.error(`文档加载失败: ${path}`);
    console.error('文档加载错误:', error);
  }
};
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes slide-in-left {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slide-in-right {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes typing-cursor {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.animate-fade-in {
  animation: fade-in 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.animate-slide-in-left {
  animation: slide-in-left 0.3s ease-out;
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

.typing-indicator::after {
  content: '▊';
  animation: typing-cursor 1s infinite;
  color: hsl(var(--bc));
  font-weight: bold;
  margin-left: 2px;
}

.streaming-message {
  border-radius: 0.75rem;
  transition: all 0.3s ease;
}

/* 用户消息样式 */
.chat {
  position: relative;
  padding: 8px 0;
}

.chat-bubble-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-end;
}

/* 删除按钮 */
.delete-from-here-button {
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease-in-out;
  background: transparent;
  border: none;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-bubble-container:hover .delete-from-here-button {
  opacity: 0.8;
  pointer-events: auto;
}

.delete-from-here-button:hover {
  opacity: 1;
  background: hsl(var(--bc) / 0.1);
}

/* 助理消息容器 */
.message-container {
  position: relative;
  padding: 8px 0;
  max-width: none;
}

/* Debug 模式 */
.raw-content-debug {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  font-size: 0.8rem;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  background: rgba(0, 0, 0, 0.05);
}

/* 压缩消息卡片样式 - 参考ToolResultCard */
.compressed-message-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
}

.compressed-message-card:hover {
  background-color: hsl(var(--b2));
  border-radius: 0.5rem;
}
</style>