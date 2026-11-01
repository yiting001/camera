import { getApiBaseUrl, getServerUrl } from '@/config'

// 动态获取 API 基础地址
const getBaseUrl = () => getApiBaseUrl()

// 获取 token
const getToken = () => localStorage.getItem('token')

/**
 * 获取 TOS 上传签名
 * @param {string} filename - 文件名
 * @param {string} folder - 存储文件夹
 * @returns {Promise} 返回签名数据
 */
export async function getTosSignature(filename, folder = 'photos') {
  const response = await fetch(`${getBaseUrl()}/tos/signature?filename=${encodeURIComponent(filename)}&folder=${folder}`)
  const result = await response.json()
  return result
}

/**
 * 上传图片到 TOS
 * @param {string} base64Data - 图片的 base64 数据
 * @param {string} filename - 文件名
 * @returns {Promise<string>} 返回公网 URL
 */
export async function uploadToTos(base64Data, filename = 'image.jpg') {
  // 1. 获取签名
  const sigResult = await getTosSignature(filename, 'photos')
  if (sigResult.code !== 200) {
    throw new Error(sigResult.message || '获取上传签名失败')
  }
  
  const sig = sigResult.data
  
  // 2. 将 base64 转为 Blob
  const base64Content = base64Data.includes(',') ? base64Data.split(',')[1] : base64Data
  const binaryStr = atob(base64Content)
  const bytes = new Uint8Array(binaryStr.length)
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: 'image/jpeg' })
  
  // 3. 构建 FormData 上传到 TOS
  const formData = new FormData()
  formData.append('key', sig.key)
  formData.append('policy', sig.policy)
  formData.append('x-tos-algorithm', sig['x-tos-algorithm'])
  formData.append('x-tos-credential', sig['x-tos-credential'])
  formData.append('x-tos-date', sig['x-tos-date'])
  formData.append('x-tos-signature', sig['x-tos-signature'])
  if (sig['x-tos-security-token']) {
    formData.append('x-tos-security-token', sig['x-tos-security-token'])
  }
  formData.append('file', blob, filename)
  
  // 4. 上传到 TOS
  const uploadUrl = `https://${sig.host}`
  const uploadRes = await fetch(uploadUrl, {
    method: 'POST',
    body: formData
  })
  
  if (!uploadRes.ok && uploadRes.status !== 204) {
    throw new Error('上传到 TOS 失败')
  }
  
  // 5. 返回公网 URL
  return sig.url
}

/**
 * AI合成接口 - 将用户人像与背景合成（使用豆包 Doubao API）
 * @param {Object} data - 合成数据
 * @param {string} data.photo - 用户照片的公网 URL（图1-人像）
 * @param {string} data.background - 背景图片的公网 URL（图2-背景）
 * @param {string} data.reference - 参考图片的公网 URL（可选）
 * @param {string} data.prompt - 提示词（可选）
 * @param {string} data.size - 输出尺寸（可选，默认 16:9）
 * @returns {Promise} 返回合成结果
 */
export async function generateAIComposite(data) {
  const token = getToken()
  
  const response = await fetch(`${getBaseUrl()}/ai/composite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      photo: data.photo,
      background: data.background,
      reference: data.reference,
      prompt: data.prompt,
      size: data.size
    })
  })
  
  const result = await response.json()
  
  // 对于 403 配额不足的情况，返回结果让调用方处理
  if (response.status === 403) {
    return result
  }
  
  if (!response.ok) {
    throw new Error(result.message || 'AI合成失败')
  }
  
  return result
}

/**
 * 保存照片到相册
 * @param {Object} data - 照片数据
 * @param {string} data.image - 照片的base64数据
 * @param {string} data.type - 照片类型 (original/composite)
 * @param {string} data.albumId - 相册ID (可选)
 * @returns {Promise} 返回保存结果
 */
export async function savePhoto(data) {
  const token = getToken()
  
  const response = await fetch(`${getBaseUrl()}/photo/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  
  const result = await response.json()
  
  if (!response.ok) {
    throw new Error(result.message || '保存失败')
  }
  
  return result
}

/**
 * 获取预设背景列表
 * @returns {Promise} 返回背景列表
 */
export async function getBackgrounds() {
  const token = getToken()
  
  const response = await fetch(`${getBaseUrl()}/photo/backgrounds`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })
  
  const result = await response.json()
  return result
}

/**
 * 获取字体列表
 * @returns {Promise} 返回字体列表
 */
export async function getFonts() {
  const token = getToken()
  
  const response = await fetch(`${getBaseUrl()}/photo/fonts`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  })
  
  const result = await response.json()
  return result
}

/**
 * 上传自定义背景
 * @param {File} file - 背景图片文件
 * @returns {Promise} 返回上传结果
 */
export async function uploadBackground(file) {
  const token = getToken()
  const formData = new FormData()
  formData.append('background', file)
  
  const response = await fetch(`${getBaseUrl()}/backgrounds/upload`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: formData
  })
  
  const result = await response.json()
  
  if (!response.ok) {
    throw new Error(result.message || '上传失败')
  }
  
  return result
}

// 获取品牌 Logo
export async function getLogo() {
  const response = await fetch(`${getBaseUrl()}/photo/logo`)
  const result = await response.json()
  return result
}

// 获取合成参考图
export async function getReference() {
  const response = await fetch(`${getBaseUrl()}/photo/reference`)
  const result = await response.json()
  return result
}

// 获取文字描述设置（后端管理控制）
export async function getTextOverlay() {
  const response = await fetch(`${getBaseUrl()}/photo/text-overlay`)
  const result = await response.json()
  return result
}

// 获取提示词模式列表
export async function getPrompts() {
  const response = await fetch(`${getBaseUrl()}/photo/prompts`)
  const result = await response.json()
  return result
}

// 保存合成图片到服务器（旧接口，走 TOS）
export async function saveComposite(imageUrl, imageData) {
  const response = await fetch(`${getBaseUrl()}/ai/save-composite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      imageUrl: imageUrl,
      imageData: imageData
    })
  })
  const result = await response.json()
  return result
}

// 上传图片到自己服务器，获取站内分享短链接（微信可直接打开，长按保存）
export async function sharePhoto(imageData) {
  const response = await fetch(`${getBaseUrl()}/photo/share`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ imageData })
  })
  const result = await response.json()
  return result
}

export default {
  getTosSignature,
  uploadToTos,
  generateAIComposite,
  savePhoto,
  getBackgrounds,
  getFonts,
  uploadBackground,
  getLogo,
  getReference,
  getTextOverlay,
  getPrompts,
  saveComposite,
  sharePhoto
}
