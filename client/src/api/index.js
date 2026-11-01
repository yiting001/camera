import { getApiBaseUrl } from '@/config'

// 动态获取 API 基础地址
const getBaseUrl = () => getApiBaseUrl()

// 通用请求方法
async function request(url, options = {}) {
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  }

  const response = await fetch(`${getBaseUrl()}${url}`, config)
  return await response.json()
}

// API 方法
export const api = {
  // 照片
  uploadPhoto: (formData) => {
    return fetch(`${getBaseUrl()}/photo/upload`, {
      method: 'POST',
      body: formData
    }).then(r => r.json())
  },
  getPhotos: (params) => request(`/photo/list?${new URLSearchParams(params)}`),
  deletePhoto: (id) => request(`/photo/${id}`, { method: 'DELETE' }),

  // 相册
  getAlbums: () => request('/photo/albums'),
  createAlbum: (data) => request('/photo/albums', { method: 'POST', body: JSON.stringify(data) }),
  updateAlbum: (id, data) => request(`/photo/albums/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAlbum: (id) => request(`/photo/albums/${id}`, { method: 'DELETE' }),

  // Logo（公开接口）
  getLogo: () => request('/photo/logo')
}

export default api
