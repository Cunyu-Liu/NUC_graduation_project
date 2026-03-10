<template>
  <div class="files-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-title">
        <h1>论文管理</h1>
        <p>管理您的论文库，支持批量操作与高级筛选</p>
      </div>
      <div class="header-meta">
        <div class="meta-item">
          <span class="meta-value">{{ files.length }}</span>
          <span class="meta-label">篇论文</span>
        </div>
      </div>
    </div>

    <!-- Batch Actions Bar -->
    <transition name="slide-down">
      <div v-if="selectedFiles.length > 0" class="batch-bar">
        <div class="batch-info">
          <el-icon><Check /></el-icon>
          <span>已选择 <strong>{{ selectedFiles.length }}</strong> 篇论文</span>
        </div>
        <div class="batch-actions">
          <button class="action-btn" @click="batchAnalyze">
            <el-icon><VideoPlay /></el-icon>
            <span>批量分析</span>
          </button>
          <button class="action-btn" @click="batchCluster" :disabled="selectedFiles.length < 2">
            <el-icon><DataAnalysis /></el-icon>
            <span>聚类分析</span>
          </button>
          <button class="action-btn secondary" @click="batchExport">
            <el-icon><Download /></el-icon>
            <span>导出</span>
          </button>
          <button class="action-btn danger" @click="batchDelete">
            <el-icon><Delete /></el-icon>
            <span>删除</span>
          </button>
          <button class="action-btn ghost" @click="clearSelection">
            <el-icon><Close /></el-icon>
            <span>取消</span>
          </button>
        </div>
      </div>
    </transition>

    <!-- Main Table Card -->
    <div class="table-card">
      <!-- Toolbar -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <button class="toolbar-btn" @click="toggleSelectAll">
            <el-icon><List /></el-icon>
            <span>{{ allSelected ? '取消全选' : '全选' }}</span>
          </button>
          <button class="toolbar-btn" @click="refreshFiles">
            <el-icon><Refresh /></el-icon>
            <span>刷新</span>
          </button>
        </div>
        <div class="toolbar-right">
          <div class="search-box">
            <el-icon><Search /></el-icon>
            <input
              v-model="searchText"
              type="text"
              placeholder="搜索论文标题、作者、期刊..."
              @input="handleSearch"
            />
          </div>
        </div>
      </div>

      <!-- Table -->
      <el-table
        ref="tableRef"
        :data="filteredFiles"
        style="width: 100%"
        :row-style="{ height: '64px' }"
        @selection-change="handleSelectionChange"
        :row-key="getRowKey"
        class="premium-table"
      >
        <el-table-column type="selection" width="48" :reserve-selection="true" />

        <el-table-column label="论文标题" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="paper-title-cell" @click="viewFileDetail(row)">
              <span class="title-text">{{ row.title || '未命名论文' }}</span>
              <el-tag v-if="row.analyzed" size="small" type="success" effect="light">已分析</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="年份" width="90" sortable>
          <template #default="{ row }">
            <span class="year-text">{{ row.year || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="发表期刊/会议" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="venue-text">{{ row.venue || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="上传时间" width="160" sortable>
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <div class="action-group">
              <button class="icon-btn" @click="analyzeFile(scope.row)" title="分析">
                <el-icon><VideoPlay /></el-icon>
              </button>
              <button class="icon-btn" @click="editFile(scope.row)" title="编辑">
                <el-icon><Edit /></el-icon>
              </button>
              <button class="icon-btn danger" @click="deleteFile(scope.row)" title="删除">
                <el-icon><Delete /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredFiles.length === 0" description="暂无论文，请先上传PDF文件" />
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentFile?.title || '论文详情'"
      width="700px"
      class="premium-dialog"
    >
      <div v-if="currentFile" class="detail-content">
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">论文ID</span>
            <span class="detail-value">{{ currentFile.id }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">年份</span>
            <span class="detail-value">{{ currentFile.year || '-' }}</span>
          </div>
          <div class="detail-item full">
            <span class="detail-label">期刊/会议</span>
            <span class="detail-value">{{ currentFile.venue || '-' }}</span>
          </div>
          <div class="detail-item full">
            <span class="detail-label">作者</span>
            <span class="detail-value">{{ currentFile.authors?.join(', ') || '-' }}</span>
          </div>
          <div class="detail-item full">
            <span class="detail-label">上传时间</span>
            <span class="detail-value">{{ formatTime(currentFile.created_at) }}</span>
          </div>
          <div class="detail-item full">
            <span class="detail-label">分析状态</span>
            <el-tag :type="currentFile.analyzed ? 'success' : 'info'" size="small" effect="light">
              {{ currentFile.analyzed ? '已分析' : '未分析' }}
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="detailDialogVisible = false">关闭</button>
        <button class="btn-primary" @click="analyzeFile(currentFile)">分析此论文</button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑论文信息"
      width="550px"
      class="premium-dialog"
    >
      <div class="edit-form">
        <div class="form-group">
          <label>论文标题</label>
          <input v-model="editForm.title" type="text" placeholder="请输入论文标题" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>年份</label>
            <input v-model.number="editForm.year" type="number" min="1900" max="2100" />
          </div>
          <div class="form-group">
            <label>期刊/会议</label>
            <input v-model="editForm.venue" type="text" placeholder="请输入期刊或会议名称" />
          </div>
        </div>
        <div class="form-group">
          <label>作者</label>
          <textarea
            v-model="editForm.authorsStr"
            rows="3"
            placeholder="多个作者用逗号分隔"
          ></textarea>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary" @click="editDialogVisible = false">取消</button>
        <button class="btn-primary" @click="saveEdit" :disabled="saving">
          <el-icon v-if="saving" class="spin"><Loading /></el-icon>
          <span>{{ saving ? '保存中...' : '保存' }}</span>
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Search, VideoPlay, DataAnalysis, Delete, Edit, Refresh, List, Close, Loading, Download } from '@element-plus/icons-vue'
import api from '@/api'

const store = useStore()
const router = useRouter()

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

const getRowKey = (row) => row.id

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
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
  clearSelection()
}

const refreshFiles = () => {
  store.dispatch('fetchFiles')
  ElMessage.success({ message: '刷新成功', customClass: 'premium-message' })
}

const viewFileDetail = (file) => {
  currentFile.value = file
  detailDialogVisible.value = true
}

const analyzeFile = (paper) => {
  if (paper) {
    router.push({ path: '/analyze', query: { paperId: paper.id } })
  }
}

const editFile = (file) => {
  currentFile.value = file
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
    const updateData = {}
    
    if (editForm.value.title !== undefined) {
      updateData.title = editForm.value.title
    }
    
    if (editForm.value.year !== undefined && editForm.value.year !== null) {
      const yearNum = parseInt(editForm.value.year)
      if (yearNum >= 1950 && yearNum <= 2100) {
        updateData.year = yearNum
      } else {
        updateData.year = null
      }
    } else {
      updateData.year = null
    }
    
    if (editForm.value.venue !== undefined) {
      updateData.venue = editForm.value.venue
    }

    const response = await api.updatePaper(editForm.value.id, updateData)

    if (response.success) {
      ElMessage.success({ message: '保存成功', customClass: 'premium-message' })
      editDialogVisible.value = false
      await store.dispatch('fetchFiles')
    } else {
      ElMessage.error({ message: response.error || '保存失败', customClass: 'premium-message' })
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error({ message: '保存失败', customClass: 'premium-message' })
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
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'premium-message-box'
      }
    )

    const success = await store.dispatch('deleteFile', paper.id)
    if (success) {
      ElMessage.success({ message: '删除成功', customClass: 'premium-message' })
      if (selectedFiles.value.find(f => f.id === paper.id)) {
        clearSelection()
      }
    } else {
      ElMessage.error({ message: '删除失败', customClass: 'premium-message' })
    }
  } catch {
    // 用户取消
  }
}

const batchAnalyze = () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning({ message: '请先选择要分析的论文', customClass: 'premium-message' })
    return
  }

  ElMessageBox.confirm(
    `将对 ${selectedFiles.value.length} 篇论文依次进行分析，是否继续？`,
    '批量分析确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
      customClass: 'premium-message-box'
    }
  ).then(() => {
    const firstPaper = selectedFiles.value[0]
    router.push({
      path: '/analyze',
      query: {
        paperId: firstPaper.id,
        batch: 'true',
        count: selectedFiles.value.length
      }
    })
    ElMessage.info({ message: '将从第一篇论文开始分析', customClass: 'premium-message' })
  }).catch(() => {})
}

