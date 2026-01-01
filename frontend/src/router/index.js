import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/analyze',
    name: 'Analyze',
    component: () => import('@/views/Analyze.vue')
  },
  {
    path: '/cluster',
    name: 'Cluster',
    component: () => import('@/views/Cluster.vue')
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/views/Files.vue')
  },
  {
    path: '/research-gaps',
    name: 'ResearchGaps',
    component: () => import('@/views/ResearchGaps.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
