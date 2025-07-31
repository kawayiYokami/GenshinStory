<template>
  <div v-if="visible" class="session-history-modal">
    <div class="modal-overlay" @click="closePanel"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3>历史会话</h3>
        <button @click="closePanel" class="close-button">&times;</button>
      </div>
      <ul v-if="gameSessions.length > 0" class="session-list">
        <li
          v-for="session in sortedSessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === activeSessionId }"
          @click="handleSwitchSession(session.id)"
        >
          <span class="session-name">{{ getSessionDisplayName(session) }}</span>
          <div class="session-actions">
            <button @click.stop="handleDeleteSession(session.id)" class="delete-button" title="删除会话">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </li>
      </ul>
      <div v-else class="empty-state">
        <p>当前游戏没有历史会话。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/stores/agent';
import { useAppStore } from '@/stores/app';

defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(['close']);

const agentStore = useAgentStore();
const { sessions, activeSessionId } = storeToRefs(agentStore);
const { switchSession, deleteSession } = agentStore;

const appStore = useAppStore();
const { currentGame } = storeToRefs(appStore);

const gameSessions = computed(() => 
  Object.values(sessions.value).filter(s => s.game === currentGame.value)
);

const sortedSessions = computed(() => 
  gameSessions.value.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
);

const getSessionDisplayName = (session) => {
  if (!session || !session.messageIds || !session.messagesById) {
    return session.name || '未命名会话';
  }
  const firstUserMessage = session.messageIds
    .map(id => session.messagesById[id])
    .find(msg => msg && msg.role === 'user' && msg.content);
    
  if (firstUserMessage) {
    return firstUserMessage.content.substring(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '');
  }
  
  return session.name;
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
.session-history-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}
.modal-content {
  background-color: var(--m3-surface);
  padding: 20px;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  z-index: 1001;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--m3-outline);
  padding-bottom: 10px;
  margin-bottom: 15px;
  flex-shrink: 0;
}
.modal-header h3 {
  margin: 0;
  color: var(--m3-on-surface);
}
.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--m3-on-surface-variant);
}
.session-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  flex-grow: 1;
}
.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  border: 1px solid transparent;
}
.session-item:hover {
  background-color: var(--m3-surface-variant);
}
.session-item.active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  border-color: var(--m3-primary);
  font-weight: bold;
}
.session-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.delete-button {
  background: transparent;
  border: none;
  color: var(--m3-on-surface-variant);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.delete-button:hover {
  background-color: var(--m3-error-container);
  color: var(--m3-on-error-container);
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--m3-on-surface-variant);
}
</style>