const { app, BrowserWindow, ipcMain, systemPreferences } = require('electron')
const path = require('path')
const fs = require('fs')

// 配置文件路径
const userDataPath = app.getPath('userData')
const configPath = path.join(userDataPath, 'app-config.json')

// 读取配置
function loadConfig() {
  try {
    if (fs.existsSync(configPath)) {
      const data = fs.readFileSync(configPath, 'utf-8')
      return JSON.parse(data)
    }
  } catch (e) {
    console.error('读取配置失败:', e)
  }
  return {}
}

// 保存配置
function saveConfig(config) {
  try {
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2))
  } catch (e) {
    console.error('保存配置失败:', e)
  }
}

let mainWindow

// 请求相机权限 (macOS)
async function requestCameraPermission() {
  if (process.platform === 'darwin') {
    const status = systemPreferences.getMediaAccessStatus('camera')
    if (status !== 'granted') {
      const granted = await systemPreferences.askForMediaAccess('camera')
      return granted
    }
    return true
  }
  return true
}

function createWindow() {
  // 读取配置判断是否需要全屏启动
  const config = loadConfig()
  const startFullscreen = config.startFullscreen !== false // 默认全屏
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: '智能拍照合成',
    fullscreen: startFullscreen,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    frame: true,
    show: false,
    backgroundColor: '#1a1a2e'
  })

  // 开发环境加载本地服务，生产环境加载打包文件
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL('http://localhost:5173')
    // mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // 设置窗口标题
  mainWindow.setTitle('智能拍照合成')
}

app.whenReady().then(async () => {
  // 请求相机权限
  await requestCameraPermission()
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// IPC 通信
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

// 检查相机权限状态
ipcMain.handle('check-camera-permission', async () => {
  if (process.platform === 'darwin') {
    return systemPreferences.getMediaAccessStatus('camera')
  }
  return 'granted'
})

// 请求相机权限
ipcMain.handle('request-camera-permission', async () => {
  return await requestCameraPermission()
})

// ========== 开机自启动功能 ==========

// 获取应用启动路径（Windows 需要特殊处理）
function getAutoLaunchPath() {
  // 打包后的应用使用 process.execPath
  // 开发模式下不支持开机自启
  if (app.isPackaged) {
    return process.execPath
  }
  return null
}

// 获取自启动状态
ipcMain.handle('get-auto-launch', () => {
  try {
    // 优先从配置文件读取（更可靠）
    const config = loadConfig()
    if (config.autoLaunch !== undefined) {
      return config.autoLaunch
    }
    
    // 如果没有配置记录，从系统获取
    if (process.platform === 'win32' && app.isPackaged) {
      const settings = app.getLoginItemSettings({
        path: process.execPath,
        args: []
      })
      return settings.openAtLogin
    } else {
      const settings = app.getLoginItemSettings()
      return settings.openAtLogin
    }
  } catch (e) {
    console.error('获取自启动状态失败:', e)
    return false
  }
})

// 设置自启动
ipcMain.handle('set-auto-launch', (event, enable) => {
  try {
    // 开发模式下跳过实际设置
    if (!app.isPackaged) {
      console.log('开发模式下跳过自启动设置')
      const config = loadConfig()
      config.autoLaunch = enable
      saveConfig(config)
      return true
    }
    
    // Windows 下需要特殊处理
    if (process.platform === 'win32') {
      app.setLoginItemSettings({
        openAtLogin: enable,
        openAsHidden: false,
        path: process.execPath,
        args: []
      })
    } else {
      // macOS / Linux
      app.setLoginItemSettings({
        openAtLogin: enable,
        openAsHidden: false
      })
    }
    
    // 保存到配置文件（确保下次启动能正确读取状态）
    const config = loadConfig()
    config.autoLaunch = enable
    saveConfig(config)
    
    console.log(`自启动已${enable ? '开启' : '关闭'}`)
    return true
  } catch (e) {
    console.error('设置自启动失败:', e)
    return false
  }
})

// 获取应用配置
ipcMain.handle('get-app-config', () => {
  return loadConfig()
})

// 保存应用配置
ipcMain.handle('save-app-config', (event, config) => {
  const currentConfig = loadConfig()
  const newConfig = { ...currentConfig, ...config }
  saveConfig(newConfig)
  return true
})

// ========== 全屏功能 ==========

// 获取全屏状态
ipcMain.handle('get-fullscreen', () => {
  if (mainWindow) {
    return mainWindow.isFullScreen()
  }
  return false
})

// 设置全屏
ipcMain.handle('set-fullscreen', (event, enable) => {
  if (mainWindow) {
    mainWindow.setFullScreen(enable)
    return true
  }
  return false
})

// 切换全屏
ipcMain.handle('toggle-fullscreen', () => {
  if (mainWindow) {
    const isFullScreen = mainWindow.isFullScreen()
    mainWindow.setFullScreen(!isFullScreen)
    return !isFullScreen
  }
  return false
})
