<template>
  <!-- 智能布局容器：支持并排和覆盖两种布局模式 -->
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
      <div class="card card-border h-full bg-base-100 shadow-md">
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
        <div class="card card-border h-full bg-base-100 shadow-md">
          <div class="card-body p-0 h-full">
            <slot name="detail"></slot>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
/**
 * 智能布局组件
 * @description 提供响应式布局，支持并排和覆盖两种模式，自动根据屏幕宽度切换
 * @author yokami
 */
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { LAYOUT_CONFIG, shouldUseOverlayLayout } from '@/features/app/configs/layoutConfig';

/**
 * 组件属性接口
 */
interface Props {
  /** 是否显示详情面板 */
  showDetail: boolean;
  /** 详情面板的ARIA标签 */
  detailAriaLabel?: string;
}

/**
 * 组件属性定义
 */
const props = withDefaults(defineProps<Props>(), {
  detailAriaLabel: '详情面板'
});

/**
 * 组件事件定义
 */
const emit = defineEmits<{
  'update:showDetail': [value: boolean];
  'close': [];
}>();

// 响应式窗口宽度
const windowWidth = ref(window.innerWidth);

/**
 * 监听窗口大小变化
 * @description 响应窗口大小变化事件，更新窗口宽度状态
 * @param {Event} e 窗口大小变化事件
 */
const handleResize = (e: Event) => {
  windowWidth.value = window.innerWidth;
};

/**
 * 组件挂载时的生命周期钩子
 * @description 添加窗口大小变化和键盘事件监听器
 */
onMounted(() => {
  window.addEventListener('resize', handleResize);
  document.addEventListener('keydown', handleKeydown);
});

/**
 * 组件卸载时的生命周期钩子
 * @description 清理事件监听器
 */
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.removeEventListener('keydown', handleKeydown);
});

/**
 * 计算布局模式
 * @description 根据窗口宽度计算使用并排模式还是覆盖模式
 * @return {boolean} 是否使用并排模式
 */
const isSplitMode = computed(() => {
  return !shouldUseOverlayLayout(windowWidth.value);
});

/**
 * 关闭详情面板
 * @description 关闭详情面板并触发相应事件
 */
const closeDetail = () => {
  emit('update:showDetail', false);
  emit('close');
};

/**
 * 监听ESC键关闭
 * @description 监听键盘事件，当按下ESC键时关闭详情面板
 * @param {KeyboardEvent} e 键盘事件
 */
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.showDetail) {
    closeDetail();
  }
};
</script>

<style scoped>
/* 样式区域：负责组件样式 */
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
  width: 100vw; /* 移动端占满屏幕 */
  max-width: 100%;
  height: calc(100dvh - var(--navbar-height));
  background-color: var(--color-surface);
  box-shadow: none; /* 移除阴影，因为已经占满屏幕 */
  z-index: var(--overlay-z-index);
  animation: slideIn var(--transition-duration) ease;
}

/* 桌面端保持原有样式 */
@media (min-width: 768px) {
  .detail-pane-overlay {
    width: min(var(--detail-pane-width), 100vw - 2rem);
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
  }
}

.detail-pane-header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-start;
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