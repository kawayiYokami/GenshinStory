<template>
  <div class="drawer-side">
    <label for="drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <div class="bg-base-200 text-base-content h-full w-80 grid grid-rows-[auto_1fr_auto]">
      <!-- Header -->
      <div class="p-4 flex justify-between items-center border-b border-base-300/50 bg-base-200/80 backdrop-blur-md">
        <ul class="menu menu-horizontal bg-base-200 rounded-box gap-2">
          <li v-for="domain in domains" :key="domain.id">
            <a @click="switchDomain(domain.id)" :class="{ 'bg-primary text-primary-content': domain.id === appStore.currentDomain }">
              {{ domain.name }}
            </a>
          </li>
        </ul>
        <div class="flex items-center">
          <a @click="navigateTo(`/domain/${appStore.currentDomain}/search`)" class="btn btn-ghost btn-square">
            <MagnifyingGlassIcon class="h-5 w-5" />
          </a>
          <label for="drawer" aria-label="close sidebar" class="btn btn-square btn-ghost btn-sm lg:hidden">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </label>
        </div>
      </div>

      <!-- Scrollable Area -->
      <div class="overflow-y-auto sidebar-scrollable">
        <ul class="menu p-4 w-full">
          <!-- Wiki -->
          <li>
            <details>
              <summary class="font-semibold">档案库</summary>
              <ul class="mt-2">
                <li v-for="navItem in wikiNavigationItems" :key="navItem.id">
                  <a @click="navigateTo(getNavPath(navItem))">
                    <NavigationIcon :icon-name="navItem.id" />
                    {{ navItem.label }}
                  </a>
                </li>
              </ul>
            </details>
          </li>

          <!-- Divider -->
          <div class="divider my-1"></div>

          <!-- Agent List -->
          <li>
            <details>
              <summary class="font-semibold">向研究员提问</summary>
              <ul class="mt-2 space-y-1 px-4">
                <li v-for="agent in availableAgentsForCurrentDomain" :key="agent.id">
                  <a @click="handleStartChatWithAgent(agent.id)" class="block p-2 rounded-lg hover:bg-base-300">
                    {{ agent.name }}
                  </a>
                </li>
              </ul>
            </details>
          </li>

          <!-- Divider -->
          <div class="divider my-1"></div>

          <!-- Session History -->
          <li>
            <details open>
              <summary class="font-semibold">会话历史</summary>
              <ul class="mt-2 space-y-1">
                <li v-for="session in currentDomainSessions" :key="session.id" :class="{ 'bordered': session.id === activeSessionId }" class="group">
                  <a @click="handleSwitchSession(session.id)" class="block p-2 rounded-lg relative">
                    <div class="font-semibold truncate">{{ getSessionSummary(session) }}</div>
                    <div class="text-xs text-base-content/70 truncate mt-1">{{ getAgentName(session.roleId) }}</div>
                    <div class="session-actions opacity-0 group-hover:opacity-100 absolute right-1 top-1/2 -translate-y-1/2">
                      <button @click.stop="handleDeleteSession(session.id)" class="session-action-btn">
                        <TrashIcon class="h-4 w-4" />
                      </button>
                    </div>
                  </a>
                </li>
              </ul>
            </details>
          </li>
        </ul>
      </div>

      <!-- Settings (Fixed Bottom) -->
      <div class="p-4 border-t border-base-300/50">
        <ul class="menu w-full">
          <li>
            <a @click="navigateTo(`/domain/${appStore.currentDomain}/settings`)">
              <Cog6ToothIcon class="h-5 w-5" />
              设置
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Cog6ToothIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import { useAgentStore, type Session } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { useDataStore } from '@/features/app/stores/data';
import NavigationIcon from '@/components/NavigationIcon.vue';

interface Domain {
  id: string;
  name: string;
}

interface NavItem {
  id: string;
  type: 'route' | 'category';
  label?: string;
  icon: string;
}

