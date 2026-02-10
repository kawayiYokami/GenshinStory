<template>
  <div v-if="question" class="card bg-base-100 shadow-sm rounded-2xl">
    <div class="card-body p-4">
      <h3 class="card-title text-base-content text-sm mb-2">{{ question.text }}</h3>
      <div class="flex flex-wrap gap-2">
        <div
          v-for="(suggestion, index) in question.suggestions"
          :key="index"
          class="question-suggestion-tag"
          @click="handleSendSuggestion(suggestion)"
        >
          <span class="flex items-center gap-1">
            <span class="badge badge-primary badge-xs flex-shrink-0">{{ index + 1 }}</span>
            <span class="text-sm leading-none">{{ suggestion }}</span>
          </span>
          <button
            class="question-suggestion-select-btn"
            @click.stop="handleSelectSuggestion(suggestion)"
            :title="'添加到输入框'"
          >
            <CornerDownLeft class="w-3 h-3" />
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
/* 建议标签样式 */
.question-suggestion-tag {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: hsl(var(--b2));
  border: 1px solid hsl(var(--b3));
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-suggestion-tag:hover {
  background-color: hsl(var(--b3));
  border-color: hsl(var(--p));
}

/* 选择按钮样式 */
.question-suggestion-select-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: transparent;
  border: none;
  border-radius: 0.25rem;
  color: hsl(var(--bc) / 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-suggestion-select-btn:hover {
  background-color: hsl(var(--p) / 0.2);
  color: hsl(var(--p));
}
</style>