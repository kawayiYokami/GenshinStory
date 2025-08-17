import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
// import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './style.css'
import { checkVersion } from '@/services/versionService';

async function initializeApp() {
  // 在执行任何 Vue 相关操作之前，首先检查版本
  await checkVersion();

  const app = createApp(App);

  // 注册Element Plus图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus)

  app.mount('#app')
}

initializeApp();