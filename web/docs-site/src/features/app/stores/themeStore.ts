import { defineStore } from 'pinia';

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
    currentTheme: (localStorage.getItem('app-theme') as ThemeName) || 'light',
  }),
  actions: {
    /**
     * Sets the application's theme.
     * Persists the selected theme to localStorage.
     * @param {ThemeName} themeName - The name of the theme to set.
     */
    setTheme(themeName: ThemeName) {
      this.currentTheme = themeName;
      localStorage.setItem('app-theme', themeName);
      // Update the DOM to reflect the new theme
      document.documentElement.setAttribute('data-theme', themeName);
    },

    /**
     * Initializes the theme on app startup.
     * Applies the theme stored in localStorage or the default theme.
     */
    initTheme() {
      const storedTheme = localStorage.getItem('app-theme') as ThemeName || this.currentTheme;
      document.documentElement.setAttribute('data-theme', storedTheme);
    }
  },
});