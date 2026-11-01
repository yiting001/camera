import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { hideLayout: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据统计', requiresAuth: true }
  },
  // 用户管理
  {
    path: '/user/list',
    name: 'UserList',
    component: () => import('@/views/user/UserList.vue'),
    meta: { title: '用户管理', requiresAuth: true }
  },
  // 背景管理
  {
    path: '/background/list',
    name: 'BackgroundList',
    component: () => import('@/views/background/BackgroundList.vue'),
    meta: { title: '背景管理', requiresAuth: true }
  },
  // 合成照片管理
  {
    path: '/photo/list',
    name: 'PhotoList',
    component: () => import('@/views/photo/PhotoList.vue'),
    meta: { title: '合成照片', requiresAuth: true }
  },
  // 字体管理
  {
    path: '/font/list',
    name: 'FontList',
    component: () => import('@/views/font/FontList.vue'),
    meta: { title: '字体管理', requiresAuth: true }
  },
  // 系统设置
  {
    path: '/settings/logo',
    name: 'LogoSetting',
    component: () => import('@/views/settings/LogoSetting.vue'),
    meta: { title: 'Logo 设置', requiresAuth: true }
  },
  {
    path: '/settings/reference',
    name: 'ReferenceSetting',
    component: () => import('@/views/settings/ReferenceSetting.vue'),
    meta: { title: '参考图设置', requiresAuth: true }
  },
  {
    path: '/settings/api',
    name: 'ApiSetting',
    component: () => import('@/views/settings/ApiSetting.vue'),
    meta: { title: 'API 配置', requiresAuth: true }
  },
  // 文字描述设置
  {
    path: '/settings/text-overlay',
    name: 'TextOverlaySetting',
    component: () => import('@/views/settings/TextOverlaySetting.vue'),
    meta: { title: '文字描述设置', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
