<template>
  <div
    v-if="visible"
    class="absolute bottom-14 left-2 z-10 w-64 rounded-xl bg-surface p-2 shadow-md"
    role="menu"
    aria-orientation="vertical"
    aria-labelledby="menu-button"
    tabindex="-1"
  >
    <!-- Theme Section -->
    <div class="px-2 py-1">
      <p class="text-sm font-semibold text-on-surface-variant">主题</p>
      <div class="mt-2 grid grid-cols-3 gap-2">
        <button
          v-for="theme in themes"
          :key="theme.name"
          @click="setTheme(theme.name)"
          class="rounded-lg p-2 text-xs font-medium transition-colors"
          :class="[
            theme.name === themeStore.currentTheme
              ? 'bg-primary-container text-on-primary-container'
              : 'hover:bg-surface-variant text-on-surface',
          ]"
        >
          {{ theme.label }}
        </button>
      </div>
    </div>

    <!-- Divider -->
    <div class="my-2 h-px bg-outline"></div>

    <!-- Domain Section -->
    <div class="px-2 py-1">
      <p class="text-sm font-semibold text-on-surface-variant">知识领域</p>
      <div class="mt-2 space-y-2">
        <button
          v-for="domain in domains"
          :key="domain.id"
          @click="switchDomain(domain.id)"
          class="w-full rounded-lg p-2 text-left text-sm font-medium transition-colors"
          :class="[
            domain.id === appStore.currentDomain
              ? 'bg-primary-container text-on-primary-container'
              : 'hover:bg-surface-variant text-on-surface',
          ]"
        >
          {{ domain.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useThemeStore } from '@/features/app/stores/themeStore';
import type { ThemeName } from '@/features/app/stores/themeStore';
import { useAppStore } from '@/features/app/stores/app';

defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

const router = useRouter();
const themeStore = useThemeStore();
const appStore = useAppStore();

interface ThemeOption {
  name: ThemeName;
  label: string;
}

const themes = ref<ThemeOption[]>([
  { name: 'light', label: '浅色' },
  { name: 'dark', label: '深色' },
  { name: 'cupcake', label: '纸杯蛋糕' },
  { name: 'bumblebee', label: '大黄蜂' },
  { name: 'emerald', label: '翡翠' },
  { name: 'corporate', label: '企业' },
  { name: 'synthwave', label: '合成波' },
  { name: 'retro', label: '复古' },
  { name: 'cyberpunk', label: '赛博朋克' },
  { name: 'valentine', label: '情人节' },
  { name: 'halloween', label: '万圣节' },
  { name: 'garden', label: '花园' },
  { name: 'forest', label: '森林' },
  { name: 'aqua', label: '水族' },
  { name: 'lofi', label: '低保真' },
  { name: 'pastel', label: '马卡龙' },
  { name: 'fantasy', label: '奇幻' },
  { name: 'wireframe', label: '线框' },
  { name: 'black', label: '黑色' },
  { name: 'luxury', label: '奢华' },
  { name: 'dracula', label: '德古拉' },
  { name: 'cmyk', label: 'CMYK' },
  { name: 'autumn', label: '秋天' },
  { name: 'business', label: '商务' },
  { name: 'acid', label: '酸味' },
  { name: 'lemonade', label: '柠檬水' },
  { name: 'night', label: '夜晚' },
  { name: 'coffee', label: '咖啡' },
  { name: 'winter', label: '冬天' },
  { name: 'dim', label: '昏暗' },
  { name: 'nord', label: '诺德' },
  { name: 'sunset', label: '日落' },
]);

const domains = ref([
  { id: 'gi', name: '原神' },
  { id: 'hsr', name: '星穹铁道' },
]);

const setTheme = (themeName: ThemeName) => {
  themeStore.setTheme(themeName);
};

const switchDomain = (domain: string) => {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    router.push(`/domain/${domain}/agent`);
  }
};
</script>