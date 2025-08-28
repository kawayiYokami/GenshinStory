<template>
  <div class="navbar bg-base-100/70 backdrop-blur-lg backdrop-saturate-150 border-b border-base-300/50 text-base-content w-full shadow-sm supports-[backdrop-filter]:bg-base-100/60">
    <div class="flex-none lg:hidden">
      <label for="drawer" aria-label="open sidebar" class="btn btn-square btn-ghost">
        <Bars3Icon class="h-6 w-6" />
      </label>
    </div>

    <div class="flex-1 flex justify-center items-center h-full p-1" id="navbar-content-target"></div>

    <div class="flex-none">
      <a @click="navigateToSearch" class="btn btn-ghost btn-square">
        <MagnifyingGlassIcon class="h-5 w-5" />
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bars3Icon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import { useRouter } from 'vue-router';

const router = useRouter();

const navigateToSearch = () => {
  // 获取当前域
  const currentDomain = localStorage.getItem('currentDomain') || 'default';
  router.push(`/domain/${currentDomain}/search`);
};
</script>