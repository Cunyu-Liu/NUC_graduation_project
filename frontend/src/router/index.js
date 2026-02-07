import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true, public: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/home',
    redirect: '/'
  },
  {
    path: '/analyze',
    name: 'Analyze',
    component: () => import('@/views/Analyze.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/cluster',
    name: 'Cluster',
    component: () => import('@/views/Cluster.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/views/Files.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/gaps',
    name: 'ResearchGaps',
    component: () => import('@/views/ResearchGaps.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/research-gaps',
    redirect: '/gaps'
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraph.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  // 代码编辑器页面（如果有）
  {
    path: '/code-editor/:id',
    name: 'CodeEditor',
    component: () => import('@/views/ResearchGaps.vue'), // 临时使用研究空白页面
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: () => {
      // 未登录时重定向到登录页，已登录时重定向到首页
      const token = localStorage.getItem('token')
      return token ? '/' : '/login'
    }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫 - 强制登录验证
router.beforeEach((to, from, next) => {
  // 从 localStorage 直接检查认证状态，确保刷新页面后仍然有效
  const token = localStorage.getItem('token')
  const isAuthenticated = !!token

  // 如果路由需要登录
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // 未登录，跳转到登录页，并保存尝试访问的路径
      console.log('[路由守卫] 未登录，重定向到登录页')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }

  // 如果路由是游客页面（登录/注册），但用户已登录
  if (to.meta.requiresGuest) {
    if (isAuthenticated) {
      // 已登录，跳转到首页或之前尝试访问的页面
      const redirect = to.query.redirect || '/'
      console.log('[路由守卫] 已登录，重定向到:', redirect)
      next(redirect)
      return
    }
  }

  // 其他情况正常跳转
  next()
})

export default router
