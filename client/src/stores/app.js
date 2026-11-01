import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 应用状态
  const isCollapse = ref(false)
  const theme = ref('light')
  
  // 设置
  const settings = ref({
    storagePath: '',
    autoBackup: false,
    imageQuality: 80
  })

  // 切换侧边栏
  const toggleCollapse = () => {
    isCollapse.value = !isCollapse.value
  }

  // 设置主题
  const setTheme = (newTheme) => {
    theme.value = newTheme
  }

  // 更新设置
  const updateSettings = (newSettings) => {
    settings.value = { ...settings.value, ...newSettings }
  }

  return {
    isCollapse,
    theme,
    settings,
    toggleCollapse,
    setTheme,
    updateSettings
  }
})
