<template>
  <div class="settings">
    <div class="settings-header">
      <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
      <h2>系统设置</h2>
    </div>
    
    <el-card>
      <el-form label-width="120px">
        <!-- 服务器地址 -->
        <el-form-item label="请求地址">
          <el-input 
            v-model="serverUrl" 
            placeholder="http://localhost:5001"
          />
          <span class="form-tip">后端服务器地址，如 http://192.168.1.100:5001</span>
        </el-form-item>

        <!-- 开机自启动 (仅Electron环境) -->
        <el-form-item label="开机自启动" v-if="isElectron">
          <el-switch 
            v-model="autoLaunch" 
            @change="handleAutoLaunchChange"
            :loading="autoLaunchLoading"
          />
          <span class="form-tip">开启后，电脑启动时自动打开软件</span>
        </el-form-item>

        <!-- 全屏启动 (仅Electron环境) -->
        <el-form-item label="全屏启动" v-if="isElectron">
          <el-switch 
            v-model="startFullscreen" 
            @change="handleFullscreenChange"
          />
          <span class="form-tip">开启后，软件启动时自动全屏显示</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig as saveAppConfig } from '@/config'
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.push('/')
}

// 服务器地址
const serverUrl = ref('http://localhost:5001')

// 开机自启动
const autoLaunch = ref(false)
const autoLaunchLoading = ref(false)

// 全屏启动
const startFullscreen = ref(true)

// 判断是否在 Electron 环境
const isElectron = computed(() => {
  return window.electronAPI && window.electronAPI.isElectron
})

// 加载服务器配置
function loadServerConfig() {
  const config = getConfig()
  serverUrl.value = config.apiBaseUrl || 'http://localhost:5001'
}

// 获取自启动状态
async function fetchAutoLaunchStatus() {
  if (!isElectron.value) return
  try {
    const status = await window.electronAPI.getAutoLaunch()
    autoLaunch.value = status
  } catch (e) {
    console.error('获取自启动状态失败:', e)
  }
}

// 获取全屏启动配置
async function fetchFullscreenConfig() {
  if (!isElectron.value) return
  try {
    const config = await window.electronAPI.getAppConfig()
    startFullscreen.value = config.startFullscreen !== false
  } catch (e) {
    console.error('获取全屏配置失败:', e)
  }
}

// 处理自启动切换
async function handleAutoLaunchChange(value) {
  if (!isElectron.value) return
  autoLaunchLoading.value = true
  try {
    const success = await window.electronAPI.setAutoLaunch(value)
    if (success) {
      ElMessage.success(value ? '已开启开机自启动' : '已关闭开机自启动')
    } else {
      ElMessage.error('设置失败')
      autoLaunch.value = !value
    }
  } catch (e) {
    console.error('设置自启动失败:', e)
    ElMessage.error('设置失败')
    autoLaunch.value = !value
  } finally {
    autoLaunchLoading.value = false
  }
}

// 处理全屏启动切换
async function handleFullscreenChange(value) {
  if (!isElectron.value) return
  try {
    await window.electronAPI.saveAppConfig({ startFullscreen: value })
    ElMessage.success(value ? '已开启全屏启动' : '已关闭全屏启动')
  } catch (e) {
    console.error('设置全屏启动失败:', e)
    ElMessage.error('设置失败')
    startFullscreen.value = !value
  }
}

// 保存设置
async function saveSettings() {
  const success = await saveAppConfig({
    apiBaseUrl: serverUrl.value
  })
  
  if (success) {
    ElMessage.success('设置已保存')
  } else {
    ElMessage.error('保存设置失败')
  }
}

// 重置设置
function resetSettings() {
  serverUrl.value = 'http://localhost:5001'
  ElMessage.info('设置已重置')
}

onMounted(() => {
  loadServerConfig()
  fetchAutoLaunchStatus()
  fetchFullscreenConfig()
})
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.settings-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
