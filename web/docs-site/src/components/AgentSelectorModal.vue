<template>
  <div v-if="visible" class="agent-selector-modal">
    <div class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3>选择一个角色</h3>
        <button @click="closeModal" class="close-button">&times;</button>
      </div>
      <ul class="agent-list">
        <li v-for="agent in agents" :key="agent.id">
          <button @click="selectAgent(agent.id)" :class="{ active: agent.id === selectedAgentId }">
            {{ agent.name }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  agents: {
    type: Array,
    required: true,
  },
  selectedAgentId: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(['close', 'select-agent']);

const closeModal = () => {
  emit('close');
};

const selectAgent = (agentId) => {
  emit('select-agent', agentId);
};
</script>

<style scoped>
.agent-selector-modal {
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
  max-width: 400px;
  z-index: 1001;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--m3-outline);
  padding-bottom: 10px;
  margin-bottom: 15px;
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
.agent-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 60vh;
  overflow-y: auto;
}
.agent-list li button {
  width: 100%;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--m3-outline);
  border-radius: 8px;
  margin-bottom: 8px;
  text-align: left;
  font-size: 1em;
  cursor: pointer;
  color: var(--m3-on-surface);
  transition: background-color 0.2s, border-color 0.2s;
}
.agent-list li button:hover {
  background-color: var(--m3-surface-variant);
  border-color: var(--m3-primary);
}
.agent-list li button.active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  border-color: var(--m3-primary);
  font-weight: bold;
}
</style>