<template>
  <div class="knowledge-graph-container">
    <div class="graph-header">
      <h2>知识图谱可视化</h2>
      <div class="controls">
        <el-button @click="refreshGraph" icon="Refresh">刷新</el-button>
        <el-button @click="resetZoom" icon="ZoomOut">重置视图</el-button>
        <el-select v-model="relationFilter" placeholder="关系类型" multiple style="width: 200px">
          <el-option v-for="type in relationTypes" :key="type" :label="type" :value="type" />
        </el-select>
      </div>
    </div>

    <!-- SVG容器 -->
    <div ref="graphContainer" class="graph-container">
      <svg ref="svgElement" width="100%" height="100%"></svg>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在构建知识图谱...</p>
    </div>

    <!-- 节点详情面板 -->
    <el-drawer v-model="drawerVisible" title="节点详情" size="400px" direction="rtl">
      <div v-if="selectedNode" class="node-detail">
        <h3>{{ selectedNode.data.title }}</h3>
        <el-divider />

        <el-descriptions :column="1" border>
          <el-descriptions-item label="ID">{{ selectedNode.data.id }}</el-descriptions-item>
          <el-descriptions-item label="年份">{{ selectedNode.data.year || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="发表场所">{{ selectedNode.data.venue || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="作者数量">
            {{ selectedNode.data.authors?.length || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="摘要长度">
            {{ selectedNode.data.abstract?.length || 0 }} 字符
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <!-- 关联论文 -->
        <h4>关联论文</h4>
        <div v-if="connectedNodes.length > 0" class="connected-papers">
          <el-card
            v-for="node in connectedNodes"
            :key="node.data.id"
            class="paper-card"
            shadow="hover"
          >
            <div class="paper-title" @click="focusNode(node.data.id)">
              {{ node.data.title }}
            </div>
            <div class="paper-meta">
              <span>{{ node.data.year }}</span>
              <span>{{ node.data.venue }}</span>
            </div>
          </el-card>
        </div>
        <el-empty v-else description="无关联论文" />
      </div>
    </el-drawer>

    <!-- 图例 -->
    <div class="legend-panel">
      <div class="legend-title">关系类型</div>
      <div v-for="type in relationTypes" :key="type" class="legend-item">
        <span class="legend-color" :style="{ backgroundColor: getRelationColor(type) }"></span>
        <span class="legend-label">{{ type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import * as d3 from 'd3'
import { ElMessage } from 'element-plus'
import api from '@/api'

// Props
const props = defineProps({
  paperIds: {
    type: Array,
    default: () => []
  }
})

// 响应式数据
const loading = ref(false)
const graphData = ref({ nodes: {}, edges: [] })
const drawerVisible = ref(false)
const selectedNode = ref(null)
const connectedNodes = ref([])
const relationFilter = ref([])

// D3相关
const svgElement = ref(null)
const graphContainer = ref(null)
let svg, g, simulation, zoom

// 关系类型颜色映射
const relationColors = {
  'cites': '#FF6B6B',
  'extends': '#4ECDC4',
  'improves': '#45B7D1',
  'applies': '#FFA07A',
  'contradicts': '#98D8C8'
}

// 计算属性
const relationTypes = computed(() => {
  const types = new Set()
  graphData.value.edges.forEach(edge => {
    types.add(edge.type)
  })
  return Array.from(types)
})

const filteredEdges = computed(() => {
  if (relationFilter.value.length === 0) {
    return graphData.value.edges
  }
  return graphData.value.edges.filter(edge =>
    relationFilter.value.includes(edge.type)
  )
})

// 方法
const initGraph = () => {
  if (!svgElement.value) return

  const container = graphContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 创建SVG
  svg = d3.select(svgElement.value)
    .attr('width', width)
    .attr('height', height)

  // 添加缩放行为
  zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  // 创建主分组
  g = svg.append('g')
    .attr('width', width)
    .attr('height', height)

  // 添加箭头标记
  svg.append('defs').selectAll('marker')
    .data(Object.keys(relationColors))
    .join('marker')
    .attr('id', d => `arrow-${d}`)
    .attr('viewBox', '0 0 10 10')
    .attr('refX', 20)
    .attr('refY', 5)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto-start-reverse')
    .append('path')
    .attr('d', 'M 0 0 L 10 5 L 0 10 z')
    .attr('fill', d => relationColors[d])
}

const updateGraph = () => {
  // 准备节点数据
  const nodes = Object.entries(graphData.value.nodes).map(([id, data]) => ({
    id: parseInt(id),
    ...data
  }))

  // 创建力导向布局
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(filteredEdges.value)
      .id(d => d.id)
      .distance(100)
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(
      graphContainer.value.clientWidth / 2,
      graphContainer.value.clientHeight / 2
    ))
    .force('collision', d3.forceCollide().radius(30))

  // 绘制边
  const links = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(filteredEdges.value)
    .join('line')
    .attr('stroke', d => relationColors[d.type] || '#999')
    .attr('stroke-width', d => Math.max(1, d.strength * 3))
    .attr('marker-end', d => `url(#arrow-${d.type})`)
    .attr('opacity', 0.6)

  // 绘制节点
  const nodeElements = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)
    )
    .on('click', (event, d) => showNodeDetail(d))

  // 节点圆形
  nodeElements.append('circle')
    .attr('r', 20)
    .attr('fill', '#4ECDC4')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  // 节点标签
  nodeElements.append('text')
    .text(d => d.data.title ? d.data.title.substring(0, 15) + '...' : 'Paper')
    .attr('x', 25)
    .attr('y', 5)
    .attr('font-size', '10px')
    .attr('fill', '#333')

  // 更新位置
  simulation.on('tick', () => {
    links
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeElements
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })
}

const showNodeDetail = (nodeData) => {
  selectedNode.value = { data: nodeData }

  // 查找关联节点
  connectedNodes.value = []
  filteredEdges.value.forEach(edge => {
    if (edge.source.id === nodeData.id) {
      const connected = graphData.value.nodes[edge.target.id]
      if (connected) {
        connectedNodes.value.push({ data: connected, relation: edge.type })
      }
    } else if (edge.target.id === nodeData.id) {
      const connected = graphData.value.nodes[edge.source.id]
      if (connected) {
        connectedNodes.value.push({ data: connected, relation: edge.type })
      }
    }
  })

  drawerVisible.value = true
}

const focusNode = (nodeId) => {
  // 缩放到指定节点
  const node = graphData.value.nodes[nodeId]
  if (node && svg) {
    const transform = d3.zoomIdentity
      .translate(
        graphContainer.value.clientWidth / 2,
        graphContainer.value.clientHeight / 2
      )
      .scale(2)
      .translate(-node.x || 0, -node.y || 0)

    svg.transition()
      .duration(750)
      .call(zoom.transform, transform)
  }
}

const dragstarted = (event, d) => {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

const dragged = (event, d) => {
  d.fx = event.x
  d.fy = event.y
}

const dragended = (event, d) => {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

const getRelationColor = (type) => {
  return relationColors[type] || '#999'
}

const refreshGraph = async () => {
  loading.value = true
  try {
    const response = await api.getKnowledgeGraph(props.paperIds)
    if (response.success) {
      graphData.value = response.data
      updateGraph()
      ElMessage.success('图谱刷新成功')
    }
  } catch (error) {
    ElMessage.error('图谱加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const resetZoom = () => {
  if (svg && zoom) {
    svg.transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity)
  }
}

// 暴露方法给父组件
defineExpose({
  refreshGraph
})

// 生命周期
onMounted(() => {
  initGraph()
  refreshGraph()

  // 响应式调整
  window.addEventListener('resize', () => {
    if (graphContainer.value && svgElement.value) {
      const width = graphContainer.value.clientWidth
      const height = graphContainer.value.clientHeight
      d3.select(svgElement.value)
        .attr('width', width)
        .attr('height', height)
    }
  })
})

// 监听props变化
watch(() => props.paperIds, () => {
  refreshGraph()
})
</script>

<style scoped>
.knowledge-graph-container {
  width: 100%;
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.graph-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.controls {
  display: flex;
  gap: 12px;
}

.graph-container {
  flex: 1;
  position: relative;
  background: #f8f9fa;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
}

.node-detail h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #303133;
}

.connected-papers {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-card {
  cursor: pointer;
}

.paper-title {
  font-size: 14px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 8px;
}

.paper-title:hover {
  text-decoration: underline;
}

.paper-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.legend-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.legend-title {
  font-weight: 600;
  margin-bottom: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.legend-color {
  width: 20px;
  height: 4px;
  border-radius: 2px;
}
</style>
