import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { initConfig } from './config'

// 初始化配置后再挂载应用
async function bootstrap() {
  // 初始化配置（从 Electron 配置文件加载）
  await initConfig()
  
  const app = createApp(App)
  
  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
  
  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus, { locale: zhCn })
  
  app.mount('#app')
}

bootstrap()
