<template>
  <div class="drawer-side">
    <label for="drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <div class="bg-base-300 text-base-content h-full w-80 grid grid-rows-[auto_1fr_auto]">
      <!-- Header -->
      <div class="p-4 flex justify-between items-center border-b border-base-300/50 bg-base-300 backdrop-blur-md">
        <div class="tabs tabs-border">
          <input
            v-for="domain in domains"
            :key="domain.id"
            type="radio"
            name="domain_tabs"
            class="tab"
            :aria-label="domain.name"
            :checked="domain.id === appStore.currentDomain"
            @change="switchDomain(domain.id)"
          />
        </div>
        <div class="flex items-center">
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
            <details ref="wikiMenu" @toggle="handleMenuToggle('wiki')" :open="activeMenu === 'wiki'">
              <summary class="font-semibold">档案库</summary>
              <Transition name="slide" mode="out-in">
                <ul v-if="activeMenu === 'wiki'" class="mt-2">
                <li v-for="navItem in wikiNavigationItems" :key="navItem.id">
                  <a @click="navigateTo(getNavPath(navItem))">
                    <NavigationIcon :icon-name="navItem.iconKey || navItem.id" />
                    {{ navItem.label }}
                  </a>
                </li>
              </ul>
              </Transition>
            </details>
          </li>

          <!-- Divider -->
          <div class="divider my-1"></div>

          <!-- Agent List -->
          <li>
            <details ref="agentMenu" @toggle="handleMenuToggle('agent')" :open="activeMenu === 'agent'">
              <summary class="font-semibold">向研究员提问</summary>
              <Transition name="slide" mode="out-in">
                <ul v-if="activeMenu === 'agent'" class="mt-2 space-y-1 px-4">
                <li v-for="agent in availableAgentsForCurrentDomain" :key="agent.id">
                  <a @click="handleStartChatWithAgent(agent.id)" class="block p-2 rounded-lg hover:bg-base-300">
                    {{ agent.name }}
                  </a>
                </li>
              </ul>
              </Transition>
            </details>
          </li>

          <!-- Divider -->
          <div class="divider my-1"></div>

          <!-- Session History -->
          <li>
            <details ref="sessionMenu" @toggle="handleMenuToggle('session')" :open="activeMenu === 'session'">
              <summary class="font-semibold">会话历史</summary>
              <Transition name="slide" mode="out-in">
                <ul v-if="activeMenu === 'session'" class="mt-1 space-y-0.5">
                <li 
                  v-for="session in currentDomainSessions" 
                  :key="session.id" 
                  class="group"
                >
                  <a 
                    @click="handleSwitchSession(session.id)" 
                    class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-accent/10 transition-colors relative"
                    :class="session.id === activeSessionId ? 'bg-accent/15 border-l-2 border-accent' : ''"
                  >
                    <div class="flex-1 min-w-0 w-0">
                      <div class="text-sm font-medium truncate text-base-content block">
                        {{ getSessionSummary(session) }}
                      </div>
                      <div class="text-[10px] text-base-content/50 truncate mt-0.5 block">
                        {{ getAgentName(session.roleId) }} · {{ formatRelativeTime(session.createdAt) }}
                      </div>
                    </div>
                    <button 
                      @click.stop="handleDeleteSession(session.id)" 
                      class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-base-300 transition-all shrink-0"
                    >
                      <Trash2 class="h-3.5 w-3.5 text-base-content/50 hover:text-error" />
                    </button>
                  </a>
                </li>
              </ul>
              </Transition>
            </details>
          </li>
        </ul>
      </div>

      <!-- Settings (Fixed Bottom) -->
      <div class="p-4 border-t border-base-300/50">
        <ul class="menu w-full">
          <li>
            <a @click="navigateTo(`/domain/${appStore.currentDomain}/settings`)">
              <Settings class="h-5 w-5" />
              设置
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Settings, Trash2, Search } from 'lucide-vue-next';
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
  iconKey?: string;
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
  router.push(`/domain/${domain}/agent`);
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
        const maxLength = 20;
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

const formatRelativeTime = (createdAt: string): string => {
  if (!createdAt) return '';
  const date = new Date(createdAt);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
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

// 互斥菜单管理
const wikiMenu = ref<HTMLDetailsElement>()
const agentMenu = ref<HTMLDetailsElement>()
const sessionMenu = ref<HTMLDetailsElement>()
const activeMenu = ref<string | null>('session') // 默认展开会话历史

const handleMenuToggle = (menuType: string) => {
  // 获取对应菜单元素
  const menuMap = {
    wiki: wikiMenu.value,
    agent: agentMenu.value,
    session: sessionMenu.value
  }

  const currentMenu = menuMap[menuType as keyof typeof menuMap]

  // 如果当前菜单正在展开，则更新activeMenu
  if (currentMenu && currentMenu.open) {
    activeMenu.value = menuType

    // 关闭其他菜单
    Object.entries(menuMap).forEach(([type, menu]) => {
      if (type !== menuType && menu && menu.open) {
        menu.open = false
      }
    })
  }
  // 如果当前菜单正在收起，且是当前激活菜单，则清空activeMenu
  else if (currentMenu && !currentMenu.open && activeMenu.value === menuType) {
    activeMenu.value = null
  }
}

// 页面类型判断函数
const getPageType = (path: string): string => {
  if (path.includes('/agent') || path.includes('/chat')) {
    return 'agent'
  } else if (path.includes('/search') || path.includes('/docs') || path.includes('/wiki')) {
    return 'knowledge'
  }
  return 'other'
}

const getTargetMenuForPath = (path: string): string | null => {
  const pageType = getPageType(path)
  switch (pageType) {
    case 'agent':
      return 'session'
    case 'knowledge':
      return 'wiki'
    default:
      return null
  }
}

const isPageTypeChanged = (newPath: string, oldPath: string): boolean => {
  return getPageType(newPath) !== getPageType(oldPath)
}

// 处理路由变化
const handleRouteChange = (newPath: string, oldPath: string) => {
  if (isPageTypeChanged(newPath, oldPath)) {
    const targetMenu = getTargetMenuForPath(newPath)
    if (targetMenu && activeMenu.value !== targetMenu) {
      activeMenu.value = targetMenu
    }
  }
}

// 监听路由变化
watch(() => route.path, (newPath, oldPath) => {
  if (oldPath) { // 避免初始加载时触发
    nextTick(() => {
      handleRouteChange(newPath, oldPath)
    })
  }
})
</script>

<style scoped>
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

/* Tab transition effects */
.tab {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab:checked {
  transform: scale(1.05);
}

.sidebar-scrollable:hover {
   scrollbar-color: hsl(var(--bc) / 0.4) transparent;
}

/* 菜单动画 */
.slide-enter-active {
  transition: all 0.3s ease-out;
}

.slide-leave-active {
  transition: all 0.2s ease-in;
}

.slide-enter-from {
  opacity: 0;
  max-height: 0;
}

.slide-enter-to {
  opacity: 1;
  max-height: 500px;
}

.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

.slide-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
