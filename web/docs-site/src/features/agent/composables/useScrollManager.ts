import { ref, watch, nextTick, onMounted, onUnmounted, type Ref } from 'vue';
import type { Message } from '@/features/agent/types';

/**
 * 滚动管理器组合式函数
 * 负责管理滚动区域的自动滚动行为，处理滚动相关的观察者逻辑
 * 
 * @param {Object} params
 * @param {Ref<HTMLElement | null>} params.scrollElement - 滚动元素
 * @param {Ref<Boolean>} params.autoScroll - 是否自动滚动
 * @returns {Object} 包含滚动管理方法的对象
 */
export default function useScrollManager({ scrollElement, autoScroll }: { scrollElement: Ref<HTMLElement | null>, autoScroll: Ref<boolean> }) {
  let mutationObserver: MutationObserver | null = null;
  let resizeObserver: ResizeObserver | null = null;
  const isUserScrolling = ref(false);
  let userScrollTimeout: number | null = null;

  /**
   * 滚动到底部
   */
  const scrollToBottom = () => {
    if (scrollElement.value) {
      scrollElement.value.scrollTo({
        top: scrollElement.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  /**
   * 处理用户滚动事件
   * 检测用户是否正在手动滚动
   */
  const handleUserScroll = () => {
    isUserScrolling.value = true;
    
    // 清除之前的超时
    if (userScrollTimeout) {
      clearTimeout(userScrollTimeout);
    }
    
    // 设置新的超时，如果用户在1秒内没有滚动，则认为用户停止滚动
    userScrollTimeout = window.setTimeout(() => {
      isUserScrolling.value = false;
    }, 1000);
  };

  /**
   * 设置自动滚动
   * 当内容变化或自动滚动条件满足时，自动滚动到底部
   */
  const setupAutoScroll = () => {
    // 监听内容变化
    if (scrollElement.value) {
      // 使用 MutationObserver 监听 DOM 变化
      mutationObserver = new MutationObserver(() => {
        if (autoScroll.value && !isUserScrolling.value) {
          nextTick(() => {
            scrollToBottom();
          });
        }
      });

      // 使用 ResizeObserver 监听元素大小变化
      resizeObserver = new ResizeObserver(() => {
        if (autoScroll.value && !isUserScrolling.value) {
          nextTick(() => {
            scrollToBottom();
          });
        }
      });

      // 开始观察
      mutationObserver.observe(scrollElement.value, {
        childList: true,
        subtree: true,
        characterData: true,
      });

      resizeObserver.observe(scrollElement.value);

      // 添加滚动事件监听器
      scrollElement.value.addEventListener('scroll', handleUserScroll);
    }
  };

  /**
   * 清理观察者和事件监听器
   */
  const cleanup = () => {
    if (mutationObserver) {
      mutationObserver.disconnect();
      mutationObserver = null;
    }
    
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    
    if (userScrollTimeout) {
      clearTimeout(userScrollTimeout);
      userScrollTimeout = null;
    }
    
    if (scrollElement.value) {
      scrollElement.value.removeEventListener('scroll', handleUserScroll);
    }
  };

  // 监听自动滚动状态变化
  watch(autoScroll, (newValue) => {
    if (newValue && !isUserScrolling.value) {
      nextTick(() => {
        scrollToBottom();
      });
    }
  });

  // 组件挂载时设置自动滚动
  onMounted(() => {
    setupAutoScroll();
  });

  // 组件卸载时清理
  onUnmounted(() => {
    cleanup();
  });

  return {
    scrollToBottom,
    setupAutoScroll
  };
}