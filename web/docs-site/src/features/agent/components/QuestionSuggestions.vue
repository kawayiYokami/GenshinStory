<template>
  <div v-if="question" class="card bg-base-200 shadow-sm border border-primary/20">
    <div class="card-body p-4">
      <h3 class="card-title text-primary text-sm mb-3">{{ question.text }}</h3>
      <div class="space-y-2">
        <div
          v-for="(suggestion, index) in question.suggestions"
          :key="index"
          class="question-suggestion-btn"
          @click="handleSendSuggestion(suggestion)"
        >
          <span class="flex items-baseline gap-2 flex-1">
            <span class="badge badge-primary badge-xs">{{ index + 1 }}</span>
            <span class="text-sm">{{ suggestion }}</span>
          </span>
          <button
            class="question-suggestion-select-btn"
            @click.stop="handleSelectSuggestion(suggestion)"
            :title="'添加到输入框'"
          >
            <CornerDownLeft class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CornerDownLeft } from 'lucide-vue-next';

// 类型定义
interface Question {
  text: string;
  suggestions: string[];
}

interface Props {
  question: Question;
}

interface Emits {
  (e: 'select-suggestion', suggestion: string): void;
  (e: 'send-suggestion', suggestion: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 事件处理函数
const handleSelectSuggestion = (suggestion: string): void => {
  emit('select-suggestion', suggestion);
};

const handleSendSuggestion = (suggestion: string): void => {
  emit('send-suggestion', suggestion);
};
</script>

<style scoped>
/* 保持按钮基本的过渡效果，但移除不必要的移动动画 */
.btn {
  transition: background-color 0.2s ease-in-out;
}
</style>