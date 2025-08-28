<template>
  <div class="min-h-screen bg-base-100 p-8">
    <div class="container mx-auto max-w-7xl">
      <h1 class="text-4xl font-bold text-center mb-8 text-base-content">
        🎨 DaisyUI 主题展示器
      </h1>

      <div class="text-center mb-8">
        <p class="text-base-content/70 mb-4">
          点击任意主题卡片即可立即切换和预览效果
        </p>
        <div class="badge badge-primary">
          当前主题: {{ currentThemeLabel }}
        </div>
      </div>

      <!-- 主题网格 -->
      <ThemePreview />

      <!-- 实时预览区域 -->
      <div class="mt-12 card bg-base-200 shadow-md">
        <div class="card-body">
          <h2 class="card-title mb-6">当前主题实时预览</h2>

          <!-- 组件展示区 -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

            <!-- 按钮组 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">按钮组件</h3>
              <div class="space-y-2">
                <button class="btn btn-primary w-full">Primary</button>
                <button class="btn btn-secondary w-full">Secondary</button>
                <button class="btn btn-accent w-full">Accent</button>
                <button class="btn btn-neutral w-full">Neutral</button>
              </div>
            </div>

            <!-- 状态按钮 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">状态按钮</h3>
              <div class="space-y-2">
                <button class="btn btn-success w-full">Success</button>
                <button class="btn btn-warning w-full">Warning</button>
                <button class="btn btn-error w-full">Error</button>
                <button class="btn btn-info w-full">Info</button>
              </div>
            </div>

            <!-- 卡片组件 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">卡片组件</h3>
              <div class="card bg-base-100 shadow">
                <div class="card-body p-4">
                  <h4 class="card-title text-sm">示例卡片</h4>
                  <p class="text-xs">这是一个示例卡片内容，展示当前主题的卡片样式。</p>
                  <div class="card-actions justify-end">
                    <button class="btn btn-primary btn-xs">查看</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 表单组件 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">表单组件</h3>
              <div class="space-y-2">
                <input type="text" class="input input-bordered w-full" placeholder="输入框" />
                <select class="select select-bordered w-full">
                  <option>选择框选项</option>
                </select>
                <label class="label cursor-pointer">
                  <span class="label-text">复选框</span>
                  <input type="checkbox" class="checkbox" />
                </label>
              </div>
            </div>

            <!-- 徽章和指示器 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">徽章指示器</h3>
              <div class="space-y-2">
                <div class="flex gap-2 flex-wrap">
                  <span class="badge badge-primary">Primary</span>
                  <span class="badge badge-secondary">Secondary</span>
                  <span class="badge badge-accent">Accent</span>
                </div>
                <div class="flex gap-2">
                  <div class="radial-progress text-primary" style="--value:70;">70%</div>
                  <div class="radial-progress text-secondary" style="--value:45;">45%</div>
                </div>
              </div>
            </div>

            <!-- 警告框 -->
            <div class="space-y-3">
              <h3 class="font-semibold text-base-content">警告框</h3>
              <div class="space-y-2">
                <div class="alert alert-success">
                  <span class="text-xs">Success alert example</span>
                </div>
                <div class="alert alert-warning">
                  <span class="text-xs">Warning alert example</span>
                </div>
                <div class="alert alert-error">
                  <span class="text-xs">Error alert example</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="text-center mt-8 text-base-content/60">
        <p class="text-sm">
          基于 DaisyUI v5 + Tailwind CSS v4 构建
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useThemeStore } from '@/features/app/stores/themeStore';
import ThemePreview from '@/components/ui/ThemePreview.vue';

const themeStore = useThemeStore();

// 主题标签映射
const themeLabels: Record<string, string> = {
  'light': '光',
  'dark': '暗',
  'cupcake': '蛋糕',
  'dracula': '德古拉',
  'autumn': '秋天',
  'winter': '冬天',
  'night': '夜晚',
  // 自定义角色主题
  'zhongli': '钟离',
  'furina': '芙宁娜',
  'nahida': '纳西妲',
  'hutao': '胡桃',
};

const currentThemeLabel = computed(() => {
  return themeLabels[themeStore.currentTheme] || themeStore.currentTheme;
});
</script>

<style scoped>
.container {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>