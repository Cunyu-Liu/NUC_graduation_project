<template>
  <div class="files">
    <h2>论文管理</h2>

    <el-card>
      <el-table :data="files" style="width: 100%">
        <el-table-column prop="title" label="论文标题" min-width="300" />
        <el-table-column prop="year" label="年份" width="100" />
        <el-table-column prop="venue" label="发表期刊/会议" width="200" />
        <el-table-column prop="created_at" label="上传时间" :formatter="formatTime" width="180" />
        <el-table-column label="操作" width="200">
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

      <el-empty v-if="files.length === 0" description="暂无论文，请先上传PDF文件" />
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

    const formatTime = (row, column, time) => {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }

    const analyzeFile = (paper) => {
      router.push({ path: '/analyze', query: { paperId: paper.id } })
    }

    const deleteFile = async (paper) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除论文 "${paper.title || '未命名'}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        const success = await store.dispatch('deleteFile', paper.id)
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
