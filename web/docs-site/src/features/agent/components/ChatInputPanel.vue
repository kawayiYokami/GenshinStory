<template>
  <div class="flex flex-col gap-2 p-3 card bg-base-100 shadow-lg">
    <!-- 主要输入区域 -->
    <div class="flex flex-col gap-2">
      <!-- 状态指示器（极简） -->
      <div v-if="isLoading || isProcessing" class="flex gap-1 px-3 py-1">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
      </div>

      <!-- 文本输入区 -->
      <div class="flex items-end gap-2 p-3 bg-base-200 rounded-xl transition-all duration-200 focus-within:bg-base-300">
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
          class="flex-1 min-h-[24px] max-h-[200px] p-0 bg-transparent border-none outline-none resize-none text-sm leading-6 text-base-content placeholder:text-base-content/50"
          rows="1"
        ></textarea>

        <!-- 发送/停止按钮 -->
        <button
          @click="isLoading ? stopAgent() : handleSend()"
          :disabled="!isLoading && (!modelValue.trim() && attachedImages.length === 0 && attachedReferences.length === 0)"
          class="btn btn-circle btn-primary btn-sm w-8 h-8 min-h-8"
          :title="isLoading ? '停止生成' : '发送消息'"
        >
          <StopIcon v-if="isLoading" class="w-5 h-5" />
          <PaperAirplaneIcon v-else class="w-5 h-5" />
        </button>
      </div>

      <!-- 附件预览区 -->
      <div v-if="hasAttachments" class="flex flex-wrap gap-2 px-3">
        <div v-for="(ref, index) in attachedReferences" :key="ref.path" class="badge badge-neutral gap-1.5 max-w-[200px]">
          <DocumentTextIcon class="w-4 h-4" />
          <span class="truncate">{{ ref.name }}</span>
          <button @click="removeReference(index)" class="btn btn-ghost btn-xs p-0 min-h-0 h-auto hover:text-error">
            <XMarkIcon class="w-3 h-3" />
          </button>
        </div>
        <div v-for="(image, index) in attachedImages" :key="index" class="badge badge-neutral gap-1.5">
          <PhotoIcon class="w-4 h-4" />
          <span>图片 {{ index + 1 }}</span>
          <button @click="removeImage(index)" class="btn btn-ghost btn-xs p-0 min-h-0 h-auto hover:text-error">
            <XMarkIcon class="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="flex justify-between items-center px-2">
      <!-- 左侧工具组 -->
      <div class="flex gap-1">
        <!-- AI 供应商选择 -->
        <div class="dropdown dropdown-top dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-sm text-xs gap-1">
            <CubeIcon class="w-4 h-4" />
            <span>{{ activeConfig?.name || 'AI' }}</span>
            <ChevronUpIcon class="w-3 h-3" />
          </div>
          <ul tabindex="0" class="dropdown-content menu p-2 shadow-lg rounded-box w-48 bg-base-200 border border-base-300 mb-1 max-h-60 overflow-y-auto z-10">
            <li v-for="config in configs" :key="config.id">
              <a @click="handleConfigChange(config.id)">
                <div class="flex items-center justify-between">
                  <span>{{ config.name }}</span>
                  <span v-if="config.id === activeConfigId" class="text-xs opacity-70">✓</span>
                </div>
              </a>
            </li>
          </ul>
        </div>

        <!-- 模型选择 -->
        <div class="dropdown dropdown-top dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-sm text-xs gap-1">
            <SparklesIcon class="w-4 h-4" />
            <span>{{ currentModel || 'Model' }}</span>
            <ChevronUpIcon class="w-3 h-3" />
          </div>
          <ul tabindex="0" class="dropdown-content menu p-2 shadow-lg rounded-box w-52 bg-base-200 border border-base-300 mb-1 z-10">
            <li v-if="!activeConfig?.availableModels || activeConfig.availableModels.length === 0" class="disabled">
              <span class="text-xs opacity-70">请先设置有效的 API Key</span>
            </li>
            <li v-for="model in activeConfig?.availableModels || []" :key="model">
              <a @click="handleModelChange(model)"
                 :class="{ 'active': model === currentModel }">
                <div class="flex items-center justify-between">
                  <span>{{ model }}</span>
                  <span v-if="model === currentModel" class="text-xs opacity-70">✓</span>
                </div>
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- 右侧工具组 -->
      <div class="flex gap-1">
        <!-- 调试按钮 (仅在开发模式下显示) -->
        <button
          v-if="isDevMode"
          @click="toggleDebugPanel"
          class="btn btn-ghost btn-sm"
          title="调试面板"
        >
          <WrenchIcon class="w-4 h-4" />
        </button>

        <!-- 新建会话 -->
        <div class="dropdown dropdown-top dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-sm" title="新建会话">
            <PlusCircleIcon class="w-4 h-4" />
          </div>
          <div tabindex="0" class="dropdown-content menu p-0 shadow-2xl rounded-box bg-base-200 border border-base-300 mb-1 w-96 z-10">
            <!-- 当前智能体（大号显示） -->
            <div v-if="currentAgent" class="p-4 border-b border-base-300">
              <div class="text-sm text-base-content/70 mb-2">当前智能体</div>
              <a @click="handleNewChatWithCurrentAgent"
                 class="block p-4 rounded-lg bg-primary text-primary-content hover:bg-primary-focus transition-colors cursor-pointer">
                <div class="text-xl font-bold mb-1">{{ currentAgent.name }}</div>
                <div class="text-sm opacity-90">{{ currentAgent.description }}</div>
              </a>
            </div>

            <!-- 其他智能体网格 -->
            <div class="p-4">
              <div class="text-sm text-base-content/70 mb-3">为以下智能体开启新会话</div>
              <div class="grid grid-cols-2 gap-2">
                <a v-for="agent in otherAgents"
                   :key="agent.id"
                   @click="handleNewChatWithAgentId(agent.id)"
                   class="block p-3 rounded-lg bg-base-100 hover:bg-base-300 transition-colors cursor-pointer">
                  <div class="font-semibold">{{ agent.name }}</div>
                  <div class="text-xs text-base-content/70 mt-1 line-clamp-2">{{ agent.description }}</div>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史记录 -->
        <button @click="emit('update:showHistoryPanel', true)" class="btn btn-ghost btn-sm" title="历史记录">
          <ClockIcon class="w-4 h-4" />
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
import { useDataStore } from '@/features/app/stores/data';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { storeToRefs } from 'pinia';
import type { AgentInfo } from '@/features/agent/types';
import ReferenceDropdown from './ReferenceDropdown.vue';
import debounce from 'lodash.debounce';
import {
  ChevronUpIcon,
  PaperAirplaneIcon,
  StopIcon,
  CubeIcon,
  SparklesIcon,
  PlusCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  PhotoIcon,
  XMarkIcon,
  WrenchIcon
} from '@heroicons/vue/24/outline';
import { useRouter } from 'vue-router';

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
const { availableAgents, currentRoleId } = storeToRefs(agentStore);
const { resetAgent, switchAgent } = agentStore;

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
  showHistoryPanel: {
    type: Boolean,
    default: false,
  },
  showRawContent: {
    type: Boolean,
    default: false,
  },
});

