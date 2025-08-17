<template>
  <div class="streaming-content-wrapper">
    <div class="streaming-html" v-html="renderedContent"></div>
    <span v-if="!isStreamComplete" class="blinking-cursor"></span>
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
.streaming-content-wrapper {
  display: inline; /* Allows cursor to be on the same line */
}
.streaming-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  color: inherit;
  display: inline; /* Critical for cursor positioning */
}

.blinking-cursor {
  display: inline-block;
  width: 9px;
  height: 1.1em;
  background-color: var(--m3-on-surface-variant);
  animation: blink 1s step-end infinite;
  vertical-align: bottom; /* Aligns the cursor with the text baseline */
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>