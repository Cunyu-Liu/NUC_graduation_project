<template>
  <el-dialog
    v-model="visible"
    title="上传PDF论文"
    width="550px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-upload
      ref="uploadRef"
      class="upload-demo"
      drag
      action="/api/upload/batch"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :on-change="handleChange"
      :http-request="customUpload"
      v-model:file-list="fileList"
      accept=".pdf"
      :limit="10"
      multiple
      :auto-upload="false"
    >
      <el-icon :size="67" color="#409eff"><Upload-filled /></el-icon>
      <div class="el-upload__text">
        将PDF文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          只支持PDF格式，单个文件不超过50MB，最多同时上传10个文件
          <span v-if="fileList.length > 0" style="color: #409eff; margin-left: 10px;">
            已选择 {{ fileList.length }} 个文件
          </span>
        </div>
      </template>
    </el-upload>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="submitUpload"
          :loading="uploading"
          :disabled="fileList.length === 0"
        >
          开始上传 ({{ fileList.length }}个文件)
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'UploadDialog',
  components: {
    UploadFilled
  },
  setup(_, { emit }) {
    const store = useStore()
    const uploadRef = ref(null)
    const fileList = ref([])
    const uploading = ref(false)

    const visible = computed({
      get: () => store.state.showUploadDialog,
      set: (val) => store.commit('SHOW_UPLOAD_DIALOG', val)
    })

    const beforeUpload = (file) => {
      const isPDF = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
      const isLt50M = file.size / 1024 / 1024 < 50

      if (!isPDF) {
        ElMessage.error('只能上传PDF文件!')
        return false
      }
      if (!isLt50M) {
        ElMessage.error('文件大小不能超过50MB!')
        return false
      }
      return true
    }

    const customUpload = async (options) => {
      // 这个函数不会被直接调用，因为我们使用批量上传
      console.log('customUpload', options)
    }

    // 处理文件列表变化
    const handleChange = (file, files) => {
      console.log('[DEBUG] 文件列表变化:', files.length, '个文件')
      fileList.value = files
    }

    // 处理对话框关闭
    const handleClose = () => {
      fileList.value = []
    }

    const submitUpload = async () => {
      if (fileList.value.length === 0) {
        ElMessage.warning('请先选择要上传的文件')
        return
      }

      uploading.value = true

      try {
        const formData = new FormData()

        // 添加所有文件到FormData
        fileList.value.forEach((file) => {
          formData.append('files', file.raw)
        })

        console.log(`[DEBUG] 开始批量上传 ${fileList.value.length} 个文件`)

        const response = await axios.post('/api/upload/batch', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 300000 // 5分钟超时
        })

        console.log('[DEBUG] 批量上传响应:', response.data)

        if (response.data.success) {
          const result = response.data.data
          const successCount = result.success?.length || 0
          const failCount = result.failed?.length || 0

          if (successCount > 0) {
            ElMessage.success({
              message: `成功上传 ${successCount} 个文件${failCount > 0 ? `，${failCount}个失败` : ''}`,
              duration: 5000,
              showClose: true
            })

            // 通知父组件刷新文件列表
            emit('uploaded', result.success)
          }

          if (failCount > 0) {
            const failNames = result.failed.map(f => f.filename).join(', ')
            ElMessage.error({
              message: `以下文件上传失败: ${failNames}`,
              duration: 8000,
              showClose: true
            })
          }

          // 清空文件列表
          fileList.value = []
          visible.value = false
        } else {
          ElMessage.error({
            message: response.data.error || '上传失败',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        console.error('[ERROR] 批量上传失败:', error)

        let errorMsg = '上传失败'
        if (error.response?.data?.error) {
          errorMsg = error.response.data.error
        } else if (error.message) {
          errorMsg = error.message
        }

        ElMessage.error({
          message: errorMsg,
          duration: 5000,
          showClose: true
        })
      } finally {
        uploading.value = false
      }
    }

    const handleSuccess = (response, file) => {
      // 批量上传不使用这个方法
      console.log('handleSuccess', response, file)
    }

    const handleError = (error) => {
      console.error('上传错误:', error)

      let errorMsg = '上传失败'

      if (error.message) {
        if (error.message.includes('403') || error.message.includes('CORS')) {
          errorMsg = '权限错误：请检查后端CORS配置'
        } else if (error.message.includes('Network Error')) {
          errorMsg = '网络错误：请检查后端服务是否启动（端口5001）'
        } else if (error.message.includes('timeout')) {
          errorMsg = '上传超时：文件可能过大，请尝试更小的文件'
        } else if (error.message.includes('413')) {
          errorMsg = '文件过大：单个文件不能超过50MB'
        } else {
          errorMsg = `上传失败: ${error.message}`
        }
      }

      ElMessage.error({
        message: errorMsg,
        duration: 5000,
        showClose: true
      })
    }

    return {
      visible,
      uploadRef,
      fileList,
      uploading,
      beforeUpload,
      customUpload,
      handleChange,
      handleClose,
      submitUpload,
      handleSuccess,
      handleError
    }
  }
}
</script>

<style scoped>
.upload-demo {
  text-align: center;
}

.el-icon-upload {
  font-size: 67px;
  color: #409eff;
  margin: 20px 0;
}

.el-upload__text {
  font-size: 14px;
  color: #606266;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
