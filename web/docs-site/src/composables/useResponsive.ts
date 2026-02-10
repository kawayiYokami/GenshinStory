/**
 * @fileoverview 响应式工具组合式函数
 * @description 提供响应式布局检测功能，监听窗口大小变化
 * @author yokami
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

/**
 * 响应式工具组合式函数
 * @description 提供设备类型检测和窗口宽度监听功能
 * @return {Object} 响应式对象，包含设备类型和窗口宽度信息
 */
export function useResponsive() {
  /** 窗口宽度 */
  const windowWidth = ref(window.innerWidth)

  /** 是否为桌面设备 */
  const isDesktop = computed(() => windowWidth.value >= 1000)
  /** 是否为平板设备 */
  const isTablet = computed(() => windowWidth.value >= 800 && windowWidth.value < 1000)
  /** 是否为移动设备 */
  const isMobile = computed(() => windowWidth.value < 800)

  /**
   * 更新窗口宽度
   * @description 监听窗口大小变化事件，更新窗口宽度状态
   */
  const updateWidth = () => {
    windowWidth.value = window.innerWidth
  }

  /**
   * 组件挂载时添加事件监听器
   */
  onMounted(() => window.addEventListener('resize', updateWidth))
  /**
   * 组件卸载时移除事件监听器
   */
  onUnmounted(() => window.removeEventListener('resize', updateWidth))

  return { isDesktop, isTablet, isMobile, windowWidth }
}