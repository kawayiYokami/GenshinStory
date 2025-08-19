import { defineStore } from 'pinia';

export type ThemeName = 'system' | 'm3-light' | 'm3-dark' | 'genshin-light';

interface ThemeState {
  currentTheme: ThemeName;
}

/**
 * Manages the application's theme state.
 * Allows switching between different themes like 'light', 'dark', or brand-specific themes.
 */
export const useThemeStore = defineStore('theme', {
  state: (): ThemeState => ({
    /**
     * The current theme of the application.
     * Defaults to 'system'.
     */
    currentTheme: (localStorage.getItem('app-theme') as ThemeName) || 'system',
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
    },
  },
});