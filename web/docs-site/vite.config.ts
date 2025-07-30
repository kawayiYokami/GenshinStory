import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: './', // Use relative paths for assets
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
