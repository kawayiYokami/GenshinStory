<template>
  <div class="relative w-full">
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      v-bind="$attrs"
      class="w-full p-2 pr-10 text-sm bg-transparent border border-(--m3-outline) rounded-md appearance-none focus:outline-none text-(--m3-on-surface)"
    >
      <slot />
    </select>
    <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
      <svg class="w-5 h-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fill-rule="evenodd" d="M10 3a.75.75 0 01.53.22l3.5 3.5a.75.75 0 01-1.06 1.06L10 4.81 7.03 7.78a.75.75 0 01-1.06-1.06l3.5-3.5A.75.75 0 0110 3zm-3.72 9.53a.75.75 0 011.06 0L10 15.19l2.97-2.97a.75.75 0 111.06 1.06l-3.5 3.5a.75.75 0 01-1.06 0l-3.5-3.5a.75.75 0 010-1.06z" clip-rule="evenodd" />
      </svg>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: [String, Number]
});

defineEmits(['update:modelValue']);

// Use defineOptions to disable attribute inheritance on the root div
// and ensure they fall through to the <select> element.
defineOptions({
  inheritAttrs: false
});
</script>