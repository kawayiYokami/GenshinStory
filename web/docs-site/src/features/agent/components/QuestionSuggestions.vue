<template>
  <div v-if="question" class="card bg-base-200 shadow-sm border border-primary/20">
    <div class="card-body p-4">
      <h3 class="card-title text-primary text-sm mb-3">{{ question.text }}</h3>
      <div class="space-y-2">
        <div
          v-for="(suggestion, index) in question.suggestions"
          :key="index"
          class="group flex w-full items-center justify-between btn btn-ghost btn-sm h-auto min-h-0 p-3 normal-case text-left transition-all duration-200 hover:bg-primary/5 hover:border-primary/30"
          @click="handleSendSuggestion(suggestion)"
        >
          <span class="flex items-baseline gap-2 flex-1">
            <span class="badge badge-primary badge-xs">{{ index + 1 }}</span>
            <span class="text-sm">{{ suggestion }}</span>
          </span>
          <button
            class="btn btn-circle btn-ghost btn-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            @click.stop="handleSelectSuggestion(suggestion)"
            :title="'添加到输入框'"
          >
            <ArrowDownLeftIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowDownLeftIcon } from '@heroicons/vue/24/outline';

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