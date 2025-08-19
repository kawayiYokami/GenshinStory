<!--
  @slot left - The content for the left resizable pane.
  @slot right - The content for the right resizable pane.
-->
<template>
  <div class="flex h-full" ref="containerRef">
    <div class="flex-shrink-0" :style="{ width: `${leftPaneWidth}px` }">
      <slot name="left"></slot>
    </div>
    <!-- Transparent, wider drag handle -->
    <div class="w-2.5 cursor-col-resize" @mousedown="startDrag">
      <!-- Visually centered 1px divider line -->
      <div class="w-px h-full mx-auto" :style="{ backgroundColor: 'transparent' }"></div>
    </div>
    <div class="flex-grow">
      <slot name="right"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Ref } from 'vue';

defineSlots<{
  left: (props: {}) => any
  right: (props: {}) => any
}>()

const containerRef: Ref<HTMLDivElement | null> = ref(null);
const STORAGE_KEY = 'resizable-panes-width';
const leftPaneWidth = ref(300); // Default width
const isDragging = ref(false);

onMounted(() => {
  const savedWidth = localStorage.getItem(STORAGE_KEY);
  if (savedWidth) {
    leftPaneWidth.value = JSON.parse(savedWidth);
  } else if (containerRef.value) {
    // If no saved width, default to half the container width, but no more than 800px
    const containerWidth = containerRef.value.getBoundingClientRect().width;
    leftPaneWidth.value = Math.min(containerWidth / 2, 800);
  }
});

const startDrag = (event: MouseEvent) => {
  event.preventDefault();
  isDragging.value = true;
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
};

const doDrag = (event: MouseEvent) => {
  if (isDragging.value && containerRef.value) {
    const containerRect = containerRef.value.getBoundingClientRect();
    const newWidth = event.clientX - containerRect.left;
    // Add constraints to prevent panes from becoming too small
    if (newWidth > 100 && newWidth < containerRect.width - 100) {
      leftPaneWidth.value = newWidth;
    }
  }
};

const stopDrag = () => {
  if (isDragging.value) {
    isDragging.value = false;
    document.removeEventListener('mousemove', doDrag);
    document.removeEventListener('mouseup', stopDrag);
    // Save the new width to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(leftPaneWidth.value));
  }
};

onUnmounted(() => {
  // Cleanup listeners just in case
  document.removeEventListener('mousemove', doDrag);
  document.removeEventListener('mouseup', stopDrag);
});
</script>