// Emits
const emit = defineEmits(['update:modelValue', 'send', 'stop', 'update:showHistoryPanel', 'update:showRawContent']);

// Local state
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const attachedImages = ref<string[]>([]);
const attachedReferences = ref<AttachmentItem[]>([]);
const currentModel = ref('');
const isDevMode = import.meta.env.DEV;
const showDebugPanel = ref(false);

// Methods
const toggleDebugPanel = () => {
  emit('update:showRawContent', !props.showRawContent);
};

// Reference states
const dropdownRef = ref<any>(null);
const showDropdown = ref(false);
const referenceItems = ref<ReferenceItem[]>([]);
const isProcessingReference = ref(false);
let referenceQuery = '';
let referenceStartPos = -1;

// Computed
const hasAttachments = computed(() =>
  attachedImages.value.length > 0 || attachedReferences.value.length > 0
);

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
      images: attachedImages.value,
      references: attachedReferences.value,
    });
    emit('update:modelValue', '');
    attachedImages.value = [];
    attachedReferences.value = [];
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
  if (!attachedReferences.value.some(ref => ref.path === item.path)) {
    attachedReferences.value.push(item);
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

const handleNewChatWithAgentId = (agentId: string) => {
  // 先切换到指定的智能体，然后新建会话
  if (agentId !== currentRoleId.value) {
    switchAgent(agentId);
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
          attachedImages.value.push(e.target.result as string);
        }
      };
      reader.readAsDataURL(blob);
    }
  }
};

const removeImage = (index: number) => {
  attachedImages.value.splice(index, 1);
};

const removeReference = (index: number) => {
  attachedReferences.value.splice(index, 1);
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