<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="title">
            <i class="el-icon-document"></i>
            科研文献摘要提取系统
          </h1>
          <div class="header-right">
            <el-badge :value="uploadedCount" class="item">
              <el-button type="primary" @click="showUploadDialog">
                <i class="el-icon-upload"></i> 上传论文
              </el-button>
            </el-badge>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 上传对话框 -->
    <UploadDialog ref="uploadDialog" @uploaded="handleFileUploaded" />

    <!-- 进度条 -->
    <ProgressDialog ref="progressDialog" />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
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

    const uploadedCount = computed(() => store.state.files.length)

    const showUploadDialog = () => {
      store.commit('SHOW_UPLOAD_DIALOG', true)
    }

    const handleFileUploaded = (file) => {
      store.dispatch('fetchFiles')
    }

    return {
      uploadedCount,
      showUploadDialog,
      handleFileUploaded
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

.main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
