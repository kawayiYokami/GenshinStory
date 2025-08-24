import { defineStore } from 'pinia';

// List of popular DaisyUI themes for the selector
export type ThemeName = 
  | 'light' 
  | 'dark' 
  | 'cupcake' 
  | 'bumblebee' 
  | 'emerald' 
  | 'corporate' 
  | 'synthwave' 
  | 'retro' 
  | 'cyberpunk' 
  | 'valentine' 
  | 'halloween' 
  | 'garden' 
  | 'forest' 
  | 'aqua' 
  | 'lofi' 
  | 'pastel' 
  | 'fantasy' 
  | 'wireframe' 
  | 'black' 
  | 'luxury' 
  | 'dracula' 
  | 'cmyk' 
  | 'autumn' 
  | 'business' 
  | 'acid' 
  | 'lemonade' 
  | 'night' 
  | 'coffee' 
  | 'winter' 
  | 'dim' 
  | 'nord' 
  | 'sunset';

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
    },
  },
});