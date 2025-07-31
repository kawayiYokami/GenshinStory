import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import wasm from "vite-plugin-wasm";
import path from 'path'; // 关键：导入 path 模块

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    wasm(),
  ],
  resolve: {
    alias: {
      // 关键：添加路径别名配置，使 Vite 能够正确解析 @/stores/... 等路径
      '@': path.resolve(__dirname, './src'),
    }
  },
  server: {
    port: 5713,
  },
});