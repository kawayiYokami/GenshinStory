<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue';
import { marked } from 'marked';
import 'github-markdown-css/github-markdown-light.css';

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
});

// This component is now "dumb" again. It only parses what it's given.
// The expensive processing is handled upstream.
const renderedContent = computed(() => {
  if (!props.content) return '';
  // The `breaks: true` option was creating double line breaks in combination
  // with the `white-space: pre-wrap` style in the parent. Removing it
  // makes the renderer compliant with standard Markdown and fixes the issue.
  return marked.parse(props.content, { gfm: true });
});
</script>

<style scoped>
.markdown-body {
  background-color: transparent !important;
  color: inherit;
  font-size: 1rem;
}
</style>