<template>
  <div
    v-if="visible"
    class="card bg-base-100 shadow-md border border-base-300 absolute bottom-14 left-2 z-10 w-64"
    role="menu"
    aria-orientation="vertical"
    aria-labelledby="menu-button"
    tabindex="-1"
  >
    <div class="card-body p-4">
      <!-- Theme Section -->
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-base-content mb-3">主题</h3>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="theme in themes"
            :key="theme.name"
            @click="setTheme(theme.name)"
            class="btn btn-xs text-xs font-medium transition-all duration-200"
            :class="[
              theme.name === themeStore.currentTheme
                ? 'btn-primary'
                : 'btn-ghost hover:btn-outline'
            ]"
          >
            {{ theme.label }}
          </button>
        </div>
      </div>

      <!-- Divider -->
      <div class="divider my-2"></div>

      <!-- Domain Section -->
      <div>
        <h3 class="text-sm font-semibold text-base-content mb-3">知识领域</h3>
        <div class="space-y-2">
          <button
            v-for="domain in domains"
            :key="domain.id"
            @click="switchDomain(domain.id)"
            class="btn btn-sm w-full justify-start text-sm font-medium transition-all duration-200"
            :class="[
              domain.id === appStore.currentDomain
                ? 'btn-primary'
                : 'btn-ghost hover:btn-outline'
            ]"
          >
            {{ domain.name }}
          </button>
        </div>
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
  // 基础主题
  { name: 'light', label: '光' },
  { name: 'dark', label: '暗' },
  { name: 'cupcake', label: '蛋糕' },
  { name: 'dracula', label: '德古拉' },
  { name: 'autumn', label: '秋天' },
  { name: 'winter', label: '冬天' },
  { name: 'night', label: '夜晚' },
  // 自定义角色主题
  { name: 'zhongli', label: '钟离' },
  { name: 'furina', label: '芙宁娜' },
  { name: 'nahida', label: '纳西妲' },
  { name: 'hutao', label: '胡桃' },
]);

const domains = ref([
  { id: 'gi', name: '原神' },
  { id: 'hsr', name: '星穹铁道' },
]);

const setTheme = (themeName: ThemeName) => {
  themeStore.setThemeWithTransition(themeName);
};

const switchDomain = (domain: string) => {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    router.push(`/domain/${domain}/agent`);
  }
};
</script>