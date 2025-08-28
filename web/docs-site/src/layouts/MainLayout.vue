<template>
  <div class="bg-base-100 drawer mx-auto lg:drawer-open">
    <input id="drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col" :style="{ height: '100dvh' }">
      <!-- Navbar -->
      <Navbar />

      <!-- Page content here -->
      <MainContent />
    </div>

    <!-- 侧边栏 -->
    <Sidebar
      :domains="domains"
      :wiki-navigation-items="wikiNavigationItems"
      :get-nav-path="getNavPath"
      @switch-domain="switchDomain"
      @navigate-to="navigateTo"
      @start-chat-with-agent="handleStartChatWithAgent"
      @switch-session="handleSwitchSession"
      @delete-session="handleDeleteSession"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTheme } from '@/composables/useTheme';
import { Menu, Settings, Plus, Edit, Trash2, Search } from 'lucide-vue-next';
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
import Navbar from './components/Navbar.vue';
import Sidebar from './components/Sidebar.vue';
import MainContent from './components/MainContent.vue';

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