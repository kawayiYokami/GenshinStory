<template>
  <div class="card card-border bg-base-100 shadow-md mb-6">
    <div class="card-body">
      <h2 class="card-title mb-6">创意工坊</h2>

      <!-- Tabs -->
      <div class="tabs tabs-boxed bg-base-200 mb-6 p-1">
        <a
          class="tab flex-1 transition-all duration-200"
          :class="{ 'tab-active bg-base-100 shadow-sm font-bold': activeTab === 'instruction' }"
          @click="activeTab = 'instruction'"
        >
          自定义指令
        </a>
        <a
          class="tab flex-1 transition-all duration-200"
          :class="{ 'tab-active bg-base-100 shadow-sm font-bold': activeTab === 'persona' }"
          @click="activeTab = 'persona'"
        >
          自定义角色
        </a>
      </div>

      <!-- Instructions List -->
      <div v-show="activeTab === 'instruction'">
        <div class="flex justify-between items-center mb-4">
          <p class="text-sm text-base-content/70">
            创建特定的交互模式，将出现在聊天界面的模式选择中。
          </p>
          <button class="btn btn-primary btn-sm" @click="openAddModal('instruction')">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            添加指令
          </button>
        </div>

        <div v-if="customInstructions.length === 0" class="text-center py-12 bg-base-200/30 rounded-xl border border-dashed border-base-300">
          <div class="w-16 h-16 mx-auto mb-3 bg-base-200 rounded-full flex items-center justify-center text-base-content/30">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <p class="text-base-content/50 font-medium">还没有自定义指令</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="instruction in customInstructions"
            :key="instruction.id"
            class="flex items-start justify-between p-4 bg-base-200/50 hover:bg-base-200 transition-colors rounded-xl border border-transparent hover:border-base-300"
          >
            <div class="flex-1 min-w-0 pr-4">
              <h3 class="font-bold text-base mb-1">{{ instruction.name }}</h3>
              <p class="text-sm text-base-content/60 line-clamp-2">
                {{ instruction.content }}
              </p>
            </div>
            <div class="flex gap-2 shrink-0">
              <button class="btn btn-ghost btn-sm btn-square" @click="openEditModal(instruction, 'instruction')">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                </svg>
              </button>
              <button class="btn btn-ghost btn-sm btn-square text-error hover:bg-error/10" @click="deleteItem(instruction.id, 'instruction')">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Personas List -->
      <div v-show="activeTab === 'persona'">
        <div class="flex justify-between items-center mb-4">
          <p class="text-sm text-base-content/70">
            创建独特的人物设定，将出现在角色选择列表中。
          </p>
          <button class="btn btn-primary btn-sm" @click="openAddModal('persona')">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            添加角色
          </button>
        </div>

        <div v-if="customPersonas.length === 0" class="text-center py-12 bg-base-200/30 rounded-xl border border-dashed border-base-300">
          <div class="w-16 h-16 mx-auto mb-3 bg-base-200 rounded-full flex items-center justify-center text-base-content/30">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <p class="text-base-content/50 font-medium">还没有自定义角色</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="persona in customPersonas"
            :key="persona.id"
            class="flex items-start justify-between p-4 bg-base-200/50 hover:bg-base-200 transition-colors rounded-xl border border-transparent hover:border-base-300"
          >
            <div class="flex-1 min-w-0 pr-4">
              <h3 class="font-bold text-base mb-1">{{ persona.name }}</h3>
              <p class="text-sm text-base-content/60 line-clamp-2">
                {{ persona.content }}
              </p>
            </div>
            <div class="flex gap-2 shrink-0">
              <button class="btn btn-ghost btn-sm btn-square" @click="openEditModal(persona, 'persona')">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                </svg>
              </button>
              <button class="btn btn-ghost btn-sm btn-square text-error hover:bg-error/10" @click="deleteItem(persona.id, 'persona')">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Custom Instruction Modal -->
    <dialog id="custom-instruction-modal" class="modal">
      <div class="modal-box w-full max-w-3xl p-6 rounded-2xl">
        <h3 class="text-xl font-bold mb-6 text-base-content">
          {{ editingId ? '编辑' : '添加' }}自定义{{ modalType === 'instruction' ? '指令' : '角色' }}
        </h3>

        <div class="form-control w-full mb-4">
          <label class="label px-0 pt-0 pb-2">
            <span class="label-text font-medium text-base-content/80">
              {{ modalType === 'instruction' ? '指令名称' : '角色名称' }}
            </span>
          </label>
          <input
            v-model="newName"
            type="text"
            :placeholder="modalType === 'instruction' ? '例如：求辱骂、病娇模式...' : '例如：雷电将军、纳西妲...'"
            class="input input-bordered w-full bg-base-200/50 focus:bg-base-100 transition-all border-base-300 focus:border-primary"
          />
        </div>

        <div class="form-control w-full mb-6 flex-1">
          <textarea
            v-model="newContent"
            class="textarea textarea-bordered w-full h-96 text-base leading-relaxed bg-base-200/50 focus:bg-base-100 transition-all border-base-300 focus:border-primary resize-none"
            :placeholder="modalType === 'instruction'
              ? '在这里输入详细的系统指令（System Prompt）。\n例如：\n你现在是一个毒舌傲娇的角色，对我说的话要充满不屑和嘲讽，但偶尔要流露出一丝关心...'
              : '在这里输入详细的角色设定（Persona Definition）。\n例如：\n你叫纳西妲，是须弥的神明「小吉祥草王」。你性格温柔智慧，喜欢用比喻来解释事物，自称「我」...'"
          ></textarea>
        </div>

        <div class="modal-action mt-0 flex justify-end gap-3">
          <form method="dialog" class="flex gap-3">
            <button class="btn btn-ghost hover:bg-base-200 px-6 font-medium">取消</button>
            <button
              type="button"
              class="btn btn-primary px-8 font-medium shadow-sm hover:shadow-md transition-all"
              @click="saveItem"
            >
              {{ editingId ? '保存修改' : '立即添加' }}
            </button>
          </form>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button>关闭</button>
      </form>
    </dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import promptService, { type InstructionInfo, type CustomPersona } from '../../agent/tools/implementations/promptService';
