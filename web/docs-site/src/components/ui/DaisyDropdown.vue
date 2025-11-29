<template>
  <div class="dropdown dropdown-top">
    <div
      tabindex="0"
      role="button"
      class="btn btn-sm btn-outline flex items-center gap-1 min-w-[60px] justify-between bg-base-100 border-base-content/20"
      :class="{ 'btn-disabled': disabled }"
    >
      <span class="truncate">{{ displayValue }}</span>
      <svg class="w-4 h-4 transform rotate-180 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    <div
      tabindex="0"
      class="dropdown-content bg-base-100 rounded-box min-w-[200px] shadow-md border-0"
    >
      <div class="max-h-120 overflow-y-auto">
        <ul class="p-2 space-y-1">
          <li v-if="placeholder && !modelValue">
            <div class="px-3 py-2 text-base-content/50">{{ placeholder }}</div>
          </li>
          <li
            v-for="option in options"
            :key="option.value"
          >
            <a
              @click="handleSelect(option)"
              :class="{
                'bg-primary text-primary-content': modelValue === option.value,
                'hover:bg-base-200': modelValue !== option.value && !option.disabled,
                'opacity-50 cursor-not-allowed': option.disabled
              }"
              class="px-3 py-2 rounded-lg transition-colors flex items-center justify-between"
            >
              <span class="truncate">{{ option.label }}</span>
              <span v-if="modelValue === option.value" class="text-xs font-bold">✓</span>
            </a>
          </li>
        </ul>
      </div>
    </div>
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
  width?: string
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'change', value: string | number): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  width: 'w-52'
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