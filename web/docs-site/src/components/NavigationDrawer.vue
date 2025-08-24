<template>
  <Dialog
    :open="isOpen"
    @close="closeDrawer"
    class="relative z-50"
  >
    <div class="fixed inset-0 bg-black/30" aria-hidden="true" />

    <div class="fixed inset-0 overflow-y-auto">
      <div class="drawer drawer-end">
        <DialogPanel
          class="drawer-side"
          @click.stop
        >
          <div class="drawer-content bg-base-100 min-h-full">
            <router-view name="nav" />
          </div>
        </DialogPanel>
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Dialog, DialogPanel } from '@headlessui/vue'

const isOpen = ref(false)

const openDrawer = () => {
  isOpen.value = true
}

const closeDrawer = () => {
  isOpen.value = false
}

// 暴露给父组件使用
defineExpose({ openDrawer, closeDrawer })
</script>