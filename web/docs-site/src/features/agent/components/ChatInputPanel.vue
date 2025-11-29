<template>
  <div class="flex flex-col gap-2 card bg-base-100 rounded-3xl shadow-lg border border-base-300">
    <!-- 主要输入区域 -->
    <div class="flex flex-col gap-2 px-2 pt-2">
      <!-- 上下文超限警告 -->
      <div v-if="isContextOverLimit" class="alert alert-warning mb-2">
        <AlertTriangle class="w-4 h-4 inline mr-2" />
        <span>上下文已达到上限，请开启新对话或压缩上下文</span>
      </div>

      <!-- 状态指示器（极简） -->
      <div v-if="isLoading || isProcessing" class="flex gap-1 py-1">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
      </div>

      <!-- 文本输入区 -->
      <ChatInputBase
        ref="chatInputBaseRef"
        v-model="localModelValue"
        :is-loading="isLoading"
        :is-processing="isProcessing"
        :show-raw-content="showRawContent"
        :attached-images="attachedImages"
        :attached-references="attachedReferences"
        @send="handleSend"
        @stop="stopAgent"
        @update:showRawContent="toggleDebugPanel"
        @update:attachedImages="updateAttachedImages"
        @update:attachedReferences="updateAttachedReferences"
      />

      <!-- 附件预览区 -->
      <ChatAttachments
        :attached-images="attachedImages"
        :attached-references="attachedReferences"
        @update:attachedImages="updateAttachedImages"
        @update:attachedReferences="updateAttachedReferences"
      />
    </div>

    <!-- 工具栏 -->
    <div class="flex justify-between items-center px-2 pb-2">
      <!-- 左侧工具组 -->
      <div class="flex gap-1">
        <!-- AI 供应商选择 -->
        <DaisyDropdown
          class="transparent-dropdown"
          :model-value="activeConfigId || undefined"
          :options="configOptions"
          placeholder="选择配置"
          @update:modelValue="(value: string | number | boolean | null) => handleConfigChange(value as string)"
        />

        <!-- 模型选择 -->
        <DaisyDropdown
          class="transparent-dropdown"
          :model-value="currentModel || undefined"
          :options="modelOptions"
          placeholder="选择模型"
          @update:modelValue="(value: string | number | boolean | null) => handleModelChange(value as string)"
        />
      </div>

      <!-- 右侧工具组 -->
      <div class="flex gap-1">
        <!-- 新会话按钮 -->
        <button
          @click="handleNewSession"
          class="new-session-btn"
          title="新会话"
        >
          <MessageCirclePlus class="w-5 h-5" />
        </button>

        <!-- 压缩上下文按钮 -->
        <button
          @click="handleCompressContext"
          :disabled="!canCompress || isCompressing"
          class="debug-panel-btn"
          title="压缩上下文"
        >
          <Archive class="w-5 h-5" v-if="!isCompressing" />
          <div v-if="isCompressing" class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
          </div>
        </button>

        <!-- 截图按钮 -->
        <button
          @click="handleScreenshot"
          class="debug-panel-btn"
          title="截图当前对话"
        >
          <Camera class="w-5 h-5" />
        </button>

        <!-- 原文切换按钮 -->
        <button
          @click="toggleDebugPanel"
          class="debug-panel-btn"
          title="原文切换"
        >
          <FileText class="w-5 h-5" />
        </button>

      </div>
    </div>

    <!-- 引用下拉框 -->
    <ReferenceDropdown
      ref="dropdownRef"
      :items="referenceItems"
      :visible="showDropdown"
      @select="handleReferenceSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue';
import { useToast } from 'vue-toastification';
import { useDataStore } from '@/features/app/stores/data';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { storeToRefs } from 'pinia';
import type { AgentInfo } from '@/features/agent/types';
import ReferenceDropdown from './ReferenceDropdown.vue';
import ChatInputBase from './ChatInputBase.vue';
import ChatAttachments from './ChatAttachments.vue';
import ChatToolbar from './ChatToolbar.vue';
import { useReferenceHandler } from './useReferenceHandler';
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue';
import { AlertTriangle, Archive, MessageCirclePlus, Camera, FileText } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { simpleContextCompressor } from '../services/simpleContextCompressor';
import tokenizerService from '@/lib/tokenizer/tokenizerService';
import html2canvas from 'html2canvas-pro';

interface ReferenceItem {
  path: string;
  name: string;
  type: string;
}

interface AttachmentItem {
  path: string;
  name: string;
  type: string;
}

// Stores
const dataStore = useDataStore();
const configStore = useConfigStore();
const agentStore = useAgentStore();
const appStore = useAppStore();
const router = useRouter();
const toast = useToast();

