<template>
  <MenuItem v-slot="{ active, disabled }">
    <button
      type="button"
      class="menu-item text-base-content ui-active:bg-primary ui-active:text-primary-content ui-disabled:opacity-50 ui-disabled:cursor-not-allowed"
      :class="{ 'active': active }"
      :disabled="disabled"
      @click="$emit('click', $event)"
    >
      <slot></slot>
    </button>
  </MenuItem>
</template>

<script setup>
import { MenuItem } from '@headlessui/vue'
defineEmits(['click']);
</script>