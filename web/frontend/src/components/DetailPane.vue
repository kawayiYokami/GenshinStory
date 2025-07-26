<template>
  <router-view />
</template>

<script setup lang="ts">
// This component is now just a placeholder for the nested detail route.
// All logic has been moved to ItemDetailView.vue, which is now a routed component.
</script>

<style scoped>
.detail-pane {
  position: relative;
  flex-grow: 1;
  display: flex; /* This is crucial for the child to fill the height */
  flex-direction: column;
  overflow-y: auto;
  background-color: var(--m3-card-color-visible);
  border-radius: 12px;
  border: 1px solid var(--m3-border-color-soft);
}

.pin-button {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 20px;
  color: var(--m3-on-surface-variant);
  cursor: pointer;
  z-index: 10; /* Ensure it's above the content */
}

.pin-button:hover {
  color: var(--m3-on-surface);
}

/* 新增：为已钉住的星星添加高亮样式 */
.pin-button.is-pinned {
  color: var(--el-color-warning); /* 使用Element Plus的警告色作为高亮 */
}

.placeholder {
  flex: 1; /* Make it fill the available space */
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: var(--m3-on-surface-variant);
}
</style>