import { watch, onMounted } from 'vue';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { storeToRefs } from 'pinia';

/**
 * A Vue composable that manages the application's theme.
 * It listens to changes in the theme store and updates the DOM accordingly.
 * It also handles the 'system' theme preference.
 */
export function useTheme() {
  const themeStore = useThemeStore();
  const { currentTheme } = storeToRefs(themeStore);

  const applyTheme = (themeName: string) => {
    const root = document.documentElement;
    
    // Clear existing theme attributes
    root.removeAttribute('data-theme');
    root.classList.remove('dark');

    if (themeName === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.setAttribute('data-theme', 'm3-dark');
        root.classList.add('dark');
      } else {
        // Default to m3-light for system's light mode
        root.setAttribute('data-theme', 'm3-light');
      }
    } else {
      root.setAttribute('data-theme', themeName);
      if (themeName.includes('dark')) {
        root.classList.add('dark');
      }
    }
  };

  onMounted(() => {
    applyTheme(currentTheme.value);

    // Watch for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleMediaChange = (e: MediaQueryListEvent) => {
      if (currentTheme.value === 'system') {
        applyTheme('system');
      }
    };
    mediaQuery.addEventListener('change', handleMediaChange);
  });

  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme);
  });
}