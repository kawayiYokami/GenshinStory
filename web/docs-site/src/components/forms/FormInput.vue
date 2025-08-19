<template>
  <input
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
    class="w-full p-2 text-sm bg-transparent border border-(--m3-outline) rounded-md focus:outline-none text-(--m3-on-surface)"
  />
</template>

<script setup>
defineProps({
  modelValue: [String, Number]
});

defineEmits(['update:modelValue']);
</script>