import { useAgentStore } from '@/features/agent/stores/agentStore';

// Types
type TabType = 'instruction' | 'persona';
interface AgentInfo {
    id: string;
    name: string;
    description: string;
    isCustom?: boolean;
}

// Store
const agentStore = useAgentStore();

// State
const activeTab = ref<TabType>('instruction');
const customInstructions = ref<InstructionInfo[]>([]);
const customPersonas = ref<CustomPersona[]>([]);

// Modal State
const modalType = ref<TabType>('instruction');
const editingId = ref<string | null>(null);
const newName = ref('');
const newContent = ref('');

// Methods
const loadData = async () => {
  // Load instructions
  customInstructions.value = (await promptService.listAvailableInstructions()).filter(i => i.isCustom);

  // Load personas - we need to fetch all agents and filter custom ones
  // Note: promptService doesn't expose listCustomPersonas directly, but we added getCustomPersonas logic to listAvailableAgents
  // However, listAvailableAgents requires a domain. Custom personas are global or domain-agnostic in our implementation?
  // Actually, our promptService implementation adds custom personas to ANY domain request.
  // So we can fetch for 'gi' domain (default) and filter.
  // BUT, to be cleaner, we should expose listCustomPersonas or getCustomPersonas from promptService if we want direct access.
  // For now, let's assume they are mixed in listAvailableAgents('gi') or we can try to access the storage key if we exported it (we didn't).
  // Wait, I updated listAvailableAgents to include custom personas.
  // Let's use a workaround: The standard listAvailableAgents returns everything.
  const agents = await promptService.listAvailableAgents('gi'); // 'gi' is just a placeholder to trigger the fetch
  customPersonas.value = agents.filter((a: any) => a.isCustom).map((a: any) => ({
    id: a.id,
    name: a.name,
    description: a.description || '',
    content: a.id, // Content is not returned by listAvailableAgents directly... this is a problem.
    isCustom: true
  }));

  // Wait, listAvailableAgents DOES NOT return content.
  // I need to update promptService to allow fetching content or listCustomPersonas properly.
  // Actually, I can just use a trick:
  // Since I can't easily change the service interface exported to 'window' or global scope without reloading,
  // I should check if I can modify promptService again to export `getCustomPersonas` or similar.
  // But wait, I already added `getCustomPersonas` logic inside `promptService.ts` but it's not exported.
  // I'll need to update promptService.ts one more time to export `listCustomPersonas` or similar.

  // For now, let's assume I will update promptService.ts to export `listCustomPersonas`
  // But since I can't do that in this single step efficiently, let's try to infer or re-fetch.
  // Actually, loadSystemPrompt can fetch content.

  // Optimization: I should have exported `getCustomPersonas` in promptService.ts.
  // Let me quickly check if I can fix promptService.ts first or if I should hack it here.
  // Hacking is bad. I will update promptService.ts after this apply_diff to export a proper list function.
  // For now, I will write the code assuming `promptService.getCustomPersonas` exists or I'll add it.

  // Let's use a temporary approach: Read from localStorage directly here since it's the same origin.
  const CUSTOM_PERSONAS_KEY = 'customPersonas';
  try {
      const stored = localStorage.getItem(CUSTOM_PERSONAS_KEY);
      customPersonas.value = stored ? JSON.parse(stored) : [];
  } catch (e) {
      console.error(e);
      customPersonas.value = [];
  }
};

