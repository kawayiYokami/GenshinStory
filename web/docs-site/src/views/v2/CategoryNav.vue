<template>
  <div class="category-nav">
    <div class="game-switcher">
      <button @click="switchGame('gi')" :class="{ active: appStore.currentGame === 'gi' }">原神</button>
      <button @click="switchGame('hsr')" :class="{ active: appStore.currentGame === 'hsr' }">星穹铁道</button>
    </div>
    <ul class="nav-list">
      <li><router-link :to="getNavPath('search')">搜索</router-link></li>
      <li v-for="cat in categories" :key="cat.path">
        <router-link :to="getNavPath('category', cat.path)" :class="{ 'router-link-active': isActive(cat.path) }">{{ cat.name }}</router-link>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Grid } from '@element-plus/icons-vue';
import { useAppStore, type Game } from '@/stores/app';

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();

const fullIndex = ref<any[]>([]);
const categories = ref<{name: string, path: string}[]>([]);

const categoryTranslations: { [key: string]: string } = {
  // HSR
  books: '书籍',
  characters: '角色',
  lightcones: '光锥',
  relics: '遗器',
  materials: '材料',
  miracles: '奇物',
  messages: '短信',
  missions: '任务',
  // GI
  quest: '任务',
  questchapter: '任务',
  character: '角色',
  weapon: '武器',
  relicset: '圣遗物',
  material: '材料',
  book: '书籍',
  readable: '读物'
};


const allNavigableCategories = computed(() => {
  if (!fullIndex.value.length) return [];
  
  const categoryNames = new Set<string>();
  fullIndex.value.forEach(item => {
    // Extract top-level category (e.g., "Weapon" from "Weapon/Sword")
    const topLevelCategory = item.type.split('/')[0];
    categoryNames.add(topLevelCategory);
  });
  
  return Array.from(categoryNames).map(name => ({
    name: categoryTranslations[name.toLowerCase()] || name,
    path: name
  }));
});

async function loadIndexAndDeriveCategories(game: string) {
  try {
    // 修正：加载正确的、用于列表展示的目录索引文件
    const response = await fetch(`/index_${game}.json`);
    if (!response.ok) throw new Error(`Failed to load index for ${game}`);
    fullIndex.value = await response.json();
    categories.value = allNavigableCategories.value;
  } catch (error) {
    console.error("Error loading index:", error);
    fullIndex.value = [];
    categories.value = [];
  }
}

watch(() => appStore.currentGame, (newGame) => {
  if (newGame) {
    loadIndexAndDeriveCategories(newGame);
  }
}, { immediate: true });

function getNavPath(type: 'search' | 'category', payload?: string) {
  const game = appStore.currentGame;
  if (type === 'search') {
    return `/v2/${game}/search`;
  }
  if (type === 'category' && payload) {
    return `/v2/${game}/category/${payload}`;
  }
  return `/v2/${game}`;
}

function switchGame(game: Game) {
  if (appStore.currentGame !== game) {
    appStore.setCurrentGame(game);
    router.push(`/v2/${game}/search`);
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