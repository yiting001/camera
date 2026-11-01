const { contextBridge, ipcRenderer } = require('electron')

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取应用版本
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 检查相机权限状态
  checkCameraPermission: () => ipcRenderer.invoke('check-camera-permission'),
  
  // 请求相机权限
  requestCameraPermission: () => ipcRenderer.invoke('request-camera-permission'),
  
  // 获取自启动状态
  getAutoLaunch: () => ipcRenderer.invoke('get-auto-launch'),
  
  // 设置自启动
  setAutoLaunch: (enable) => ipcRenderer.invoke('set-auto-launch', enable),
  
  // 获取应用配置
  getAppConfig: () => ipcRenderer.invoke('get-app-config'),
  
  // 保存应用配置
  saveAppConfig: (config) => ipcRenderer.invoke('save-app-config', config),
  
  // 获取全屏状态
  getFullscreen: () => ipcRenderer.invoke('get-fullscreen'),
  
  // 设置全屏
  setFullscreen: (enable) => ipcRenderer.invoke('set-fullscreen', enable),
  
  // 切换全屏
  toggleFullscreen: () => ipcRenderer.invoke('toggle-fullscreen'),
  
  // 判断是否在 Electron 环境中
  isElectron: true
})
