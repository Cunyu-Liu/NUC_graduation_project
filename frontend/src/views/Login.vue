<template>
  <div class="login-page">
    <!-- 左侧装饰区域 -->
    <div class="login-left">
      <div class="left-content">
        <div class="brand">
          <div class="brand-logo">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1 class="brand-name">科研文献智能分析系统</h1>
        </div>
        <p class="brand-desc">
          基于大语言模型的螺旋式知识积累与代码生成平台<br/>
          实现从文献分析到代码智能生成的完整闭环
        </p>
        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">📄</div>
            <span>智能PDF解析</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🧠</div>
            <span>AI摘要生成</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🔍</div>
            <span>研究空白挖掘</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">💻</div>
            <span>智能代码生成</span>
          </div>
        </div>
      </div>
      <!-- 背景装饰 -->
      <div class="bg-decoration">
        <div class="circle c1"></div>
        <div class="circle c2"></div>
        <div class="circle c3"></div>
      </div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="login-right">
      <div class="login-box">
        <!-- 标题 -->
        <div class="login-header">
          <h2 class="login-title">{{ isLoginMode ? '欢迎回来' : '创建账号' }}</h2>
          <p class="login-subtitle">{{ isLoginMode ? '请登录您的账户' : '注册新账户开始使用' }}</p>
        </div>

        <!-- 切换标签 -->
        <div class="tab-switcher">
          <button 
            :class="['tab-btn', { active: isLoginMode }]" 
            @click="isLoginMode = true"
          >
            登录
          </button>
          <button 
            :class="['tab-btn', { active: !isLoginMode }]" 
            @click="isLoginMode = false"
          >
            注册
          </button>
        </div>

        <!-- 登录表单 -->
        <transition name="form-fade" mode="out-in">
          <form v-if="isLoginMode" key="login" @submit.prevent="handleLogin" class="auth-form">
            <div class="form-item">
              <label class="form-label">
                <el-icon><User /></el-icon>
                用户名 / 邮箱
              </label>
              <input
                v-model="loginForm.identifier"
                type="text"
                class="form-control"
                placeholder="请输入用户名或邮箱"
                required
              />
            </div>

            <div class="form-item">
              <label class="form-label">
                <el-icon><Lock /></el-icon>
                密码
              </label>
              <div class="password-wrapper">
                <input
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-control"
                  placeholder="请输入密码"
                  required
                />
                <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                  <el-icon v-if="showPassword"><ViewIcon /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div v-if="errorMessage" class="error-alert">
              <el-icon><Warning /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>

            <button type="submit" class="submit-button" :disabled="loading">
              <el-icon v-if="loading" class="loading-icon"><Loading /></el-icon>
              <span>{{ loading ? '登录中...' : '登 录' }}</span>
            </button>
          </form>

          <!-- 注册表单 -->
          <form v-else key="register" @submit.prevent="handleRegister" class="auth-form">
            <div class="form-row">
              <div class="form-item half">
                <label class="form-label">
                  <el-icon><User /></el-icon>
                  用户名
                </label>
                <input
                  v-model="registerForm.username"
                  type="text"
                  class="form-control"
                  placeholder="3-20个字符"
                  minlength="3"
                  maxlength="20"
                  required
                />
              </div>
              <div class="form-item half">
                <label class="form-label">
                  <el-icon><Message /></el-icon>
                  邮箱
                </label>
                <input
                  v-model="registerForm.email"
                  type="email"
                  class="form-control"
                  placeholder="example@email.com"
                  required
                />
              </div>
            </div>

            <div class="form-item">
              <label class="form-label">
                <el-icon><Lock /></el-icon>
                密码
              </label>
              <div class="password-wrapper">
                <input
                  v-model="registerForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-control"
                  placeholder="至少6个字符"
                  minlength="6"
                  required
                />
                <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                  <el-icon v-if="showPassword"><ViewIcon /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div class="form-item">
              <label class="form-label">
                <el-icon><Lock /></el-icon>
                确认密码
              </label>
              <div class="password-wrapper">
                <input
                  v-model="registerForm.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  class="form-control"
                  placeholder="再次输入密码"
                  minlength="6"
                  required
                />
                <button type="button" class="eye-btn" @click="showConfirmPassword = !showConfirmPassword">
                  <el-icon v-if="showConfirmPassword"><View /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div v-if="errorMessage" class="error-alert">
              <el-icon><Warning /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>

            <button type="submit" class="submit-button" :disabled="loading">
              <el-icon v-if="loading" class="loading-icon"><Loading /></el-icon>
              <span>{{ loading ? '注册中...' : '注 册' }}</span>
            </button>
          </form>
        </transition>

        <!-- 底部版权 -->
        <div class="login-footer">
          <p>&copy; 2025 科研文献智能分析系统 | NUC毕业设计</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { User, Lock, Message, View as ViewIcon, Hide, Loading, Warning } from '@element-plus/icons-vue'

