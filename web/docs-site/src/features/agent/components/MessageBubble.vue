<template>
  <!-- 用户消息：保持简单的气泡设计 -->
  <div v-if="message.role === 'user'" class="chat chat-end animate-slide-in-right" style="animation-duration: 0.3s;" :data-message-id="message.id" :data-message-role="message.role">
    <!-- 压缩摘要消息特殊样式 -->
    <div v-if="message.isCompressed" class="card bg-base-200 border border-base-300 shadow-xs rounded-2xl">
      <div class="card-body p-0">
        <div class="collapse collapse-arrow bg-base-100 p-0 rounded-2xl">
          <!-- 直接绑定到 isCompressedExpanded 是合理的，因为每个消息气泡组件实例都有自己的状态 -->
          <input type="checkbox" v-model="isCompressedExpanded" />
          <div class="collapse-title compressed-message-card">
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
      <div class="bg-primary text-primary-content rounded-2xl px-4 py-2 shadow-sm border border-primary">
        <div v-if="Array.isArray(message.content)" class="space-y-2">
          <div v-for="(item, index) in message.content" :key="index">
            <p v-if="item.type === 'text'" class="whitespace-pre-wrap text-sm inline-block">{{ item.text }}</p>
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
        <span v-else class="whitespace-pre-wrap text-sm inline-block">{{ message.content }}</span>
      </div>
    </div>

  </div>

  <!-- 助理消息：简化为直接内容展示，靠左对齐，右侧留空 -->
  <div v-else-if="!shouldHideAssistantMessage" class="message-container animate-slide-in-left" :class="{ 'streaming-message': !message.streamCompleted && message.type === 'text' && message.status !== 'error', 'typing-indicator': !message.streamCompleted && message.type === 'text' && message.status !== 'error' }" style="animation-duration: 0.3s;" :data-message-id="message.id" :data-message-role="message.role">
    <!-- DEBUG: Raw Content View -->
    <pre v-if="showRawContent" class="raw-content-debug">{{ message }}</pre>

    <!-- 助理文本消息 -->
    <template v-else-if="message.type === 'text'">
      <!-- 独立思维链（来自 DeepSeek、OpenAI o1、Gemini 等） -->
      <div v-if="reasoningContent" class="collapse collapse-arrow bg-base-100 border border-base-300 rounded-lg shadow mb-3">
        <input type="checkbox" />
        <div class="collapse-title text-sm font-medium flex items-center gap-2">
          <MessageSquareMore class="h-4 w-4" />
          <span>{{ reasoningStatusLabel }}</span>
          <span v-if="!message.streamCompleted" class="loading loading-dots loading-xs"></span>
        </div>
        <div class="collapse-content bg-base-100">
          <div class="text-sm whitespace-pre-wrap font-mono p-3">
            {{ reasoningContent }}
          </div>
        </div>
      </div>

      <!-- 内嵌思维链（从正文中提取的 <think>...</think>） -->
      <div v-if="thinkingContent" class="collapse collapse-arrow bg-base-100 border border-base-300 rounded-lg shadow mb-3">
        <input type="checkbox" />
        <div class="collapse-title text-sm font-medium flex items-center gap-2">
          <MessageSquareMore class="h-4 w-4" />
          <span>{{ thinkingStatusLabel }}</span>
          <span v-if="!message.streamCompleted" class="loading loading-dots loading-xs"></span>
        </div>
        <div class="collapse-content bg-base-100">
          <div class="text-sm whitespace-pre-wrap font-mono p-3">
            {{ thinkingContent }}
          </div>
        </div>
      </div>

      <!-- 主要内容 -->
      <div v-if="renderedHtml" class="prose-styling-container" v-html="renderedHtml"></div>

      <!-- 建议问题（从内容中解析） -->
      <div v-if="parsedQuestion" class="mt-3">
        <QuestionSuggestions
          :question="parsedQuestion"
          @select-suggestion="handleSuggestionClick"
          @send-suggestion="handleSendSuggestion"
        />
      </div>
    </template>

    <ToolResultCard
      v-else-if="message.type === 'tool_status' || message.type === 'tool_result'"
      :content="typeof message.content === 'string' ? message.content : JSON.stringify(message.content, null, 2)"
      :tool-name="message.toolName"
      :tool-input="message.toolInput"
      :status="message.status"
      :is-pending="message.type === 'tool_status' || message.status === 'rendering'"
    />

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
import { Trash2, RefreshCw, Archive, MessageSquareMore } from 'lucide-vue-next';
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
  role: 'user' | 'assistant' | 'tool';
  type?: 'text' | 'tool_status' | 'tool_result' | 'error' | 'compression_summary';
  content: string | ContentPart[];
  tool_calls?: ToolCall[];
  toolCallId?: string;
  toolName?: string;
  toolInput?: Record<string, unknown>;
  question?: Question;
  streamCompleted?: boolean;
  status?: string;
  isCompressed?: boolean;
  /** 独立思维链（来自 DeepSeek、OpenAI o1、Gemini 等模型的 reasoning 字段） */
  reasoning?: string;
  /** 思维链耗时（秒） */
  reasoningDuration?: number;
  /** 随机种子，用于确定性选择表情图片 */
  randomSeed?: number;
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
const localContent = ref<string>(cleanContentFromToolCalls(props.message.content as string || ' ', props.message.tool_calls));
const renderCompleted = ref<boolean>(props.message.streamCompleted || false);

