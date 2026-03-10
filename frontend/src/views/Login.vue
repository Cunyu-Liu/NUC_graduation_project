<template>
  <div class="login-page">
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="brand-mark">
          <div class="brand-logo">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <h1 class="brand-title">Research<span class="accent">Flow</span></h1>
        </div>
        
        <p class="brand-tagline">
          基于大语言模型的螺旋式知识积累与代码生成平台<br/>
          实现从文献分析到代码智能生成的完整闭环
        </p>
        
        <div class="feature-list">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><DocumentChecked /></el-icon>
            </div>
            <span>智能PDF解析</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Cpu /></el-icon>
            </div>
            <span>AI摘要生成</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Search /></el-icon>
            </div>
            <span>研究空白挖掘</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <span>智能代码生成</span>
          </div>
        </div>
      </div>
      
      <!-- 装饰元素 -->
      <div class="decoration">
        <div class="deco-circle c1"></div>
        <div class="deco-circle c2"></div>
        <div class="deco-circle c3"></div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="auth-section">
      <div class="auth-card">
        <div class="auth-header">
          <h2 class="auth-title">{{ isLoginMode ? '欢迎回来' : '创建账号' }}</h2>
          <p class="auth-subtitle">{{ isLoginMode ? '请登录您的账户' : '注册新账户开始使用' }}</p>
        </div>

        <!-- 切换标签 -->
        <div class="auth-tabs">
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

        <!-- 表单 -->
        <transition name="form-slide" mode="out-in">
          <form v-if="isLoginMode" key="login" @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group">
              <label class="form-label">
                <el-icon><User /></el-icon>
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
                <el-icon><Lock /></el-icon>
                密码
              </label>
              <div class="password-field">
                <input
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="请输入密码"
                  required
                />
                <button type="button" class="toggle-password" @click="showPassword = !showPassword">
                  <el-icon v-if="showPassword"><ViewIcon /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div v-if="errorMessage" class="error-message">
              <el-icon><Warning /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>

            <button type="submit" class="submit-btn" :disabled="loading">
              <el-icon v-if="loading" class="spin"><Loading /></el-icon>
              <span>{{ loading ? '登录中...' : '登 录' }}</span>
            </button>
          </form>

          <form v-else key="register" @submit.prevent="handleRegister" class="auth-form">
            <div class="form-row">
              <div class="form-group half">
                <label class="form-label">
                  <el-icon><User /></el-icon>
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
              <div class="form-group half">
                <label class="form-label">
                  <el-icon><Message /></el-icon>
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
            </div>

            <div class="form-group">
              <label class="form-label">
                <el-icon><Lock /></el-icon>
                密码
              </label>
              <div class="password-field">
                <input
                  v-model="registerForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="至少6个字符"
                  minlength="6"
                  required
                />
                <button type="button" class="toggle-password" @click="showPassword = !showPassword">
                  <el-icon v-if="showPassword"><ViewIcon /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                <el-icon><Lock /></el-icon>
                确认密码
              </label>
              <div class="password-field">
                <input
                  v-model="registerForm.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="再次输入密码"
                  minlength="6"
                  required
                />
                <button type="button" class="toggle-password" @click="showConfirmPassword = !showConfirmPassword">
                  <el-icon v-if="showConfirmPassword"><ViewIcon /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </button>
              </div>
            </div>

            <div v-if="errorMessage" class="error-message">
              <el-icon><Warning /></el-icon>
              <span>{{ errorMessage }}</span>
            </div>

            <button type="submit" class="submit-btn" :disabled="loading">
              <el-icon v-if="loading" class="spin"><Loading /></el-icon>
              <span>{{ loading ? '注册中...' : '注 册' }}</span>
            </button>
          </form>
        </transition>

        <div class="auth-footer">
          <p>2025 ResearchFlow | NUC毕业设计</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { 
  User, Lock, Message, View as ViewIcon, Hide, Loading, Warning,
  Document, DocumentChecked, Cpu, Search, Monitor
} from '@element-plus/icons-vue'

