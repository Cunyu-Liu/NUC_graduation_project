<template>
  <div id="app">
    <el-container v-if="isAuthenticated" class="app-container">
      <!-- 顶部导航栏 - Premium minimal design -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="brand">
            <div class="brand-icon">
              <el-icon :size="24"><Document /></el-icon>
            </div>
            <span class="brand-text">Research<span class="brand-accent">Flow</span></span>
          </div>
          
          <div class="header-actions">
            <button class="action-btn primary" @click="showUploadDialog">
              <el-icon><Upload /></el-icon>
              <span>上传论文</span>
            </button>
            
            <el-dropdown @command="handleUserCommand" trigger="click">
              <button class="user-menu-trigger">
                <el-avatar :size="32" :src="userAvatar" class="user-avatar">
                  {{ userInitial }}
                </el-avatar>
                <span class="user-name">{{ currentUser?.full_name || currentUser?.username }}</span>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu class="user-dropdown-menu">
                  <div class="user-dropdown-header">
                    <div class="user-dropdown-name">{{ currentUser?.full_name || currentUser?.username }}</div>
                    <div class="user-dropdown-email">{{ currentUser?.email }}</div>
                  </div>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    <span>个人信息</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout" class="logout-item">
                    <el-icon><SwitchButton /></el-icon>
                    <span>退出登录</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-container class="main-container">
        <!-- 侧边栏 - Clean minimal navigation -->
        <el-aside :width="isSidebarCollapsed ? '64px' : '220px'" class="app-sidebar">
          <div class="sidebar-header">
            <button class="collapse-btn" @click="toggleSidebar">
              <el-icon><Fold v-if="!isSidebarCollapsed" /><Expand v-else /></el-icon>
            </button>
          </div>
          
          <el-menu
            :default-active="currentRoute"
            router
            class="sidebar-menu"
            :collapse="isSidebarCollapsed"
            :collapse-transition="false"
          >
            <el-menu-item index="/home" class="nav-item">
              <el-icon><HomeFilled /></el-icon>
              <template #title>
                <span class="nav-label">首页</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/analyze" class="nav-item">
              <el-icon><Document /></el-icon>
              <template #title>
                <span class="nav-label">单篇分析</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/cluster" class="nav-item">
              <el-icon><DataAnalysis /></el-icon>
              <template #title>
                <span class="nav-label">聚类分析</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/files" class="nav-item">
              <el-icon><Folder /></el-icon>
              <template #title>
                <span class="nav-label">文件管理</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/gaps" class="nav-item">
              <el-icon><Search /></el-icon>
              <template #title>
                <span class="nav-label">研究空白</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/knowledge-graph" class="nav-item">
              <el-icon><Share /></el-icon>
              <template #title>
                <span class="nav-label">知识图谱</span>
              </template>
            </el-menu-item>

            <div class="nav-divider"></div>

            <el-menu-item index="/chat" class="nav-item">
              <el-icon><ChatDotRound /></el-icon>
              <template #title>
                <span class="nav-label">AI 助手</span>
              </template>
            </el-menu-item>

            <el-menu-item index="/workflow" class="nav-item">
              <el-icon><Connection /></el-icon>
              <template #title>
                <span class="nav-label">链式工作流</span>
              </template>
            </el-menu-item>
          </el-menu>
          
          <div v-if="!isSidebarCollapsed" class="sidebar-footer">
            <div class="sidebar-version">v4.2.0</div>
          </div>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>

    <!-- 未登录时显示路由内容 -->
    <router-view v-else />

    <!-- 全局对话框 -->
    <UploadDialog ref="uploadDialog" @uploaded="handleFileUploaded" />
    <ProgressDialog ref="progressDialog" />
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Upload, ArrowDown, User, SwitchButton,
  HomeFilled, DataAnalysis, Folder, Search, Share,
  ChatDotRound, Connection, Fold, Expand
} from '@element-plus/icons-vue'
import UploadDialog from '@/components/UploadDialog.vue'
import ProgressDialog from '@/components/ProgressDialog.vue'

