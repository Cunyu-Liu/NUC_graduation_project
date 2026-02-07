import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const app = createApp(App)

app.use(store)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 应用启动时验证token有效性
const token = localStorage.getItem('token')
if (token) {
  // 设置认证状态
  store.commit('SET_TOKEN', token)
  // 获取用户信息
  store.dispatch('fetchCurrentUser').then(response => {
    if (!response.success) {
      console.log('[App] Token无效，清除认证状态')
      store.commit('CLEAR_AUTH')
      // 如果不在登录页，跳转到登录页
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
  })
}

app.mount('#app')
