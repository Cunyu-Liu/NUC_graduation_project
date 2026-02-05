<template>
  <div class="cluster">
    <h2>多篇论文主题聚类分析</h2>

    <el-card class="select-card">
      <div class="select-header">
        <h3>选择要分析的论文（至少2篇）</h3>
        <el-button @click="refreshFiles" size="small">
          <el-icon><Refresh /></el-icon>
          刷新列表
        </el-button>
      </div>
      <el-table
        :data="files"
        style="width: 100%; margin-top: 20px"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="论文标题" min-width="250">
          <template #default="scope">
            {{ scope.row.title || '未命名论文' }}
          </template>
        </el-table-column>
        <el-table-column prop="year" label="年份" width="80">
          <template #default="scope">
            {{ scope.row.year || '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="venue" label="期刊/会议" min-width="150" />
      </el-table>
    </el-card>

    <el-card class="options-card">
      <h3>聚类选项</h3>
      <el-form :model="options" label-width="120px">
        <el-form-item label="聚类数量">
          <el-input-number v-model="options.nClusters" :min="2" :max="10" />
        </el-form-item>
        <el-form-item label="聚类方法">
          <el-select v-model="options.method">
            <el-option label="K-Means" value="kmeans" />
            <el-option label="DBSCAN" value="dbscan" />
            <el-option label="层次聚类" value="hierarchical" />
          </el-select>
        </el-form-item>
        <el-form-item label="论文语言">
          <el-select v-model="options.language">
            <el-option label="中文" value="chinese" />
            <el-option label="英文" value="english" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-button
        type="primary"
        size="large"
        @click="startCluster"
        :disabled="selectedFiles.length < 2"
        :loading="clustering"
      >
        <el-icon><DataAnalysis /></el-icon> 开始聚类分析
      </el-button>
    </el-card>

    <!-- 历史聚类结果 -->
    <el-card class="history-card" v-if="clusterHistory.length > 0">
      <div class="history-header">
        <h3>历史聚类结果</h3>
        <el-button @click="clearHistory" type="danger" size="small" plain>清空历史</el-button>
      </div>
      <el-table :data="clusterHistory" style="width: 100%; margin-top: 10px">
        <el-table-column prop="createdAt" label="时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="clusterCount" label="聚类数" width="80" />
        <el-table-column prop="method" label="方法" width="120" />
        <el-table-column prop="paperCount" label="论文数" width="80" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="loadHistoryResult(scope.row)">查看</el-button>
            <el-button type="danger" size="small" @click="deleteHistoryResult(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="result-card" v-if="result">
      <div class="result-header">
        <h3>聚类结果</h3>
        <div class="result-actions-top">
          <el-tag type="success" size="large" effect="dark">
            {{ result.clusterCount }} 个主题类别
          </el-tag>
          <el-button
            v-if="currentResultId"
            type="warning"
            size="small"
            @click="saveCurrentResult"
          >
            <el-icon><Star /></el-icon>
            保存结果
          </el-button>
        </div>
      </div>

      <el-collapse v-model="activeClusters">
        <el-collapse-item
          v-for="(cluster, index) in Object.entries(result.clusterAnalysis)"
          :key="cluster[0]"
          :name="cluster[0]"
        >
          <template #title>
            <div class="cluster-title">
              <span class="cluster-name">聚类 {{ parseInt(cluster[0]) + 1 }}</span>
              <el-tag type="success" size="small">
                {{ cluster[1]?.paper_count || 0 }} 篇论文
              </el-tag>
              <el-tag
                v-if="cluster[1]?.top_keywords?.length > 0"
                type="info"
                size="small"
                style="margin-left: 8px;"
              >
                {{ cluster[1].top_keywords.slice(0, 3).join(', ') }}
              </el-tag>
            </div>
          </template>

          <div class="cluster-content">
            <h4>核心关键词</h4>
            <el-space wrap v-if="cluster[1].top_keywords && cluster[1].top_keywords.length > 0">
              <el-tag
                v-for="(keyword, kIndex) in cluster[1].top_keywords.slice(0, 10)"
                :key="kIndex"
                type="success"
                effect="dark"
              >
                {{ keyword }}
              </el-tag>
            </el-space>
            <el-empty v-else description="暂无关键词" :image-size="60" />

            <h4 style="margin-top: 20px">包含论文</h4>
            <ul v-if="cluster[1].papers && cluster[1].papers.length > 0" class="paper-list">
              <li v-for="(paper, pIndex) in cluster[1].papers" :key="pIndex">
                {{ paper }}
              </li>
            </ul>
            <el-empty v-else description="暂无论文" :image-size="60" />

            <h4 style="margin-top: 20px">代表性论文</h4>
            <div
              v-if="cluster[1].representative_papers && cluster[1].representative_papers.length > 0"
            >
              <div
                v-for="(rep, rIndex) in cluster[1].representative_papers"
                :key="rIndex"
                class="rep-paper"
              >
                <p><strong>{{ rep.title || '无标题' }}</strong></p>
                <p class="rep-abstract">{{ rep.abstract || '无摘要' }}</p>
              </div>
            </div>
            <el-empty v-else description="暂无代表性论文" :image-size="60" />
          </div>
        </el-collapse-item>
      </el-collapse>

      <div class="result-actions">
        <el-button type="primary" @click="downloadVisualization">
          <el-icon><PictureIcon /></el-icon>
          下载高清可视化图
        </el-button>
        <el-button @click="downloadReport">
          <el-icon><Document /></el-icon>
          下载聚类报告
        </el-button>
      </div>
    </el-card>

    <!-- 聚类可视化对话框 -->
    <el-dialog
      v-model="showVisualization"
      title="聚类可视化"
      width="90%"
      :fullscreen="true"
    >
      <div class="visualization-container">
        <canvas ref="vizCanvas" class="viz-canvas"></canvas>
      </div>
      <template #footer>
        <el-button @click="showVisualization = false">关闭</el-button>
        <el-button type="primary" @click="downloadHighResVisualization">下载高清图</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import api, { connectSocket } from '@/api'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Refresh, Star, Picture as PictureIcon, Document } from '@element-plus/icons-vue'

export default {
  name: 'Cluster',
  components: {
    DataAnalysis,
    Refresh,
    Star,
    PictureIcon,
    Document
  },
  setup() {
    const store = useStore()

    const files = computed(() => store.state.files)
    const selectedFiles = ref([])
    const loading = ref(false)
    const options = ref({
      nClusters: 5,
      method: 'kmeans',
      language: 'chinese'
    })
    const clustering = ref(false)
    const result = ref(null)
    const activeClusters = ref(['0', '1', '2'])
    const showVisualization = ref(false)
    const vizCanvas = ref(null)

    // 当前聚类结果ID
    const currentResultId = ref(null)

    // 聚类历史记录
    const clusterHistory = ref([])

    // 从localStorage加载历史记录
    const loadHistory = () => {
      try {
        const saved = localStorage.getItem('cluster_history')
        if (saved) {
          clusterHistory.value = JSON.parse(saved)
        }
      } catch (e) {
        console.error('加载历史记录失败:', e)
      }
    }

    // 保存历史记录到localStorage
    const saveHistory = () => {
      try {
        localStorage.setItem('cluster_history', JSON.stringify(clusterHistory.value))
      } catch (e) {
        console.error('保存历史记录失败:', e)
      }
    }

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }

    // 加载历史结果
    const loadHistoryResult = (historyItem) => {
      result.value = historyItem.data
      currentResultId.value = null // 历史结果不需要再保存
      activeClusters.value = Object.keys(historyItem.data.clusterAnalysis).slice(0, 3)
      ElMessage.success('已加载历史聚类结果')
    }

    // 删除历史结果
    const deleteHistoryResult = (index) => {
      clusterHistory.value.splice(index, 1)
      saveHistory()
      ElMessage.success('已删除')
    }

    // 清空历史
    const clearHistory = () => {
      clusterHistory.value = []
      saveHistory()
      ElMessage.success('历史记录已清空')
    }

    // 保存当前结果
    const saveCurrentResult = () => {
      if (!result.value) return

      const historyItem = {
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        clusterCount: result.value.clusterCount,
        method: result.value.method,
        paperCount: result.value.papers?.length || 0,
        data: result.value
      }

      clusterHistory.value.unshift(historyItem)
      saveHistory()
      currentResultId.value = null // 已保存，不需要再显示保存按钮
      ElMessage.success('聚类结果已保存到历史记录')
    }

    const handleSelectionChange = (selection) => {
      selectedFiles.value = selection
    }

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

    const startCluster = async () => {
      if (selectedFiles.value.length < 2) {
        ElMessage.warning('请至少选择2篇论文')
        return
      }

      // 验证聚类数量
      const maxClusters = Math.min(20, selectedFiles.value.length)
      if (options.value.method !== 'dbscan' && (options.value.nClusters < 2 || options.value.nClusters > maxClusters)) {
        ElMessage.warning(`聚类数量必须在 2 到 ${maxClusters} 之间`)
        return
      }

      // 连接WebSocket
      connectSocket()
      store.commit('SHOW_PROGRESS_DIALOG', true)
      store.commit('SET_PROGRESS', { progress: 0, message: '开始聚类分析...', step: '' })

      clustering.value = true

      try {
        // 使用论文ID而不是文件路径
        const paperIds = selectedFiles.value.map(f => f.id)

        console.log('[DEBUG] 开始聚类, paper_ids:', paperIds)
        console.log('[DEBUG] 聚类选项:', options.value)

        const response = await api.clusterPapers(
          paperIds,
          options.value.nClusters,
          options.value.method,
          options.value.language
        )

        console.log('[DEBUG] 聚类响应:', response)

        if (response.success) {
          // 格式化结果
          result.value = {
            clusterCount: response.data.n_clusters,
            clusterAnalysis: response.data.cluster_analysis,
            papers: response.data.papers || [],
            method: options.value.method,
            createdAt: new Date().toISOString()
          }

          // 生成新的结果ID
          currentResultId.value = Date.now().toString()

          store.commit('SET_PROGRESS', { progress: 100, message: '聚类完成!' })
          ElMessage.success(`聚类分析完成! 共发现 ${response.data.n_clusters} 个主题类别`)

          // 自动展开前3个聚类
          const clusterIds = Object.keys(response.data.cluster_analysis)
          activeClusters.value = clusterIds.slice(0, 3)

          // 自动保存到历史记录
          saveCurrentResult()
        } else {
          ElMessage.error({
            message: response.error || '聚类失败',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        console.error('[ERROR] 聚类错误:', error)

        // 提供更详细的错误提示
        let errorMsg = '聚类失败'
        const errorDetail = error.response?.data?.error || error.message

        if (errorDetail) {
          if (errorDetail.includes('论文') || errorDetail.includes('PDF')) {
            errorMsg = '论文加载或解析失败，请检查文件是否完整'
          } else if (errorDetail.includes('聚类') || errorDetail.includes('算法')) {
            errorMsg = '聚类算法执行失败，请尝试调整参数'
          } else if (errorDetail.includes('数量') || errorDetail.includes('不足')) {
            errorMsg = '可用论文数量不足，无法进行聚类'
          } else if (errorDetail.includes('timeout') || errorDetail.includes('超时')) {
            errorMsg = '聚类超时，请减少论文数量或降低聚类数量'
          } else {
            errorMsg = `聚类失败: ${errorDetail}`
          }
        } else if (error.message) {
          errorMsg = `聚类失败: ${error.message}`
        }

        ElMessage.error({
          message: errorMsg,
          duration: 5000,
          showClose: true
        })
      } finally {
        clustering.value = false
        store.commit('SHOW_PROGRESS_DIALOG', false)
      }
    }

    const downloadVisualization = () => {
      showVisualization.value = true
      // 在对话框打开后绘制可视化
      setTimeout(() => {
        drawVisualization()
      }, 100)
    }

    const drawVisualization = () => {
      const canvas = vizCanvas.value
      if (!canvas) return

      // 设置高分辨率画布
      const dpr = window.devicePixelRatio || 1
      const width = window.innerWidth * 0.85
      const height = window.innerHeight * 0.75

      canvas.width = width * dpr
      canvas.height = height * dpr
      canvas.style.width = width + 'px'
      canvas.style.height = height + 'px'

      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr)

      // 背景
      ctx.fillStyle = '#f8f9fa'
      ctx.fillRect(0, 0, width, height)

      // 标题
      ctx.fillStyle = '#333'
      ctx.font = 'bold 28px Arial'
      ctx.textAlign = 'center'
      ctx.fillText('论文主题聚类可视化', width / 2, 50)

      if (!result.value || !result.value.clusterAnalysis) {
        return
      }

      // 绘制聚类圆形图
      const clusters = Object.entries(result.value.clusterAnalysis)
      const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B500', '#6C5CE7']

      const centerX = width / 2
      const centerY = height / 2 + 30
      const maxRadius = Math.min(width, height) * 0.35

      // 计算总论文数
      const totalPapers = clusters.reduce((sum, [, info]) => sum + (info.paper_count || 0), 0)

      // 绘制聚类圆圈
      let currentAngle = 0
      clusters.forEach(([clusterId, info], index) => {
        const color = colors[index % colors.length]
        const ratio = (info.paper_count || 0) / Math.max(totalPapers, 1)
        const angle = ratio * Math.PI * 2

        // 绘制扇形
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, maxRadius, currentAngle, currentAngle + angle)
        ctx.closePath()
        ctx.fillStyle = color + '40' // 添加透明度
        ctx.fill()
        ctx.strokeStyle = color
        ctx.lineWidth = 3
        ctx.stroke()

        // 绘制标签
        const labelAngle = currentAngle + angle / 2
        const labelRadius = maxRadius + 40
        const labelX = centerX + Math.cos(labelAngle) * labelRadius
        const labelY = centerY + Math.sin(labelAngle) * labelRadius

        ctx.fillStyle = color
        ctx.font = 'bold 16px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(`聚类 ${parseInt(clusterId) + 1}`, labelX, labelY - 10)
        ctx.font = '14px Arial'
        ctx.fillStyle = '#666'
        ctx.fillText(`${info.paper_count || 0}篇`, labelX, labelY + 10)

        currentAngle += angle
      })

      // 中心圆
      ctx.beginPath()
      ctx.arc(centerX, centerY, maxRadius * 0.3, 0, Math.PI * 2)
      ctx.fillStyle = 'white'
      ctx.fill()
      ctx.strokeStyle = '#ddd'
      ctx.lineWidth = 2
      ctx.stroke()

      // 中心文字
      ctx.fillStyle = '#333'
      ctx.font = 'bold 20px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(`${clusters.length}`, centerX, centerY - 5)
      ctx.font = '14px Arial'
      ctx.fillStyle = '#666'
      ctx.fillText('个聚类', centerX, centerY + 15)

      // 绘制图例
      let legendY = height - 100
      const legendX = width / 2 - (clusters.length * 150) / 2

      clusters.forEach(([clusterId, info], index) => {
        const color = colors[index % colors.length]
        const x = legendX + (index % 5) * 150
        const y = legendY + Math.floor(index / 5) * 40

        ctx.fillStyle = color
        ctx.fillRect(x, y, 20, 20)
        ctx.fillStyle = '#333'
        ctx.font = '12px Arial'
        ctx.textAlign = 'left'
        const keywords = info.top_keywords?.slice(0, 2).join(', ') || '无关键词'
        ctx.fillText(`聚类${parseInt(clusterId) + 1}: ${keywords}`, x + 30, y + 15)
      })
    }

    const downloadHighResVisualization = () => {
      const canvas = vizCanvas.value
      if (!canvas) return

      // 创建高分辨率下载
      const link = document.createElement('a')
      link.download = `cluster_visualization_${Date.now()}_highres.png`
      link.href = canvas.toDataURL('image/png', 1.0)
      link.click()
      ElMessage.success('高清可视化图下载成功')
    }

    const downloadReport = async () => {
      if (!result.value) {
        ElMessage.warning('没有可导出的聚类结果')
        return
      }

      try {
        // 生成报告内容
        let content = '论文主题聚类分析报告\n'
        content += '=' .repeat(80) + '\n\n'
        content += `生成时间: ${formatDate(result.value.createdAt)}\n`
        content += `聚类方法: ${result.value.method || 'K-Means'}\n`
        content += `聚类数量: ${result.value.clusterCount}\n`
        content += `论文总数: ${result.value.papers?.length || 0}\n\n`

        // 每个聚类的详细信息
        Object.entries(result.value.clusterAnalysis).forEach(([clusterId, info], index) => {
          content += `\n${'=' .repeat(80)}\n`
          content += `聚类 ${parseInt(clusterId) + 1}\n`
          content += `${'-' .repeat(40)}\n`
          content += `论文数: ${info.paper_count || 0}\n`
          content += `关键词: ${info.top_keywords?.join(', ') || '无'}\n\n`

          if (info.papers && info.papers.length > 0) {
            content += '包含论文:\n'
            info.papers.forEach((paper, i) => {
              content += `  ${i + 1}. ${paper}\n`
            })
          }

          if (info.representative_papers && info.representative_papers.length > 0) {
            content += '\n代表性论文:\n'
            info.representative_papers.forEach((paper, i) => {
              content += `  ${i + 1}. ${paper.title || '无标题'}\n`
              if (paper.abstract) {
                content += `     摘要: ${paper.abstract}\n`
              }
            })
          }
        })

        content += `\n${'=' .repeat(80)}\n`
        content += '报告结束\n'

        // 下载文件
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `cluster_report_${Date.now()}.txt`
        a.click()
        URL.revokeObjectURL(url)

        ElMessage.success('聚类报告下载成功')
      } catch (error) {
        console.error('[ERROR] 导出报告失败:', error)
        ElMessage.error('导出报告失败')
      }
    }

    onMounted(() => {
      store.dispatch('fetchFiles')
      loadHistory()
    })

    return {
      files,
      selectedFiles,
      loading,
      options,
      clustering,
      result,
      activeClusters,
      currentResultId,
      clusterHistory,
      showVisualization,
      vizCanvas,
      handleSelectionChange,
      refreshFiles,
      formatDate,
      startCluster,
      downloadVisualization,
      drawVisualization,
      downloadHighResVisualization,
      downloadReport,
      saveCurrentResult,
      loadHistoryResult,
      deleteHistoryResult,
      clearHistory
    }
  }
}
</script>

<style scoped>
.cluster {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.select-card,
.options-card,
.result-card,
.history-card {
  margin-bottom: 20px;
}

.select-header,
.history-header,
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.select-header h3,
.history-header h3,
.result-header h3 {
  margin: 0;
}

.result-actions-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cluster-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cluster-name {
  font-weight: 600;
}

.cluster-content h4 {
  color: #409eff;
  margin: 20px 0 10px 0;
}

.paper-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.paper-list li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
  border-bottom: 1px solid #eee;
}

.paper-list li:before {
  content: '•';
  position: absolute;
  left: 0;
  color: #409eff;
  font-weight: bold;
}

.rep-paper {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.rep-paper p {
  margin: 5px 0;
}

.rep-abstract {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.visualization-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 500px;
  background: #f8f9fa;
  border-radius: 8px;
}

.viz-canvas {
  max-width: 100%;
  max-height: 80vh;
}

/* 表格样式优化 */
:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-tag) {
  font-size: 12px;
}
</style>