const batchCluster = () => {
  if (selectedFiles.value.length < 2) {
    ElMessage.warning({ message: '请至少选择2篇论文进行聚类分析', customClass: 'premium-message' })
    return
  }

  router.push({
    path: '/cluster',
    state: {
      selectedPapers: selectedFiles.value.map(f => f.id)
    }
  })
  ElMessage.success({ message: `已选择 ${selectedFiles.value.length} 篇论文，正在跳转`, customClass: 'premium-message' })
}

const batchExport = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning({ message: '请先选择要导出的论文', customClass: 'premium-message' })
    return
  }

  try {
    const headers = ['ID', '标题', '年份', '期刊/会议', '作者', '上传时间']
    const rows = selectedFiles.value.map(file => [
      file.id,
      file.title || '',
      file.year || '',
      file.venue || '',
      file.authors?.join('; ') || '',
      formatTime(file.created_at)
    ])

    const csv = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n')

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `papers_export_${new Date().getTime()}.csv`
    a.click()
    URL.revokeObjectURL(url)

    ElMessage.success({ message: `成功导出 ${selectedFiles.value.length} 篇论文信息`, customClass: 'premium-message' })
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error({ message: '导出失败', customClass: 'premium-message' })
  }
}

const batchDelete = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning({ message: '请先选择要删除的论文', customClass: 'premium-message' })
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
        customClass: 'premium-message-box'
      }
    )

    const paperIds = selectedFiles.value.map(f => f.id)
    const response = await api.batchDeletePapers(paperIds)

    if (response.success) {
      ElMessage.success({ message: `成功删除 ${response.data.deleted_count || paperIds.length} 篇论文`, customClass: 'premium-message' })
      clearSelection()
      await store.dispatch('fetchFiles')
    } else {
      ElMessage.error({ message: response.error || '批量删除失败', customClass: 'premium-message' })
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error({ message: '批量删除失败', customClass: 'premium-message' })
    }
  }
}

