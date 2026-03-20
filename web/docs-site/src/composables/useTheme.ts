/**
 * @fileoverview 主题管理组合式函数
 * @description 管理应用程序主题，监听主题变化并更新DOM
 * @author yokami
 */
import { watch, onMounted } from 'vue';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { storeToRefs } from 'pinia';
import { LAYOUT_CONFIG } from '@/features/app/configs/layoutConfig';

/**
 * 主题管理组合式函数
 * @description 监听主题存储变化，自动更新DOM主题属性和CSS变量
 * DaisyUI会根据主题名称自动处理暗色模式
 * @return {void}
 */
export function useTheme() {
  const themeStore = useThemeStore();
  const { currentTheme } = storeToRefs(themeStore);

  /**
   * 应用主题到DOM
   * @description 设置主题属性和CSS自定义属性
   * @param {string} themeName 主题名称
   */
  const applyTheme = (themeName: string) => {
    const root = document.documentElement;

    // 设置主题属性
    root.setAttribute('data-theme', themeName);

    // 设置布局相关的CSS自定义属性
    root.style.setProperty('--navbar-height', `${LAYOUT_CONFIG.navbarHeight}px`);
    root.style.setProperty('--function-pane-max-width', `${LAYOUT_CONFIG.functionPaneMaxWidth}px`);
    root.style.setProperty('--detail-pane-width', `${LAYOUT_CONFIG.detailPaneWidth}px`);
    root.style.setProperty('--overlay-threshold', `${LAYOUT_CONFIG.overlayThreshold}px`);
    root.style.setProperty('--transition-duration', `${LAYOUT_CONFIG.transitionDuration}ms`);
    root.style.setProperty('--overlay-z-index', LAYOUT_CONFIG.overlayZIndex.toString());
  };

  /**
   * 组件挂载时应用当前主题
   */
  onMounted(() => {
    applyTheme(currentTheme.value);
  });

  /**
   * 监听主题变化并自动应用
   */
  watch(currentTheme, (newTheme) => {
    // 添加主题过渡类
    const root = document.documentElement;
    root.classList.add('theme-transitioning');

    // 应用新主题
    applyTheme(newTheme);

    // 在过渡完成后移除过渡类
    setTimeout(() => {
      root.classList.remove('theme-transitioning');
    }, LAYOUT_CONFIG.transitionDuration);
  });
}