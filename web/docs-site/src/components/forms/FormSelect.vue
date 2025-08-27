<template>
  <DaisyDropdown
    :model-value="modelValue"
    :options="options"
    :placeholder="placeholder"
    :disabled="disabled"
    @update:modelValue="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
    class="w-full"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { VNode } from 'vue'
import DaisyDropdown from '@/components/ui/DaisyDropdown.vue'

interface Option {
  value: string | number
  label: string
  disabled?: boolean
}

const props = defineProps({
  modelValue: [String, Number],
  disabled: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue', 'change'])

// Parse slot options to work with DaisyDropdown
const slots = defineSlots()
const options = computed(() => {
  if (!slots.default) return []

  const slotContent = slots.default()
  const options: Option[] = []

  slotContent.forEach((node: VNode) => {
    if (node.type === 'option' && node.props) {
      options.push({
        value: node.props.value,
        label: node.children || node.props.value,
        disabled: node.props.disabled
      })
    }
  })

  return options
})

defineOptions({
  inheritAttrs: false
})
</script>