<template>
  <div class="flex flex-col gap-2 card bg-base-200 shadow-lg">
    <!-- 主要输入区域 -->
    <div class="flex flex-col gap-2 px-4 pt-3">
      <!-- 状态指示器（极简） -->
      <div v-if="isLoading || isProcessing" class="flex gap-1 py-1">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
      </div>

      <!-- 文本输入区 -->
      <ChatInputBase
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
    <div class="flex justify-between items-center px-4 pb-3">
      <!-- 左侧工具组 -->
      <div class="flex gap-1">
        <!-- AI 供应商选择 -->
        <DaisyDropdown
          :model-value="activeConfigId || undefined"
          :options="configOptions"
          placeholder="选择配置"
          @update:modelValue="(value: string | number | boolean | null) => handleConfigChange(value as string)"
        />

        <!-- 模型选择 -->
        <DaisyDropdown
          :model-value="currentModel || undefined"
          :options="modelOptions"
          placeholder="选择模型"
          @update:modelValue="(value: string | number | boolean | null) => handleModelChange(value as string)"
        />
      </div>

      <!-- 右侧工具组 -->
      <div class="flex gap-1">
        <!-- 调试按钮 (仅在开发模式下显示) -->
        <button
          v-if="isDevMode"
          @click="toggleDebugPanel"
          class="debug-panel-btn"
          title="调试面板"
        >
          <WrenchIcon class="w-4 h-4" />
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
import ChatInputBase from './ChatInputBase.vue';
import ChatAttachments from './ChatAttachments.vue';
import ChatToolbar from './ChatToolbar.vue';
import { useReferenceHandler } from './useReferenceHandler';
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue';
import {
  PaperAirplaneIcon,
  StopIcon,
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
  type: string;
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
const { switchAgent, resetAgent } = agentStore;

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

// Computed
const hasAttachments = computed(() =>
  attachedImages.value.length > 0 || attachedReferences.value.length > 0
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
  // Handle config change
};

const handleModelChange = (model: string) => {
  // Handle model change
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
  // Expose methods that might be needed by parent components
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