<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- 顶部标题栏 -->
      <header class="app-header">
        <div class="logo">
          <img v-if="logoUrl" :src="logoUrl" alt="Logo" class="header-logo-img" />
          <el-icon v-else :size="32"><Monitor /></el-icon>
          <span class="logo-text">微光汇聚工作站</span>
        </div>
        <div class="header-right">
          <el-button type="info" size="small" @click="router.push('/settings')">
            服务器设置
          </el-button>
        </div>
      </header>

      <!-- 主内容区 - 拍照合成 -->
      <main class="app-main">
        <router-view />
      </main>

      <!-- 断网提示 -->
      <div v-if="showOfflineOverlay" class="network-overlay" role="alertdialog" aria-modal="true">
        <div class="network-card">
          <div class="network-icon">
            <el-icon :size="46"><Connection /></el-icon>
          </div>
          <h2>{{ offlineReason === 'device' ? '设备未联网' : '无法连接服务器' }}</h2>
          <p class="network-desc">
            {{ offlineReason === 'device'
              ? '请连接网络后重试，联网后会自动恢复'
              : '请检查网络连接或服务器地址后重试' }}
          </p>
          <p class="network-server">服务器地址：{{ serverAddress }}</p>
          <div class="network-actions">
            <el-button type="primary" :loading="checking" @click="checkNetwork">重新检测</el-button>
            <el-button @click="goSettings">服务器设置</el-button>
          </div>
        </div>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { Monitor, Connection } from '@element-plus/icons-vue'
import { api } from '@/api/index'
import { getServerUrl, getApiBaseUrl, getAssetUrl } from '@/config'

const router = useRouter()
const route = useRoute()
const logoUrl = ref(null)

// 联网状态
const networkOffline = ref(false)
const offlineReason = ref('') // device: 设备没网；server: 连不上服务器
const checking = ref(false)
const serverAddress = computed(() => getServerUrl())
// 在「服务器设置」页不遮挡，方便用户修改地址
const showOfflineOverlay = computed(() => networkOffline.value && route.path !== '/settings')

let checkTimer = null

// 检测：先看设备网络，再实际请求一次服务器
async function checkNetwork() {
  if (checking.value) return
  checking.value = true

  try {
    if (!navigator.onLine) {
      markOffline('device')
      return
    }

    let reachable = false
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 5000)
      const res = await fetch(`${getApiBaseUrl()}/photo/text-overlay`, {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal
      })
      clearTimeout(timer)
      if (res.ok) {
        const data = await res.json()
        reachable = data && data.code === 200
      }
    } catch (e) {
      reachable = false
    }

    if (reachable) {
      const recovered = networkOffline.value
      networkOffline.value = false
      offlineReason.value = ''
      if (recovered) {
        ElMessage.success('网络已恢复')
        // 通知页面重新拉取背景、提示词等数据
        window.dispatchEvent(new Event('app-network-online'))
      }
    } else {
      markOffline('server')
    }
  } finally {
    checking.value = false
  }
}

function markOffline(reason) {
  networkOffline.value = true
  offlineReason.value = reason
}

function handleOffline() {
  markOffline('device')
}

function handleOnline() {
  checkNetwork()
}

function handleNetworkError() {
  markOffline('server')
}

function goSettings() {
  router.push('/settings')
}

// 从设置页返回时重新检测
watch(() => route.path, (path) => {
  if (path !== '/settings' && networkOffline.value) {
    checkNetwork()
  }
})

// 获取 Logo
async function fetchLogo() {
  try {
    const res = await api.getLogo()
    if (res.code === 200 && res.data?.url) {
      // 外部图片走服务器代理，避免客户端访问不了 TOS
      logoUrl.value = getAssetUrl(res.data.url, { width: 200 })
    }
  } catch (error) {
    console.error('获取 Logo 失败:', error)
  }
}

onMounted(() => {
  fetchLogo()

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  window.addEventListener('app-network-error', handleNetworkError)
  window.addEventListener('app-network-device-offline', handleOffline)

  checkNetwork()
  checkTimer = setInterval(checkNetwork, 15000)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  window.removeEventListener('app-network-error', handleNetworkError)
  window.removeEventListener('app-network-device-offline', handleOffline)
  if (checkTimer) {
    clearInterval(checkTimer)
    checkTimer = null
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
}

.app-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
}

.header-logo-img {
  max-width: 40px;
  max-height: 40px;
  object-fit: contain;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
}

.app-main {
  flex: 1;
  overflow: hidden;
}

/* 断网提示 */
.network-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(10, 14, 25, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.network-card {
  width: min(440px, 92vw);
  background: #16213e;
  border: 1px solid #0f3460;
  border-radius: 16px;
  padding: 32px 28px;
  text-align: center;
  color: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.network-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 77, 77, 0.12);
  color: #ff6b6b;
}

.network-card h2 {
  margin: 0 0 10px;
  font-size: 24px;
}

.network-desc {
  margin: 0 0 10px;
  color: #a7b0c4;
  font-size: 14px;
  line-height: 1.7;
}

.network-server {
  margin: 0 0 22px;
  color: #6f7a90;
  font-size: 12px;
  word-break: break-all;
}

.network-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>
