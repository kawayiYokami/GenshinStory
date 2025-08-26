<template>
  <div class="smart-layout-container" :class="{ 'detail-open': showDetail && isSplitMode }">
    <!-- Master 区域（功能区） -->
    <div class="flex flex-col h-full overflow-y-auto overflow-x-hidden items-center master-scrollbar" :class="{ 'master-pane-split': showDetail && isSplitMode }">
      <slot name="function"></slot>
    </div>

    <!-- Detail 区域（详情区）- 并排模式 -->
    <div
      v-if="showDetail && isSplitMode"
      class="detail-pane detail-pane-split"
    >
      <div class="card card-border h-full bg-base-100 shadow-xl">
        <div class="card-body h-full p-4">
          <slot name="detail"></slot>
        </div>
      </div>
    </div>

    <!-- Detail 区域 - 覆盖模式 -->
    <Teleport to="body" v-else-if="showDetail">
      <!-- 覆盖层背景 -->
      <div
        class="overlay-backdrop"
        @click="closeDetail"
      ></div>

      <!-- 详情面板 -->
      <div
        class="detail-pane detail-pane-overlay"
        role="dialog"
        aria-modal="true"
        :aria-label="detailAriaLabel"
      >
        <div class="card card-border h-full bg-base-100 shadow-xl">
          <div class="card-body p-0 h-full">
            <slot name="detail"></slot>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { LAYOUT_CONFIG, shouldUseOverlayLayout } from '@/features/app/configs/layoutConfig';

interface Props {
  showDetail: boolean;
  detailAriaLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  detailAriaLabel: '详情面板'
});

const emit = defineEmits<{
  'update:showDetail': [value: boolean];
  'close': [];
}>();

// 响应式窗口宽度
const windowWidth = ref(window.innerWidth);

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.removeEventListener('keydown', handleKeydown);
});

// 计算布局模式
const isSplitMode = computed(() => {
  return !shouldUseOverlayLayout(windowWidth.value);
});

// 关闭详情面板
const closeDetail = () => {
  emit('update:showDetail', false);
  emit('close');
};

// 监听ESC键关闭
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.showDetail) {
    closeDetail();
  }
};
</script>

<style scoped>
.smart-layout-container {
  display: grid;
  grid-template-columns: 1fr 0fr;
  width: 100%;
  height: 100%;
  transition: grid-template-columns var(--transition-duration) ease;
}

.detail-open {
  grid-template-columns: 1fr var(--detail-pane-width);
}

.master-pane-split {
  padding-right: 0;
}

/* 并排模式的Detail面板 */
.detail-pane-split {
  overflow: hidden;
  padding-left: 0.5rem;  /* 只添加左边距 */
}

/* 覆盖模式的Detail面板 */
.detail-pane-overlay {
  position: fixed;
  right: 0;
  top: var(--navbar-height);
  width: min(var(--detail-pane-width), 100vw - 2rem); /* 不超过屏幕宽度，留出边距 */
  max-width: 100%; /* 确保不会超出 */
  height: calc(100vh - var(--navbar-height));
  background-color: var(--color-surface);
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
  z-index: var(--overlay-z-index);
  animation: slideIn var(--transition-duration) ease;
}

.detail-pane-header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  background-color: var(--color-surface);
}

.close-button {
  padding: 0.5rem;
  border-radius: 0.375rem;
  color: var(--color-muted-foreground);
  transition: all 0.2s;
}

.close-button:hover {
  background-color: var(--color-muted);
  color: var(--color-foreground);
}

.detail-pane-content {
  height: calc(100% - 65px);
  overflow-y: auto;
  background-color: var(--color-background);
}

.overlay-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--overlay-z-index) - 1);
  animation: fadeIn var(--transition-duration) ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Master 区域滚动条样式 - 类似 AgentChatView 的实现 */
.master-scrollbar {
  scrollbar-color: transparent transparent; /* Firefox: thumb track */
}

.master-scrollbar:hover,
.master-scrollbar:focus-within {
  scrollbar-color: hsl(var(--muted) / 0.3) transparent; /* Firefox: thumb track */
}

/* 针对 Webkit 浏览器 (Chrome, Safari) 的悬停隐藏效果 */
.master-scrollbar::-webkit-scrollbar-thumb {
  background-color: transparent;
}

.master-scrollbar:hover::-webkit-scrollbar-thumb,
.master-scrollbar:focus-within::-webkit-scrollbar-thumb {
  background-color: hsl(var(--muted) / 0.3);
}

.master-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--muted) / 0.5);
}

/* CSS变量 */
:root {
  --function-pane-max-width: 1200px;
  --detail-pane-width: 600px;
  --overlay-threshold: 1400px;
  --transition-duration: 300ms;
  --overlay-z-index: 40;
  --navbar-height: 64px;
  --navbar-border-width: 1px;
}
</style>