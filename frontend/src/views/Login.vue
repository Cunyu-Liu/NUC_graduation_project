<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <div class="login-card">
      <!-- Logo和标题 -->
      <div class="header">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="title">科研文献摘要提取系统</h1>
        <p class="subtitle">Literature Analysis System</p>
      </div>

      <!-- 切换登录/注册 -->
      <div class="tabs">
        <button
          :class="['tab', { active: isLoginMode }]"
          @click="isLoginMode = true"
        >
          登录
        </button>
        <button
          :class="['tab', { active: !isLoginMode }]"
          @click="isLoginMode = false"
        >
          注册
        </button>
      </div>

      <!-- 登录表单 -->
      <transition name="fade" mode="out-in">
        <form v-if="isLoginMode" @submit.prevent="handleLogin" class="form">
          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              用户名 / 邮箱
            </label>
            <input
              v-model="loginForm.identifier"
              type="text"
              class="form-input"
              placeholder="请输入用户名或邮箱"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              密码
            </label>
            <div class="password-input">
              <input
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="请输入密码"
                required
              />
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
              >
                <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M1 1l22 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="loading">登录中...</span>
            <span v-else>登录</span>
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister" class="form">
          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              用户名
            </label>
            <input
              v-model="registerForm.username"
              type="text"
              class="form-input"
              placeholder="3-20个字符"
              minlength="3"
              maxlength="20"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              邮箱
            </label>
            <input
              v-model="registerForm.email"
              type="email"
              class="form-input"
              placeholder="example@email.com"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              密码
            </label>
            <input
              v-model="registerForm.password"
              type="password"
              class="form-input"
              placeholder="至少6个字符"
              minlength="6"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              确认密码
            </label>
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              class="form-input"
              placeholder="再次输入密码"
              minlength="6"
              required
            />
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="loading">注册中...</span>
            <span v-else>注册</span>
          </button>
        </form>
      </transition>

      <!-- 底部信息 -->
      <div class="footer">
        <p>&copy; 2025 科研文献摘要提取系统 | NUC毕业设计</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const store = useStore()

    const isLoginMode = ref(true)
    const showPassword = ref(false)
    const loading = ref(false)
    const errorMessage = ref('')

    const loginForm = ref({
      identifier: '',
      password: ''
    })

    const registerForm = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })

    // 登录处理
    const handleLogin = async () => {
      errorMessage.value = ''
      loading.value = true

      try {
        const response = await store.dispatch('login', {
          login_identifier: loginForm.value.identifier,
          password: loginForm.value.password
        })

        if (response.success) {
          // 登录成功，跳转到首页
          router.push('/')
        } else {
          errorMessage.value = response.error || '登录失败，请检查用户名和密码'
        }
      } catch (error) {
        errorMessage.value = error.message || '登录失败，请稍后重试'
        console.error('登录错误:', error)
      } finally {
        loading.value = false
      }
    }

    // 注册处理
    const handleRegister = async () => {
      errorMessage.value = ''

      // 验证密码
      if (registerForm.value.password !== registerForm.value.confirmPassword) {
        errorMessage.value = '两次输入的密码不一致'
        return
      }

      loading.value = true

      try {
        const response = await store.dispatch('register', {
          username: registerForm.value.username,
          email: registerForm.value.email,
          password: registerForm.value.password
        })

        if (response.success) {
          // 注册成功，自动登录并跳转到首页
          router.push('/')
        } else {
          errorMessage.value = response.error || '注册失败，请稍后重试'
        }
      } catch (error) {
        errorMessage.value = error.message || '注册失败，请稍后重试'
        console.error('注册错误:', error)
      } finally {
        loading.value = false
      }
    }

    return {
      isLoginMode,
      showPassword,
      loading,
      errorMessage,
      loginForm,
      registerForm,
      handleLogin,
      handleRegister
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 背景装饰 */
.background-decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: 10%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
  }
}

/* 登录卡片 */
.login-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 50px 45px;
  width: 100%;
  max-width: 450px;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 头部 */
.header {
  text-align: center;
  margin-bottom: 35px;
}

.logo {
  width: 70px;
  height: 70px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo svg {
  width: 40px;
  height: 40px;
}

.title {
  font-size: 26px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  letter-spacing: 0.5px;
}

.subtitle {
  font-size: 14px;
  color: #718096;
  margin: 0;
  font-weight: 400;
}

/* 标签切换 */
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  background: #f7fafc;
  padding: 5px;
  border-radius: 12px;
}

.tab {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  color: #718096;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.tab.active {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.tab:hover:not(.active) {
  background: rgba(255, 255, 255, 0.5);
}

/* 表单 */
.form {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 22px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 8px;
}

.form-label svg {
  color: #667eea;
  flex-shrink: 0;
}

.form-input {
  width: 100%;
  padding: 13px 15px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: white;
  color: #2d3748;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input::placeholder {
  color: #a0aec0;
}

/* 密码输入框 */
.password-input {
  position: relative;
}

.password-input .form-input {
  padding-right: 45px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.toggle-password:hover {
  color: #667eea;
}

/* 错误消息 */
.error-message {
  padding: 12px 15px;
  background: #fed7d7;
  color: #c53030;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
  border-left: 3px solid #c53030;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 底部 */
.footer {
  text-align: center;
  padding-top: 25px;
  border-top: 1px solid #e2e8f0;
  margin-top: 25px;
}

.footer p {
  font-size: 13px;
  color: #a0aec0;
  margin: 0;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 35px 25px;
  }

  .title {
    font-size: 22px;
  }

  .form-input {
    padding: 11px 13px;
    font-size: 14px;
  }

  .submit-btn {
    padding: 12px;
    font-size: 15px;
  }
}
</style>
