<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';
import 'github-markdown-css/github-markdown-light.css';

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
});

// This component is now "dumb" again. It only parses what it's given.
// The expensive processing is handled upstream.
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
});

const renderedContent = computed(() => {
  if (!props.content) return '';
  return md.render(props.content);
});
</script>

<style scoped>
.markdown-body {
  background-color: transparent !important;
  color: inherit;
  font-size: 1rem;
}
</style>