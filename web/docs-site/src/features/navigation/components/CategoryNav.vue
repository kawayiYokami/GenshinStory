<template>
  <div class="category-nav">
    <div class="game-switcher">
      <button @click="switchDomain('gi')" :class="{ active: appStore.currentDomain === 'gi' }">原神</button>
      <button @click="switchDomain('hsr')" :class="{ active: appStore.currentDomain === 'hsr' }">星穹铁道</button>
    </div>

    <!-- Guarded Content -->
    <div v-if="appStore.isCoreDataReady" class="nav-list-wrapper">
      <ul class="nav-list">
        <li><router-link :to="getNavPath('agent')">问答</router-link></li>
        <li><router-link :to="getNavPath('search')">搜索</router-link></li>
        <li v-for="cat in categories" :key="cat.path">
          <router-link :to="getNavPath('category', cat.path)" :class="{ 'router-link-active': isActive(cat.path) }">{{ cat.name }}</router-link>
        </li>
      </ul>
    </div>
    <!-- Loading Indicator -->
    <div v-else class="loading-indicator">
      <p>加载中...</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { watch, computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAppStore } from "@/features/app/stores/app";
import { useDataStore } from "@/features/app/stores/data";
import { storeToRefs } from 'pinia';

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const dataStore = useDataStore();

const { indexData: fullIndex } = storeToRefs(dataStore);
const categoryTranslations = ref<{ [key: string]: string }>({});

const categories = computed(() => {
  console.log('[CategoryNav] Computed `categories` is running...');
  console.log(`[CategoryNav] fullIndex length: ${fullIndex.value.length}`);
  if (!fullIndex.value.length) return [];
  
  const categoryNames = new Set<string>();
  fullIndex.value.forEach(item => {
    // Extract top-level category (e.g., "Weapon" from "Weapon/Sword")
    if (item && typeof item.type === 'string') {
      const topLevelCategory = item.type.split('/')[0];
      categoryNames.add(topLevelCategory);
    }
  });
  
  console.log(`[CategoryNav] Found category names:`, categoryNames);

  const result = Array.from(categoryNames).map(name => ({
    name: categoryTranslations.value[name.toLowerCase()] || name,
    path: name
  }));

  console.log(`[CategoryNav] Final categories array:`, result);
  return result;
});

async function loadUiConfig(domain: string) {
    try {
        const response = await fetch(`/domains/${domain}/metadata/uiconfig.json`);
        if (!response.ok) {
            throw new Error(`Failed to load UI config for domain ${domain}`);
        }
        const config = await response.json();
        categoryTranslations.value = config.categoryTranslations || {};
    } catch (error) {
        console.error(error);
        categoryTranslations.value = {}; // Reset on error
    }
}

watch(() => appStore.currentDomain, (newDomain) => {
  if (newDomain) {
    // dataStore.fetchIndex(newDomain); // This is now handled by the layout orchestrator
    loadUiConfig(newDomain);
  }
}, { immediate: true });

function getNavPath(type: 'search' | 'category' | 'agent', payload?: string) {
  const domain = appStore.currentDomain;
  if (type === 'search') {
    return `/domain/${domain}/search`;
  }
  if (type === 'agent') {
    return `/domain/${domain}/agent`;
  }
  if (type === 'category' && payload) {
    return `/domain/${domain}/category/${payload}`;
  }
  return `/domain/${domain}`;
}

function switchDomain(domain: string) {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    router.push(`/domain/${domain}/agent`);
  }
}

function isActive(categoryPath: string) {
  const currentCategory = route.params.categoryName;
  return currentCategory === categoryPath;
}
</script>

<style scoped>
.category-nav {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.game-switcher {
  display: flex;
  padding: 16px;
  gap: 8px;
  border-bottom: 1px solid var(--genshin-bg-primary);
}

.game-switcher button {
  flex: 1;
  padding: 8px;
  background-color: var(--genshin-tab-inactive-bg);
  color: var(--genshin-text-secondary);
  border: 1px solid var(--genshin-accent-gold);
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s ease-out;
  border-radius: 4px;
}

.game-switcher button.active {
  background-color: var(--genshin-accent-gold);
  color: var(--genshin-text-primary);
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
a {
  display: block;
  padding: 12px 24px;
  text-decoration: none;
  color: var(--genshin-text-secondary);
  background-color: transparent;
  font-weight: bold;
  transition: all 0.2s ease-out;
}
a.router-link-active {
  background-color: var(--genshin-tab-active-bg);
  color: var(--genshin-tab-active-text);
}
</style>