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
 * @description 优先挂载Vue应用，版本检查在后台异步执行
 */
async function initializeApp() {
  const app = createApp(App);

  app.use(createPinia())
  app.use(router)

  app.mount('#app')

  // 在应用挂载后异步检查版本，不阻塞UI
  checkVersion().catch(error => {
    console.warn('版本检查失败:', error);
  });

  // 注册 Service Worker 用于移动端离线支持
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          // 监听 SW 更新事件
          registration.onupdatefound = () => {
            const installingWorker = registration.installing;
            if (installingWorker == null) {
              return;
            }
            installingWorker.onstatechange = () => {
              if (installingWorker.state === 'installed') {
                if (navigator.serviceWorker.controller) {
                  console.log('New content is available; please refresh.');
                } else {
                  console.log('Content is cached for offline use.');
                }
              }
            };
          };
        })
        .catch(registrationError => {
          console.log('SW registration failed: ', registrationError);
        });

      // 监听 controllerchange 事件，当新 SW 接管时刷新页面
      // 配合 sw.js 中的 self.skipWaiting() 和 self.clients.claim()
      // 这能确保用户总是看到最新版本
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          window.location.reload();
          refreshing = true;
        }
      });
    });
  }
}

initializeApp();