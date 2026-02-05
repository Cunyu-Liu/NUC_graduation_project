<template>
  <div class="analyze">
    <h2>单篇论文分析</h2>

    <el-card class="select-card" v-if="!currentPaper">
      <div class="select-header">
        <h3>选择要分析的论文</h3>
        <el-button @click="refreshFiles" icon="Refresh" size="small">刷新列表</el-button>
      </div>
      <el-table :data="files" style="width: 100%; margin-top: 20px" v-loading="loading">
        <el-table-column label="论文标题" min-width="300">
          <template #default="scope">
            <div class="paper-title-cell">
              <span class="paper-title-text">{{ scope.row.title || '未命名论文' }}</span>
              <el-tag v-if="scope.row.analyzed" size="small" type="success">已分析</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="年份" width="100">
          <template #default="scope">
            {{ formatYear(scope.row.year) }}
          </template>
        </el-table-column>
        <el-table-column prop="venue" label="期刊/会议" width="200">
          <template #default="scope">
            {{ scope.row.venue || '未知' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="selectPaper(scope.row)">
              分析此论文
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="files.length === 0 && !loading" description="暂无论文，请先上传" />
    </el-card>

    <div v-else>
      <el-card class="paper-card">
        <div class="paper-info">
          <el-button @click="currentPaper = null" icon="ArrowLeft" circle size="large" class="back-button" />
          <i class="el-icon-document paper-icon"></i>
          <div class="paper-details">
            <h3>{{ currentPaper.title || '未命名论文' }}</h3>
            <p>年份: {{ formatYear(currentPaper.year) }} | 发表于: {{ currentPaper.venue || '未知' }}</p>
          </div>
        </div>
      </el-card>

      <el-card class="options-card">
        <h3>分析选项</h3>
        <el-checkbox-group v-model="selectedTasks">
          <el-checkbox label="summary">生成摘要</el-checkbox>
          <el-checkbox label="keypoints">提取要点</el-checkbox>
          <el-checkbox label="gaps">研究空白挖掘</el-checkbox>
        </el-checkbox-group>

        <div style="margin-top: 20px; display: flex; gap: 10px;">
          <el-button type="primary" size="large" @click="startAnalysis" :loading="analyzing">
            <i class="el-icon-video-play"></i> 开始分析
          </el-button>
          <el-button
            v-if="result"
            type="warning"
            size="large"
            @click="reanalyze"
            :loading="analyzing"
          >
            <i class="el-icon-refresh"></i> 重新分析
          </el-button>
        </div>
      </el-card>

      <el-card class="result-card" v-if="result">
        <div class="result-header">
          <h3>分析结果</h3>
          <div class="result-meta">
            <el-tag v-if="isHistoricalData" type="info" size="small">
              <i class="el-icon-time"></i> 历史数据
            </el-tag>
            <el-tag v-if="analysisTime" type="success" size="small" style="margin-left: 8px">
              分析时间: {{ analysisTime }}
            </el-tag>
          </div>
        </div>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="摘要" name="summary" v-if="result.summary">
            <div class="markdown-content summary-content" v-html="renderedSummary"></div>
          </el-tab-pane>

          <el-tab-pane label="要点" name="keypoints" v-if="result.keypoints">
            <div class="keypoints-content">
              <div v-for="(items, category) in keypointsDisplay" :key="category" class="keypoint-category">
                <h4>{{ categoryNames[category] || category }}</h4>
                <ul>
                  <li v-for="(item, index) in items" :key="index">{{ item }}</li>
                </ul>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="研究空白" name="gaps" v-if="result.gaps && result.gaps.length > 0">
            <div class="gaps-content">
              <div v-for="(gap, index) in result.gaps" :key="index" class="gap-item">
                <div class="gap-header">
                  <h4>研究空白 #{{ index + 1 }}</h4>
                  <el-button
                    v-if="!gap.editing"
                    type="primary"
                    size="small"
                    @click="startEditGap(gap, index)"
                    icon="Edit"
                  >
                    编辑
                  </el-button>
                  <template v-else>
                    <el-button type="success" size="small" @click="saveGap(gap, index)" icon="Check">
                      保存
                    </el-button>
                    <el-button size="small" @click="cancelEditGap(gap, index)" icon="Close">
                      取消
                    </el-button>
                  </template>
                </div>

                <el-descriptions :column="1" border v-if="!gap.editing">
                  <el-descriptions-item label="类型">
                    <el-tag :type="getGapTypeColor(gap.gap_type)">{{ getGapTypeLabel(gap.gap_type) }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="描述">{{ gap.description }}</el-descriptions-item>
                  <el-descriptions-item label="重要性">
                    <el-tag :type="gap.importance === 'high' ? 'danger' : gap.importance === 'medium' ? 'warning' : 'info'">
                      {{ gap.importance === 'high' ? '高' : gap.importance === 'medium' ? '中' : '低' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="难度">
                    <el-tag :type="gap.difficulty === 'high' ? 'danger' : gap.difficulty === 'medium' ? 'warning' : 'info'">
                      {{ gap.difficulty === 'high' ? '高' : gap.difficulty === 'medium' ? '中' : '低' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="潜在解决方法" v-if="gap.potential_approach">
                    <div class="gap-detail-text">{{ gap.potential_approach }}</div>
                  </el-descriptions-item>
                  <el-descriptions-item label="预期影响" v-if="gap.expected_impact">
                    <div class="gap-detail-text">{{ gap.expected_impact }}</div>
                  </el-descriptions-item>
                  <el-descriptions-item label="代码状态">
                    <el-tag v-if="gap.generated_code_id" type="success">已生成</el-tag>
                    <el-tag v-else type="info">未生成</el-tag>
                    <el-button
                      v-if="!gap.generated_code_id"
                      type="primary"
                      size="small"
                      style="margin-left: 10px;"
                      @click="generateCode(gap, index)"
                      :loading="gap.generating"
                    >
                      生成代码
                    </el-button>
                    <el-button
                      v-else
                      type="success"
                      size="small"
                      style="margin-left: 10px;"
                      @click="viewCode(gap)"
                    >
                      查看代码
                    </el-button>
                  </el-descriptions-item>
                </el-descriptions>

                <el-form v-else label-width="120px" class="gap-edit-form">
                  <el-form-item label="类型">
                    <el-select v-model="gap.editData.gap_type" style="width: 100%;">
                      <el-option label="方法论" value="methodological" />
                      <el-option label="理论" value="theoretical" />
                      <el-option label="数据" value="data" />
                      <el-option label="应用" value="application" />
                      <el-option label="评估" value="evaluation" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="描述">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.description" />
                  </el-form-item>
                  <el-form-item label="重要性">
                    <el-rate
                      v-model="gap.editData.importance"
                      :max="3"
                      :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                      show-score
                      :score-template="{1: '低', 2: '中', 3: '高'}[gap.editData.importance]"
                    />
                  </el-form-item>
                  <el-form-item label="难度">
                    <el-rate
                      v-model="gap.editData.difficulty"
                      :max="3"
                      :colors="['#67C23A', '#E6A23C', '#F56C6C']"
                      show-score
                      :score-template="{1: '低', 2: '中', 3: '高'}[gap.editData.difficulty]"
                    />
                  </el-form-item>
                  <el-form-item label="潜在解决方法">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.potential_approach" placeholder="请详细描述可能的解决方案..." />
                  </el-form-item>
                  <el-form-item label="预期影响">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.expected_impact" placeholder="请描述实施该方案的预期学术和实际影响..." />
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>

        <div class="result-actions">
          <el-button @click="downloadResult">
            <i class="el-icon-download"></i> 下载结果
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import api, { connectSocket } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// 改进的Markdown渲染器 - 更好的格式支持
const renderMarkdown = (text) => {
  if (!text) return ''

  // HTML转义，防止XSS
  const escapeHtml = (unsafe) => {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;")
  }

  let html = escapeHtml(text)

  // 代码块 (```language\ncode\n```)
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<div class="code-block"><pre class="language-${lang || 'text'}"><code>${code.trim()}</code></pre></div>`
  })

  // 行内代码 (`code`)
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // 标题 (# ## ### #### ##### ######)
  html = html.replace(/^######\s+(.+)$/gm, '<h6 class="md-h6">$1</h6>')
  html = html.replace(/^#####\s+(.+)$/gm, '<h5 class="md-h5">$1</h5>')
  html = html.replace(/^####\s+(.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^###\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^##\s+(.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^#\s+(.+)$/gm, '<h1 class="md-h1">$1</h1>')

  // 粗体和斜体
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="md-bold">$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em class="md-italic">$1</em>')

  // 删除线
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

  // 引用块
  html = html.replace(/^&gt;\s+(.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')
  html = html.replace(/(<blockquote[^>]*>[\s\S]*?<\/blockquote>)/g, '<div class="md-blockquote">$1</div>')

  // 分隔线
  html = html.replace(/^---+$/gm, '<hr class="md-hr" />')

  // 无序列表 - 先处理列表项
  html = html.replace(/^([*-])\s+(.+)$/gm, '<li class="md-li">$2</li>')
  // 然后将连续的li包装成ul
  html = html.replace(/(<li[^>]*>[\s\S]*?<\/li>)(\s*<li[^>]*>[\s\S]*?<\/li>)*/g, (match) => {
    return `<ul class="md-ul">${match}</ul>`
  })

  // 有序列表
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="md-ol-li">$1</li>')
  html = html.replace(/(<li class="md-ol-li">[\s\S]*?<\/li>)(\s*<li class="md-ol-li">[\s\S]*?<\/li>)*/g, (match) => {
    return `<ol class="md-ol">${match.replace(/md-ol-li/g, 'md-li')}</ol>`
  })

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="md-link">$1</a>')

  // 图片 ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="md-img" />')

  // 将文本段落包装
  const paragraphs = html.split(/\n\n+/)
  html = paragraphs.map(p => {
    p = p.trim()
    if (!p) return ''
    // 如果已经是以标签开头，不再包装
    if (p.startsWith('<') && !p.startsWith('<br')) {
      return p
    }
    return `<p class="md-paragraph">${p}</p>`
  }).join('\n')

  // 单换行转为br（在段落内部）
  html = html.replace(/([^>])\n/g, '$1<br>')

  return html
}

export default {
  name: 'Analyze',
  setup() {
    const store = useStore()
    const route = useRoute()

    const files = computed(() => store.state.files)
    const currentPaper = ref(null)
    const selectedTasks = ref(['summary', 'keypoints', 'gaps'])
    const analyzing = ref(false)
    const result = ref(null)
    const activeTab = ref('summary')
    const isHistoricalData = ref(false)
    const analysisTime = ref('')
    const loading = ref(false)

    // Markdown渲染计算属性
    const renderedSummary = computed(() => {
      if (!result.value?.summary) return ''
      return renderMarkdown(result.value.summary)
    })

    const categoryNames = {
      innovations: '核心创新点',
      methods: '主要方法',
      experiments: '实验设计',
      conclusions: '主要结论',
      contributions: '学术贡献',
      limitations: '局限性',
      background: '研究背景',
      assumptions: '关键假设',
      implications: '应用与影响',
      future_work: '未来工作'
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

    const keypointsDisplay = computed(() => {
      if (!result.value?.keypoints) return {}
      const filtered = {}
      for (const [key, value] of Object.entries(result.value.keypoints)) {
        if (value && value.length > 0) {
          filtered[key] = value
        }
      }
      return filtered
    })

    // 格式化年份显示
    const formatYear = (year) => {
      if (!year || year === 'unknown' || year === 0) return '未知'
      // 确保年份是数字
      const yearNum = parseInt(year)
      if (isNaN(yearNum)) return '未知'
      return yearNum
    }

    // 刷新文件列表
    const refreshFiles = async () => {
      loading.value = true
      try {
        await store.dispatch('fetchFiles')
        ElMessage.success('论文列表已刷新')
      } catch (error) {
        console.error('刷新失败:', error)
        ElMessage.error('刷新失败')
      } finally {
        loading.value = false
      }
    }

    const selectPaper = async (paper) => {
      console.log('[DEBUG] selectPaper 被调用:', paper)

      // 确保paper对象有id字段
      if (!paper || !paper.id) {
        ElMessage.error('论文数据无效')
        return
      }

      // 创建深拷贝避免引用问题
      currentPaper.value = { ...paper }
      result.value = null
      isHistoricalData.value = false
      analysisTime.value = ''

      console.log('[DEBUG] currentPaper.value 已设置:', currentPaper.value)

      // 确保数据完整性，如果缺少关键信息则从API重新获取
      if (!paper.year || !paper.venue || !paper.authors) {
        try {
          const response = await api.getPaper(paper.id)
          if (response.success && response.data) {
            // 合并API返回的数据
            currentPaper.value = { ...currentPaper.value, ...response.data }
            console.log('[DEBUG] 从API更新了论文信息:', currentPaper.value)
          }
        } catch (error) {
          console.error('[ERROR] 获取论文详情失败:', error)
        }
      }

      // 自动加载历史分析结果
      try {
        console.log('[DEBUG] 加载历史分析结果, paper_id:', paper.id)
        const response = await api.getPaperAnalysis(paper.id)

        console.log('[DEBUG] 历史分析响应:', response)

        if (response.success && response.data) {
          const analysisData = response.data

          // 格式化结果以便显示
          result.value = {
            summary: analysisData.summary_text,
            keypoints: analysisData.keypoints || {},
            gaps: analysisData.gaps || []
          }

          // 标记为历史数据
          isHistoricalData.value = true

          // 显示分析时间
          if (analysisData.created_at) {
            const createdDate = new Date(analysisData.created_at)
            analysisTime.value = createdDate.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })
          }

          ElMessage.info('已加载历史分析结果')
        }
      } catch (error) {
        console.error('[ERROR] 加载历史分析失败:', error)
        // 不显示错误提示，因为可能只是没有历史记录
      }

      console.log('[DEBUG] selectPaper 完成, currentPaper.value.id =', currentPaper.value?.id)
    }

    const startAnalysis = async () => {
      // 验证已选择论文 - 使用更健壮的方式获取论文ID
      console.log('[DEBUG] startAnalysis 被调用')
      console.log('[DEBUG] currentPaper.value:', currentPaper.value)

      // 尝试从currentPaper获取ID（支持多种格式）
      let paperId = null
      if (currentPaper.value) {
        paperId = currentPaper.value.id || currentPaper.value.paper_id
      }

      console.log('[DEBUG] 提取的paperId:', paperId)

      if (!paperId) {
        console.error('[ERROR] 没有选择论文或论文ID为空')
        ElMessage.error('请先选择要分析的论文')
        return
      }

      // 确保currentPaper有正确的id字段
      if (!currentPaper.value.id && paperId) {
        currentPaper.value.id = paperId
      }

      if (selectedTasks.value.length === 0) {
        ElMessage.warning('请至少选择一项分析任务')
        return
      }

      // 开始新分析时，清除历史数据标志
      isHistoricalData.value = false
      analysisTime.value = ''

      // 连接WebSocket
      connectSocket()
      store.commit('SHOW_PROGRESS_DIALOG', true)
      store.commit('SET_PROGRESS', { progress: 0, message: '开始分析...', step: '' })

      analyzing.value = true

      try {
        console.log('[DEBUG] 开始分析, paper_id:', currentPaper.value.id)
        console.log('[DEBUG] 分析任务:', selectedTasks.value)

        const response = await api.analyzePaperV4(
          paperId,
          selectedTasks.value,
          true  // auto_generate_code
        )

        console.log('[DEBUG] 分析响应:', response)

        if (response.success) {
          // 提取分析结果
          const analysisData = response.data

          // 格式化结果以便显示
          result.value = {
            summary: analysisData.summary_text,
            keypoints: analysisData.keypoints || {},
            gaps: analysisData.gaps || []
          }

          // 更新论文状态为已分析
          store.commit('UPDATE_FILE_STATUS', {
            paperId: paperId,
            analyzed: true,
            analysisData: {
              summary: result.value.summary,
              keypoints: result.value.keypoints
            }
          })

          store.commit('SET_PROGRESS', { progress: 100, message: '分析完成!' })
          ElMessage.success('分析完成!')
        } else {
          ElMessage.error(response.error || '分析失败')
        }
      } catch (error) {
        console.error('[ERROR] 分析失败:', error)

        // 提供更友好的错误提示
        let errorMsg = '分析失败'
        const errorDetail = error.response?.data?.error || error.message

        if (errorDetail) {
          if (errorDetail.includes('PDF') || errorDetail.includes('文件')) {
            errorMsg = 'PDF文件读取失败，请检查文件是否存在'
          } else if (errorDetail.includes('LLM') || errorDetail.includes('AI')) {
            errorMsg = 'AI分析服务异常，请稍后重试'
          } else if (errorDetail.includes('timeout') || errorDetail.includes('超时')) {
            errorMsg = '分析超时，请稍后重试或减少分析任务'
          } else if (errorDetail.includes('网络') || errorDetail.includes('network')) {
            errorMsg = '网络连接异常，请检查网络连接'
          } else {
            errorMsg = `分析失败: ${errorDetail}`
          }
        }

        ElMessage.error({
          message: errorMsg,
          duration: 5000,
          showClose: true
        })
      } finally {
        analyzing.value = false
        store.commit('SHOW_PROGRESS_DIALOG', false)
      }
    }

    const reanalyze = async () => {
      // 确认是否要重新分析
      try {
        await ElMessageBox.confirm(
          '重新分析将覆盖当前的分析结果，是否继续？',
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        // 清除历史数据标志
        isHistoricalData.value = false
        analysisTime.value = ''

        // 清空当前结果
        result.value = null

        // 开始新的分析
        await startAnalysis()
      } catch {
        // 用户取消操作
        ElMessage.info('已取消重新分析')
      }
    }

    const downloadResult = () => {
      const filename = (currentPaper.value.title || 'paper').replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')
      if (activeTab.value === 'summary' && result.value?.summary) {
        const blob = new Blob([result.value.summary], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${filename}_summary.txt`
        a.click()
        URL.revokeObjectURL(url)
      } else if (activeTab.value === 'keypoints' && result.value?.keypoints) {
        const content = Object.entries(result.value.keypoints)
          .map(([key, items]) => `${categoryNames[key] || key}:\n${items.map(i => `  - ${i}`).join('\n')}`)
          .join('\n\n')
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${filename}_keypoints.txt`
        a.click()
        URL.revokeObjectURL(url)
      }
    }

    // 研究空白编辑功能
    const startEditGap = (gap, index) => {
      // 保存原始数据
      gap.originalData = { ...gap }
      // 将字符串importance转换为数值用于el-rate
      const importanceValue = gap.importance === 'high' ? 3 : gap.importance === 'medium' ? 2 : 1
      const difficultyValue = gap.difficulty === 'high' ? 3 : gap.difficulty === 'medium' ? 2 : 1
      // 创建编辑副本
      gap.editData = {
        gap_type: gap.gap_type || '',
        description: gap.description || '',
        importance: importanceValue,
        difficulty: difficultyValue,
        potential_approach: gap.potential_approach || '',
        expected_impact: gap.expected_impact || ''
      }
      gap.editing = true
    }

    const saveGap = async (gap, index) => {
      try {
        // 转换数值为字符串
        const importanceStr = gap.editData.importance >= 3 ? 'high' : gap.editData.importance >= 2 ? 'medium' : 'low'
        const difficultyStr = gap.editData.difficulty >= 3 ? 'high' : gap.editData.difficulty >= 2 ? 'medium' : 'low'

        // 调用API保存到数据库
        const response = await api.updateGap(gap.id, {
          gap_type: gap.editData.gap_type,
          description: gap.editData.description,
          importance: importanceStr,
          difficulty: difficultyStr,
          potential_approach: gap.editData.potential_approach,
          expected_impact: gap.editData.expected_impact
        })

        if (response.success) {
          // 更新本地数据
          Object.assign(gap, gap.editData)
          gap.editing = false
          ElMessage.success('保存成功')
        } else {
          ElMessage.error(response.error || '保存失败')
        }
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error('保存失败: ' + (error.message || '未知错误'))
      }
    }

    const cancelEditGap = (gap, index) => {
      // 恢复原始数据
      Object.assign(gap, gap.originalData)
      gap.editing = false
      delete gap.originalData
      delete gap.editData
    }

    const generateCode = async (gap, index) => {
      try {
        gap.generating = true
        ElMessage.info('正在生成代码，请稍候...')

        // 调用代码生成API
        const response = await api.generateCode(gap.id, 'method_improvement')

        if (response.success) {
          gap.generated_code_id = response.data.id
          ElMessage.success('代码生成成功！')
        } else {
          ElMessage.error(response.error || '代码生成失败')
        }
      } catch (error) {
        console.error('代码生成失败:', error)
        ElMessage.error('代码生成失败: ' + (error.message || '未知错误'))
      } finally {
        gap.generating = false
      }
    }

    const viewCode = async (gap) => {
      try {
        if (!gap.generated_code_id) {
          ElMessage.warning('暂无生成的代码')
          return
        }

        // 获取代码详情
        const response = await api.getCode(gap.generated_code_id)
        if (response.success && response.data) {
          const code = response.data.code || '// 暂无代码内容'
          const language = response.data.language || 'python'

          // 打开代码查看对话框
          ElMessageBox.alert(
            `<div style="max-height: 500px; overflow: auto;">
              <pre style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; font-size: 13px; line-height: 1.6; margin: 0;"><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
            </div>`,
            `查看代码 (${language})`,
            {
              confirmButtonText: '关闭',
              dangerouslyUseHTMLString: true,
              customClass: 'code-view-dialog'
            }
          )
        } else {
          ElMessage.error('获取代码失败')
        }
      } catch (error) {
        console.error('获取代码失败:', error)
        ElMessage.error('获取代码失败: ' + (error.message || '未知错误'))
      }
    }

    onMounted(async () => {
      // 先等待文件列表加载完成
      await store.dispatch('fetchFiles')

      // 等待一下确保store已更新
      await new Promise(resolve => setTimeout(resolve, 100))

      // 检查URL参数中的paperId
      const paperIdFromQuery = route.query.paperId
      if (paperIdFromQuery) {
        console.log('[DEBUG] 从URL获取paperId:', paperIdFromQuery)
        console.log('[DEBUG] 当前文件列表:', store.state.files.length)

        // 从store中查找对应的论文
        const paper = store.state.files.find(f => f.id === parseInt(paperIdFromQuery))
        if (paper) {
          console.log('[DEBUG] 找到论文，自动选中:', paper.title)
          await selectPaper(paper)
        } else {
          console.error('[ERROR] 未找到论文ID:', paperIdFromQuery)
          ElMessage.error(`未找到ID为 ${paperIdFromQuery} 的论文`)
        }
      }
    })

    return {
      files,
      currentPaper,
      selectedTasks,
      analyzing,
      result,
      activeTab,
      isHistoricalData,
      analysisTime,
      categoryNames,
      keypointsDisplay,
      renderedSummary,
      loading,
      formatYear,
      refreshFiles,
      getGapTypeLabel,
      getGapTypeColor,
      selectPaper,
      startAnalysis,
      reanalyze,
      downloadResult,
      startEditGap,
      saveGap,
      cancelEditGap,
      generateCode,
      viewCode
    }
  }
}
</script>

<style scoped>
.analyze {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.select-card,
.paper-card,
.options-card,
.result-card {
  margin-bottom: 20px;
}

.paper-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-button {
  flex-shrink: 0;
}

.paper-icon {
  font-size: 48px;
  color: #409eff;
}

.paper-details {
  flex: 1;
}

.paper-details h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.paper-details p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.markdown-content {
  line-height: 1.8;
  color: #303133;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #2c3e50;
}

.markdown-content h1:first-child {
  margin-top: 0;
}

.markdown-content p {
  margin-bottom: 15px;
}

.markdown-content ul,
.markdown-content ol {
  margin-bottom: 15px;
  padding-left: 30px;
}

.markdown-content li {
  margin-bottom: 5px;
}

.markdown-content code {
  background: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-content pre {
  background: #2d2d2d;
  color: #ccc;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
  margin-bottom: 15px;
}

.markdown-content pre code {
  background: transparent;
  padding: 0;
  color: #ccc;
}

.summary-content {
  white-space: pre-wrap;
  line-height: 1.9;
  font-size: 15px;
}

.summary-content h1,
.summary-content h2,
.summary-content h3,
.summary-content h4,
.summary-content h5,
.summary-content h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: #2c3e50;
}

.summary-content h1 { font-size: 28px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
.summary-content h2 { font-size: 24px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; }
.summary-content h3 { font-size: 20px; }
.summary-content h4 { font-size: 18px; }
.summary-content h5 { font-size: 16px; }
.summary-content h6 { font-size: 14px; }

.summary-content p {
  margin-bottom: 16px;
  text-align: justify;
  text-indent: 2em;
}

.summary-content ul,
.summary-content ol {
  margin-bottom: 20px;
  padding-left: 30px;
}

.summary-content li {
  margin-bottom: 10px;
  line-height: 1.8;
}

.summary-content ul li {
  list-style-type: disc;
}

.summary-content ol li {
  list-style-type: decimal;
}

.summary-content code {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  color: #e74c3c;
}

.summary-content pre {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 20px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 20px;
  border: 1px solid #404040;
}

.summary-content pre code {
  background: transparent;
  border: none;
  padding: 0;
  color: #f8f8f2;
  font-size: 13px;
  line-height: 1.6;
}

.summary-content blockquote {
  margin: 20px 0;
  padding: 12px 20px;
  border-left: 4px solid #409eff;
  background: #ecf5ff;
  color: #606266;
  font-style: italic;
}

.summary-content table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.summary-content table th,
.summary-content table td {
  border: 1px solid #d0d7de;
  padding: 10px 12px;
  text-align: left;
}

.summary-content table th {
  background: #f6f8fa;
  font-weight: 600;
}

.summary-content strong {
  font-weight: 600;
  color: #2c3e50;
}

.summary-content em {
  font-style: italic;
  color: #555;
}

.summary-content a {
  color: #409eff;
  text-decoration: none;
  border-bottom: 1px solid #409eff;
}

.summary-content a:hover {
  color: #66b1ff;
  border-bottom-color: #66b1ff;
}

.keypoints-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.keypoint-category {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.keypoint-category h4 {
  color: #409eff;
  margin-bottom: 10px;
}

.keypoint-category ul {
  list-style: none;
  padding: 0;
}

.keypoint-category li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
}

.keypoint-category li:before {
  content: '•';
  position: absolute;
  left: 0;
  color: #409eff;
  font-weight: bold;
}

.gaps-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.gap-item {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.gap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.gap-header h4 {
  color: #409eff;
  margin: 0;
}

.gap-item p {
  margin: 8px 0;
  line-height: 1.6;
}

.gap-edit-form {
  background: white;
  padding: 20px;
  border-radius: 4px;
  margin-top: 15px;
}

.gap-detail-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.code-view-dialog {
  max-width: 800px;
}

.result-actions {
  margin-top: 20px;
  text-align: right;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h3 {
  margin: 0;
  color: #303133;
}

.result-meta {
  display: flex;
  align-items: center;
}

/* 选择论文表格样式 */
.select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.select-header h3 {
  margin: 0;
}

.paper-title-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.paper-title-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 返回按钮样式增强 */
.back-button {
  margin-right: 10px;
  transition: all 0.3s;
}

.back-button:hover {
  transform: scale(1.1);
}
</style>
