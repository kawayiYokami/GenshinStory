/**
 * 智能布局系统配置
 */
export const LAYOUT_CONFIG = {
  // 功能区最大宽度
  functionPaneMaxWidth: 800,
  
  // 详情区固定宽度
  detailPaneWidth: 600,
  
  // 并排布局最小宽度阈值
  overlayThreshold: 1400,
  
  // 过渡动画时长 (ms)
  transitionDuration: 300,
  
  // 导航栏高度
  navbarHeight: 64,
  
  // 覆盖层z-index
  overlayZIndex: 40
} as const;

// 计算是否应该使用覆盖布局
export const shouldUseOverlayLayout = (windowWidth: number): boolean => {
  return windowWidth < LAYOUT_CONFIG.overlayThreshold;
};

// 计算并排布局时的功能区宽度
export const calculateSplitPaneWidth = (windowWidth: number): number => {
  return windowWidth - LAYOUT_CONFIG.detailPaneWidth;
};