<template>
  <div class="flex items-center gap-4 relative">
    <div class="flex items-center gap-2">
      <div class="avatar">
        <div class="w-7 rounded-full bg-base-200">
          <img
            v-if="currentAgentIcon"
            :src="currentAgentIcon"
            alt="agent avatar"
            class="object-cover w-full h-full"
            @error="handleIconError"
          />
          <span
            v-else
            class="w-full h-full inline-flex items-center justify-center text-[10px] font-medium text-base-content/70"
          >
            {{ getInitial(activeAgentName) }}
          </span>
        </div>
      </div>
      <span class="text-lg font-bold">{{ activeAgentName }}</span>
    </div>
    <!-- 思考状态指示器 - 绝对定位避免布局跳动，带渐变效果 -->
    <Transition name="fade">
      <span v-if="(isLoading || isProcessing)" class="loading loading-spinner loading-xs absolute -right-6 top-1/2 -translate-y-1/2"></span>
    </Transition>
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
import { useAppStore } from '@/features/app/stores/app';
import { storeToRefs } from 'pinia';

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
 * 用于获取当前智能体相关信息和加载状态
 */
const agentStore = useAgentStore();
const appStore = useAppStore();
const { isLoading, isProcessing, availableAgents, currentRoleId } = storeToRefs(agentStore);
const { currentDomain } = storeToRefs(appStore);

const currentAgentIcon = computed(() => {
  if (!currentDomain.value || !currentRoleId.value) return undefined;
  const agents = availableAgents.value[currentDomain.value] || [];
  const currentAgent = agents.find(agent => agent.id === currentRoleId.value);
  return currentAgent?.icon;
});

/**
 * 事件处理函数：处理新会话
 * 当用户点击新会话按钮时触发
 */
const handleNewSession = async () => {
  if (props.activeAgentName) {
    emit('new-session');
  }
};

const getInitial = (name: string): string => {
  if (!name) return '?';
  return name.trim().slice(0, 1).toUpperCase();
};

const handleIconError = (event: Event): void => {
  const target = event.target as HTMLImageElement;
  target.style.display = 'none';
};
</script>

<style scoped>
/* 渐变动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
