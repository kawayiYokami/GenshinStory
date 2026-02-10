<template>
  <div class="flex items-end gap-2 p-2 bg-base-100 rounded-3xl transition-all duration-200 focus-within:bg-base-200/80">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      @input="handleInput"
      placeholder="输入消息... (@ 引用文档, Ctrl+V 粘贴图片)"
      @keydown.enter.exact.prevent="handleKeyDown"
      @keydown.up.prevent="handleKeyDown"
      @keydown.down.prevent="handleKeyDown"
      @keydown.esc.prevent="handleKeyDown"
      @keydown.backspace="handleKeyDown"
      :disabled="isLoading"
      @paste="handlePaste"
      maxlength="10000"
      class="flex-1 min-h-6 max-h-[200px] p-0 bg-transparent border-none outline-none resize-none text-sm leading-6 text-base-content placeholder:text-base-content/50"
      rows="1"
    ></textarea>

    <!-- 发送/停止按钮 -->
    <button
      @click="isLoading ? stopAgent() : handleSend()"
      :disabled="!isLoading && (!modelValue.trim() && attachedImages.length === 0 && attachedReferences.length === 0) || isContextOverLimit || isCompressing"
      class="btn btn-circle btn-primary btn-sm w-8 h-8 min-h-8"
      :title="isCompressing ? '正在压缩上下文...' : (isContextOverLimit ? '上下文已达到上限，请压缩上下文' : (isLoading ? '停止生成' : '发送消息'))"
    >
      <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
      <Send v-else class="w-5 h-5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue';
import { useDataStore } from '@/features/app/stores/data';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { storeToRefs } from 'pinia';
import type { AgentInfo } from '@/features/agent/types';
import ReferenceDropdown from './ReferenceDropdown.vue';
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue';
import debounce from 'lodash.debounce';
import {
  Send,
  Square,
  CirclePlus,
  Clock,
  FileText,
  Image,
  X,
  Wrench,
  AlertTriangle
} from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import tokenizerService from '@/lib/tokenizer/tokenizerService';

interface ReferenceItem {
  path: string;
  name: string;
  type: string;
}

interface AttachmentItem {
  path: string;
  name: string;
}

// Stores
const dataStore = useDataStore();
const configStore = useConfigStore();
const agentStore = useAgentStore();
const appStore = useAppStore();
const router = useRouter();

const { configs, activeConfigId, activeConfig } = storeToRefs(configStore);
const { fetchModels, setActiveConfig } = configStore;
const { availableAgents, currentRoleId, orderedMessages, isCompressing } = storeToRefs(agentStore);
const { switchAgent, resetAgent } = agentStore;


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
  attachedImages: {
    type: Array,
    default: () => []
  },
  attachedReferences: {
    type: Array,
    default: () => []
  }
});

// Emits
const emit = defineEmits(['update:modelValue', 'send', 'stop', 'update:showRawContent', 'update:attachedImages', 'update:attachedReferences']);

// Local state
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const currentModel = ref('');
const isDevMode = import.meta.env.DEV;
const showDebugPanel = ref(false);

// Computed
const isContextOverLimit = computed(() => {
  if (!orderedMessages.value || orderedMessages.value.length === 0) return false;
  const currentTokens = tokenizerService.countTokens(
    orderedMessages.value.map(m =>
      Array.isArray(m.content) ? m.content.map(c => c.text || '').join(' ') : m.content || ''
    ).join(' ')
  );
  const maxContextLength = activeConfig.value?.maxContextLength || 128000;
  return currentTokens > maxContextLength * 0.9;
});

// Methods
const toggleDebugPanel = () => {
  emit('update:showRawContent', !props.showRawContent);
};

// Reference states
const dropdownRef = ref<InstanceType<typeof ReferenceDropdown> | null>(null);
const showDropdown = ref(false);
const referenceItems = ref<ReferenceItem[]>([]);
const isProcessingReference = ref(false);
let referenceQuery = '';
let referenceStartPos = -1;

// Computed
const hasAttachments = computed(() =>
  props.attachedImages.length > 0 || props.attachedReferences.length > 0
);

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
const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 200)}px`;
  }
};

const handleInput = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLInputElement).value);
};

const handleSend = () => {
  if (props.modelValue.trim() || hasAttachments.value) {
    emit('send', {
      text: props.modelValue,
      images: props.attachedImages,
      references: props.attachedReferences,
    });
    emit('update:modelValue', '');
    emit('update:attachedImages', []);
    emit('update:attachedReferences', []);
  }
};

const stopAgent = () => {
  emit('stop');
};

// Reference handling
const searchReferences = debounce(async (query) => {
  if (query) {
    referenceItems.value = await dataStore.searchCatalog(query);
    showDropdown.value = referenceItems.value.length > 0;
  } else {
    showDropdown.value = false;
  }
}, 300);

const handleReferenceSelect = (item: ReferenceItem) => {
  if (!props.attachedReferences.some((ref: any) => ref.path === item.path)) {
    const newReferences = [...props.attachedReferences, item];
    emit('update:attachedReferences', newReferences);
  }

  const text = props.modelValue;
  const newText = text.substring(0, referenceStartPos);
  emit('update:modelValue', newText);

  showDropdown.value = false;
  isProcessingReference.value = false;
  referenceItems.value = [];

  nextTick(() => {
    textareaRef.value?.focus();
  });
};

// Toolbar actions

const handleConfigChange = (configId: string) => {
  if (configId) {
    setActiveConfig(configId);
  }
};

const handleModelChange = (model: string) => {
  currentModel.value = model;
  // 保存到配置中
  if (activeConfig.value && activeConfigId.value) {
    configStore.updateConfig(activeConfigId.value, { modelName: model });
  }
};

const handleNewChat = () => {
  resetAgent();
};

const handleNewChatWithCurrentAgent = () => {
  resetAgent();
};

const handleNewChatWithAgentId = async (agentId: string) => {
  // 先切换到指定的智能体，然后新建会话
  if (agentId !== currentRoleId.value) {
    await switchAgent(agentId);
  }
  resetAgent();
};


// Keyboard handling
const handleKeyDown = (event: KeyboardEvent) => {
  if (showDropdown.value) {
    switch (event.key) {
      case 'ArrowUp':
        dropdownRef.value?.moveUp();
        break;
      case 'ArrowDown':
        dropdownRef.value?.moveDown();
        break;
      case 'Enter':
        event.preventDefault();
        dropdownRef.value?.selectActiveItem();
        break;
      case 'Escape':
        showDropdown.value = false;
        isProcessingReference.value = false;
        break;
    }
  } else if (event.key === 'Enter' && !event.shiftKey) {
    handleSend();
  }
};

// Image paste handling
const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault();
      const blob = item.getAsFile();
      if (!blob) continue;

      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          const newImages = [...props.attachedImages, e.target.result as string];
          emit('update:attachedImages', newImages);
        }
      };
      reader.readAsDataURL(blob);
    }
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
  nextTick(adjustTextareaHeight);

  const cursorPos = textareaRef.value?.selectionStart || 0;
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
      referenceStartPos = lastAt;
      referenceQuery = query;
      searchReferences(referenceQuery);
    }
  } else if (isProcessingReference.value) {
    showDropdown.value = false;
    isProcessingReference.value = false;
  }
});

// Lifecycle
onMounted(() => {
  adjustTextareaHeight();
});

defineExpose({
  adjustTextareaHeight,
  focus: () => textareaRef.value?.focus(),
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

/* 文本截断（Tailwind已有，但保留以防兼容性问题） */
.line-clamp-2 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>