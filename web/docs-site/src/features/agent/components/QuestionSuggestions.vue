<template>
  <div v-if="question" class="mt-4 space-y-3 rounded-lg text-on-surface-variant">
    <p class="font-medium text-on-surface">{{ question.text }}</p>
    <div class="flex flex-col items-start gap-2">
      <div
        v-for="(suggestion, index) in question.suggestions"
        :key="index"
        class="group flex w-full cursor-pointer items-center justify-between rounded-lg border border-outline bg-surface px-3 py-2 text-sm"
        @click="$emit('send-suggestion', suggestion)"
      >
        <span class="flex items-baseline gap-2">
          <span class="font-semibold">{{ index + 1 }}.</span>
          <span>{{ suggestion }}</span>
        </span>
        <button class="ml-auto cursor-pointer rounded-full bg-surface-variant p-1.5 text-on-surface-variant opacity-0 transition-opacity duration-200 group-hover:opacity-100" @click.stop="$emit('select-suggestion', suggestion)" title="添加到输入框">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="7" x2="7" y2="17"></line><polyline points="17 17 7 17 7 7"></polyline></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  question: {
    type: Object,
    required: true,
  },
});

defineEmits(['select-suggestion', 'send-suggestion']);
</script>

<style scoped lang="postcss">
</style>