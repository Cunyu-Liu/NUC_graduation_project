<template>
  <div class="research-gaps-manager">
    <div class="gaps-header">
      <h2>研究空白管理</h2>
      <div class="header-actions">
        <el-button @click="refreshGaps" icon="Refresh">刷新</el-button>
        <el-button @click="exportGaps" icon="Download">导出报告</el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="gaps-filter">
      <el-form :inline="true">
        <el-form-item label="重要性">
          <el-select v-model="filters.importance" placeholder="全部" clearable style="width: 120px">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>

        <el-form-item label="难度">
          <el-select v-model="filters.difficulty" placeholder="全部" clearable style="width: 120px">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>

        <el-form-item label="类型">
          <el-select v-model="filters.gapType" placeholder="全部" clearable style="width: 150px">
            <el-option label="方法论" value="methodological" />
            <el-option label="理论" value="theoretical" />
            <el-option label="数据" value="data" />
            <el-option label="应用" value="application" />
            <el-option label="评估" value="evaluation" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 130px">
            <el-option label="已识别" value="identified" />
            <el-option label="生成中" value="code_generating" />
            <el-option label="已实现" value="implemented" />
            <el-option label="已验证" value="verified" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="applyFilters">应用筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ stats.total }}</div>
              <div class="stat-label">总空白数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card priority-high">
            <div class="stat-content">
              <div class="stat-number">{{ stats.high_priority }}</div>
              <div class="stat-label">高优先级</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card code-generated">
            <div class="stat-content">
              <div class="stat-number">{{ stats.code_generated }}</div>
              <div class="stat-label">已生成代码</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card implemented">
            <div class="stat-content">
              <div class="stat-number">{{ stats.implemented }}</div>
              <div class="stat-label">已实现</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 空白列表 -->
    <div class="gaps-table-container">
      <el-table
        :data="filteredGaps"
        v-loading="loading"
        style="width: 100%"
        :row-class-name="getRowClassName"
        @row-click="showGapDetail"
      >
        <el-table-column prop="id" label="ID" width="60" />

        <el-table-column label="描述" min-width="300">
          <template #default="{ row }">
            <div class="gap-description">{{ row.description }}</div>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="getGapTypeColor(row.gap_type)">
              {{ getGapTypeLabel(row.gap_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="重要性" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.importance === 'high' ? 'danger' : row.importance === 'medium' ? 'warning' : 'info'" size="small">
              {{ getImportanceLabel(row.importance) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="难度" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.difficulty === 'high' ? 'danger' : row.difficulty === 'medium' ? 'warning' : 'info'" size="small">
              {{ getDifficultyLabel(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                size="small"
                @click.stop="generateCode(row)"
                :disabled="row.status !== 'identified' || generatingCode"
                :loading="generatingCode && currentGeneratingGap === row.id"
                icon="MagicStick"
              >
                {{ generatingCode && currentGeneratingGap === row.id ? '生成中...' : '生成代码' }}
              </el-button>
              <el-button
                size="small"
                @click.stop="editGap(row)"
                icon="Edit"
              >
                编辑
              </el-button>
              <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
                <el-button size="small" icon="More">
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-item command="viewPaper" icon="Document">
                    查看论文
                  </el-dropdown-item>
                  <el-dropdown-item command="viewAnalysis" icon="DataAnalysis">
                    查看分析
                  </el-dropdown-item>
                  <el-dropdown-item command="export" icon="Download">
                    导出
                  </el-dropdown-item>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedGap ? `研究空白详情 #${selectedGap.id}` : '研究空白详情'"
      width="70%"
    >
      <div v-if="selectedGap" class="gap-detail">
        <!-- 基本信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag :type="getGapTypeColor(selectedGap.gap_type)">
              {{ getGapTypeLabel(selectedGap.gap_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="重要性">
            <el-tag :type="selectedGap.importance === 'high' ? 'danger' : selectedGap.importance === 'medium' ? 'warning' : 'info'">
              {{ getImportanceLabel(selectedGap.importance) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="难度">
            <el-tag :type="selectedGap.difficulty === 'high' ? 'danger' : selectedGap.difficulty === 'medium' ? 'warning' : 'info'">
              {{ getDifficultyLabel(selectedGap.difficulty) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedGap.status)">
              {{ getStatusLabel(selectedGap.status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <!-- 详细描述 -->
        <h3>研究空白描述</h3>
        <p class="gap-description-full">{{ selectedGap.description }}</p>

        <!-- 潜在方法 -->
        <h3>潜在解决方法</h3>
        <p class="gap-text-content">{{ selectedGap.potential_approach || '暂无' }}</p>

        <!-- 预期影响 -->
        <h3>预期影响</h3>
        <p class="gap-text-content">{{ selectedGap.expected_impact || '暂无' }}</p>

        <!-- 已生成代码 -->
        <div v-if="selectedGap.generated_code_id">
          <h3>生成的代码</h3>
          <el-button type="primary" @click="viewGeneratedCode(selectedGap.generated_code_id)" icon="View">
            查看代码
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 代码查看对话框 -->
    <el-dialog
      v-model="showCodeDialog"
      title="生成的代码"
      width="90%"
      top="5vh"
      :fullscreen="isCodeFullscreen"
      class="code-dialog"
      :style="{ maxHeight: '90vh' }"
    >
      <template #header>
        <div class="code-dialog-header">
          <span>生成的代码 {{ currentCode?.id ? `#${currentCode.id}` : '' }}</span>
          <div class="code-dialog-actions">
            <el-button 
              :icon="isCodeFullscreen ? 'Close' : 'FullScreen'" 
              @click="isCodeFullscreen = !isCodeFullscreen"
              size="small"
            >
              {{ isCodeFullscreen ? '退出全屏' : '全屏' }}
            </el-button>
            <el-button icon="Download" @click="downloadCode" size="small">下载</el-button>
            <el-button icon="CopyDocument" @click="copyCode" size="small">复制</el-button>
          </div>
        </div>
      </template>
      
      <div v-if="codeLoading" class="code-loading">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载代码中...</p>
      </div>
      
      <div v-else-if="currentCode" class="code-content-wrapper">
        <el-descriptions :column="3" border class="code-meta">
          <el-descriptions-item label="编程语言">
            <el-tag type="primary">{{ currentCode.language || 'Python' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="框架">
            <el-tag type="success">{{ currentCode.framework || 'PyTorch' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentCode.status === 'generated' ? 'success' : 'info'">
              {{ currentCode.status === 'generated' ? '已生成' : currentCode.status }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="code-block-wrapper">
          <div class="code-block-header">
            <span class="code-filename">generated_code.py</span>
          </div>
          <pre class="code-block"><code>{{ currentCode.code }}</code></pre>
        </div>
        
        <div v-if="currentCode.docstring" class="code-docstring">
          <h4>代码说明</h4>
          <pre class="docstring-content">{{ currentCode.docstring }}</pre>
        </div>
        
        <div v-if="currentCode.dependencies" class="code-dependencies">
          <h4>依赖项</h4>
          <pre class="dependencies-content">{{ currentCode.dependencies }}</pre>
        </div>
      </div>
      
      <el-empty v-else description="暂无代码数据" />
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editForm ? `编辑研究空白 #${editForm.id}` : '编辑研究空白'"
      width="60%"
    >
      <el-form :model="editForm" label-width="120px" v-if="editForm">
        <el-form-item label="类型">
          <el-select v-model="editForm.gap_type" placeholder="请选择类型">
            <el-option label="方法论" value="methodological" />
            <el-option label="理论" value="theoretical" />
            <el-option label="数据" value="data" />
            <el-option label="应用" value="application" />
            <el-option label="评估" value="evaluation" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            type="textarea"
            :rows="4"
            v-model="editForm.description"
            placeholder="请详细描述研究空白"
          />
        </el-form-item>

        <el-form-item label="重要性">
          <el-select v-model="editForm.importance" placeholder="请选择重要性">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>

        <el-form-item label="难度">
          <el-select v-model="editForm.difficulty" placeholder="请选择难度">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>

        <el-form-item label="潜在解决方法">
          <el-input
            type="textarea"
            :rows="4"
            v-model="editForm.potential_approach"
            placeholder="请详细描述可能的解决方案、实现路径等"
          />
        </el-form-item>

        <el-form-item label="预期影响">
          <el-input
            type="textarea"
            :rows="4"
            v-model="editForm.expected_impact"
            placeholder="请描述实施该方案的预期学术贡献和实际影响"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="editForm.status" placeholder="请选择状态">
            <el-option label="已识别" value="identified" />
            <el-option label="生成中" value="code_generating" />
            <el-option label="已实现" value="implemented" />
            <el-option label="已验证" value="verified" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const gaps = ref([])
const selectedGap = ref({})
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const editForm = ref(null)
const saving = ref(false)

// 代码查看相关
const showCodeDialog = ref(false)
const currentCode = ref(null)
const codeLoading = ref(false)
const isCodeFullscreen = ref(false)

// 筛选器
const filters = ref({
  importance: '',
  difficulty: '',
  gapType: '',
  status: ''
})

// 统计数据
const stats = ref({
  total: 0,
  high_priority: 0,
  code_generated: 0,
  implemented: 0
})

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 计算属性
const filteredGaps = computed(() => {
  return gaps.value.filter(gap => {
    if (filters.value.importance && gap.importance !== filters.value.importance) return false
    if (filters.value.difficulty && gap.difficulty !== filters.value.difficulty) return false
    if (filters.value.gapType && gap.gap_type !== filters.value.gapType) return false
    if (filters.value.status && gap.status !== filters.value.status) return false
    return true
  })
})

// 方法
const loadGaps = async () => {
  loading.value = true
  try {
    const response = await api.getPriorityGaps(1000)

    if (response.success) {
      const allGaps = response.data || []

      if (allGaps.length === 0) {
        ElMessage.info('暂无研究空白数据，请先分析论文')
        gaps.value = []
        pagination.value.total = 0
        updateStats()
        return
      }

      // 添加评分字段
      gaps.value = allGaps.map(gap => ({
        ...gap,
        importance_level: { 'high': 3, 'medium': 2, 'low': 1 }[gap.importance] || 2,
        difficulty_level: { 'low': 1, 'medium': 2, 'high': 3 }[gap.difficulty] || 2
      }))

      pagination.value.total = allGaps.length
      updateStats()
      ElMessage.success(`成功加载 ${allGaps.length} 个研究空白`)
    } else {
      ElMessage.error(response.error || '加载研究空白失败')
    }
  } catch (error) {
    console.error('加载研究空白失败:', error)
    if (error.response) {
      ElMessage.error(`服务器错误: ${error.response.status}`)
    } else if (error.request) {
      ElMessage.error('网络错误，请检查后端服务是否启动')
    } else {
      ElMessage.error('加载研究空白失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.value = {
    total: gaps.value.length,
    high_priority: gaps.value.filter(g => g.importance === 'high').length,
    code_generated: gaps.value.filter(g => g.generated_code_id).length,
    implemented: gaps.value.filter(g => g.status === 'implemented').length
  }
}

const applyFilters = () => {
  // 触发计算属性重新计算
  ElMessage.success('筛选已应用')
}

const resetFilters = () => {
  filters.value = {
    importance: '',
    difficulty: '',
    gapType: '',
    status: ''
  }
  ElMessage.info('筛选已重置')
}

const getGapTypeLabel = (type) => {
  const labels = {
    'methodological': '方法论',
    'theoretical': '理论',
    'data': '数据',
    'application': '应用',
    'evaluation': '评估'
  }
  return labels[type] || type
}

const getGapTypeColor = (type) => {
  const colors = {
    'methodological': 'primary',
    'theoretical': 'success',
    'data': 'warning',
    'application': 'info',
    'evaluation': 'danger'
  }
  return colors[type] || ''
}

const getStatusLabel = (status) => {
  const labels = {
    'identified': '已识别',
    'code_generating': '生成中',
    'implemented': '已实现',
    'verified': '已验证'
  }
  return labels[status] || status
}

const getStatusType = (status) => {
  const types = {
    'identified': 'info',
    'code_generating': 'warning',
    'implemented': 'success',
    'verified': 'success'
  }
  return types[status] || 'info'
}

const getImportanceLabel = (importance) => {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[importance] || importance
}

const getDifficultyLabel = (difficulty) => {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[difficulty] || difficulty
}

const getRowClassName = ({ row }) => {
  if (row.importance === 'high') {
    return 'high-priority-row'
  }
  return ''
}

const showGapDetail = (row) => {
  selectedGap.value = row
  showDetailDialog.value = true
}

const generatingCode = ref(false)
const currentGeneratingGap = ref(null)

const generateCode = async (gap) => {
  // 防止重复点击
  if (generatingCode.value) {
    ElMessage.warning('正在生成代码，请稍候...')
    return
  }
  
  try {
    generatingCode.value = true
    currentGeneratingGap.value = gap.id
    
    // 更新本地状态显示生成中
    gap.status = 'code_generating'
    
    ElMessage.info('正在生成代码，这可能需要一些时间...')
    
    const response = await api.generateCode(gap.id, 'method_improvement')
    
    if (response.success) {
      ElMessage.success('代码生成成功！')
      // 更新本地状态
      gap.generated_code_id = response.data.id
      gap.status = 'implemented'
      await loadGaps()
    } else {
      // 恢复状态
      gap.status = 'identified'
      ElMessage.error(response.error || '代码生成失败')
    }
  } catch (error) {
    // 恢复状态
    gap.status = 'identified'
    console.error('代码生成错误:', error)
    
    // 提供更详细的错误信息
    let errorMsg = '代码生成失败'
    if (error.response?.data?.error) {
      errorMsg += `: ${error.response.data.error}`
    } else if (error.message) {
      errorMsg += `: ${error.message}`
    }
    ElMessage.error(errorMsg)
  } finally {
    generatingCode.value = false
    currentGeneratingGap.value = null
  }
}

const editGap = (gap) => {
  // 创建编辑表单的副本
  editForm.value = {
    id: gap.id,
    gap_type: gap.gap_type || '',
    description: gap.description || '',
    importance: gap.importance || 'medium',
    difficulty: gap.difficulty || 'medium',
    potential_approach: gap.potential_approach || '',
    expected_impact: gap.expected_impact || '',
    status: gap.status || 'identified'
  }
  showEditDialog.value = true
}

const saveEdit = async () => {
  try {
    saving.value = true

    const response = await api.updateGap(editForm.value.id, {
      gap_type: editForm.value.gap_type,
      description: editForm.value.description,
      importance: editForm.value.importance,
      difficulty: editForm.value.difficulty,
      potential_approach: editForm.value.potential_approach,
      expected_impact: editForm.value.expected_impact,
      status: editForm.value.status
    })

    if (response.success) {
      ElMessage.success('保存成功')
      showEditDialog.value = false
      // 刷新列表
      await loadGaps()
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

const viewGeneratedCode = async (codeId) => {
  // 打开代码查看对话框
  showCodeDialog.value = true
  codeLoading.value = true
  currentCode.value = null
  
  try {
    const response = await api.getCode(codeId)
    if (response.success) {
      currentCode.value = response.data
    } else {
      ElMessage.error(response.error || '获取代码失败')
    }
  } catch (error) {
    console.error('获取代码失败:', error)
    ElMessage.error('获取代码失败: ' + (error.message || '未知错误'))
  } finally {
    codeLoading.value = false
  }
}

const downloadCode = () => {
  if (!currentCode.value?.code) return
  
  const blob = new Blob([currentCode.value.code], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `generated_code_${currentCode.value.id}.py`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('代码下载成功')
}

const copyCode = () => {
  if (!currentCode.value?.code) return
  
  navigator.clipboard.writeText(currentCode.value.code).then(() => {
    ElMessage.success('代码已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

const handleCommand = (command, row) => {
  switch (command) {
    case 'viewPaper':
      window.open(`#/papers/${row.analysis_id}`, '_blank')
      break
    case 'viewAnalysis':
      window.open(`#/analysis/${row.analysis_id}`, '_blank')
      break
    case 'export':
      exportSingleGap(row)
      break
  }
}

const exportSingleGap = (gap) => {
  const content = `
研究空白详情 #${gap.id}

类型: ${getGapTypeLabel(gap.gap_type)}
重要性: ${gap.importance}
难度: ${gap.difficulty}

描述:
${gap.description}

潜在方法:
${gap.potential_approach}

预期影响:
${gap.expected_impact}
  `.trim()

  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `research_gap_${gap.id}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

const exportGaps = () => {
  try {
    if (filteredGaps.value.length === 0) {
      ElMessage.warning('没有可导出的研究空白')
      return
    }

    // 创建导出内容
    let content = '研究空白汇总报告\n'
    content += '=' .repeat(80) + '\n\n'
    content += `导出时间: ${new Date().toLocaleString('zh-CN')}\n`
    content += `总计: ${filteredGaps.value.length} 个研究空白\n\n`

    // 统计信息
    content += '统计信息\n'
    content += '-' .repeat(40) + '\n'
    content += `高优先级: ${filteredGaps.value.filter(g => g.importance === 'high').length}\n`
    content += `已生成代码: ${filteredGaps.value.filter(g => g.generated_code_id).length}\n`
    content += `已实现: ${filteredGaps.value.filter(g => g.status === 'implemented').length}\n\n`

    // 按类型分组
    const gapsByType = {}
    filteredGaps.value.forEach(gap => {
      const type = getGapTypeLabel(gap.gap_type)
      if (!gapsByType[type]) gapsByType[type] = []
      gapsByType[type].push(gap)
    })

    // 详细列表
    content += '详细列表\n'
    content += '=' .repeat(80) + '\n\n'

    Object.keys(gapsByType).forEach((type, typeIndex) => {
      content += `\n${typeIndex + 1}. ${type}类空白 (${gapsByType[type].length}个)\n`
      content += '-' .repeat(80) + '\n'

      gapsByType[type].forEach((gap, index) => {
        content += `\n[${index + 1}] 空白ID: ${gap.id}\n`
        content += `     类型: ${getGapTypeLabel(gap.gap_type)}\n`
        content += `     重要性: ${gap.importance} | 难度: ${gap.difficulty}\n`
        content += `     描述: ${gap.description}\n`
        if (gap.potential_approach) {
          content += `     潜在方法: ${gap.potential_approach}\n`
        }
        if (gap.expected_impact) {
          content += `     预期影响: ${gap.expected_impact}\n`
        }
        content += `     状态: ${getStatusLabel(gap.status)}\n`
      })
    })

    content += '\n' + '=' .repeat(80) + '\n'
    content += '报告结束\n'

    // 下载文件
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `research_gaps_export_${new Date().getTime()}.md`
    a.click()
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${filteredGaps.value.length} 个研究空白`)
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
    console.error('Export error:', error)
  }
}

const refreshGaps = () => {
  loadGaps()
}

const handlePageChange = (page) => {
  pagination.value.page = page
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
}

// 生命周期
onMounted(() => {
  loadGaps()
})
</script>

<style scoped>
.research-gaps-manager {
  padding: 20px;
}

.gaps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.gaps-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.gaps-filter {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 16px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.priority-high .stat-number {
  color: #F56C6C;
}

.code-generated .stat-number {
  color: #409EFF;
}

.implemented .stat-number {
  color: #67C23A;
}

.gaps-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.gap-description {
  font-size: 14px;
  color: #303133;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.gaps-table :deep(.el-table__row) {
  cursor: pointer;
}

.gaps-table :deep(.high-priority-row) {
  background: #fef0f0;
}

.gaps-table :deep(.el-table__row:hover) {
  background: #f5f7fa;
}

.pagination-container {
  padding: 16px;
  display: flex;
  justify-content: center;
}

.gap-detail h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: #303133;
}

.gap-description-full {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  color: #606266;
  margin-bottom: 16px;
}

.gap-text-content {
  padding: 12px;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  line-height: 1.8;
  color: #606266;
  margin-bottom: 16px;
  min-height: 60px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 代码对话框样式 */
.code-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.code-dialog-actions {
  display: flex;
  gap: 8px;
}

.code-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #909399;
}

.code-loading p {
  margin-top: 16px;
}

.code-content-wrapper {
  max-height: none;
  overflow-y: visible;
}

.code-meta {
  margin-bottom: 20px;
}

.code-block-wrapper {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.code-block-header {
  background: #2d2d2d;
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #3d3d3d;
}

.code-filename {
  color: #cccccc;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.code-block {
  margin: 0;
  padding: 16px;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: none;
  overflow-y: visible;
}

.code-docstring, .code-dependencies {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.code-docstring h4, .code-dependencies h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.docstring-content, .dependencies-content {
  margin: 0;
  padding: 12px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: none;
  overflow-y: visible;
}
</style>
