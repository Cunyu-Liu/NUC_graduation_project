<template>
  <div id="app">
    <el-container v-if="isAuthenticated">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="title">
            <i class="el-icon-document"></i>
            科研文献智能分析系统
          </h1>
          <div class="header-right">
            <el-badge :value="uploadedCount" class="item">
              <el-button type="primary" @click="showUploadDialog">
                <i class="el-icon-upload"></i> 上传论文
              </el-button>
            </el-badge>

            <!-- 用户信息 -->
            <el-dropdown @command="handleUserCommand" class="user-dropdown">
              <span class="user-info">
                <el-avatar :size="32" :src="userAvatar" class="user-avatar">
                  {{ userInitial }}
                </el-avatar>
                <span class="username">{{ currentUser?.full_name || currentUser?.username }}</span>
                <i class="el-icon-arrow-down el-icon--right"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled class="user-info-item">
                    <div class="user-detail">
                      <div class="user-detail-name">{{ currentUser?.full_name || currentUser?.username }}</div>
                      <div class="user-detail-email">{{ currentUser?.email }}</div>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item divided command="profile">
                    <i class="el-icon-user"></i> 个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="logout">
                    <i class="el-icon-switch-button"></i> 退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏菜单 -->
        <el-aside width="200px" class="aside">
          <el-menu
            :default-active="currentRoute"
            router
            class="menu"
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409eff"
          >
            <el-menu-item index="/home">
              <i class="el-icon-house"></i>
              <span>首页</span>
            </el-menu-item>

            <el-menu-item index="/analyze">
              <i class="el-icon-document"></i>
              <span>单篇分析</span>
            </el-menu-item>

            <el-menu-item index="/cluster">
              <i class="el-icon-data-analysis"></i>
              <span>聚类分析</span>
            </el-menu-item>

            <el-menu-item index="/files">
              <i class="el-icon-folder"></i>
              <span>文件管理</span>
            </el-menu-item>

            <el-menu-item index="/gaps">
              <i class="el-icon-search"></i>
              <span>研究空白</span>
            </el-menu-item>

            <el-menu-item index="/knowledge-graph">
              <i class="el-icon-share"></i>
              <span>知识图谱</span>
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
import UploadDialog from '@/components/UploadDialog.vue'
import ProgressDialog from '@/components/ProgressDialog.vue'

export default {
  name: 'App',
  components: {
    UploadDialog,
    ProgressDialog
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const isAuthenticated = computed(() => store.getters.isAuthenticated)
    const currentUser = computed(() => store.getters.currentUser)
    const uploadedCount = computed(() => store.state.files.length)
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
          // 可以跳转到个人信息页面或显示对话框
          ElMessage.info('个人信息功能开发中')
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

            // 退出登录
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
      uploadedCount,
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
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}

.el-container {
  height: 100%;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: 60px !important;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 30px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
}

.title i {
  margin-right: 10px;
}

.aside {
  background-color: #304156;
  overflow-x: hidden;
}

.menu {
  border: none;
  height: 100%;
}

.menu .el-menu-item {
  min-height: 50px;
  line-height: 50px;
}

.menu .el-menu-item i {
  margin-right: 8px;
}

.main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 用户相关样式 */
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-dropdown {
  margin-left: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  font-weight: 600;
}

.username {
  margin: 0 8px;
  font-size: 15px;
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-info-item {
  padding: 0 !important;
}

.user-detail {
  padding: 10px 15px;
}

.user-detail-name {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.user-detail-email {
  font-size: 13px;
  color: #718096;
}
</style>
