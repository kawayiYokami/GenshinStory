<template>
  <div class="card bg-base-200 border border-base-300 shadow-sm">
    <div class="card-body p-0">
      <div class="collapse collapse-arrow bg-base-200/50 p-0">
        <input type="checkbox" />
        <div class="tool-result-card p-0">
          <div class="flex h-7 w-7 items-center justify-center rounded-full bg-info/20">
            <Info class="h-4 w-4 text-info" />
          </div>
          <span class="font-medium text-sm">资料</span>
        </div>
        <div class="collapse-content">
          <div class="divider mt-0 mb-3"></div>
          <pre v-if="content" class="whitespace-pre-wrap break-all font-mono text-xs bg-base-200 p-3">{{ content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Info } from 'lucide-vue-next';

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