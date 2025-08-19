<template>
  <button
    type="button"
    class="block w-full text-left px-4 py-2 text-sm transition-colors duration-150 bg-transparent border-none text-on-surface hover:bg-surface-variant hover:text-on-surface-variant"
    role="menuitem"
    tabindex="-1"
    @click="$emit('click', $event)"
  >
    <slot></slot>
  </button>
</template>

<script setup>
defineEmits(['click']);
</script>