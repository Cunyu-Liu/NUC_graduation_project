<template>
  <el-dialog
    v-model="visible"
    title="上传PDF论文"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-upload
      class="upload-demo"
      drag
    action="/api/upload"
    :on-success="handleSuccess"
    :on-error="handleError"
    :before-upload="beforeUpload"
    :file-list="fileList"
    accept=".pdf"
    :limit="5"
    multiple
    >
      <i class="el-icon-upload"></i>
      <div class="el-upload__text">
        将PDF文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          只支持PDF格式，单个文件不超过50MB
        </div>
      </template>
    </el-upload>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'

export default {
  name: 'UploadDialog',
  setup(_, { emit }) {
    const store = useStore()
    const fileList = ref([])

    const visible = computed({
      get: () => store.state.showUploadDialog,
      set: (val) => store.commit('SHOW_UPLOAD_DIALOG', val)
    })

    const beforeUpload = (file) => {
      const isPDF = file.type === 'application/pdf'
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

    const handleSuccess = (response, file) => {
      if (response.success) {
        ElMessage.success(`${file.name} 上传成功`)
        emit('uploaded', response.data)
        fileList.value = []
      } else {
        ElMessage.error(response.error || '上传失败')
      }
    }

    const handleError = (error) => {
      console.error('上传错误:', error)
      if (error.message && error.message.includes('403')) {
        ElMessage.error('上传失败：权限错误，请检查后端CORS配置')
      } else if (error.message && error.message.includes('Network Error')) {
        ElMessage.error('网络错误：请检查后端服务是否启动（端口5001）')
      } else {
        ElMessage.error('上传失败: ' + (error.message || '未知错误'))
      }
    }

    return {
      visible,
      fileList,
      beforeUpload,
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
</style>
