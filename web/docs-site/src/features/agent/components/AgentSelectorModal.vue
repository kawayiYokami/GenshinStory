<template>
  <Dialog
    :open="visible"
    @close="closeModal"
    class="relative z-50"
  >
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-black/50" aria-hidden="true" />

    <!-- Modal container -->
    <div class="fixed inset-0 flex items-center justify-center p-4">
      <DialogPanel
        class="modal modal-bottom sm:modal-middle w-full max-w-sm bg-base-100 text-base-content"
      >
        <!-- Modal header -->
        <div class="modal-box">
          <h3 class="text-lg font-bold">选择一个角色</h3>
          <button
            @click="closeModal"
            class="close-btn absolute right-2 top-2"
          >
            ✕
          </button>
        </div>

        <!-- Agent list -->
        <div class="modal-body max-h-[60vh] overflow-y-auto p-0">
          <ul class="menu menu-vertical p-0">
            <li v-for="agent in agents" :key="agent.id">
              <button
                @click="selectAgent(agent.id)"
                :class="[
                  'w-full text-left justify-start',
                  agent.id === selectedAgentId
                    ? 'active bg-primary text-primary-content'
                    : 'hover:bg-base-200'
                ]"
              >
                {{ agent.name }}
              </button>
            </li>
          </ul>
        </div>
      </DialogPanel>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog, DialogPanel } from '@headlessui/vue';

// 类型定义
interface Agent {
  id: string;
  name: string;
}

interface Props {
  visible: boolean;
  agents: Agent[];
  selectedAgentId?: string | null;
}

interface Emits {
  (e: 'close'): void;
  (e: 'select-agent', agentId: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  selectedAgentId: null
});

const emit = defineEmits<Emits>();

const closeModal = (): void => {
  emit('close');
};

const selectAgent = (agentId: string): void => {
  emit('select-agent', agentId);
};
</script>