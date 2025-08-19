<template>
  <details class="group mt-1 flex w-full flex-col items-center">
    <summary class="flex w-full cursor-pointer list-none items-center justify-between rounded-lg bg-surface-variant px-3 py-2 text-sm font-medium text-on-surface-variant">
      <div class="flex items-center gap-2">
        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        <span>研究记录</span>
      </div>
      <svg class="h-5 w-5 transition-transform duration-300 group-open:rotate-180" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
    </summary>
    <div class="mt-2 w-full rounded-lg bg-surface-variant p-4 text-on-surface-variant">
      <pre v-if="content" class="whitespace-pre-wrap break-all font-mono text-xs">{{ content }}</pre>
    </div>
  </details>
</template>

<script setup>
defineProps({
  content: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
/* All styles are handled by Tailwind utility classes. */
</style>