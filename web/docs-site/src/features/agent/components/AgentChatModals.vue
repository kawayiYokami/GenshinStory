<template>
  <!-- 模态框组件 -->
  <AgentSelectorModal
    :visible="isAgentSelectorVisible"
    :agents="availableAgents[currentDomain] || []"
    :selected-agent-id="currentRoleId"
    @close="toggleAgentSelector"
    @select-agent="handleSelectAgent"
  />
</template>

<script setup lang="ts">
/**
 * AgentChatModals 组件
 *
 * 这是智能体聊天界面的模态框组件容器，
 * 负责管理智能体选择器模态框的显示和交互。
 */

import { computed } from 'vue';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import AgentSelectorModal from './AgentSelectorModal.vue';

/**
 * 组件属性定义
 * @property {boolean} isAgentSelectorVisible - 智能体选择器是否可见
 * @property {Record<string, any[]>} availableAgents - 可用的智能体列表
 * @property {string} currentRoleId - 当前角色ID
 * @property {string} currentDomain - 当前域
 */
const props = defineProps<{
  isAgentSelectorVisible: boolean;
  availableAgents: Record<string, any[]>;
  currentRoleId: string;
  currentDomain: string;
}>();

/**
 * 组件事件定义
 * @event toggle-agent-selector - 切换智能体选择器显示状态时触发
 * @event select-agent - 选择智能体时触发
 */
const emit = defineEmits<{
  (e: 'toggle-agent-selector'): void;
  (e: 'select-agent', roleId: string): void;
}>();

/**
 * 智能体状态存储
 * 用于获取智能体相关信息
 */
const agentStore = useAgentStore();

/**
 * 应用状态存储
 * 用于获取应用相关信息
 */
const appStore = useAppStore();

/**
 * 事件处理函数：切换智能体选择器
 * 控制智能体选择器模态框的显示/隐藏
 */
const toggleAgentSelector = () => {
  emit('toggle-agent-selector');
};

/**
 * 事件处理函数：处理智能体选择
 * 当用户选择一个智能体时触发
 * @param {string} roleId - 选中的智能体ID
 */
const handleSelectAgent = (roleId: string) => {
  emit('select-agent', roleId);
};
</script>