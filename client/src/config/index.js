/**
 * 应用配置模块
 * 支持 Electron 环境下的配置文件读写
 */

// 默认配置
const DEFAULT_CONFIG = {
  apiBaseUrl: 'http://39.102.118.126:5001',
  apiPath: '/api'
}

// 当前配置（运行时）
let currentConfig = { ...DEFAULT_CONFIG }

/**
 * 获取完整的 API 基础地址
 */
export function getApiBaseUrl() {
  return `${currentConfig.apiBaseUrl}${currentConfig.apiPath}`
}

/**
 * 获取服务器地址（不含 /api 路径）
 */
export function getServerUrl() {
  return currentConfig.apiBaseUrl
}

/**
 * 获取当前配置
 */
export function getConfig() {
  return { ...currentConfig }
}

/**
 * 更新配置
 */
export function setConfig(newConfig) {
  currentConfig = { ...currentConfig, ...newConfig }
}

/**
 * 初始化配置（从 Electron 配置文件加载）
 */
export async function initConfig() {
  // 检查是否在 Electron 环境
  if (window.electronAPI && window.electronAPI.getAppConfig) {
    try {
      const savedConfig = await window.electronAPI.getAppConfig()
      if (savedConfig && savedConfig.apiBaseUrl) {
        currentConfig.apiBaseUrl = savedConfig.apiBaseUrl
      }
      console.log('配置加载成功:', currentConfig)
    } catch (error) {
      console.error('加载配置失败:', error)
    }
  }
  return currentConfig
}

/**
 * 保存配置到文件
 */
export async function saveConfig(config) {
  if (window.electronAPI && window.electronAPI.saveAppConfig) {
    try {
      await window.electronAPI.saveAppConfig(config)
      setConfig(config)
      console.log('配置保存成功:', currentConfig)
      return true
    } catch (error) {
      console.error('保存配置失败:', error)
      return false
    }
  }
  // 非 Electron 环境，仅更新运行时配置
  setConfig(config)
  return true
}

export default {
  getApiBaseUrl,
  getServerUrl,
  getConfig,
  setConfig,
  initConfig,
  saveConfig
}
