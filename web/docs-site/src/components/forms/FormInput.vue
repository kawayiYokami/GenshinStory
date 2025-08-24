<template>
  <input
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
    class="input input-bordered w-full bg-base-100 text-base-content focus:outline-none focus:ring-2 focus:ring-primary"
    :placeholder="placeholder"
    :type="type"
    :disabled="disabled"
  />
</template>

<script setup>
defineProps({
  modelValue: [String, Number],
  placeholder: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

defineEmits(['update:modelValue']);
</script>