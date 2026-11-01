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
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { Monitor } from '@element-plus/icons-vue'
import { api } from '@/api/index'
import { getServerUrl } from '@/config'

const router = useRouter()
const logoUrl = ref(null)

// 获取 Logo
async function fetchLogo() {
  try {
    const res = await api.getLogo()
    if (res.code === 200 && res.data?.url) {
      logoUrl.value = `${getServerUrl()}${res.data.url}`
    }
  } catch (error) {
    console.error('获取 Logo 失败:', error)
  }
}

onMounted(() => {
  fetchLogo()
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
</style>
