<template>
  <details class="collapse group mt-1">
    <summary class="collapse-title flex items-center justify-between text-base-content">
      <div class="flex items-center gap-2">
        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        <span>研究记录</span>
      </div>
    </summary>
    <div class="collapse-content">
      <pre v-if="content" class="whitespace-pre-wrap break-all font-mono text-xs bg-base-200 p-4 rounded-lg">{{ content }}</pre>
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