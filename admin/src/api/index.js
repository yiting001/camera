import axios from 'axios'

const instance = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

const api = {
  // 认证
  login: (data) => instance.post('/auth/login', data),
  
  // 看板数据
  getDashboard: () => instance.get('/admin/dashboard'),
  
  // 用户管理
  getUsers: (params) => instance.get('/admin/users', { params }),
  getUser: (id) => instance.get(`/admin/users/${id}`),
  updateUser: (id, data) => instance.put(`/admin/users/${id}`, data),
  deleteUser: (id) => instance.delete(`/admin/users/${id}`),
  
  // 照片管理
  getPhotos: (params) => instance.get('/admin/photos', { params }),
  deletePhoto: (id) => instance.delete(`/admin/photos/${id}`),
  
  // 相册管理
  getAlbums: (params) => instance.get('/admin/albums', { params }),
  deleteAlbum: (id) => instance.delete(`/admin/albums/${id}`),
  
  // 背景管理
  getBackgrounds: (params) => instance.get('/admin/backgrounds', { params }),
  
  // 系统配置
  getConfig: () => instance.get('/admin/config'),
  updateConfig: (data) => instance.put('/admin/config', data),
  
  // 操作日志
  getLogs: (params) => instance.get('/admin/logs', { params }),
  
  // 字体管理
  getFonts: (params) => instance.get('/admin/fonts', { params }),
  uploadFont: (formData) => instance.post('/admin/fonts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  updateFont: (id, data) => instance.put(`/admin/fonts/${id}`, data),
  deleteFont: (id) => instance.delete(`/admin/fonts/${id}`),
  toggleFont: (id) => instance.post(`/admin/fonts/${id}/toggle`),
  
  // Logo 管理
  getLogo: () => instance.get('/admin/logo'),
  uploadLogo: (formData) => instance.post('/admin/logo/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteLogo: () => instance.delete('/admin/logo'),
  
  // 参考图管理
  getReference: () => instance.get('/admin/reference'),
  uploadReference: (formData) => instance.post('/admin/reference/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteReference: () => instance.delete('/admin/reference'),
  
  // Coze API 配置
  getMjConfig: () => instance.get('/admin/mj-config'),
  saveMjConfig: (data) => instance.post('/admin/mj-config', data),
  testMjComposite: (data) => {
    // 支持 FormData 和 JSON
    if (data instanceof FormData) {
      return instance.post('/admin/mj-config/test', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000
      })
    }
    return instance.post('/admin/mj-config/test', data, { timeout: 300000 })
  },
  
  // 文字描述设置
  getTextOverlay: () => instance.get('/admin/text-overlay'),
  saveTextOverlay: (data) => instance.post('/admin/text-overlay', data)
}

export default api
