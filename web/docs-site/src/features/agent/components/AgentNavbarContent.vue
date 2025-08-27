<template>
  <div class="flex items-center gap-4">
    <span class="text-lg font-bold">{{ activeAgentName }}</span>
    <div class="h-4 border-l border-base-content/30"></div>
    <button @click="handleNewSession" class="new-session-btn" title="新会话">
      <PlusIcon class="w-4 h-4" />
    </button>
  </div>
</template>

<script setup lang="ts">
/**
 * AgentNavbarContent 组件
 *
 * 这是智能体聊天界面顶部导航栏的内容组件，
 * 显示当前智能体名称和新会话按钮。
 */

import { computed } from 'vue';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { PlusIcon } from '@heroicons/vue/24/outline';

/**
 * 组件属性定义
 * @property {string} activeAgentName - 当前激活的智能体名称
 */
const props = defineProps<{
  activeAgentName: string;
}>();

/**
 * 组件事件定义
 * @event new-session - 当用户点击新会话按钮时触发
 */
const emit = defineEmits<{
  (e: 'new-session'): void;
}>();

/**
 * 智能体状态存储
 * 用于获取当前智能体相关信息
 */
const agentStore = useAgentStore();

/**
 * 事件处理函数：处理新会话
 * 当用户点击新会话按钮时触发
 */
const handleNewSession = async () => {
  if (props.activeAgentName) {
    emit('new-session');
  }
};
</script>