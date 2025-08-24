import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath, URL } from 'url';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    topLevelAwait(),
    wasm(),
    tailwindcss(),
  ],
  base: './',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  worker: {
    format: 'es',
    plugins: () => [
      topLevelAwait(),
      wasm()
    ]
  },
  optimizeDeps: {
    exclude: ['@dqbd/tiktoken']
  },
  server: {
    port: 5713
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          daisyui: ['daisyui']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
})