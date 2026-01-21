<template>
  <div class="analyze">
    <h2>单篇论文分析</h2>

    <el-card class="select-card" v-if="!currentPaper">
      <h3>选择要分析的论文</h3>
      <el-table :data="files" style="width: 100%; margin-top: 20px">
        <el-table-column prop="title" label="论文标题" min-width="300" />
        <el-table-column prop="year" label="年份" width="100" />
        <el-table-column prop="venue" label="期刊/会议" width="200" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="selectPaper(scope.row)">
              分析此论文
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div v-else>
      <el-card class="paper-card">
        <div class="paper-info">
          <el-button @click="currentPaper = null" icon="ArrowLeft" circle size="large" class="back-button" />
          <i class="el-icon-document paper-icon"></i>
          <div class="paper-details">
            <h3>{{ currentPaper.title || '未命名论文' }}</h3>
            <p>年份: {{ currentPaper.year || '未知' }} | 发表于: {{ currentPaper.venue || '未知' }}</p>
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
                  <el-descriptions-item label="类型">{{ gap.gap_type }}</el-descriptions-item>
                  <el-descriptions-item label="描述">{{ gap.description }}</el-descriptions-item>
                  <el-descriptions-item label="重要性">{{ gap.importance }}/10</el-descriptions-item>
                  <el-descriptions-item label="潜在解决方法" v-if="gap.potential_approach">
                    {{ gap.potential_approach }}
                  </el-descriptions-item>
                  <el-descriptions-item label="预期影响" v-if="gap.expected_impact">
                    {{ gap.expected_impact }}
                  </el-descriptions-item>
                  <el-descriptions-item label="生产代码" v-if="gap.code_generated">
                    <el-tag type="success">已生成</el-tag>
                  </el-descriptions-item>
                </el-descriptions>

                <el-form v-else label-width="120px" class="gap-edit-form">
                  <el-form-item label="类型">
                    <el-input v-model="gap.editData.gap_type" />
                  </el-form-item>
                  <el-form-item label="描述">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.description" />
                  </el-form-item>
                  <el-form-item label="重要性">
                    <el-rate v-model="gap.editData.importance" :max="10" show-score />
                  </el-form-item>
                  <el-form-item label="潜在解决方法">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.potential_approach" placeholder="请详细描述可能的解决方案..." />
                  </el-form-item>
                  <el-form-item label="预期影响">
                    <el-input type="textarea" :rows="3" v-model="gap.editData.expected_impact" placeholder="请描述实施该方案的预期学术和实际影响..." />
                  </el-form-item>
                  <el-form-item label="生产代码">
                    <el-button type="primary" @click="generateCode(gap, index)" :loading="gap.generating" icon="MagicStick">
                      {{ gap.code_generated ? '重新生成' : '生成代码' }}
                    </el-button>
                    <el-button v-if="gap.code_id" @click="viewCode(gap)" type="success" icon="View">
                      查看代码
                    </el-button>
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
import api, { connectSocket } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// 简单的Markdown渲染器
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
    return `<pre><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`
  })

  // 行内代码 (`code`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // 标题 (# ## ### #### ##### ######)
  html = html.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>')
  html = html.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>')
  html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')

  // 粗体和斜体
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>')
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>')
  html = html.replace(/_(.+?)_/g, '<em>$1</em>')

  // 删除线
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

  // 无序列表
  html = html.replace(/^\* (.+)$/gm, '<li>$1</li>')
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // 有序列表
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ol>$&</ol>')

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')

  // 图片 ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')

  // 段落（双换行）
  html = html.replace(/\n\n/g, '</p><p>')

  // 单换行转为br
  html = html.replace(/\n/g, '<br>')

  // 包装在p标签中
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>'
  }

  return html
}

export default {
  name: 'Analyze',
  setup() {
    const store = useStore()

    const files = computed(() => store.state.files)
    const currentPaper = ref(null)
    const selectedTasks = ref(['summary', 'keypoints', 'gaps'])
    const analyzing = ref(false)
    const result = ref(null)
    const activeTab = ref('summary')
    const isHistoricalData = ref(false)
    const analysisTime = ref('')

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

    const selectPaper = async (paper) => {
      currentPaper.value = paper
      result.value = null
      isHistoricalData.value = false
      analysisTime.value = ''

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
    }

    const startAnalysis = async () => {
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
          currentPaper.value.id,
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
      // 创建编辑副本
      gap.editData = {
        gap_type: gap.gap_type || '',
        description: gap.description || '',
        importance: gap.importance || 5,
        potential_approach: gap.potential_approach || '',
        expected_impact: gap.expected_impact || ''
      }
      gap.editing = true
    }

    const saveGap = async (gap, index) => {
      try {
        // 更新数据
        Object.assign(gap, gap.editData)
        gap.editing = false

        // TODO: 调用API保存到数据库
        ElMessage.success('保存成功')
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error('保存失败: ' + error.message)
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

        // TODO: 调用代码生成API
        // const response = await api.generateCode(gap.id)

        // 模拟生成
        await new Promise(resolve => setTimeout(resolve, 2000))

        gap.code_generated = true
        gap.code_id = `code_${Date.now()}`

        ElMessage.success('代码生成成功！')
      } catch (error) {
        console.error('代码生成失败:', error)
        ElMessage.error('代码生成失败: ' + error.message)
      } finally {
        gap.generating = false
      }
    }

    const viewCode = (gap) => {
      // 打开代码查看对话框
      ElMessageBox.alert(
        `代码ID: ${gap.code_id}\n\n// 这里应该显示生成的代码内容`,
        '查看代码',
        {
          confirmButtonText: '关闭',
          customClass: 'code-view-dialog'
        }
      )
    }

    onMounted(() => {
      store.dispatch('fetchFiles')
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
</style>
