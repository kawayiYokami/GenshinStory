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
  { name: 'm3-light', label: '浅色' },
  { name: 'm3-dark', label: '深色' },
  { name: 'genshin-light', label: '原神' },
  { name: 'system', label: '系统' },
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