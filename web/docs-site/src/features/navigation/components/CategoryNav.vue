<template>
  <div class="relative h-full flex flex-col">
    <!-- Header: Current Domain -->
    <div class="flex h-16 items-center justify-center p-4">
      <span class="font-bold text-lg">{{ currentDomainName }}</span>
    </div>

    <!-- Navigation List -->
    <div v-if="appStore.isCoreDataReady" class="flex-grow overflow-y-auto">
      <ul class="list-none p-0 m-0 mt-4 space-y-1 px-2">
        <li v-for="navItem in navigationItems" :key="navItem.id">
          <router-link
            :to="getNavPath(navItem)"
            class="flex items-center gap-3 rounded-lg p-2 no-underline bg-transparent font-medium transition-colors duration-150 ease-out hover:bg-white/10 [&.router-link-exact-active]:bg-primary [&.router-link-exact-active]:text-on-primary"
          >
            <span v-html="navItem.icon" class="h-6 w-6"></span>
            <span>{{ navItem.label }}</span>
          </router-link>
        </li>
      </ul>
    </div>
    
    <!-- Loading Indicator -->
    <div v-else class="flex-grow flex items-center justify-center">
      <p>加载中...</p>
    </div>

    <!-- Footer: Settings Button -->
    <div class="flex-shrink-0 p-2">
      <button @click="toggleSettingsMenu" class="w-full flex items-center gap-3 rounded-lg p-2 text-left hover:bg-white/10 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="text-sm font-medium">设置</span>
      </button>
    </div>

    <!-- Settings Menu Pop-up -->
    <Teleport to="body">
      <SettingsMenu :visible="isSettingsMenuOpen" />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { watch, computed, ref, Teleport } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from "@/features/app/stores/app";
import SettingsMenu from './SettingsMenu.vue';

interface NavItem {
  id: string;
  type: 'route' | 'category';
  label?: string;
  icon: string;
}

const route = useRoute();
const appStore = useAppStore();

const navigationItems = ref<NavItem[]>([]);
const isSettingsMenuOpen = ref(false);

const currentDomainName = computed(() => {
  if (appStore.currentDomain === 'gi') return '原神';
  if (appStore.currentDomain === 'hsr') return '星穹铁道';
  return '知识领域';
});

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

watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    loadUiConfig(newDomain);
    isSettingsMenuOpen.value = false; // Close menu on domain switch
  }
}, { immediate: true });

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

function toggleSettingsMenu() {
  isSettingsMenuOpen.value = !isSettingsMenuOpen.value;
}
</script>

