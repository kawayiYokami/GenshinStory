<template>
  <!-- 用户消息：保持简单的气泡设计 -->
  <div v-if="message.role === 'user'" class="chat chat-end animate-fade-in" style="animation-duration: 0.3s;">
    <button class="delete-message-btn" @click="handleDeleteFromHere" title="从此处删除后续对话">
      <Trash2 class="w-4 h-4" />
    </button>
    <div class="chat-bubble chat-bubble-primary">
      <div v-if="Array.isArray(message.content)" class="space-y-2">
        <div v-for="(item, index) in message.content" :key="index">
          <p v-if="item.type === 'text'" class="whitespace-pre-wrap text-sm">{{ item.text }}</p>
          <div v-if="item.type === 'image_url' && item.image_url" class="card bg-base-100 shadow-sm">
            <figure class="px-2 pt-2">
              <img :src="item.image_url.url" class="rounded-lg max-h-64 object-contain" alt="User uploaded content"/>
            </figure>
          </div>
          <div v-if="item.type === 'doc' && item.path" class="card card-compact bg-base-100 shadow-sm border-l-4 border-primary">
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

  <!-- 助理消息：简化为直接内容展示，靠左对齐，右侧留空 -->
  <div v-else class="message-container animate-fade-in mr-12" style="animation-duration: 0.3s;">
    <!-- DEBUG: Raw Content View -->
    <pre v-if="showRawContent" class="raw-content-debug">{{ message }}</pre>

    <!-- 助理文本消息 -->
    <template v-else-if="message.type === 'text'">
      <div v-if="renderedHtml" class="prose-styling-container" v-html="renderedHtml"></div>

      <!-- 工具调用 -->
      <template v-if="message.tool_calls && message.tool_calls.length > 0">
        <div class="divider divider-start text-xs opacity-60 mt-4">工具调用</div>
        <div class="flex flex-wrap gap-2">
          <ToolCallCard v-for="toolCall in message.tool_calls" :key="toolCall.xml" :tool-call="toolCall" />
        </div>
      </template>

      <!-- 建议问题 -->
      <div v-if="message.question" class="mt-4">
        <QuestionSuggestions
          :question="message.question"
          @select-suggestion="handleSuggestionClick"
          @send-suggestion="handleSendSuggestion"
        />
      </div>
    </template>

    <!-- 其他消息类型 -->
    <div v-else-if="message.type === 'tool_status'" class="card bg-info text-info-content shadow-sm">
      <div class="card-body p-3">
        <div class="flex items-center gap-2">
          <span class="loading loading-spinner loading-xs"></span>
          <span class="text-sm font-medium">{{ message.content }}</span>
        </div>
      </div>
    </div>

    <ToolResultCard v-else-if="message.type === 'tool_result'" :content="typeof message.content === 'string' ? message.content : JSON.stringify(message.content, null, 2)" />

    <div v-else-if="message.type === 'error'" class="card bg-error text-error-content shadow-sm">
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
import { Trash2, RefreshCw } from 'lucide-vue-next';
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

interface ToolCall {
  xml: string;
  name: string;
  params: Record<string, any>;
}

interface Question {
  text: string;
  suggestions: string[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  type?: 'text' | 'tool_status' | 'tool_result' | 'error';
  content: string | ContentPart[];
  tool_calls?: ToolCall[];
  question?: Question;
  streamCompleted?: boolean;
  status?: string;
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

// 创建本地 refs 来驱动 useSmartBuffer
const localContent = ref<string>(props.message.content as string);
const renderCompleted = ref<boolean>(props.message.streamCompleted || false);

// 当 props 变化时，更新本地 refs
watch(() => props.message.content, (newContent) => {
  localContent.value = typeof newContent === 'string' ? newContent : JSON.stringify(newContent);
});

watch(() => props.message.streamCompleted, (newValue) => {
  renderCompleted.value = newValue || false;
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

const renderedHtml = ref<string>('');
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
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

/* 用户消息样式 */
.chat {
  position: relative;
  padding: 1px 0;
}

/* 助理消息容器 */
.message-container {
  position: relative;
  padding: 2px 0;
  max-width: none;
}

/* 删除按钮 */
.delete-from-here-button {
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease-in-out;
}

.chat:hover .delete-from-here-button {
  opacity: 0.8;
  pointer-events: auto;
}

.delete-from-here-button:hover {
  opacity: 1;
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
</style>