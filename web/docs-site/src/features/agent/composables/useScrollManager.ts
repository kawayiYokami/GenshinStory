import { ref, watch, nextTick, onMounted, onUnmounted, type Ref } from 'vue';

/**
 * 滚动位置类型
 */
type ScrollPosition = 'top' | 'bottom' | 'center';

/**
 * 滚动管理器组合式函数
 * 类似 Gemini 的简单实现，利用容器自然流特性，不使用观察者
 *
 * @param {Object} params
 * @param {Ref<HTMLElement | null>} params.scrollElement - 滚动元素
 * @param {Ref<Boolean>} params.autoScroll - 是否自动滚动
 * @returns {Object} 包含滚动管理方法的对象
 */
export default function useScrollManager({ scrollElement, autoScroll }: { scrollElement: Ref<HTMLElement | null>, autoScroll: Ref<boolean> }) {
  const isUserScrolling = ref(false);
  let userScrollTimeout: number | null = null;

  // 滚动到底部按钮相关状态
  const showScrollToBottomButton = ref(false);
  let lastScrollTop = 0;
  let scrollDirection: 'up' | 'down' = 'down';
  let buttonShowTimeout: number | null = null;

  /**
   * 滚动到指定消息的特定位置
   */
  const scrollToMessage = (messageId: string, position: ScrollPosition = 'top') => {
    if (!scrollElement.value) return;

    const messageElement = scrollElement.value.querySelector(`[data-message-id="${messageId}"]`) as HTMLElement;
    if (!messageElement) {
      console.warn(`[useScrollManager] 未找到消息元素: ${messageId}`);
      return;
    }

    const elementRect = messageElement.getBoundingClientRect();
    const containerRect = scrollElement.value.getBoundingClientRect();
    const relativeTop = elementRect.top - containerRect.top + scrollElement.value.scrollTop;

    let targetScrollTop: number;

    switch (position) {
      case 'top':
        targetScrollTop = relativeTop - 20;
        break;
      case 'center':
        targetScrollTop = relativeTop - (scrollElement.value.clientHeight / 2) + (elementRect.height / 2);
        break;
      case 'bottom':
        targetScrollTop = scrollElement.value.scrollHeight;
        break;
      default:
        targetScrollTop = relativeTop;
    }

    scrollElement.value.scrollTo({
      top: Math.max(0, targetScrollTop),
      behavior: 'smooth'
    });
  };

  /**
   * 处理用户消息发送时的滚动
   */
  const scrollToUserMessage = (_messageId: string) => {
    scrollToBottom();
  };

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
   * 检查是否在底部附近（50px容差）
   */
  const isNearBottom = () => {
    if (!scrollElement.value) return false;
    const element = scrollElement.value;
    return element.scrollTop + element.clientHeight >= element.scrollHeight - 50;
  };

  /**
   * 智能自动滚动 - 只在用户在底部附近时自动滚动
   */
  const autoScrollIfNeeded = () => {
    if (!scrollElement.value || !autoScroll.value || isUserScrolling.value) return;

    if (isNearBottom()) {
      scrollToBottom();
    }
  };

  /**
   * 处理用户滚动 - 设置用户滚动状态和按钮显示逻辑
   */
  const handleUserScroll = () => {
    if (!scrollElement.value) return;

    isUserScrolling.value = true;

    if (userScrollTimeout) {
      clearTimeout(userScrollTimeout);
    }

    userScrollTimeout = window.setTimeout(() => {
      isUserScrolling.value = false;
    }, 3000);

    // 检测滚动方向
    const currentScrollTop = scrollElement.value.scrollTop;
    scrollDirection = currentScrollTop > lastScrollTop ? 'down' : 'up';
    lastScrollTop = currentScrollTop;

    // 清除之前的超时
    if (buttonShowTimeout) {
      clearTimeout(buttonShowTimeout);
    }

    // 判断是否显示滚动到底部按钮
    // 当用户向下滚动（离开底部）时显示按钮，向上滚动时隐藏
    const shouldShowButton = !isNearBottom() && currentScrollTop > 200 && scrollDirection === 'down';

    // 使用防抖来避免频繁显示/隐藏
    buttonShowTimeout = window.setTimeout(() => {
      showScrollToBottomButton.value = shouldShowButton;
    }, 10);
  };

  /**
   * 设置滚动监听 - 极简实现，类似 Gemini
   */
  const setupAutoScroll = () => {
    if (scrollElement.value) {
      scrollElement.value.addEventListener('scroll', handleUserScroll, { passive: true });
    }
  };

  /**
   * 清理事件监听器
   */
  const cleanup = () => {
    if (userScrollTimeout) {
      clearTimeout(userScrollTimeout);
      userScrollTimeout = null;
    }

    if (buttonShowTimeout) {
      clearTimeout(buttonShowTimeout);
      buttonShowTimeout = null;
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
    scrollToMessage,
    autoScrollIfNeeded,
    isNearBottom,
    setupAutoScroll,
    showScrollToBottomButton
  };
}