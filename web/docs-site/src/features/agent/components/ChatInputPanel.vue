<template>
  <div class="flex flex-col gap-2 card bg-base-100 rounded-3xl shadow-lg border border-base-300 relative">
    <!-- 遮罩层：防止操作并显示加载状态 -->
    <div v-if="isGeneratingPaper || isCompressing" class="absolute inset-0 bg-base-100/70 z-50 flex flex-col items-center justify-center rounded-3xl backdrop-blur-sm cursor-not-allowed">
      <Loader2 class="w-8 h-8 animate-spin text-primary mb-2" />
      <span class="text-sm font-medium text-base-content/70">
        {{ isGeneratingPaper ? '正在生成知识报告...' : '正在压缩上下文...' }}
      </span>
    </div>

    <!-- 主要输入区域 -->
    <div class="flex flex-col gap-2 px-2 pt-2">
      <!-- 上下文超限警告 -->
      <div v-if="isContextOverLimit" class="alert alert-warning mb-2">
        <AlertTriangle class="w-4 h-4 inline mr-2" />
        <span>上下文已达到上限，请开启新对话或压缩上下文</span>
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
        <!-- 指令模式选择 -->
        <DaisyDropdown
          class="transparent-dropdown"
          :model-value="currentInstructionId || undefined"
          :options="instructionOptions"
          placeholder="选择模式"
          @update:modelValue="(value: string | number | boolean | null) => handleInstructionChange(value as string)"
        />

        <!-- AI 供应商选择 -->
        <DaisyDropdown
          class="transparent-dropdown"
          :model-value="activeConfigId || undefined"
          :options="configOptions"
          placeholder="选择配置"
          @update:modelValue="(value: string | number | boolean | null) => handleConfigChange(value as string)"
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

        <!-- 生成知识报告按钮 -->
        <button
          @click="handleGeneratePaper"
          :disabled="!canGeneratePaper || isGeneratingPaper || isCompressing"
          class="debug-panel-btn"
          title="生成报告"
        >
          <GraduationCap class="w-5 h-5" v-if="!isGeneratingPaper" />
          <Loader2 v-else class="w-5 h-5 animate-spin" />
        </button>

        <!-- 压缩上下文按钮 -->
        <button
          @click="handleCompressContext"
          :disabled="!canCompress || isCompressing || isGeneratingPaper"
          class="debug-panel-btn"
          title="压缩上下文"
        >
          <Minimize2 class="w-5 h-5" v-if="!isCompressing" />
          <Loader2 v-else class="w-5 h-5 animate-spin" />
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
import { AlertTriangle, Minimize2, MessageCirclePlus, Camera, FileText, GraduationCap, Loader2 } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import tokenizerService from '@/lib/tokenizer/tokenizerService';
import { snapdom } from '@zumer/snapdom';
import { academicPaperGeneratorService } from '../tools/implementations/academicPaperGeneratorService';
import promptService from '../tools/implementations/promptService';

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
const { availableAgents, currentRoleId, orderedMessages, isCompressing, currentInstructionId } = storeToRefs(agentStore);
const { switchAgent, resetAgent, compressAndStartNewChat, sendMessage, startNewSession, startNewSessionWithCurrentAgent, setInstruction } = agentStore;

// 指令列表
const instructionOptions = ref<{ value: string; label: string }[]>([]);

// 生成论文状态
const isGeneratingPaper = ref(false);

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
  const maxContextLength = activeConfig.value?.maxContextLength || 128000;
  return currentTokens > maxContextLength * 0.9;
});

const canCompress = computed(() => {
  return orderedMessages.value.length > 3; // 只要有足够的消息就可以压缩
});

const canGeneratePaper = computed(() => {
  return academicPaperGeneratorService.canGeneratePaper(orderedMessages.value);
});

