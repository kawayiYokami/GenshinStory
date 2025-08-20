import { watch, onMounted } from 'vue';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { storeToRefs } from 'pinia';

/**
 * A Vue composable that manages the application's theme.
 * It listens to changes in the theme store and updates the DOM accordingly.
 */
export function useTheme() {
  const themeStore = useThemeStore();
  const { currentTheme } = storeToRefs(themeStore);

  const applyTheme = (themeName: string) => {
    const root = document.documentElement;
    
    // Clear existing theme attributes
    root.removeAttribute('data-theme');
    root.classList.remove('dark');

    root.setAttribute('data-theme', themeName);
    if (themeName.includes('dark')) {
      root.classList.add('dark');
    }
  };

  onMounted(() => {
    applyTheme(currentTheme.value);
  });

  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme);
  });
}