export default {
  name: 'App',
  components: {
    UploadDialog,
    ProgressDialog,
    Document, Upload, ArrowDown, User, SwitchButton,
    HomeFilled, DataAnalysis, Folder, Search, Share,
    ChatDotRound, Connection, Fold, Expand
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    const isSidebarCollapsed = ref(false)

    const isAuthenticated = computed(() => store.getters.isAuthenticated)
    const currentUser = computed(() => store.getters.currentUser)
    const currentRoute = computed(() => route.path)

    const userAvatar = computed(() => currentUser.value?.avatar || '')
    const userInitial = computed(() => {
      const name = currentUser.value?.full_name || currentUser.value?.username || ''
      return name.charAt(0).toUpperCase()
    })

    const toggleSidebar = () => {
      isSidebarCollapsed.value = !isSidebarCollapsed.value
    }

    const showUploadDialog = () => {
      store.commit('SHOW_UPLOAD_DIALOG', true)
    }

    const handleFileUploaded = () => {
      store.dispatch('fetchFiles')
    }

    const handleUserCommand = async (command) => {
      switch (command) {
        case 'profile':
          router.push('/profile')
          break
        case 'logout':
          try {
            await ElMessageBox.confirm(
              '确定要退出登录吗？',
              '退出确认',
              {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                customClass: 'premium-message-box'
              }
            )
            await store.dispatch('logout')
            ElMessage.success({ message: '已退出登录', customClass: 'premium-message' })
            router.push('/login')
          } catch (error) {
            // 用户取消
          }
          break
      }
    }

    return {
      isAuthenticated,
      currentUser,
      currentRoute,
      isSidebarCollapsed,
      userAvatar,
      userInitial,
      toggleSidebar,
      showUploadDialog,
      handleFileUploaded,
      handleUserCommand
    }
  }
}
</script>

<style>
/* Import Design System */
@import './styles/design-system.css';

/* ============================================
   APP CONTAINER
   ============================================ */
#app {
  font-family: var(--font-family-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  background: var(--color-bg-secondary);
}

.app-container {
  height: 100vh;
  overflow: hidden;
}

/* ============================================
   HEADER STYLES
   ============================================ */
.app-header {
  height: var(--header-height) !important;
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border-primary);
  padding: 0 !important;
  position: relative;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 var(--space-6);
  max-width: 1920px;
  margin: 0 auto;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.brand-icon {
  width: 40px;
  height: 40px;
  background: var(--color-primary-800);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-inverse);
}

.brand-text {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  letter-spacing: var(--tracking-tight);
}

.brand-accent {
  color: var(--color-accent-500);
  font-weight: var(--font-bold);
}

/* Header Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: transparent;
  color: var(--color-text-secondary);
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.action-btn.primary {
  background: var(--color-primary-800);
  color: var(--color-text-inverse);
}

.action-btn.primary:hover {
  background: var(--color-primary-900);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* User Menu */
.user-menu-trigger {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) var(--space-2) var(--space-1) var(--space-1);
  background: transparent;
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-menu-trigger:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-focus);
}

.user-avatar {
  background: var(--color-accent-500);
  color: var(--color-text-inverse);
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* User Dropdown Menu */
.user-dropdown-menu {
  padding: var(--space-2) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-lg) !important;
  border: 1px solid var(--color-border-primary) !important;
  min-width: 200px !important;
}

.user-dropdown-header {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-secondary);
  margin-bottom: var(--space-1);
}

.user-dropdown-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.user-dropdown-email {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

.user-dropdown-menu .el-dropdown-menu__item {
  padding: var(--space-2) var(--space-3) !important;
  border-radius: var(--radius-md);
  margin: var(--space-1) 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.user-dropdown-menu .el-dropdown-menu__item:hover {
  background: var(--color-bg-tertiary) !important;
  color: var(--color-text-primary) !important;
}

.logout-item {
  color: var(--color-error) !important;
}

/* ============================================
   SIDEBAR STYLES
   ============================================ */
.app-sidebar {
  background: var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border-primary);
  transition: width var(--transition-base);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: var(--space-4);
  display: flex;
  justify-content: flex-end;
  border-bottom: 1px solid var(--color-border-secondary);
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

/* Sidebar Menu */
.sidebar-menu {
  border: none !important;
  background: transparent !important;
  flex: 1;
  padding: var(--space-3);
}

.sidebar-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  margin: var(--space-1) 0;
  padding: 0 var(--space-3) !important;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary) !important;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
}