export default {
  name: 'Login',
  components: {
    User, Lock, Message, ViewIcon, Hide, Loading, Warning,
    Document, DocumentChecked, Cpu, Search, Monitor
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

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

    const handleLogin = async () => {
      errorMessage.value = ''
      loading.value = true

      try {
        const response = await store.dispatch('login', {
          login_identifier: loginForm.value.identifier,
          password: loginForm.value.password
        })

        if (response.success) {
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

    const handleRegister = async () => {
      errorMessage.value = ''

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
@import '../styles/design-system.css';

.login-page {
  min-height: 100vh;
  display: flex;
  width: 100%;
}

/* ============================================
   BRAND SECTION (Left Side)
   ============================================ */
.brand-section {
  flex: 1;
  background: linear-gradient(145deg, var(--color-primary-800) 0%, var(--color-primary-900) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  position: relative;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
  max-width: 480px;
  color: var(--color-text-inverse);
}

.brand-mark {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.brand-logo {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.brand-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  margin: 0;
  letter-spacing: var(--tracking-tight);
  color: white;
}

.accent {
  color: var(--color-accent-300);
}

.brand-tagline {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-10);
  opacity: 0.85;
  color: rgba(255, 255, 255, 0.9);
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  background: rgba(255, 255, 255, 0.08);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
}

.feature-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
}

/* Decoration */
.decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
}

.c1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -200px;
}

.c2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
}

.c3 {
  width: 300px;
  height: 300px;
  top: 50%;
  right: 10%;
  background: rgba(201, 162, 39, 0.05);
}

/* ============================================
   AUTH SECTION (Right Side)
   ============================================ */
.auth-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  background: var(--color-bg-secondary);
}

.auth-card {
  width: 100%;
  max-width: 440px;
  background: var(--color-bg-primary);
  border-radius: var(--radius-2xl);
  padding: var(--space-10);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border-primary);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.auth-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
  letter-spacing: var(--tracking-tight);
}

.auth-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Tabs */
.auth-tabs {
  display: flex;
  gap: var(--space-2);
  background: var(--color-bg-tertiary);
  padding: var(--space-1);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-8);
}

.tab-btn {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-secondary);
}

.tab-btn.active {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

/* Form */
.auth-form {
  min-height: 280px;
}

.form-row {
  display: flex;
  gap: var(--space-4);
}

.form-group {
  margin-bottom: var(--space-5);
  flex: 1;
}

.form-group.half {
  flex: 1;
}

.form-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.form-label .el-icon {
  color: var(--color-accent-500);
  font-size: var(--text-base);
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  transition: all var(--transition-fast);
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent-400);
  box-shadow: 0 0 0 3px rgba(201, 162, 39, 0.08);
}

.form-input::placeholder {
  color: var(--color-text-muted);
}

.password-field {
  position: relative;
}

.password-field .form-input {
  padding-right: 44px;
}

.toggle-password {
  position: absolute;
  right: var(--space-1);
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.toggle-password:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-light);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
  margin-bottom: var(--space-5);
}

.error-message .el-icon {
  font-size: var(--text-base);
  flex-shrink: 0;
}

/* Submit Button */
.submit-btn {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  background: var(--color-primary-800);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-md);
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-900);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Footer */
.auth-footer {
  margin-top: var(--space-8);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border-secondary);
  text-align: center;
}

.auth-footer p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: 0;
}

/* ============================================
   ANIMATIONS
   ============================================ */
.form-slide-enter-active,
.form-slide-leave-active {
  transition: all var(--transition-slow);
}

.form-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.form-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 1024px) {
  .brand-section {
    padding: var(--space-8);
  }
  
  .feature-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .brand-section {
    display: none;
  }
  
  .auth-section {
    flex: 1;
    padding: var(--space-4);
    background: linear-gradient(145deg, var(--color-primary-800) 0%, var(--color-primary-900) 100%);
  }
  
  .auth-card {
    max-width: 400px;
    padding: var(--space-6);
    border-radius: var(--radius-xl);
  }
  
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}

@media (max-width: 480px) {
  .auth-card {
    padding: var(--space-5);
    border-radius: var(--radius-lg);
  }
  
  .auth-title {
    font-size: var(--text-xl);
  }
  
  .form-input {
    height: 44px;
  }
}
</style>