// 当 props 变化时，更新本地 refs
watch(() => props.message.content, (newContent) => {
  const contentStr = typeof newContent === 'string' ? newContent : (newContent ? JSON.stringify(newContent) : ' ');
  localContent.value = cleanContentFromToolCalls(contentStr || ' ', props.message.tool_calls);
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
  const content = props.message.content;
  const contentStr = typeof content === 'string' ? content : (content ? JSON.stringify(content) : ' ');
  localContent.value = cleanContentFromToolCalls(contentStr || ' ', newToolCalls);
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
import { ContentProcessor } from '@/features/agent/processing/responses/parsers/ContentProcessor';
import { simpleSyntaxParser } from '@/features/agent/processing/responses/parsers/SimpleSyntaxParser';

// 独立思维链（来自 DeepSeek、OpenAI o1、Gemini 等模型的 reasoning 字段）
const reasoningContent = computed(() => {
  return props.message.reasoning?.trim() || null;
});

// 独立思维链状态标签
const reasoningStatusLabel = computed(() => {
  if (!reasoningContent.value) return null;

  // 流式传输中：显示"思考中..."
  if (!props.message.streamCompleted) {
    return '思考中...';
  }

  // 完成后：显示"已思考（Xs）"
  const duration = props.message.reasoningDuration;
  if (duration !== undefined && duration !== null) {
    return `已思考（${duration}s）`;
  }

  return '已思考';
});

// 从原始内容解析内嵌思维链 <think>...</think>
const thinkingContent = computed(() => {
  const content = localContent.value || '';
  const match = content.match(/<think>([\s\S]*?)<\/think>/);
  return match ? match[1].trim() : null;
});

// 内嵌思维链状态标签（<think>标签无法追踪时间，只显示状态）
const thinkingStatusLabel = computed(() => {
  if (!thinkingContent.value) return null;

  if (!props.message.streamCompleted) {
    return '思考中...';
  }

  return '已思考';
});

// 移除思维链后的原始内容
const contentWithoutThinkingRaw = computed(() => {
  return (localContent.value || '').replace(/<think>[\s\S]*?<\/think>/g, '').trim();
});

// useSmartBuffer 使用移除思维链后的内容
const { renderedHtml: smartBufferHtml, renderableContent } = useSmartBuffer(
  contentWithoutThinkingRaw, // 传递移除思维链后的内容
  renderCompleted
);

// 解析问题语法 [?问题|选项1|选项2]（从原始内容解析）
const parsedQuestion = computed(() => {
  const content = contentWithoutThinkingRaw.value;
  const askData = simpleSyntaxParser.extractAsk(content);
  if (askData) {
    return {
      text: askData.question,
      suggestions: askData.suggestions
    };
  }
  return null;
});

// 移除问题语法后的内容，然后渲染表情
const renderedHtml = computed(() => {
  let content = smartBufferHtml.value;
  // 移除问题语法
  content = simpleSyntaxParser.removeAskSyntax(content);
  // 渲染表情
  content = ContentProcessor.renderWithEmotes(content, props.message.randomSeed);
  return content;
});

const shouldHideAssistantMessage = computed(() => {
  if (props.message.role !== 'assistant' || props.message.type !== 'text') return false;
  const hasToolCalls = Array.isArray(props.message.tool_calls) && props.message.tool_calls.length > 0;
  if (!hasToolCalls) return false;
  const contentText = typeof props.message.content === 'string'
    ? props.message.content.trim()
    : props.message.content
        .map(item => item.type === 'text' ? (item.text || '') : '')
        .join('')
        .trim();
  const hasReasoning = Boolean(props.message.reasoning?.trim());
  return !contentText && !hasReasoning;
});



// 新增的 watch，用于在消息变化时重置状态
watch(() => props.message.id, () => {
  hasSignaledRenderComplete.value = false;
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
  // if (newType === 'tool_result') {
  //   console.log(`ToolResultCard Status: ${props.message.id} - status: ${newStatus}, hasSignaled: ${hasSignaledRenderComplete.value}`);
  // }
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
  cursor: pointer;
}

.compressed-message-card:hover {
  background-color: hsl(var(--b2));
  border-radius: 0.5rem;
}

/* 内联表情样式 */
:deep(.inline-emote) {
  display: block;
  margin: 0.5em 0;
  max-width: 300px;
  max-height: 300px;
}
</style>