.sidebar-menu .el-menu-item:hover {
  background: var(--color-bg-tertiary) !important;
  color: var(--color-text-primary) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--color-primary-800) !important;
  color: var(--color-text-inverse) !important;
  font-weight: var(--font-semibold);
}

.sidebar-menu .el-icon {
  font-size: 18px;
  margin-right: var(--space-3);
}

.nav-label {
  letter-spacing: var(--tracking-wide);
}

.nav-divider {
  height: 1px;
  background: var(--color-border-primary);
  margin: var(--space-3) var(--space-4);
}

.sidebar-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-secondary);
}

.sidebar-version {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
}

/* ============================================
   MAIN CONTENT AREA
   ============================================ */
.main-container {
  height: calc(100vh - var(--header-height));
}

.app-main {
  background: var(--color-bg-secondary);
  padding: var(--space-6);
  overflow-y: auto;
  overflow-x: hidden;
}

/* ============================================
   PAGE TRANSITIONS
   ============================================ */
.page-enter-active,
.page-leave-active {
  transition: all var(--transition-slow);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ============================================
   ELEMENT PLUS OVERRIDES
   ============================================ */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--color-border-primary) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: box-shadow var(--transition-base) !important;
}

.el-card:hover {
  box-shadow: var(--shadow-md) !important;
}

.el-button {
  border-radius: var(--radius-md) !important;
  font-weight: var(--font-medium) !important;
  transition: all var(--transition-fast) !important;
}

.el-button--primary {
  background: var(--color-primary-800) !important;
  border-color: var(--color-primary-800) !important;
}

.el-button--primary:hover {
  background: var(--color-primary-900) !important;
  border-color: var(--color-primary-900) !important;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.el-input__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: 0 0 0 1px var(--color-border-primary) inset !important;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--color-primary-400) inset !important;
}

.el-table {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.el-table th {
  background: var(--color-bg-secondary) !important;
  font-weight: var(--font-semibold) !important;
  color: var(--color-text-secondary) !important;
  text-transform: uppercase;
  font-size: var(--text-xs);
  letter-spacing: var(--tracking-wide);
}

.el-tag {
  border-radius: var(--radius-full) !important;
  font-weight: var(--font-medium) !important;
}

.el-dialog {
  border-radius: var(--radius-xl) !important;
  overflow: hidden;
  box-shadow: var(--shadow-xl) !important;
}

.el-dialog__header {
  padding: var(--space-5) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-primary) !important;
  margin-right: 0 !important;
}

.el-dialog__title {
  font-weight: var(--font-semibold) !important;
  font-size: var(--text-lg) !important;
  color: var(--color-text-primary) !important;
}

.el-dialog__body {
  padding: var(--space-6) !important;
}

.el-dialog__footer {
  padding: var(--space-4) var(--space-6) !important;
  border-top: 1px solid var(--color-border-primary) !important;
}

/* Message Box */
.premium-message-box .el-message-box__title {
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.premium-message-box .el-message-box__content {
  color: var(--color-text-secondary);
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 768px) {
  .header-content {
    padding: 0 var(--space-4);
  }
  
  .brand-text {
    display: none;
  }
  
  .user-name {
    display: none;
  }
  
  .action-btn span {
    display: none;
  }
  
  .app-sidebar {
    position: fixed;
    left: 0;
    top: var(--header-height);
    bottom: 0;
    z-index: 99;
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }
  
  .app-sidebar.is-open {
    transform: translateX(0);
  }
  
  .app-main {
    padding: var(--space-4);
  }
}
</style>
