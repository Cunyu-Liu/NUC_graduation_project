<template>
  <div class="knowledge-graph-page">
    <el-card class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h2>
            <el-icon><Share /></el-icon>
            知识图谱
          </h2>
          <p>可视化展示论文之间的引用和关联关系</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="buildGraph" :loading="building">
            <el-icon><Refresh /></el-icon>
            构建图谱
          </el-button>
          <el-button @click="showStats = true">
            <el-icon><InfoFilled /></el-icon>
            统计信息
          </el-button>
          <el-button @click="exportGraph">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计信息对话框 -->
    <el-dialog v-model="showStats" title="知识图谱统计" width="500px">
      <el-descriptions :column="1" border v-if="stats">
        <el-descriptions-item label="节点数（论文）">{{ stats.total_nodes || 0 }}</el-descriptions-item>
        <el-descriptions-item label="边数（关系）">{{ stats.total_edges || 0 }}</el-descriptions-item>
        <el-descriptions-item label="平均度数">{{ (stats.avg_degree || 0).toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="暂无统计信息" />
    </el-dialog>

    <KnowledgeGraph ref="graphComponent" />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Share, Refresh, Download, InfoFilled } from '@element-plus/icons-vue'
import KnowledgeGraph from '@/components/KnowledgeGraph.vue'
import api from '@/api'

export default {
  name: 'KnowledgeGraphView',
  components: {
    KnowledgeGraph,
    Share,
    Refresh,
    Download,
    InfoFilled
  },
  setup() {
    const graphComponent = ref(null)
    const building = ref(false)
    const showStats = ref(false)
    const stats = ref(null)

    // 页面加载时自动构建图谱
    onMounted(async () => {
      await loadStats()
      // 自动构建图谱（如果还没有数据）
      await buildGraph()
    })

    const loadStats = async () => {
      try {
        const response = await api.getStatistics()
        if (response.success) {
          stats.value = {
            total_nodes: response.data.total_papers,
            total_edges: response.data.total_relations,
            avg_degree: response.data.total_relations * 2 / Math.max(response.data.total_papers, 1)
          }
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }

    const buildGraph = async () => {
      try {
        building.value = true
        ElMessage.info('正在构建知识图谱，请稍候...')

        const response = await api.buildKnowledgeGraph([])

        if (response.success) {
          ElMessage.success(response.message || '知识图谱构建成功')
          if (graphComponent.value) {
            await graphComponent.value.refreshGraph()
          }
          // 刷新统计信息
          await loadStats()
        } else {
          ElMessage.warning(response.message || '图谱构建未完成')
        }
      } catch (error) {
        console.error('构建知识图谱失败:', error)
        // 不显示错误，因为可能是图谱已经存在
        // 直接刷新图谱显示
        if (graphComponent.value) {
          await graphComponent.value.refreshGraph()
        }
      } finally {
        building.value = false
      }
    }

    const exportGraph = () => {
      // 导出当前图谱为图片
      const svg = document.querySelector('.knowledge-graph-container svg')
      if (!svg) {
        ElMessage.warning('没有可导出的图谱')
        return
      }

      const svgData = new XMLSerializer().serializeToString(svg)
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      canvas.width = 1920
      canvas.height = 1080

      img.onload = () => {
        ctx.fillStyle = '#f8f9fa'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

        canvas.toBlob((blob) => {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `knowledge_graph_${Date.now()}.png`
          a.click()
          URL.revokeObjectURL(url)
          ElMessage.success('图谱导出成功')
        })
      }

      img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
    }

    return {
      graphComponent,
      building,
      showStats,
      stats,
      buildGraph,
      exportGraph
    }
  }
}
</script>

<style scoped>
.knowledge-graph-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: center;
}

.header-left h2 i {
  margin-right: 10px;
  color: #409eff;
}

.header-left p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.header-right {
  display: flex;
  gap: 10px;
}
</style>
