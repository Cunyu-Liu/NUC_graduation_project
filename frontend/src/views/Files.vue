<template>
  <div class="files">
    <h2>文件管理</h2>

    <el-card>
      <el-table :data="files" style="width: 100%">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="size" label="大小" :formatter="formatSize" />
        <el-table-column prop="uploadedAt" label="上传时间" :formatter="formatTime" />
        <el-table-column label="操作" width="300">
          <template #default="scope">
            <el-button size="small" @click="analyzeFile(scope.row)">
              <i class="el-icon-video-play"></i> 分析
            </el-button>
            <el-button size="small" type="danger" @click="deleteFile(scope.row)">
              <i class="el-icon-delete"></i> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="files.length === 0" description="暂无文件，请先上传" />
    </el-card>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Files',
  setup() {
    const store = useStore()
    const router = useRouter()

    const files = computed(() => store.state.files)

    const formatSize = (row, column, size) => {
      return (size / 1024 / 1024).toFixed(2) + ' MB'
    }

    const formatTime = (row, column, time) => {
      return new Date(time).toLocaleString('zh-CN')
    }

    const analyzeFile = (file) => {
      router.push({ path: '/analyze', query: { file: file.filename } })
    }

    const deleteFile = async (file) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除文件 "${file.filename}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        const success = await store.dispatch('deleteFile', file.filename)
        if (success) {
          ElMessage.success('删除成功')
        } else {
          ElMessage.error('删除失败')
        }
      } catch {
        // 用户取消
      }
    }

    onMounted(() => {
      store.dispatch('fetchFiles')
    })

    return {
      files,
      formatSize,
      formatTime,
      analyzeFile,
      deleteFile
    }
  }
}
</script>

<style scoped>
.files {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}
</style>
