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

  app.mount('#app')
}

initializeApp();