const openAddModal = (type: TabType) => {
  modalType.value = type;
  editingId.value = null;
  newName.value = '';
  newContent.value = '';
  const modal = document.getElementById('custom-instruction-modal') as HTMLDialogElement;
  if (modal) modal.showModal();
};

const openEditModal = (item: any, type: TabType) => {
  modalType.value = type;
  editingId.value = item.id;
  newName.value = item.name;
  newContent.value = item.content || '';
  const modal = document.getElementById('custom-instruction-modal') as HTMLDialogElement;
  if (modal) modal.showModal();
};

const deleteItem = (id: string, type: TabType) => {
  if (!confirm(`确定要删除这个自定义${type === 'instruction' ? '指令' : '角色'}吗？`)) return;

  if (type === 'instruction') {
    promptService.removeCustomInstruction(id);
  } else {
    promptService.removeCustomPersona(id);
  }
  loadData();
  agentStore.refreshAvailableAgents();
};

const saveItem = () => {
  if (!newName.value.trim() || !newContent.value.trim()) {
    alert('请填写完整信息');
    return;
  }

  if (editingId.value) {
    if (modalType.value === 'instruction') {
      promptService.removeCustomInstruction(editingId.value);
      promptService.addCustomInstruction(newName.value, newContent.value);
    } else {
      promptService.removeCustomPersona(editingId.value);
      promptService.addCustomPersona(newName.value, newContent.value);
    }
  } else {
    if (modalType.value === 'instruction') {
      promptService.addCustomInstruction(newName.value, newContent.value);
    } else {
      promptService.addCustomPersona(newName.value, newContent.value);
    }
  }

  loadData();
  agentStore.refreshAvailableAgents();

  const modal = document.getElementById('custom-instruction-modal') as HTMLDialogElement;
  if (modal) modal.close();
};

// Load on mount
onMounted(() => {
  loadData();
});

// Expose methods
defineExpose({
  loadCustomInstructions: loadData // Keep backward compatibility name for now
});
</script>