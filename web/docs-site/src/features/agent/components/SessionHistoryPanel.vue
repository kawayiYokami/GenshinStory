<template>
  <Teleport to="body">
    <!-- 遮罩层 -->
    <div v-if="visible" class="fixed inset-0 z-40 bg-black/50" @click="closePanel"></div>
    
    <!-- 下拉面板 - 屏幕中间 -->
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      <div class="dropdown-content menu p-0 shadow-2xl rounded-box bg-base-200 border border-base-300 w-96 pointer-events-auto">
        <!-- 标题栏 -->
        <div class="flex justify-between items-center p-4 border-b border-base-300">
          <h3 class="text-lg font-semibold">历史会话</h3>
          <button @click="closePanel" class="p-2 hover:bg-base-300 rounded-full transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <!-- 会话列表 -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="gameSessions.length > 0" class="p-2">
            <div v-for="session in sortedSessions" :key="session.id"
                 class="p-3 rounded-lg bg-base-100 hover:bg-base-300 transition-colors cursor-pointer mb-2">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0 pr-2" @click="handleSwitchSession(session.id)">
                  <div class="text-xs text-base-content/70 mb-1">{{ getSessionAgentName(session) }}</div>
                  <div class="text-sm font-medium truncate">{{ getSessionDisplayName(session) }}</div>
                </div>
                <button @click.stop="handleDeleteSession(session.id)" 
                        class="flex-shrink-0 p-1 hover:bg-error/20 rounded transition-colors text-error">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div v-else class="flex items-center justify-center h-32 text-base-content/50">
            暂无历史会话
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';

defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(['close']);

const agentStore = useAgentStore();
const { sessions, activeSessionId, availableAgents } = storeToRefs(agentStore);
const { switchSession, deleteSession } = agentStore;

const appStore = useAppStore();
const { currentDomain } = storeToRefs(appStore);

const gameSessions = computed(() =>
  Object.values(sessions.value).filter(s => s.domain === currentDomain.value)
);

const sortedSessions = computed(() =>
  gameSessions.value.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
);

const getSessionAgentName = (session) => {
  if (!session?.roleId || !session?.domain || !availableAgents.value[session.domain]) {
    return '未知角色';
  }
  const agent = availableAgents.value[session.domain].find(a => a.id === session.roleId);
  return agent ? agent.name : '未知角色';
};

const getSessionDisplayName = (session) => {
  if (!session || !session.messageIds || !session.messagesById) {
    return session.name || '未命名会话';
  }
  
  const firstUserMessage = session.messageIds
    .map(id => session.messagesById[id])
    .find(msg => msg && msg.role === 'user' && msg.content);
    
  if (!firstUserMessage) {
    return '新会话';
  }

  let previewText = '';
  const { content } = firstUserMessage;

  if (typeof content === 'string') {
    previewText = content;
  } else if (Array.isArray(content)) {
    const textPart = content.find(part => part.type === 'text');
    if (textPart) {
      previewText = textPart.text;
    } else {
      const docPart = content.find(part => part.type === 'doc');
      const imagePart = content.find(part => part.type === 'image_url');
      if (docPart) previewText = `[文档] ${docPart.name}`;
      else if (imagePart) previewText = `[图片]`;
      else previewText = '[附件]';
    }
  }
  
  const trimmedText = previewText.trim();
  if (trimmedText) {
    return trimmedText.substring(0, 30) + (trimmedText.length > 30 ? '...' : '');
  }
  
  return '新会话';
};

const handleSwitchSession = (sessionId) => {
  switchSession(sessionId);
  closePanel();
};

const handleDeleteSession = (sessionId) => {
  if (confirm(`确定要删除会话 "${sessions.value[sessionId].name}" 吗？此操作无法撤销。`)) {
    deleteSession(sessionId);
  }
};

const closePanel = () => {
  emit('close');
};
</script>

<style scoped>
/* All styles are now handled by Tailwind utility classes directly in the template. */
</style>