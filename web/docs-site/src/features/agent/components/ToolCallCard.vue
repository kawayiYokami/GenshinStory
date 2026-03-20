<template>
  <div class="card card-compact bg-base-100 border border-base-300 rounded-2xl shadow-sm">
    <div class="card-body p-2">
      <div class="tool-call-card">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-info">
          <!-- Search Icon -->
          <Search v-if="toolCall.tool === 'search_docs'" class="h-4 w-4 text-base-content" />
          <!-- Read Doc Icon -->
          <FileText v-else-if="toolCall.tool === 'read_doc'" class="h-4 w-4 text-base-content" />
          <!-- Resolve Source Link Icon -->
          <Link2 v-else-if="toolCall.tool === 'resolve_source_link'" class="h-4 w-4 text-base-content" />
          <!-- List Docs Icon -->
          <List v-else-if="toolCall.tool === 'list_docs'" class="h-4 w-4 text-base-content" />
          <!-- Ask Choice Icon -->
          <List v-else-if="toolCall.tool === 'ask_choice'" class="h-4 w-4 text-base-content" />
          <!-- Explore Icon -->
          <Compass v-else-if="toolCall.tool === 'explore'" class="h-4 w-4 text-base-content" />
          <!-- Default/Generic Tool Icon -->
          <Wrench v-else class="h-4 w-4 text-base-content" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-base-content">{{ formattedToolName }}</div>
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
  Link2,
  List,
  Compass,
  Wrench
} from 'lucide-vue-next';
import { extractFileName } from '@/utils/pathUtils';

interface ToolCall {
  tool: string;
  tasks?: string[];
  query?: string;
  path?: string;
  limit?: number;
  maxResults?: number;
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
  resolve_source_link: '信源链接',
  list_docs: '列出文档',
  ask_choice: '询问选择',
  explore: '探索任务',
  memory: '记忆工具',
  switch_behavior: '切换行为',
  world_tree_query: '世界树查询',
  world_tree_expand: '世界树扩展',
  world_tree_paths: '世界树路径'
};

const formattedToolName = computed(() => {
  return toolNameMap[props.toolCall.tool] || props.toolCall.tool;
});

const displayValue = computed(() => {
  switch (props.toolCall.tool) {
    case 'search_docs': {
      let displayText = props.toolCall.query || '';
      // 添加 maxResults 信息
      if (props.toolCall.maxResults) {
        displayText += ` (最多${props.toolCall.maxResults}条结果)`;
      }
      return displayText;
    }
    case 'read_doc': {
      const path = props.toolCall.path;
      let displayText = path ? extractFileName(path) : '';
      // 添加行范围信息
      if (props.toolCall.line_range) {
        displayText += ` (行: ${props.toolCall.line_range})`;
      }
      return displayText;
    }
    case 'resolve_source_link': {
      const title = (props.toolCall as any).title || props.toolCall.path || (props.toolCall as any).fileName || '';
      const k = Number((props.toolCall as any).k || 0);
      const minScore = (props.toolCall as any).minScore;
      let displayText = title ? extractFileName(String(title)) : '解析信源链接';
      if (k > 0) displayText += ` (k=${k})`;
      if (typeof minScore === 'number') displayText += ` (≥${minScore})`;
      return displayText;
    }
    case 'ask_choice':
      return props.toolCall.question || '';
    case 'explore':
      return `任务数: ${Array.isArray(props.toolCall.tasks) ? props.toolCall.tasks.length : 0}`;
    case 'memory': {
      const action = String((props.toolCall as any).action || 'add');
      if (action === 'recall') {
        const query = String((props.toolCall as any).query || '').trim();
        return query ? `recall: ${query}` : 'recall';
      }
      const keywords = (props.toolCall as any).keywords;
      if (Array.isArray(keywords) && keywords.length > 0) {
        return `${action}: ${keywords.join('、')}`;
      }
      return action;
    }
    case 'switch_behavior': {
      const instructionId = String((props.toolCall as any).instructionId || '').trim();
      return instructionId ? `-> ${instructionId}` : '切换行为';
    }
    default:
      return JSON.stringify(props.toolCall);
  }
});
</script>

<style scoped>
</style>
