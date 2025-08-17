<template>
  <div class="tool-call-card">
    <span class="tool-name">{{ formattedToolName }}:</span>
    <span class="tool-value">{{ displayValue }}</span>
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
.tool-call-card {
  border: 1px solid var(--m3-outline);
  border-radius: 8px;
  padding: 8px 12px; /* 减小垂直 padding */
  margin: 8px 0;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  font-size: 0.9rem;
  display: flex; /* 改为 flex 布局 */
  align-items: baseline; /* 基线对齐 */
  gap: 8px;
  white-space: nowrap; /* 防止换行 */
  overflow: hidden; /* 隐藏溢出内容 */
}

.tool-name {
  font-weight: 600;
  color: var(--m3-primary);
  flex-shrink: 0; /* 防止工具名被压缩 */
}

.tool-value {
  flex-grow: 1; /* 占据剩余空间 */
  overflow: hidden; /* 隐藏溢出内容 */
  text-overflow: ellipsis; /* 显示省略号 */
  white-space: nowrap; /* 确保单行 */
}
</style>