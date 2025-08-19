fen<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="fixed inset-0 bg-black/50" @click="closePanel"></div>
    <div class="relative bg-surface rounded-lg shadow-md w-full max-w-md mx-auto flex flex-col max-h-[80vh]">
      <div class="flex justify-between items-center p-4 border-b border-outline">
        <h3 class="text-lg font-semibold text-on-surface">历史会话</h3>
        <button @click="closePanel" class="text-on-surface-variant hover:text-on-surface">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div v-if="gameSessions.length > 0" ref="parentRef" class="overflow-y-auto">
        <div :style="{ height: `${totalSize}px`, width: '100%', position: 'relative' }">
          <div
            v-for="virtualRow in virtualRows"
            :key="sortedSessions[virtualRow.index].id"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }"
          >
            <div
              :class="[
                'border-b border-outline cursor-pointer h-full',
                { 'bg-primary-container': sortedSessions[virtualRow.index].id === activeSessionId }
              ]"
              @click="handleSwitchSession(sortedSessions[virtualRow.index].id)"
            >
              <div class="flex justify-between items-center p-4 hover:bg-surface-variant transition-colors duration-150 h-full">
                <div class="flex flex-col overflow-hidden">
                  <span class="text-xs text-on-surface-variant">{{ getSessionAgentName(sortedSessions[virtualRow.index]) }}</span>
                  <span class="text-sm font-medium text-on-surface truncate">{{ getSessionDisplayName(sortedSessions[virtualRow.index]) }}</span>
                </div>
                <div class="flex-shrink-0 ml-4">
                  <button @click.stop="handleDeleteSession(sortedSessions[virtualRow.index].id)" class="p-2 rounded-full hover:bg-error-container text-on-surface-variant hover:text-on-error-container transition-colors duration-150" title="删除会話">
                    <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="flex items-center justify-center h-48">
        <p class="text-on-surface-variant">当前游戏没有历史会话。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useVirtualizer } from '@tanstack/vue-virtual';
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

// --- Virtual Scrolling Setup ---
const parentRef = ref(null);

const virtualizerOptions = computed(() => ({
  count: sortedSessions.value.length,
  getScrollElement: () => parentRef.value,
  estimateSize: () => 69,
  overscan: 5,
}));

const rowVirtualizer = useVirtualizer(virtualizerOptions);

const virtualRows = computed(() => rowVirtualizer.value.getVirtualItems());
const totalSize = computed(() => rowVirtualizer.value.getTotalSize());

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
    // Find the first text part in the content array
    const textPart = content.find(part => part.type === 'text');
    if (textPart) {
      previewText = textPart.text;
    } else {
      // If no text, show a placeholder for attachments
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