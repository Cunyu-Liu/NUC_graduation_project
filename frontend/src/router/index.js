import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
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
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated

  // 如果路由需要登录
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // 未登录，跳转到登录页
      next('/login')
      return
    }
  }

  // 如果路由是游客页面（登录/注册），但用户已登录
  if (to.meta.requiresGuest) {
    if (isAuthenticated) {
      // 已登录，跳转到首页
      next('/')
      return
    }
  }

  // 其他情况正常跳转
  next()
})

export default router