const { configs, activeConfigId, activeConfig } = storeToRefs(configStore);
const { fetchModels, setActiveConfig } = configStore;
const { availableAgents, currentRoleId, orderedMessages, isCompressing } = storeToRefs(agentStore);
const { switchAgent, resetAgent, compressAndStartNewChat, sendMessage, startNewSession, startNewSessionWithCurrentAgent } = agentStore;

// Composables
const {
  showDropdown,
  referenceItems,
  isProcessingReference,
  referenceStartPos,
  searchReferences,
  handleReferenceSelect: handleReferenceSelectInternal
} = useReferenceHandler();

// Props
const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Object,
    default: null,
  },
  isProcessing: {
    type: Boolean,
    default: false,
  },
  thinkingTime: {
    type: Number,
    default: 0,
  },
  showRawContent: {
    type: Boolean,
    default: false,
  },
});

// Emits
const emit = defineEmits(['update:modelValue', 'send', 'stop', 'update:showRawContent']);

// Local state
const localModelValue = ref(props.modelValue);
const attachedImages = ref<string[]>([]);
const attachedReferences = ref<AttachmentItem[]>([]);
const currentModel = ref('');
const isDevMode = import.meta.env.DEV;

// Reference states
const dropdownRef = ref<InstanceType<typeof ReferenceDropdown> | null>(null);
const chatInputBaseRef = ref<InstanceType<typeof ChatInputBase> | null>(null);

// Computed
const hasAttachments = computed(() =>
  attachedImages.value.length > 0 || attachedReferences.value.length > 0
);

// 上下文检查
const isContextOverLimit = computed(() => {
  if (!orderedMessages.value || orderedMessages.value.length === 0) return false;
  const currentTokens = tokenizerService.countTokens(
    orderedMessages.value.map(m =>
      Array.isArray(m.content) ? m.content.map(c => c.text || '').join(' ') : m.content || ''
    ).join('\n')
  );
  const maxTokens = activeConfig.value?.maxTokens || 128000;
  return currentTokens > maxTokens * 0.9;
});

const canCompress = computed(() => {
  return orderedMessages.value.length > 3; // 只要有足够的消息就可以压缩
});

// 下拉框选项
const configOptions = computed(() => {
  return configs.value.map(config => ({
    value: config.id,
    label: config.name
  }));
});

const modelOptions = computed(() => {
  if (!activeConfig.value?.availableModels) return []
  return activeConfig.value.availableModels.map(model => ({
    value: model,
    label: model
  }))
});

// 当前智能体
const currentAgent = computed(() => {
  if (!currentRoleId.value || !appStore.currentDomain || !availableAgents.value[appStore.currentDomain]) return null;
  return availableAgents.value[appStore.currentDomain].find((agent: AgentInfo) => agent.id === currentRoleId.value);
});

// 其他智能体（排除当前智能体）
const otherAgents = computed(() => {
  if (!appStore.currentDomain || !availableAgents.value[appStore.currentDomain]) return [];
  return availableAgents.value[appStore.currentDomain].filter((agent: AgentInfo) => agent.id !== currentRoleId.value);
});

// Methods
const toggleDebugPanel = () => {
  emit('update:showRawContent', !props.showRawContent);
};

const updateAttachedImages = (images: string[]) => {
  attachedImages.value = images;
};

const updateAttachedReferences = (references: AttachmentItem[]) => {
  attachedReferences.value = references;
};

const updateCurrentModel = (model: string) => {
  currentModel.value = model;
};

const handleConfigChange = (configId: string) => {
  if (configId) {
    setActiveConfig(configId);
  }
};

const handleModelChange = (model: string) => {
  // 更新当前模型
  currentModel.value = model;
  // 保存到配置中
  if (activeConfig.value && activeConfigId.value) {
    configStore.updateConfig(activeConfigId.value, { modelName: model });
  }
};

const handleSend = (payload: { text: string; images: string[]; references: AttachmentItem[] }) => {
  emit('send', payload);
  localModelValue.value = '';
  attachedImages.value = [];
  attachedReferences.value = [];
};

const stopAgent = () => {
  emit('stop');
};

const handleReferenceSelect = (item: ReferenceItem) => {
  handleReferenceSelectInternal(item, attachedReferences.value, updateAttachedReferences);

  const text = localModelValue.value;
  const newText = text.substring(0, referenceStartPos.value);
  localModelValue.value = newText;

  nextTick(() => {
    // Focus handling would need to be done through the ChatInputBase component
  });
};

// 压缩处理方法
const handleCompressContext = async () => {
  if (!canCompress.value || isCompressing.value) return;

  try {
    await compressAndStartNewChat();
    toast.success('上下文压缩成功，已开启新对话');
  } catch (error) {
    console.error('上下文压缩失败:', error);
    const errorMessage = error instanceof Error ? error.message : '上下文压缩失败，请稍后重试';
    toast.error(errorMessage);
  }
};