// 下拉框选项
const configOptions = computed(() => {
  return configs.value.map(config => ({
    value: config.id,
    label: config.name
  }));
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

const handleInstructionChange = (instructionId: string) => {
  setInstruction(instructionId);
  // Optional: Trigger new session or update system prompt immediately?
  // For now, we just update the store state, which will be used for the next message/session.
  // Ideally, changing instruction should probably restart session or at least warn user.
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

// 生成论文处理方法
const handleGeneratePaper = async () => {
  if (!canGeneratePaper.value || isGeneratingPaper.value || isCompressing.value) return;

  try {
    isGeneratingPaper.value = true;

    // 生成论文
    const result = await academicPaperGeneratorService.generateAcademicPaper(orderedMessages.value);

    if (result.success && result.paperContent) {
      // 提供格式选择
      const format = await askUserForFormat();

      // 下载报告
      academicPaperGeneratorService.downloadPaper(result.paperContent, format);
      toast.success(`知识分析报告已生成并下载为${format.toUpperCase()}格式`);
    } else {
      toast.error(result.error || '生成知识报告失败，请稍后重试');
    }
  } catch (error) {
    console.error('生成知识报告失败:', error);
    const errorMessage = error instanceof Error ? error.message : '生成知识报告失败，请稍后重试';
    toast.error(errorMessage);
  } finally {
    isGeneratingPaper.value = false;
  }
};

// 询问用户下载格式
const askUserForFormat = async (): Promise<'md' | 'pdf'> => {
  return new Promise((resolve) => {
    // 创建选择对话框
    const modal = document.createElement('div');
    modal.className = 'modal modal-open';
    modal.innerHTML = `
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">选择下载格式</h3>
        <div class="flex gap-4 justify-center">
          <button class="btn btn-primary" id="md-btn">Markdown</button>
          <button class="btn btn-secondary" id="pdf-btn">PDF</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const mdBtn = modal.querySelector('#md-btn') as HTMLButtonElement;
    const pdfBtn = modal.querySelector('#pdf-btn') as HTMLButtonElement;

    const closeModal = () => {
      document.body.removeChild(modal);
    };

    mdBtn.onclick = () => {
      closeModal();
      resolve('md');
    };

    pdfBtn.onclick = () => {
      closeModal();
      resolve('pdf');
    };

    // 点击背景关闭
    modal.onclick = (e) => {
      if (e.target === modal) {
        closeModal();
        resolve('md'); // 默认格式
      }
    };
  });
};

// 压缩处理方法
const handleCompressContext = async () => {
  if (!canCompress.value || isCompressing.value || isGeneratingPaper.value) return;

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

// 截图处理方法 - 使用 snapdom
// 截图处理方法 - 使用 snapdom 并手动展开滚动区域
// 截图处理方法 - 使用 snapdom 并手动展开滚动区域
const handleScreenshot = async () => {
  const historyPanel = document.querySelector('.overflow-y-auto.scrollbar-hide.flex-1') as HTMLElement;
  if (!historyPanel) {
    toast.error('找不到聊天历史容器');
    console.error('找不到聊天历史容器');
    return;
  }

  // 保存原始样式
  const originalStyle = {
    overflow: historyPanel.style.overflow,
    maxHeight: historyPanel.style.maxHeight,
  };

  try {
    toast.info('正在准备截图, 请稍候...');

    // 临时修改样式以显示完整内容
    historyPanel.style.overflow = 'visible';
    historyPanel.style.maxHeight = 'none';

    // 滚动到顶部以确保从头开始捕获
    historyPanel.scrollTop = 0;

    // 等待DOM更新
    await nextTick();

    toast.info('正在生成截图...');
    console.log('开始截图 (snapdom)...');

    // 获取主容器的背景色
    const mainContainer = document.querySelector('.drawer.mx-auto.lg\\:drawer-open') as HTMLElement;
    const bgColor = mainContainer
      ? getComputedStyle(mainContainer).backgroundColor
      : '#ffffff';

    // 使用 snapdom 捕获 DOM
    const result = await snapdom(historyPanel, {
      backgroundColor: bgColor,
      embedFonts: true,
    });

    // 从捕获结果中生成 PNG data URL
    const dataUrl = await result.toPng();

    // 下载图片
    const link = document.createElement('a');
    link.download = `对话截图-${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.png`;
    link.href = dataUrl.src;
    link.click();

    console.log('截图已下载');
    toast.success('截图已保存');
  } catch (error) {
    console.error('截图失败:', error);
    toast.error(`截图失败: ${error instanceof Error ? error.message : '未知错误'}`);
  } finally {
    // 无论成功或失败，都恢复原始样式
    historyPanel.style.overflow = originalStyle.overflow;
    historyPanel.style.maxHeight = originalStyle.maxHeight;
    console.log('截图流程结束，样式已恢复');
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
onMounted(async () => {
  // Initialization handled by child components
  try {
    const instructions = await promptService.listAvailableInstructions();
    instructionOptions.value = instructions.map(instr => ({
      value: instr.id,
      label: instr.name
    }));
  } catch (error) {
    console.error('Failed to load instructions:', error);
    toast.error('加载指令失败');
  }
});

defineExpose({
  focus: () => chatInputBaseRef.value?.focus?.(),
  adjustTextareaHeight: () => chatInputBaseRef.value?.adjustTextareaHeight?.(),
});
</script>

<style scoped>
/* 透明下拉框样式 - 去掉边框和阴影，使其像普通按钮 */
:deep(.transparent-dropdown .btn) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

:deep(.transparent-dropdown .btn-outline) {
  border-color: transparent !important;
}

:deep(.transparent-dropdown .btn-outline:hover) {
  background: hsl(var(--bc) / 0.1) !important;
  border-color: transparent !important;
}
</style>
