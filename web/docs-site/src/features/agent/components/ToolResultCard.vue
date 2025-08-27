<template>
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-4">
      <div class="collapse collapse-arrow bg-base-200/50">
        <input type="checkbox" />
        <div class="tool-result-card">
          <div class="flex h-7 w-7 items-center justify-center rounded-full bg-info/20">
            <InformationCircleIcon class="h-4 w-4 text-info" />
          </div>
          <span class="font-medium text-sm">研究记录</span>
        </div>
        <div class="collapse-content">
          <div class="divider mt-0 mb-3"></div>
          <pre v-if="content" class="whitespace-pre-wrap break-all font-mono text-xs bg-base-300/30 p-3 rounded-lg border">{{ content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { InformationCircleIcon } from '@heroicons/vue/24/outline';

interface Props {
  content?: string;
}

withDefaults(defineProps<Props>(), {
  content: ''
});
</script>

<style scoped>
/* All styles are handled by Tailwind utility classes. */
</style>