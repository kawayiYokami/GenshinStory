import { defineStore } from 'pinia';
import storageFacade from '@/features/app/services/storageFacade';

// List of curated DaisyUI themes for the selector
export type ThemeName =
  | 'light'
  | 'dark'
  | 'cupcake'
  | 'dracula'
  | 'autumn'
  | 'winter'
  | 'night'
  // Custom themes based on character color schemes
  | 'zhongli'
  | 'furina'
  | 'nahida'
  | 'hutao';

interface ThemeState {
  currentTheme: ThemeName;
  isTransitioning: boolean;
}

/**
 * Manages the application's theme state.
 * Uses DaisyUI's built-in themes for consistent styling.
 */
export const useThemeStore = defineStore('theme', {
  state: (): ThemeState => ({
    /**
     * The current theme of the application.
     * Defaults to 'light'.
     */
    currentTheme: (storageFacade.getTheme() as ThemeName) || 'light',
    /**
     * Whether a theme transition is currently in progress.
     */
    isTransitioning: false,
  }),
  actions: {
    /**
     * Sets the application's theme.
     * Persists the selected theme to localStorage.
     * @param {ThemeName} themeName - The name of the theme to set.
     */
    setTheme(themeName: ThemeName) {
      this.currentTheme = themeName;
      storageFacade.setTheme(themeName);
      // Update the DOM to reflect the new theme
      document.documentElement.setAttribute('data-theme', themeName);
    },

    /**
     * Sets the application's theme with a transition effect.
     * @param {ThemeName} themeName - The name of the theme to set.
     */
    setThemeWithTransition(themeName: ThemeName) {
      this.isTransitioning = true;
      // Use a small delay to ensure the transition class is applied before the theme change
      setTimeout(() => {
        this.setTheme(themeName);
        this.isTransitioning = false;
      }, 50);
    },

    /**
     * Initializes the theme on app startup.
     * Applies the theme stored in localStorage or the default theme.
     */
    initTheme() {
      const storedTheme = storageFacade.getTheme() as ThemeName || this.currentTheme;
      document.documentElement.setAttribute('data-theme', storedTheme);
    }
  },
});
