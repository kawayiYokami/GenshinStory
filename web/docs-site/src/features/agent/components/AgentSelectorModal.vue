<template>
  <div v-if="visible" class="fixed inset-0 z- flex items-center justify-center">
    <div class="absolute inset-0 bg-black/50" @click="closeModal"></div>
    <div class="relative z- flex w-11/12 max-w-sm flex-col rounded-xl bg-surface p-4 shadow-md">
      <div class="mb-4 flex items-center justify-between border-b border-outline pb-2">
        <h3 class="text-lg font-semibold text-on-surface">选择一个角色</h3>
        <button @click="closeModal" class="border-none bg-transparent text-2xl font-bold text-on-surface-variant hover:text-on-surface">&times;</button>
      </div>
      <ul class="m-0 max-h-[60vh] list-none overflow-y-auto p-0">
        <li v-for="agent in agents" :key="agent.id" class="mb-2">
          <button
            @click="selectAgent(agent.id)"
            :class="[
              'w-full rounded-lg p-3 text-left transition-colors',
              agent.id === selectedAgentId
                ? 'bg-primary-container text-on-primary-container'
                : 'hover:bg-surface-variant text-on-surface'
            ]"
          >
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
/* All styles are now handled by Tailwind utility classes directly in the template. */
</style>