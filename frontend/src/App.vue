<template>
  <div id="app">
    <el-container v-if="isAuthenticated">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <div class="logo">
            <el-icon :size="28" color="#fff"><Document /></el-icon>
            <h1 class="title">科研文献智能分析系统</h1>
          </div>
          <div class="header-right">
            <el-button type="primary" @click="showUploadDialog" class="upload-btn">
              <el-icon><Upload /></el-icon>
              <span>上传论文</span>
            </el-button>

            <!-- 用户信息 -->
            <el-dropdown @command="handleUserCommand" class="user-dropdown">
              <div class="user-info">
                <el-avatar :size="32" :src="userAvatar" class="user-avatar">
                  {{ userInitial }}
                </el-avatar>
                <span class="username">{{ currentUser?.full_name || currentUser?.username }}</span>
                <el-icon color="#fff"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled class="user-info-item">
                    <div class="user-detail">
                      <div class="user-detail-name">{{ currentUser?.full_name || currentUser?.username }}</div>
                      <div class="user-detail-email">{{ currentUser?.email }}</div>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item divided command="profile">
                    <el-icon><User /></el-icon> 个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="logout">
                    <el-icon><SwitchButton /></el-icon> 退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏菜单 -->
        <el-aside width="220px" class="aside">
          <el-menu
            :default-active="currentRoute"
            router
            class="menu"
            background-color="#001529"
            text-color="rgba(255,255,255,0.65)"
            active-text-color="#fff"
            :collapse-transition="false"
          >
            <el-menu-item index="/home">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>

            <el-menu-item index="/analyze">
              <el-icon><Document /></el-icon>
              <span>单篇分析</span>
            </el-menu-item>

            <el-menu-item index="/cluster">
              <el-icon><DataAnalysis /></el-icon>
              <span>聚类分析</span>
            </el-menu-item>

            <el-menu-item index="/files">
              <el-icon><Folder /></el-icon>
              <span>文件管理</span>
            </el-menu-item>

            <el-menu-item index="/gaps">
              <el-icon><Search /></el-icon>
              <span>研究空白</span>
            </el-menu-item>

            <el-menu-item index="/knowledge-graph">
              <el-icon><Share /></el-icon>
              <span>知识图谱</span>
            </el-menu-item>

            <el-menu-item index="/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>AI 助手</span>
            </el-menu-item>

            <el-menu-item index="/workflow">
              <el-icon><Connection /></el-icon>
              <span>链式工作流</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- 未登录时只显示路由内容 -->
    <router-view v-else />

    <!-- 上传对话框 -->
    <UploadDialog ref="uploadDialog" @uploaded="handleFileUploaded" />

    <!-- 进度条 -->
    <ProgressDialog ref="progressDialog" />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Upload, ArrowDown, User, SwitchButton,
  HomeFilled, DataAnalysis, Folder, Search, Share,
  ChatDotRound, Connection
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
    ChatDotRound, Connection
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const isAuthenticated = computed(() => store.getters.isAuthenticated)
    const currentUser = computed(() => store.getters.currentUser)
    const currentRoute = computed(() => route.path)

    // 用户头像（默认使用首字母）
    const userAvatar = computed(() => currentUser.value?.avatar || '')
    const userInitial = computed(() => {
      const name = currentUser.value?.full_name || currentUser.value?.username || ''
      return name.charAt(0).toUpperCase()
    })

    const showUploadDialog = () => {
      store.commit('SHOW_UPLOAD_DIALOG', true)
    }

    const handleFileUploaded = (file) => {
      store.dispatch('fetchFiles')
    }

    // 处理用户下拉菜单命令
    const handleUserCommand = async (command) => {
      switch (command) {
        case 'profile':
          router.push('/profile')
          break
        case 'logout':
          try {
            await ElMessageBox.confirm(
              '确定要退出登录吗？',
              '提示',
              {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
              }
            )
            await store.dispatch('logout')
            ElMessage.success('已退出登录')
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
      userAvatar,
      userInitial,
      showUploadDialog,
      handleFileUploaded,
      handleUserCommand
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}

.el-container {
  height: 100%;
}

/* 顶部导航栏 - 深色简洁风格 */
.header {
  background-color: #001529;
  color: white;
  padding: 0 !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  height: 64px !important;
  line-height: 64px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 20px;
  font-weight: 500;
  margin: 0;
  color: #fff;
  letter-spacing: 0.5px;
}

/* 侧边栏 - 深色菜单 */
.aside {
  background-color: #001529;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.menu {
  border: none;
  height: 100%;
  padding-top: 16px;
}

.menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 0;
  padding-left: 24px !important;
  font-size: 14px;
  transition: all 0.3s;
}

.menu .el-menu-item:hover {
  background-color: #1890ff !important;
  color: #fff !important;
}

.menu .el-menu-item.is-active {
  background-color: #1890ff !important;
  color: #fff !important;
}

.menu .el-menu-item i {
  margin-right: 10px;
  font-size: 16px;
}

/* 主内容区 */
.main {
  background-color: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
  height: calc(100vh - 64px);
}

/* 防止内部元素产生额外滚动条 */
.main > * {
  max-height: none;
}

/* 确保页面内容不会超出视口 */
.el-container {
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏滚动控制 */
.aside {
  overflow-y: auto;
  overflow-x: hidden;
}

/* 头部右侧 */
.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.upload-btn {
  background-color: #1890ff;
  border-color: #1890ff;
  height: 36px;
  padding: 0 20px;
}

.upload-btn:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.upload-btn span {
  margin-left: 6px;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background-color: #1890ff;
  color: white;
  font-weight: 500;
}

.username {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.85);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-info-item {
  padding: 0 !important;
}

.user-detail {
  padding: 12px 16px;
  min-width: 160px;
}

.user-detail-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.user-detail-email {
  font-size: 12px;
  color: #8c8c8c;
}

/* 卡片样式统一 */
.el-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), 0 1px 6px rgba(0, 0, 0, 0.04) !important;
  transition: all 0.3s;
}

.el-card:hover {
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.08), 0 6px 16px rgba(0, 0, 0, 0.06) !important;
}

/* 按钮样式 */
.el-button {
  border-radius: 6px;
  font-weight: 400;
}

.el-button--primary {
  background-color: #1890ff;
  border-color: #1890ff;
}

.el-button--primary:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.el-button--success {
  background-color: #52c41a;
  border-color: #52c41a;
}

.el-button--success:hover {
  background-color: #73d13d;
  border-color: #73d13d;
}

.el-button--danger {
  background-color: #ff4d4f;
  border-color: #ff4d4f;
}

.el-button--danger:hover {
  background-color: #ff7875;
  border-color: #ff7875;
}

/* 表格样式 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table th {
  background-color: #fafafa !important;
  font-weight: 500;
  color: #262626;
}

/* 标签样式 */
.el-tag {
  border-radius: 4px;
  font-weight: 400;
}

/* 输入框样式 */
.el-input__wrapper {
  border-radius: 6px;
}

/* 分页样式 */
.el-pagination {
  justify-content: flex-end;
  margin-top: 16px;
}

/* 空状态样式 */
.el-empty {
  padding: 48px 0;
}

/* 对话框样式 */
.el-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.el-dialog__header {
  border-bottom: 1px solid #f0f0f0;
  padding: 20px 24px;
  margin-right: 0;
}

.el-dialog__title {
  font-weight: 500;
  font-size: 16px;
}

.el-dialog__body {
  padding: 24px;
}

.el-dialog__footer {
  border-top: 1px solid #f0f0f0;
  padding: 16px 24px;
}
</style>
