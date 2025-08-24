import { watch, onMounted } from 'vue';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { storeToRefs } from 'pinia';
import { LAYOUT_CONFIG } from '@/features/app/configs/layoutConfig';

/**
 * A Vue composable that manages the application's theme.
 * It listens to changes in the theme store and updates the DOM accordingly.
 * DaisyUI handles dark mode automatically based on the theme name.
 */
export function useTheme() {
  const themeStore = useThemeStore();
  const { currentTheme } = storeToRefs(themeStore);

  const applyTheme = (themeName: string) => {
    const root = document.documentElement;
    
    // Set the data-theme attribute
    root.setAttribute('data-theme', themeName);
    
    // Set CSS custom properties for layout
    root.style.setProperty('--navbar-height', `${LAYOUT_CONFIG.navbarHeight}px`);
    root.style.setProperty('--function-pane-max-width', `${LAYOUT_CONFIG.functionPaneMaxWidth}px`);
    root.style.setProperty('--detail-pane-width', `${LAYOUT_CONFIG.detailPaneWidth}px`);
    root.style.setProperty('--overlay-threshold', `${LAYOUT_CONFIG.overlayThreshold}px`);
    root.style.setProperty('--transition-duration', `${LAYOUT_CONFIG.transitionDuration}ms`);
    root.style.setProperty('--overlay-z-index', LAYOUT_CONFIG.overlayZIndex.toString());
  };

  onMounted(() => {
    applyTheme(currentTheme.value);
  });

  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme);
  });
}