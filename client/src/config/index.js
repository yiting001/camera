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
 * 获取默认服务器地址
 */
export function getDefaultServerUrl() {
  return DEFAULT_CONFIG.apiBaseUrl
}

/**
 * 获取可访问的资源地址
 * - 相对路径：拼接服务器地址
 * - TOS 绝对地址：走服务器代理（客户端网络可能无法直连 TOS）
 * - 其他绝对地址：原样返回
 * @param {string} url
 * @param {{ width?: number }} options 图片缩略图宽度
 */
export function getAssetUrl(url, options = {}) {
  if (!url) return ''
  if (url.startsWith('data:') || url.startsWith('blob:')) return url

  if (!url.startsWith('http')) {
    return `${currentConfig.apiBaseUrl}${url}`
  }

  try {
    const parsed = new URL(url)
    if (parsed.hostname.endsWith('.tos-cn-beijing.volces.com')) {
      const width = options.width ? `&w=${options.width}` : ''
      return `${getApiBaseUrl()}/photo/proxy-image?url=${encodeURIComponent(url)}${width}`
    }
  } catch (e) {
    // URL 解析失败时按原地址使用
  }

  return url
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
      const savedUrl = ((savedConfig && savedConfig.apiBaseUrl) || '').trim().replace(/\/+$/, '')
      const isLocalhost = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(savedUrl)

      if (/^https?:\/\/.+/i.test(savedUrl) && !isLocalhost) {
        currentConfig.apiBaseUrl = savedUrl
      } else if (isLocalhost) {
        // 旧版本「重置」按钮会保存 localhost，导致打包后的客户端连不上服务器
        console.warn('检测到本地服务器地址，已自动使用默认地址:', DEFAULT_CONFIG.apiBaseUrl)
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
  getDefaultServerUrl,
  getAssetUrl,
  getConfig,
  setConfig,
  initConfig,
  saveConfig
}
