<template>
  <div class="card card-compact bg-base-200 border border-base-300 shadow-xs rounded-2xl shadow-sm">
    <div class="card-body p-2">
      <div class="tool-call-card">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20">
          <!-- Search Icon -->
          <Search v-if="toolCall.tool === 'search_docs'" class="h-4 w-4 text-primary" />
          <!-- Read Doc Icon -->
          <FileText v-else-if="toolCall.tool === 'read_doc'" class="h-4 w-4 text-primary" />
          <!-- List Docs Icon -->
          <List v-else-if="toolCall.tool === 'list_docs'" class="h-4 w-4 text-primary" />
          <!-- Default/Generic Tool Icon -->
          <Wrench v-else class="h-4 w-4 text-primary" />
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
  Search,
  FileText,
  List,
  Wrench
} from 'lucide-vue-next';
import { extractFileName } from '@/utils/pathUtils';

interface ToolCall {
  tool: string;
  query?: string;
  path?: string;
  limit?: number;
  line_range?: string;
  question?: string;
  suggestions?: string[];
  original?: string;
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
  return toolNameMap[props.toolCall.tool] || props.toolCall.tool;
});

const displayValue = computed(() => {
  switch (props.toolCall.tool) {
    case 'search_docs':
      return props.toolCall.query || '';
    case 'read_doc': {
      const path = props.toolCall.path;
      return path ? extractFileName(path) : '';
    }
    case 'ask':
      return props.toolCall.question || '';
    default:
      return JSON.stringify(props.toolCall);
  }
});
</script>

<style scoped>
</style>