<template>
  <div class="badge badge-outline my-1 gap-2">
    <div class="flex h-5 w-5 items-center justify-center" >
      <!-- Search Icon -->
      <svg v-if="toolCall.name === 'search_docs'" class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      <!-- Read Doc Icon -->
      <svg v-else-if="toolCall.name === 'read_doc'" class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
      <!-- List Docs Icon -->
      <svg v-else-if="toolCall.name === 'list_docs'" class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>
      <!-- Default/Generic Tool Icon -->
      <svg v-else class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>
    </div>
    <span class="font-medium">{{ formattedToolName }}:</span>
    <span class="truncate font-semibold">{{ displayValue }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  }
});

const toolNameMap = {
  search_docs: '检索文档',
  read_doc: '阅读文档',
  list_docs: '列出文档'
};

const formattedToolName = computed(() => {
  return toolNameMap[props.toolCall.name] || props.toolCall.name;
});

const displayValue = computed(() => {
  const params = props.toolCall.params;
  switch (props.toolCall.name) {
    case 'search_docs':
      return params.query;
    case 'read_doc': {
      const pathMatch = params.args.match(/<path>(.*?)<\/path>/);
      return pathMatch ? pathMatch[1] : params.args;
    }
    // 可以为其他工具添加更多 case
    default:
      // 对于未知工具，将参数对象转换为字符串
      return JSON.stringify(params);
  }
});
</script>

<style scoped>
</style>