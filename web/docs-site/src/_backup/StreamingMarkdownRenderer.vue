<template>
  <div class="inline">
    <div class="streaming-html" v-html="renderedContent"></div>
    <span v-if="!isStreamComplete" class="inline-block w-[9px] h-[1.1em] bg-m3-on-surface-variant animate-blink align-bottom ml-[2px]"></span>
  </div>
</template>

<script setup>
// This component now renders real-time Markdown HTML.
// It receives pre-rendered, sanitized HTML from the parent component.
defineProps({
  renderedContent: {
    type: String,
    required: true,
  },
  isStreamComplete: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped>
@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
.animate-blink {
  animation: blink 1s step-end infinite;
}
</style>