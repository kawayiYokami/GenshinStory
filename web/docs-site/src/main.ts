/**
 * @fileoverview 应用程序入口文件
 * @description 负责初始化Vue应用，配置路由、状态管理和Service Worker
 * @author yokami
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './assets/css/tailwind.css'
import { checkVersion } from '@/features/app/services/versionService';

/**
 * 初始化Vue应用程序
 * @description 在应用启动前检查版本，创建Vue实例并挂载
 */
async function initializeApp() {
  // 在执行任何 Vue 相关操作之前，首先检查版本
  await checkVersion();

  const app = createApp(App);

  app.use(createPinia())
  app.use(router)

  // 注册 Service Worker 用于移动端离线支持
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('SW registered: ', registration);
        })
        .catch(registrationError => {
          console.log('SW registration failed: ', registrationError);
        });
    });
  }

  app.mount('#app')
}

initializeApp();