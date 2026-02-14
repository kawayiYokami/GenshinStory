<template>
  <div class="navbar bg-base-100/70 backdrop-blur-lg backdrop-saturate-150 border-b border-base-300/50 text-base-content w-full shadow-sm supports-[backdrop-filter]:bg-base-100/60">
    <div class="flex-none lg:hidden">
      <label for="drawer" aria-label="open sidebar" class="btn btn-square btn-ghost">
        <Menu class="h-6 w-6" />
      </label>
    </div>

    <div class="flex-1 flex justify-center items-center h-full p-1" id="navbar-content-target"></div>

    <div class="flex-none flex items-center gap-1">
      <!-- 搜索按钮：只在非搜索页面显示 -->
      <a v-if="showSearchButton" @click="navigateToSearch" class="btn btn-ghost btn-square">
        <Search class="h-5 w-5" />
      </a>

      <!-- 问答按钮：只在非问答页面显示 -->
      <a v-if="showAgentButton" @click="navigateToAgent" class="btn btn-ghost btn-square">
        <MessageCircle class="h-5 w-5" />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Menu, Search, MessageCircle } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router';
import { computed } from 'vue';
import storageFacade from '@/features/app/services/storageFacade';

const router = useRouter();
const route = useRoute();

// 页面类型判断函数
const getPageType = (path: string): string => {
  if (path.includes('/agent')) {
    return 'agent'
  } else if (path.includes('/search')) {
    return 'knowledge'
  }
  return 'other'
}

// 当前页面类型
const currentPageType = computed(() => getPageType(route.path))

// 按钮显示条件
const showSearchButton = computed(() => currentPageType.value !== 'knowledge')
const showAgentButton = computed(() => currentPageType.value !== 'agent')

const navigateToSearch = () => {
  // 获取当前域
  const targetDomain = route.params.domain || storageFacade.getCurrentDomain() || 'default';
  router.push(`/domain/${targetDomain}/search`);
};
const navigateToAgent = () => {
  // 使用与侧边栏相同的域处理逻辑
  const targetDomain = route.params.domain || storageFacade.getCurrentDomain() || 'default';
  router.push(`/domain/${targetDomain}/agent`);
  // 关闭可能打开的侧边栏
  const drawerCheckbox = document.getElementById('drawer') as HTMLInputElement;
  if (drawerCheckbox && drawerCheckbox.checked) {
    drawerCheckbox.checked = false;
  }
};
</script>