export default {
  name: 'Login',
  components: {
    User, Lock, Message, ViewIcon, Hide, Loading, Warning
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

    // 获取redirect参数，登录成功后跳转
    const redirect = route.query.redirect || '/'

    const isLoginMode = ref(true)
    const showPassword = ref(false)
    const showConfirmPassword = ref(false)
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
          // 登录成功，跳转到之前尝试访问的页面或首页
          router.push(redirect)
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
          // 注册成功，自动登录并跳转到之前尝试访问的页面或首页
          router.push(redirect)
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
      showConfirmPassword,
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
.login-page {
  min-height: 100vh;
  display: flex;
  width: 100%;
}

/* 左侧装饰区域 */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}

.left-content {
  position: relative;
  z-index: 2;
  max-width: 480px;
  color: white;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.brand-logo svg {
  width: 32px;
  height: 32px;
  color: white;
}

.brand-name {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.5px;
}

.brand-desc {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 48px;
  opacity: 0.9;
}

.features {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.15);
  padding: 12px 20px;
  border-radius: 10px;
  backdrop-filter: blur(10px);
  font-size: 14px;
  font-weight: 500;
}

.feature-icon {
  font-size: 20px;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.c1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
}

.c2 {
  width: 300px;
  height: 300px;
  bottom: -50px;
  left: -50px;
}

.c3 {
  width: 200px;
  height: 200px;
  top: 40%;
  right: 20%;
}

/* 右侧登录区域 */
.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #f8fafc;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 20px;
  padding: 48px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 15px;
  color: #64748b;
  margin: 0;
}

/* 标签切换 */
.tab-switcher {
  display: flex;
  gap: 8px;
  background: #f1f5f9;
  padding: 6px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.tab-btn {
  flex: 1;
  padding: 12px 24px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  color: #667eea;
}

.tab-btn.active {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

/* 表单样式 */
.auth-form {
  min-height: 280px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item.half {
  flex: 1;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-label .el-icon {
  color: #667eea;
  font-size: 16px;
}

.form-control {
  width: 100%;
  height: 46px;
  padding: 0 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  color: #1e293b;
  background: white;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-control::placeholder {
  color: #94a3b8;
}

/* 密码输入框 */
.password-wrapper {
  position: relative;
}

.password-wrapper .form-control {
  padding-right: 44px;
}

.eye-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.eye-btn:hover {
  background: #f1f5f9;
  color: #667eea;
}

/* 错误提示 */
.error-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 20px;
}

.error-alert .el-icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* 提交按钮 */
.submit-button {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
  margin-top: 8px;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 底部版权 */
.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
  text-align: center;
}

.login-footer p {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

/* 表单切换动画 */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: all 0.3s ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 响应式设计 */
@media (max-width: 992px) {
  .login-left {
    display: none;
  }
  
  .login-right {
    flex: 1;
    padding: 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .login-box {
    max-width: 400px;
    padding: 32px 24px;
  }
}

@media (max-width: 480px) {
  .login-right {
    padding: 16px;
  }
  
  .login-box {
    padding: 28px 20px;
    border-radius: 16px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 0;
  }
  
  .form-control {
    height: 44px;
  }
}
</style>
