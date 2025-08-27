<template>
  <div class="card card-compact bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/20">
    <div class="card-body">
      <div class="tool-call-card">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20">
          <!-- Search Icon -->
          <MagnifyingGlassIcon v-if="toolCall.name === 'search_docs'" class="h-4 w-4 text-primary" />
          <!-- Read Doc Icon -->
          <DocumentTextIcon v-else-if="toolCall.name === 'read_doc'" class="h-4 w-4 text-primary" />
          <!-- List Docs Icon -->
          <ListBulletIcon v-else-if="toolCall.name === 'list_docs'" class="h-4 w-4 text-primary" />
          <!-- Default/Generic Tool Icon -->
          <WrenchScrewdriverIcon v-else class="h-4 w-4 text-primary" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-primary">{{ formattedToolName }}</div>
          <div class="text-xs opacity-70 truncate">{{ displayValue }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ListBulletIcon,
  WrenchScrewdriverIcon
} from '@heroicons/vue/24/outline';

interface ToolCall {
  name: string;
  params: Record<string, any>;
  xml?: string;
}

interface Props {
  toolCall: ToolCall;
}

const props = defineProps<Props>();

const toolNameMap: Record<string, string> = {
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