const props = defineProps<{
  domains: Domain[];
  wikiNavigationItems: NavItem[];
  getNavPath: (item: NavItem) => string;
}>();

const emit = defineEmits<{
  (e: 'switchDomain', domain: string): void;
  (e: 'navigateTo', path: string): void;
  (e: 'startChatWithAgent', agentId: string): void;
  (e: 'switchSession', sessionId: string): void;
  (e: 'deleteSession', sessionId: string): void;
}>();

const route = useRoute();
const router = useRouter();
const agentStore = useAgentStore();
const appStore = useAppStore();
const dataStore = useDataStore();

// Navigation
const navigateTo = (path: string) => {
  emit('navigateTo', path);
  const drawerCheckbox = document.getElementById('drawer') as HTMLInputElement;
  if (drawerCheckbox && drawerCheckbox.checked) {
    drawerCheckbox.checked = false;
  }
};

const switchDomain = (domain: string) => {
  emit('switchDomain', domain);
};

// Session & Agent Management
const sessions = computed(() => Object.values(agentStore.sessions));
const activeSessionId = computed(() => agentStore.activeSessionId);
const availableAgentsForCurrentDomain = computed(() => {
  const domain = appStore.currentDomain;
  if (!domain || !agentStore.availableAgents) return [];
  return agentStore.availableAgents[domain] || [];
});

const currentDomainSessions = computed(() => {
  return sessions.value
    .filter(s => s.domain === appStore.currentDomain)
    .sort((a, b) => b.id.localeCompare(a.id));
});

const getSessionSummary = (session: Session): string => {
  if (agentStore.isSessionEmpty(session)) return '空会话';

  for (const msgId of session.messageIds) {
    const msg = session.messagesById[msgId];
    if (msg && msg.role !== 'system') {
      let textContent = '';
      if (typeof msg.content === 'string') {
        textContent = msg.content;
      } else if (Array.isArray(msg.content)) {
        const textPart = msg.content.find(p => p.type === 'text');
        if (textPart && 'text' in textPart) {
          textContent = textPart.text || '';
        }
      }
      if (textContent) {
        const maxLength = 30;
        return textContent.length > maxLength ? textContent.substring(0, maxLength) + '...' : textContent;
      }
    }
  }
  return '无文本内容';
};

const getAgentName = (roleId: string): string => {
  const agent = availableAgentsForCurrentDomain.value.find((a: any) => a.id === roleId);
  return agent ? agent.name : '未知智能体';
};

const handleStartChatWithAgent = async (agentId: string) => {
  emit('startChatWithAgent', agentId);
};

const handleSwitchSession = (sessionId: string) => {
  emit('switchSession', sessionId);
};

const handleDeleteSession = (sessionId: string) => {
  if (confirm("确定要删除这个会话吗？此操作无法撤销。")) {
    emit('deleteSession', sessionId);
  }
};
</script>

<style scoped>
.session-actions {
  transition: opacity 0.2s ease-in-out;
}

li > a:hover .session-actions,
li.bordered a .session-actions {
  opacity: 1;
}

/* --- Custom Scrollbar --- */
.sidebar-scrollable::-webkit-scrollbar {
  width: 8px;
}

.sidebar-scrollable::-webkit-scrollbar-track {
  background: transparent;
}

/* Make thumb transparent by default */
.sidebar-scrollable::-webkit-scrollbar-thumb {
  background-color: transparent;
  border-radius: 4px;
}

/* On hover of the container, make the scrollbar thumb visible */
.sidebar-scrollable:hover::-webkit-scrollbar-thumb {
  background-color: hsl(var(--bc) / 0.4);
}

/* Hide the scrollbar buttons */
.sidebar-scrollable::-webkit-scrollbar-button {
  display: none;
}

/* Firefox scrollbar styling */
.sidebar-scrollable {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent; /* thumb track */
}

.sidebar-scrollable:hover {
   scrollbar-color: hsl(var(--bc) / 0.4) transparent;
}
</style>