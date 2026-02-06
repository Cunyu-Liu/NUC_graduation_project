<template>
  <div class="files">
    <div class="page-header">
      <h2>论文管理</h2>
      <div class="header-stats">
        <el-tag>总计: {{ files.length }} 篇</el-tag>
        <el-tag type="success" v-if="selectedFiles.length > 0">
          已选: {{ selectedFiles.length }} 篇
        </el-tag>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <el-card class="batch-actions-card" v-if="selectedFiles.length > 0">
      <div class="batch-actions">
        <div class="batch-info">
          <el-icon class="batch-icon"><Check /></el-icon>
          <span>已选择 <strong>{{ selectedFiles.length }}</strong> 篇论文</span>
        </div>

        <el-divider direction="vertical" />

        <div class="batch-buttons">
          <el-button
            type="primary"
            @click="batchAnalyze"
            :disabled="selectedFiles.length === 0"
            icon="VideoPlay"
          >
            批量分析 ({{ selectedFiles.length }})
          </el-button>

          <el-button
            type="success"
            @click="batchCluster"
            :disabled="selectedFiles.length < 2"
            icon="DataAnalysis"
          >
            聚类分析
          </el-button>

          <el-button
            @click="batchExport"
            :disabled="selectedFiles.length === 0"
            icon="Download"
          >
            批量导出
          </el-button>

          <el-button
            type="danger"
            @click="batchDelete"
            :disabled="selectedFiles.length === 0"
            icon="Delete"
          >
            批量删除
          </el-button>

          <el-button @click="clearSelection" icon="Close">
            取消选择
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 论文列表 -->
    <el-card class="table-card">
      <!-- 工具栏 -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <el-button @click="toggleSelectAll" icon="List">
            {{ allSelected ? '取消全选' : '全选' }}
          </el-button>
          <el-button @click="refreshFiles" icon="Refresh">刷新</el-button>
        </div>

        <div class="toolbar-right">
          <el-input
            v-model="searchText"
            placeholder="搜索论文标题、作者、期刊..."
            clearable
            style="width: 300px"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <el-table
        ref="tableRef"
        :data="filteredFiles"
        style="width: 100%"
        :row-style="{ height: '60px' }"
        @selection-change="handleSelectionChange"
        :row-key="getRowKey"
      >
        <el-table-column type="selection" width="55" :reserve-selection="true" />

        <el-table-column prop="title" label="论文标题" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tooltip :content="row.title || '无标题'" placement="top" effect="dark">
              <div class="table-cell-text" @click="viewFileDetail(row)">
                {{ row.title || '无标题' }}
              </div>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="year" label="年份" width="100" sortable>
          <template #default="{ row }">
            <el-tag v-if="row.year" size="small">{{ row.year }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="venue" label="发表期刊/会议" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tooltip :content="row.venue || '未知'" placement="top" effect="dark">
              <div class="table-cell-text">{{ row.venue || '未知' }}</div>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="上传时间" :formatter="formatTime" width="180" sortable />

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.analyzed" type="success" size="small">已分析</el-tag>
            <el-tag v-else type="info" size="small">未分析</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button-group>
              <el-button size="small" @click="analyzeFile(scope.row)" icon="VideoPlay">
                分析
              </el-button>
              <el-button size="small" @click="editFile(scope.row)" icon="Edit">
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteFile(scope.row)"
                icon="Delete"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredFiles.length === 0" description="暂无论文，请先上传PDF文件" />
    </el-card>

    <!-- 论文详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentFile?.title || '论文详情'"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentFile">
        <el-descriptions-item label="论文ID">{{ currentFile.id }}</el-descriptions-item>
        <el-descriptions-item label="年份">{{ currentFile.year || '-' }}</el-descriptions-item>
        <el-descriptions-item label="期刊/会议" :span="2">
          {{ currentFile.venue || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="作者">
          {{ currentFile.authors?.join(', ') || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="上传时间">
          {{ formatTime(null, null, currentFile.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="文件路径" :span="2">
          {{ currentFile.pdf_path || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="分析状态" :span="2">
          <el-tag :type="currentFile.analyzed ? 'success' : 'info'">
            {{ currentFile.analyzed ? '已分析' : '未分析' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="analyzeFile(currentFile)">分析此论文</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑论文信息"
      width="600px"
    >
      <el-form :model="editForm" label-width="100px" ref="editFormRef">
        <el-form-item label="论文标题">
          <el-input v-model="editForm.title" placeholder="请输入论文标题" />
        </el-form-item>
        <el-form-item label="年份">
          <el-input-number v-model="editForm.year" :min="1900" :max="2100" />
        </el-form-item>
        <el-form-item label="期刊/会议">
          <el-input v-model="editForm.venue" placeholder="请输入期刊或会议名称" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input
            v-model="editForm.authorsStr"
            type="textarea"
            :rows="3"
            placeholder="多个作者用逗号分隔"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Search, VideoPlay, DataAnalysis, Download, Delete, Edit, Refresh, List, Close } from '@element-plus/icons-vue'
import api from '@/api'

const store = useStore()
const router = useRouter()

// 响应式数据
const tableRef = ref(null)
const selectedFiles = ref([])
const searchText = ref('')
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const currentFile = ref(null)
const saving = ref(false)

const editForm = ref({
  id: null,
  title: '',
  year: null,
  venue: '',
  authorsStr: ''
})

// 计算属性
const files = computed(() => store.state.files || [])

const filteredFiles = computed(() => {
  if (!searchText.value) return files.value

  const search = searchText.value.toLowerCase()
  return files.value.filter(file => {
    return (
      (file.title?.toLowerCase().includes(search)) ||
      (file.venue?.toLowerCase().includes(search)) ||
      (file.authors?.some(a => a.toLowerCase().includes(search))) ||
      (file.year?.toString().includes(search))
    )
  })
})

const allSelected = computed(() => {
  return selectedFiles.value.length === filteredFiles.value.length && filteredFiles.value.length > 0
})

// 方法
const getRowKey = (row) => row.id

const formatTime = (row, column, time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    tableRef.value?.clearSelection()
  } else {
    filteredFiles.value.forEach(row => {
      tableRef.value?.toggleRowSelection(row, true)
    })
  }
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const handleSearch = () => {
  // 搜索时清空选择
  clearSelection()
}

const refreshFiles = () => {
  store.dispatch('fetchFiles')
  ElMessage.success('刷新成功')
}

const viewFileDetail = (file) => {
  currentFile.value = file
  detailDialogVisible.value = true
}

const analyzeFile = (paper) => {
  if (paper) {
    router.push({ path: '/analyze', query: { paperId: paper.id } })

    // 添加路由守卫，从分析页面返回时刷新列表
    const unwatch = router.afterEach((to, from) => {
      if (from.path === '/analyze' && to.path === '/files') {
        // 延迟刷新，确保数据库已更新
        setTimeout(() => {
          store.dispatch('fetchFiles')
        }, 500)
        unwatch()
      }
    })
  }
}

const editFile = (file) => {
  currentFile.value = file
  // 确保年份是有效的整数，避免null或undefined导致的问题
  const yearValue = file.year ? parseInt(file.year) : null
  editForm.value = {
    id: file.id,
    title: file.title || '',
    year: yearValue && yearValue > 1900 ? yearValue : null,
    venue: file.venue || '',
    authorsStr: file.authors?.join(', ') || ''
  }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  try {
    saving.value = true

    // 构建更新数据，只包含 Paper 模型支持的字段
    const updateData = {}
    
    // 标题必填
    if (editForm.value.title !== undefined) {
      updateData.title = editForm.value.title
    }
    
    // 年份处理：确保是有效的整数或null，不能是1900
    if (editForm.value.year !== undefined && editForm.value.year !== null) {
      const yearNum = parseInt(editForm.value.year)
      // 只接受合理的年份范围
      if (yearNum >= 1950 && yearNum <= 2100) {
        updateData.year = yearNum
      } else {
        updateData.year = null
      }
    } else {
      updateData.year = null
    }
    
    // 期刊/会议
    if (editForm.value.venue !== undefined) {
      updateData.venue = editForm.value.venue
    }

    const response = await api.updatePaper(editForm.value.id, updateData)

    if (response.success) {
      ElMessage.success('保存成功')
      editDialogVisible.value = false
      await store.dispatch('fetchFiles')
    } else {
      ElMessage.error(response.error || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const deleteFile = async (paper) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除论文 "${paper.title || '未命名'}" 吗？此操作不可恢复！`,
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
      // 清空选择
      if (selectedFiles.value.find(f => f.id === paper.id)) {
        clearSelection()
      }
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 用户取消
  }
}

// 批量操作
const batchAnalyze = () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要分析的论文')
    return
  }

  ElMessageBox.confirm(
    `将对 ${selectedFiles.value.length} 篇论文依次进行分析，是否继续？`,
    '批量分析确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    // 跳转到分析页面，传递第一篇论文ID
    const firstPaper = selectedFiles.value[0]
    router.push({
      path: '/analyze',
      query: {
        paperId: firstPaper.id,
        batch: 'true',
        count: selectedFiles.value.length
      }
    })
    ElMessage.info('将从第一篇论文开始分析，完成后请继续分析其他论文')
  }).catch(() => {
    // 用户取消
  })
}

const batchCluster = () => {
  if (selectedFiles.value.length < 2) {
    ElMessage.warning('请至少选择2篇论文进行聚类分析')
    return
  }

  // 跳转到聚类页面
  router.push({
    path: '/cluster',
    state: {
      selectedPapers: selectedFiles.value.map(f => f.id)
    }
  })
  ElMessage.success(`已选择 ${selectedFiles.value.length} 篇论文，正在跳转到聚类页面`)
}

const batchExport = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要导出的论文')
    return
  }

  try {
    // 生成CSV格式
    const headers = ['ID', '标题', '年份', '期刊/会议', '作者', '上传时间']
    const rows = selectedFiles.value.map(file => [
      file.id,
      file.title || '',
      file.year || '',
      file.venue || '',
      file.authors?.join('; ') || '',
      formatTime(null, null, file.created_at)
    ])

    const csv = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n')

    // 下载文件
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `papers_export_${new Date().getTime()}.csv`
    a.click()
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${selectedFiles.value.length} 篇论文信息`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + error.message)
  }
}

const batchDelete = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要删除的论文')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.length} 篇论文吗？此操作不可恢复！`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    // 调用批量删除API
    const paperIds = selectedFiles.value.map(f => f.id)
    const response = await api.batchDeletePapers(paperIds)

    if (response.success) {
      ElMessage.success(`成功删除 ${response.data.deleted_count || paperIds.length} 篇论文`)
      clearSelection()
      await store.dispatch('fetchFiles')
    } else {
      ElMessage.error(response.error || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 生命周期
onMounted(() => {
  store.dispatch('fetchFiles')
})
</script>

<style scoped>
.files {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.header-stats {
  display: flex;
  gap: 10px;
}

.batch-actions-card {
  margin-bottom: 20px;
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.batch-actions-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 20px;
  color: #262626;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
}

.batch-icon {
  font-size: 20px;
  color: #1890ff;
}

.batch-buttons {
  display: flex;
  gap: 10px;
  flex: 1;
}

.table-card {
  margin-bottom: 20px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 10px;
}

.table-cell-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  color: #303133;
}

.table-cell-text:hover {
  color: #409EFF;
}

:deep(.el-button-group) {
  display: flex;
}

:deep(.el-divider--vertical) {
  height: 40px;
  border-color: rgba(255, 255, 255, 0.3);
}
</style>
