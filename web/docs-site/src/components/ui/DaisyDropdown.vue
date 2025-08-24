<template>
  <div class="dropdown dropdown-top">
    <div
      tabindex="0"
      role="button"
      class="btn btn-sm btn-ghost flex items-center gap-1 min-w-[120px] justify-between"
      :class="{ 'btn-disabled': disabled }"
    >
      <span class="truncate">{{ displayValue }}</span>
      <svg class="w-4 h-4 transform rotate-180 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    <ul
      tabindex="0"
      class="dropdown-content menu p-2 shadow rounded-box w-52 bg-base-200 border border-base-300 max-h-60 overflow-y-auto"
    >
      <li v-if="placeholder && !modelValue" class="disabled">
        <span>{{ placeholder }}</span>
      </li>
      <li
        v-for="option in options"
        :key="option.value"
        :class="{ 'disabled': option.disabled }"
      >
        <a
          @click="handleSelect(option)"
          :class="{ 'active': modelValue === option.value }"
        >
          {{ option.label }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Option {
  value: string | number
  label: string
  disabled?: boolean
}

interface Props {
  modelValue?: string | number
  options: Option[]
  placeholder?: string
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'change', value: string | number): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<Emits>()

const displayValue = computed(() => {
  if (!props.modelValue) return props.placeholder || '请选择'
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option?.label || props.placeholder || '请选择'
})

const handleSelect = (option: Option) => {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  emit('change', option.value)
}
</script>