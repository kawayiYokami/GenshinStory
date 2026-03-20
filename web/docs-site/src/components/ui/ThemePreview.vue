<template>
  <div class="theme-preview-container space-y-6">
    <h2 class="text-2xl font-bold text-base-content mb-4">主题预览</h2>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div
        v-for="theme in themes"
        :key="theme.name"
        class="theme-card cursor-pointer border-2 border-base-300 hover:border-primary rounded-lg overflow-hidden transition-all duration-200"
        :class="{
          'border-primary ring-2 ring-primary ring-opacity-50': theme.name === currentTheme
        }"
        @click="selectTheme(theme.name)"
        :data-theme="theme.name"
      >
        <!-- 主题名称 -->
        <div class="p-3 bg-base-100 text-base-content border-b border-base-300">
          <div class="font-semibold text-sm">{{ theme.label }}</div>
        </div>

        <!-- 主题色彩预览 -->
        <div class="p-4 bg-base-100 space-y-3">
          <!-- 主要颜色带图标 -->
          <div class="flex gap-1">
            <div class="w-10 h-10 rounded bg-primary flex items-center justify-center">
              <ArrowUp class="w-5 h-5 text-primary-content" />
            </div>
            <div class="w-10 h-10 rounded bg-secondary flex items-center justify-center">
              <ArrowUp class="w-5 h-5 text-secondary-content" />
            </div>
            <div class="w-10 h-10 rounded bg-accent flex items-center justify-center">
              <ArrowUp class="w-5 h-5 text-accent-content" />
            </div>
            <div class="w-10 h-10 rounded bg-neutral flex items-center justify-center">
              <ArrowUp class="w-5 h-5 text-neutral-content" />
            </div>
          </div>

          <!-- 小的颜色示例网格 -->
          <div class="grid grid-cols-5 gap-1">
            <div class="w-full h-6 rounded bg-base-200"></div>
            <div class="w-full h-6 rounded bg-base-300"></div>
            <div class="w-full h-6 col-start-1 row-start-3 rounded bg-base-300"></div>
            <div class="w-full h-6 rounded bg-base-100 col-span-4 col-start-2 row-start-3 flex items-center justify-between px-2">
              <div class="w-3 h-3 rounded-full bg-primary"></div>
              <div class="flex gap-1">
                <div class="w-2 h-2 rounded bg-base-content/20"></div>
                <div class="w-2 h-2 rounded bg-base-content/20"></div>
                <div class="w-2 h-2 rounded bg-base-content/20"></div>
              </div>
            </div>
          </div>

          <!-- 按钮和状态示例 -->
          <div class="space-y-1">
            <div class="flex gap-1">
              <div class="flex-1 h-6 rounded bg-primary flex items-center justify-center">
                <span class="text-xs text-primary-content font-medium">A</span>
              </div>
              <div class="flex-1 h-6 rounded bg-secondary flex items-center justify-center">
                <span class="text-xs text-secondary-content font-medium">A</span>
              </div>
            </div>
            <div class="flex gap-1">
              <div class="w-3 h-3 rounded-full bg-success"></div>
              <div class="w-3 h-3 rounded-full bg-warning"></div>
              <div class="w-3 h-3 rounded-full bg-error"></div>
              <div class="w-3 h-3 rounded-full bg-info"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/features/app/stores/themeStore'
import type { ThemeName } from '@/features/app/stores/themeStore'
import { ArrowUp } from 'lucide-vue-next'

const themeStore = useThemeStore()

// 精选主题列表
const themes = [
  // 基础主题
  { name: 'light' as const, label: '光' },
  { name: 'dark' as const, label: '暗' },
  { name: 'cupcake' as const, label: '蛋糕' },
  { name: 'dracula' as const, label: '德古拉' },
  { name: 'autumn' as const, label: '秋天' },
  { name: 'winter' as const, label: '冬天' },
  { name: 'night' as const, label: '夜晚' },
  // 自定义角色主题
  { name: 'zhongli' as const, label: '钟离' },
  { name: 'furina' as const, label: '芙宁娜' },
  { name: 'nahida' as const, label: '纳西妲' },
  { name: 'hutao' as const, label: '胡桃' }
]

const currentTheme = computed(() => themeStore.currentTheme)

const selectTheme = (themeName: ThemeName) => {
  console.log('Theme selected:', themeName)
  themeStore.setThemeWithTransition(themeName)
}
</script>

<style scoped>
.theme-card {
  transition: all 0.2s ease;
}

.theme-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 确保主题预览卡片内的元素使用正确的主题 */
.theme-card[data-theme] * {
  transition: none;
}
</style>