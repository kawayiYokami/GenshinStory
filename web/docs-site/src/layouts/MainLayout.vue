<template>
  <div class="drawer">
    <input id="nav-drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col h-screen">
      <!-- Navbar -->
      <div class="navbar bg-base-100/70 backdrop-blur-lg backdrop-saturate-150 border-b border-base-300/50 text-base-content w-full shadow-sm supports-[backdrop-filter]:bg-base-100/60">
        <div class="flex-none lg:hidden">
          <label for="nav-drawer" aria-label="open sidebar" class="btn btn-square btn-ghost">
            <Bars3Icon class="h-6 w-6" />
          </label>
        </div>

        <!-- 居中的导航项 -->
        <div class="flex-1 hidden lg:flex justify-center">
          <ul class="menu menu-horizontal justify-center gap-1">
            <!-- 桌面端水平菜单 - 动态加载的导航项 -->
            <li v-for="navItem in navigationItems" :key="navItem.id">
              <a @click="navigateTo(getNavPath(navItem))" class="flex items-center justify-center">
                <NavigationIcon :icon-name="navItem.id" />
              </a>
            </li>
          </ul>
        </div>

        <!-- 右侧：域名下拉菜单和设置 -->
        <div class="flex items-center gap-4">
          <!-- 域名下拉菜单 -->
          <div class="dropdown">
            <div tabindex="0" role="button" class="btn btn-ghost text-xl font-bold">
              {{ currentDomainName }}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <div tabindex="0" class="dropdown-content bg-base-100 rounded-box z-[1] w-32 shadow-xl border-0">
              <div class="max-h-60 overflow-y-auto">
                <ul class="p-2 space-y-1">
                  <li v-for="domain in domains" :key="domain.id">
                    <a @click="switchDomain(domain.id)"
                       class="px-3 py-2 rounded-lg transition-colors flex items-center justify-between"
                       :class="{
                         'bg-primary text-primary-content': domain.id === appStore.currentDomain,
                         'hover:bg-base-200': domain.id !== appStore.currentDomain
                       }">
                      <span class="truncate">{{ domain.name }}</span>
                      <span v-if="domain.id === appStore.currentDomain" class="text-xs font-bold">✓</span>
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="hidden lg:block">
            <a @click="navigateTo(`/domain/${appStore.currentDomain}/settings`)"
               class="btn btn-square btn-ghost">
              <Cog6ToothIcon class="h-5 w-5" />
            </a>
          </div>
        </div>
      </div>

      <!-- Page content here -->
      <div class="flex-1 overflow-hidden">
        <!-- 智能布局系统 -->
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

    <!-- 侧边栏 - 移动端使用 -->
    <div class="drawer-side">
      <label for="nav-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
      <div class="bg-base-200 text-base-content min-h-full w-80 flex flex-col">
        <!-- 自定义头部 - 域名在右边 -->
        <div class="p-4 flex justify-between items-center border-b border-base-300/50 bg-base-200/80 backdrop-blur-md">
          <label for="nav-drawer" aria-label="close sidebar" class="btn btn-square btn-ghost btn-sm lg:hidden">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </label>
          <div class="text-lg font-bold">{{ currentDomainName }}</div>
        </div>

        <!-- 导航列表 -->
        <ul class="menu p-4 flex-1">
          <!-- Navigation List -->
          <li v-for="navItem in navigationItems" :key="navItem.id">
            <a @click="navigateTo(getNavPath(navItem))">
              <NavigationIcon :icon-name="navItem.id" />
              {{ navItem.label }}
            </a>
          </li>

          <!-- Settings at Bottom -->
          <li class="mt-auto">
            <a @click="navigateTo(`/domain/${appStore.currentDomain}/settings`)">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              设置
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTheme } from '@/composables/useTheme';
import { Bars3Icon, Cog6ToothIcon } from '@heroicons/vue/24/outline';
import { useAgentStore } from '@/features/agent/stores/agentStore';
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

// 导航函数
const navigateTo = (path: string) => {
  router.push(path);
  };

// Activate the global theme service
useTheme();

// 组件映射
const componentMap = {
  'ItemListView': ItemListView,
  'SearchView': SearchView,
  'AgentChatView': AgentChatView,
  'SettingsView': SettingsView
};

const functionComponent = computed(() => {
  const componentName = route.meta.functionPane as keyof typeof componentMap;
  if (componentName && componentMap[componentName]) {
    return componentMap[componentName];
  }
  return ItemListView;
});

// 当前游戏名称
const currentDomainName = computed(() => {
  if (appStore.currentDomain === 'gi') return '原神';
  if (appStore.currentDomain === 'hsr') return '星穹铁道';
  return '知识领域';
});

// 领域列表
const domains = [
  { id: 'gi', name: '原神' },
  { id: 'hsr', name: '星穹铁道' },
];

// 切换领域
const switchDomain = (domain: string) => {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    // 关闭下拉菜单
    const dropdown = document.activeElement as HTMLElement;
    if (dropdown) {
      dropdown.blur();
    }
  }
};

// 导航项数据
const navigationItems = ref<NavItem[]>([]);

// 加载导航配置
async function loadUiConfig(domain: string) {
  try {
    const response = await fetch(`/domains/${domain}/metadata/uiconfig.json`);
    if (!response.ok) throw new Error(`Failed to load UI config for domain ${domain}`);
    const config = await response.json();

    // Remap navigation items to include translations
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

// 获取导航路径
function getNavPath(item: NavItem) {
  const domain = appStore.currentDomain;
  if (item.type === 'route') {
    return `/domain/${domain}/${item.id}`;
  }
  if (item.type === 'category') {
    return `/domain/${domain}/category/${item.id}`;
  }
  return `/domain/${domain}`;
}

// 监听游戏变化并更新相关存储
async function initializeApplication(domain: string) {
  if (!domain) return;

  appStore.isCoreDataReady = false;

  // 顺序很重要
  await dataStore.fetchIndex(domain);
  await agentStore.switchDomainContext(domain);

  appStore.isCoreDataReady = true;
}

watch(() => appStore.currentDomain, (newDomain, oldDomain) => {
  if (newDomain && newDomain !== oldDomain) {
    initializeApplication(newDomain);
  }
}, { immediate: true });

// 监听域名变化以加载导航配置
watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    loadUiConfig(newDomain);
  }
}, { immediate: true });

onMounted(async () => {
  // 1. 首先加载游戏列表
  await appStore.loadDomains();
  // 2. 从缓存初始化代理存储
  await agentStore.initializeStoreFromCache();
  // 3. 根据当前游戏触发初始应用设置
  // 上面的观察者会处理第一次初始化
});
</script>