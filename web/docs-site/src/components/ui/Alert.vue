<template>
  <div
    v-if="visible"
    :class="[
      'alert',
      `alert-${type}`,
      { 'alert-soft': soft },
      { 'shadow-lg': shadow }
    ]"
    role="alert"
  >
    <div class="flex items-center">
      <component
        :is="iconComponent"
        v-if="showIcon"
        class="w-6 h-6 mr-2"
      />
      <div>
        <h4
          v-if="title"
          class="font-bold"
        >
          {{ title }}
        </h4>
        <div
          v-if="message"
          class="text-sm"
        >
          {{ message }}
        </div>
        <slot />
      </div>
    </div>
    <button
      v-if="closable"
      type="button"
      class="btn btn-sm btn-ghost"
      @click="handleClose"
    >
      <X class="w-4 h-4" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Info,
  TriangleAlert,
  CircleCheck,
  X
} from 'lucide-vue-next'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['info', 'success', 'warning', 'error'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  closable: {
    type: Boolean,
    default: false
  },
  soft: {
    type: Boolean,
    default: false
  },
  shadow: {
    type: Boolean,
    default: false
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  modelValue: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const iconMap = {
  info: Info,
  success: CircleCheck,
  warning: TriangleAlert,
  error: TriangleAlert
}

const iconComponent = computed(() => iconMap[props.type])

const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>