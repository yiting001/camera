<template>
  <el-config-provider :locale="zhCn">
    <!-- 登录页面不显示布局 -->
    <router-view v-if="route.meta.hideLayout" />
    
    <!-- 主布局 -->
    <el-container v-else class="app-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
        <div class="logo">
          <el-icon :size="28" color="#409eff"><Monitor /></el-icon>
          <span v-show="!isCollapse" class="logo-text">微光汇聚工作站</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          router
          class="menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>数据统计</template>
          </el-menu-item>
          
          <el-menu-item index="/user/list">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          
          <el-menu-item index="/background/list">
            <el-icon><Picture /></el-icon>
            <template #title>背景管理</template>
          </el-menu-item>
          
          <el-menu-item index="/photo/list">
            <el-icon><Camera /></el-icon>
            <template #title>合成照片</template>
          </el-menu-item>
          
          <el-menu-item index="/font/list">
            <el-icon><EditPen /></el-icon>
            <template #title>字体管理</template>
          </el-menu-item>
          
          <el-menu-item index="/settings/logo">
            <el-icon><PictureFilled /></el-icon>
            <template #title>Logo 设置</template>
          </el-menu-item>
          
          <el-menu-item index="/settings/reference">
            <el-icon><Picture /></el-icon>
            <template #title>参考图设置</template>
          </el-menu-item>
          
          <el-menu-item index="/settings/text-overlay">
            <el-icon><Document /></el-icon>
            <template #title>文字描述设置</template>
          </el-menu-item>
          
          <el-menu-item index="/settings/api">
            <el-icon><Setting /></el-icon>
            <template #title>API 配置</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 顶部栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-button @click="toggleCollapse" :icon="isCollapse ? 'Expand' : 'Fold'" circle />
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <div class="user-info">
                <el-avatar :size="32" :icon="UserFilled" />
                <span class="username">{{ currentUser.username || '管理员' }}</span>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                  <el-dropdown-item command="password">修改密码</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { Monitor, DataAnalysis, User, Picture, Camera, UserFilled, EditPen, PictureFilled, Setting, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('admin_user') || '{}')
  } catch {
    return {}
  }
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    router.push('/login')
  }
}
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
}

.aside {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  gap: 10px;
  border-bottom: 1px solid #3d4a5a;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
}

.menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  background: #fff;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  color: #606266;
}

.main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