// 新会话处理方法
const handleNewSession = async () => {
  try {
    // 在开启新会话前先停止当前正在进行的请求
    stopAgent();

    // 等待一小段时间确保中断完成
    await new Promise(resolve => setTimeout(resolve, 100));

    await startNewSessionWithCurrentAgent();
    console.log('新会话已开启');
  } catch (error) {
    console.error('开启新会话失败:', error);
  }
};

// 截图处理方法
const handleScreenshot = async () => {
  try {
    console.log('开始截图...');

    // 找到聊天历史容器 - 使用更精确的选择器
    const historyPanel = document.querySelector('.overflow-y-auto.scrollbar-hide.flex-1') as HTMLElement;
    if (!historyPanel) {
      console.error('找不到聊天历史容器');
      toast.error('找不到聊天历史容器');
      return;
    }

    console.log('找到历史容器:', historyPanel);

    // 存储原始样式
    const originalMaxHeight = historyPanel.style.maxHeight;
    const originalOverflow = historyPanel.style.overflow;

    console.log('原始样式:', { maxHeight: originalMaxHeight, overflow: originalOverflow });

    // 临时解除滚动限制
    historyPanel.style.maxHeight = 'unset';
    historyPanel.style.overflow = 'unset';

    // 修复动画和透明度问题 - 临时禁用所有动画和过渡
    const style = document.createElement('style');
    style.textContent = `
      .overflow-y-auto.scrollbar-hide.flex-1 * {
        transition: none !important;
        animation: none !important;
        animation-play-state: paused !important;
      }
    `;
    document.head.appendChild(style);

    console.log('已解除滚动限制并禁用动画');

    // 等待DOM更新和动画停止
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 100)); // 等待动画完全停止

    console.log('开始生成截图...');

    // 获取主容器的背景色
    const mainContainer = document.querySelector('.drawer.mx-auto.lg\\:drawer-open') as HTMLElement;
    const bgColor = mainContainer
      ? getComputedStyle(mainContainer).backgroundColor
      : '#ffffff';

    console.log('获取到的背景色:', bgColor);

    // 截图 - 使用html2canvas-pro简化配置，设置正确的背景色
    const canvas = await html2canvas(historyPanel, {
      useCORS: true,
      backgroundColor: bgColor
    });

    console.log('截图生成成功，Canvas尺寸:', canvas.width, 'x', canvas.height);

    // 恢复原始样式
    historyPanel.style.maxHeight = originalMaxHeight;
    historyPanel.style.overflow = originalOverflow;

    // 移除临时样式，恢复动画
    if (style.parentNode) {
      style.parentNode.removeChild(style);
    }

    console.log('已恢复原始样式和动画');

    // 下载图片
    const link = document.createElement('a');
    link.download = `对话截图-${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.png`;
    link.href = canvas.toDataURL();
    link.click();

    console.log('截图已下载');
    toast.success('截图已保存');
  } catch (error) {
    console.error('截图失败:', error);
    toast.error('截图失败，请重试');
  }
};

// Watchers
// 同步模型名称
watch(() => activeConfig.value?.modelName, (newModelName) => {
  if (newModelName && newModelName !== currentModel.value) {
    currentModel.value = newModelName;
  }
}, { immediate: true });

watch(() => props.modelValue, (newValue) => {
  localModelValue.value = newValue;

  const cursorPos = 0; // This would need to be handled through the ChatInputBase component
  const textBeforeCursor = newValue.substring(0, cursorPos);
  const lastAt = textBeforeCursor.lastIndexOf('@');

  if (lastAt !== -1) {
    const query = textBeforeCursor.substring(lastAt + 1);
    if (/[\s\p{P}\p{S}]/u.test(query)) {
      if (isProcessingReference.value) {
        showDropdown.value = false;
        isProcessingReference.value = false;
      }
    } else {
      isProcessingReference.value = true;
      referenceStartPos.value = lastAt;
      // referenceQuery.value = query;
      searchReferences(query);
    }
  } else if (isProcessingReference.value) {
    showDropdown.value = false;
    isProcessingReference.value = false;
  }
});

// Lifecycle
onMounted(() => {
  // Initialization handled by child components
});

defineExpose({
  adjustTextareaHeight: () => chatInputBaseRef.value?.adjustTextareaHeight(),
  focus: () => chatInputBaseRef.value?.focus(),
});
</script>

<style scoped>
/* 思考点动画（DaisyUI没有提供） */
.thinking-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 9999px;
  background-color: hsl(var(--p));
  animation: pulse 1.4s ease-in-out infinite both;
}

.thinking-dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes pulse {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 压缩时的思考点动画容器 */
.thinking-dots {
  display: flex;
  gap: 2px;
  align-items: center;
}
.line-clamp-2 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 无边框透明下拉框样式 */
.transparent-dropdown :deep(.btn) {
  background: transparent;
  border-color: transparent;
}

.transparent-dropdown :deep(.btn:hover) {
  background: rgba(0, 0, 0, 0.05) !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}


</style>