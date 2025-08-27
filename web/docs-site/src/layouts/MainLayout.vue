web\docs-site\src\layouts\MainLayout.vue<template>
  <div class="bg-base-100 drawer mx-auto lg:drawer-open">
    <input id="drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col h-screen">
      <!-- Navbar -->
      <div class="navbar bg-base-100/70 backdrop-blur-lg backdrop-saturate-150 border-b border-base-300/50 text-base-content w-full shadow-sm supports-[backdrop-filter]:bg-base-100/60">
        <div class="flex-none lg:hidden">
          <label for="drawer" aria-label="open sidebar" class="btn btn-square btn-ghost">
            <Bars3Icon class="h-6 w-6" />
          </label>
        </div>

        <div class="flex-1 flex justify-center items-center px-4" id="navbar-content-target"></div>
      </div>

      <!-- Page content here -->
      <div class="flex-1 overflow-hidden">
        <SmartLayout
          v-model:show-detail="docViewerStore.isVisible"
          detail-aria-label="文档详情"
          @close="docViewerStore.close"
        >
          <template #function>
            <component :is="functionComponent" />
          </template>
          <template #detail>
            <DocumentViewer />
          </template>
        </SmartLayout>
      </div>
    </div>

    <!-- 侧边栏 -->
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
                        <button @click.stop="handleDeleteSession(session.id)" class="btn btn-ghost btn-xs text-error">
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTheme } from '@/composables/useTheme';
import { Bars3Icon, Cog6ToothIcon, PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import { useAgentStore, type Session } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { useDataStore } from '@/features/app/stores/data';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import SmartLayout from '@/components/SmartLayout.vue';
import DocumentViewer from '@/features/docs/components/DocumentViewer.vue';
import ItemListView from '@/features/docs/views/ItemListView.vue';
import SearchView from '@/features/search/views/SearchView.vue';
import AgentChatView from '@/features/agent/views/AgentChatView.vue';
import SettingsView from '@/features/settings/views/SettingsView.vue';
import NavigationIcon from '@/components/NavigationIcon.vue';

interface NavItem {
  id: string;
  type: 'route' | 'category';
  label?: string;
  icon: string;
}

const route = useRoute();
const router = useRouter();
const agentStore = useAgentStore();
const appStore = useAppStore();
const dataStore = useDataStore();
const docViewerStore = useDocumentViewerStore();

// Navigation
const navigateTo = (path: string) => {
  const drawerCheckbox = document.getElementById('drawer') as HTMLInputElement;
  if (drawerCheckbox && drawerCheckbox.checked) {
    drawerCheckbox.checked = false;
  }
  router.push(path);
};

// Activate the global theme service
useTheme();

// Component Mapping for Main View
const componentMap = {
  'ItemListView': ItemListView,
  'SearchView': SearchView,
  'AgentChatView': AgentChatView,
  'SettingsView': SettingsView
};

const functionComponent = computed(() => {
  const componentName = route.meta.functionPane as keyof typeof componentMap;
  return componentMap[componentName] || ItemListView;
});

// Domain Info
const currentDomainName = computed(() => {
  if (appStore.currentDomain === 'gi') return '原神';
  if (appStore.currentDomain === 'hsr') return '星穹铁道';
  return '知识领域';
});

const domains = [
  { id: 'gi', name: '原神' },
  { id: 'hsr', name: '星穹铁道' },
];

const switchDomain = (domain: string) => {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    const dropdown = document.activeElement as HTMLElement;
    if (dropdown) dropdown.blur();
  }
};

// Navigation Items
const navigationItems = ref<NavItem[]>([]);
const wikiNavigationItems = computed(() => {
  const excludedIds = ['search', 'agent'];
  return navigationItems.value.filter(item => !excludedIds.includes(item.id));
});

async function loadUiConfig(domain: string) {
  try {
    const response = await fetch(`/domains/${domain}/metadata/uiconfig.json`);
    if (!response.ok) throw new Error(`Failed to load UI config for domain ${domain}`);
    const config = await response.json();
    const categoryTranslations = config.categoryTranslations || {};
    navigationItems.value = config.navigation.map((item: NavItem) => ({
      ...item,
      label: item.label || categoryTranslations[item.id] || item.id,
    }));
  } catch (error) {
    console.error(error);
    navigationItems.value = [];
  }
}

function getNavPath(item: NavItem) {
  const domain = appStore.currentDomain;
  if (item.type === 'route') return `/domain/${domain}/${item.id}`;
  if (item.type === 'category') return `/domain/${domain}/category/${item.id}`;
  return `/domain/${domain}`;
}

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
  if (!session || session.messageIds.length === 0) return '空会话';

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
  await agentStore.startNewChatWithAgent(agentId);
  navigateTo(`/domain/${appStore.currentDomain}/agent`);
};

const handleSwitchSession = (sessionId: string) => {
  agentStore.switchSession(sessionId);
  navigateTo(`/domain/${appStore.currentDomain}/agent`);
};

const handleDeleteSession = (sessionId: string) => {
  if (confirm("确定要删除这个会话吗？此操作无法撤销。")) {
    agentStore.deleteSession(sessionId);
  }
};

// App Initialization Logic
async function initializeApplication(domain: string) {
  if (!domain) return;
  appStore.isCoreDataReady = false;
  await dataStore.fetchIndex(domain);
  await agentStore.switchDomainContext(domain);
  appStore.isCoreDataReady = true;
}

watch(() => appStore.currentDomain, (newDomain, oldDomain) => {
  if (newDomain && newDomain !== oldDomain) {
    initializeApplication(newDomain);
  }
}, { immediate: true });

watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    loadUiConfig(newDomain);
  }
}, { immediate: true });

onMounted(async () => {
  await appStore.loadDomains();
  await agentStore.initializeStoreFromCache();
});
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