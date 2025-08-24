import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './assets/css/tailwind.css'
import { checkVersion } from '@/features/app/services/versionService';

async function initializeApp() {
  // 在执行任何 Vue 相关操作之前，首先检查版本
  await checkVersion();

  const app = createApp(App);

  app.use(createPinia())
  app.use(router)

  // Register service worker for mobile offline support
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