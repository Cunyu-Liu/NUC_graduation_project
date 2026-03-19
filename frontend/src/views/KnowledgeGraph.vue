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
      // 导出当前图谱为图片 - 修复版
      const svg = document.querySelector('.knowledge-graph-container svg')
      if (!svg) {
        ElMessage.warning('没有可导出的图谱')
        return
      }

      // 克隆SVG以便修改
      const clonedSvg = svg.cloneNode(true)
      
      // 获取SVG的实际尺寸
      const svgRect = svg.getBoundingClientRect()
      const width = Math.max(svgRect.width, 800) || 1920
      const height = Math.max(svgRect.height, 600) || 1080
      
      // 设置必要的属性
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
      clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
      clonedSvg.setAttribute('width', width)
      clonedSvg.setAttribute('height', height)
      
      // 添加内联样式
      const style = document.createElementNS('http://www.w3.org/2000/svg', 'style')
      style.textContent = `
        .node circle { fill: #409eff; stroke: #fff; stroke-width: 2; }
        .node text { font-family: Arial, sans-serif; font-size: 12px; fill: #333; }
        .links line { stroke-opacity: 0.6; }
        .link-labels text { font-family: Arial, sans-serif; font-size: 11px; fill: #444; }
      `
      clonedSvg.insertBefore(style, clonedSvg.firstChild)
      
      // 添加白色背景
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
      rect.setAttribute('width', '100%')
      rect.setAttribute('height', '100%')
      rect.setAttribute('fill', '#f8f9fa')
      clonedSvg.insertBefore(rect, clonedSvg.firstChild)
      
      // 序列化SVG
      const svgData = new XMLSerializer().serializeToString(clonedSvg)
      
      // 创建Canvas
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()
      
      // 设置Canvas尺寸（保持比例）
      const scale = 2 // 高清导出
      canvas.width = width * scale
      canvas.height = height * scale

      img.onload = () => {
        // 绘制白色背景
        ctx.fillStyle = '#f8f9fa'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        
        // 绘制SVG图像
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

        // 导出为PNG
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `knowledge_graph_${Date.now()}.png`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
            ElMessage.success('图谱导出成功')
          } else {
            ElMessage.error('导出失败：无法生成图片')
          }
        }, 'image/png')
      }

      img.onerror = (err) => {
        console.error('图片加载失败:', err)
        ElMessage.error('图谱导出失败，请重试')
      }

      // 使用 Blob URL 加载 SVG
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)
      img.src = url
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