onMounted(() => {
  store.dispatch('fetchFiles')
})
</script>

<style scoped>
@import '../styles/design-system.css';

.files-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* ============================================
   PAGE HEADER
   ============================================ */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
}

.header-title h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: var(--tracking-tight);
}

.header-title p {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}

.header-meta {
  display: flex;
  gap: var(--space-4);
}

.meta-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-primary);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-primary);
}

.meta-value {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
}

.meta-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

/* ============================================
   BATCH BAR
   ============================================ */
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  background: var(--color-primary-800);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-5);
  box-shadow: var(--shadow-md);
}

.batch-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-inverse);
}

.batch-info .el-icon {
  font-size: var(--text-base);
}

.batch-actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  color: var(--color-text-inverse);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.05);
}

.action-btn.danger {
  background: rgba(220, 38, 38, 0.8);
  border-color: rgba(220, 38, 38, 0.5);
}

.action-btn.danger:hover {
  background: rgba(220, 38, 38, 1);
}

.action-btn.ghost {
  background: transparent;
  border-color: transparent;
}

/* ============================================
   TABLE CARD
   ============================================ */
.table-card {
  background: var(--color-bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-primary);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

/* Toolbar */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-secondary);
}

.toolbar-left {
  display: flex;
  gap: var(--space-2);
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-focus);
  color: var(--color-text-primary);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  width: 280px;
}

.search-box .el-icon {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  outline: none;
}

.search-box input::placeholder {
  color: var(--color-text-muted);
}

/* Table Styles */
.paper-title-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
}

.title-text {
  color: var(--color-text-primary);
  font-weight: var(--font-medium);
}

.paper-title-cell:hover .title-text {
  color: var(--color-accent-500);
}

.year-text, .venue-text, .time-text {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

.action-group {
  display: flex;
  gap: var(--space-1);
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.icon-btn.danger:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* ============================================
   DIALOG STYLES
   ============================================ */
.detail-content {
  padding: var(--space-4) 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.detail-item.full {
  grid-column: span 2;
}

.detail-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-muted);
}

.detail-value {
  font-size: var(--text-sm);
  color: var(--color-text-primary);
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-group label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

.form-group input,
.form-group textarea {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  transition: all var(--transition-fast);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent-400);
  box-shadow: 0 0 0 3px rgba(201, 162, 39, 0.08);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-primary-800);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover {
  background: var(--color-primary-900);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all var(--transition-base);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-16px);
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--space-4);
  }
  
  .batch-bar {
    flex-direction: column;
    gap: var(--space-3);
  }
  
  .batch-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .table-toolbar {
    flex-direction: column;
    gap: var(--space-3);
    align-items: stretch;
  }
  
  .search-box {
    width: 100%;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-item.full {
    grid-column: span 1;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
