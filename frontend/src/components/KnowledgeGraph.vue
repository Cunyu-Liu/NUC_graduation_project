<template>
  <div class="knowledge-graph-container">
    <div class="graph-header">
      <h2>知识图谱可视化</h2>
      <div class="controls">
        <el-button @click="refreshGraph" icon="Refresh" :loading="loading">刷新</el-button>
        <el-button @click="fitGraphToView" icon="FullScreen">适应视图</el-button>
        <el-button @click="resetZoom" icon="ZoomOut">重置缩放</el-button>
        <el-select v-model="relationFilter" placeholder="关系类型" multiple style="width: 200px">
          <el-option v-for="type in relationTypes" :key="type" :label="relationTypeNames[type] || type" :value="type" />
        </el-select>
      </div>
    </div>

    <!-- SVG容器 -->
    <div ref="graphContainer" class="graph-container">
      <svg ref="svgElement" width="100%" height="100%"></svg>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && Object.keys(graphData.nodes).length === 0"
        description="暂无图谱数据，请先分析论文或构建图谱"
        class="graph-empty"
      >
        <el-button type="primary" @click="$emit('build')">构建知识图谱</el-button>
      </el-empty>

      <!-- 只有节点没有边的情况 -->
      <el-alert
        v-if="!loading && Object.keys(graphData.nodes).length > 0 && filteredEdges.length === 0"
        title="论文已加载，暂无关系数据"
        type="info"
        :closable="false"
        class="graph-info"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在构建知识图谱...</p>
    </div>

    <!-- 节点详情面板 -->
    <el-drawer v-model="drawerVisible" title="节点详情" size="400px" direction="rtl">
      <div v-if="selectedNode" class="node-detail">
        <h3>{{ selectedNode.data.title || '未命名论文' }}</h3>
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
              {{ node.data.title || '未命名论文' }}
            </div>
            <div class="paper-meta">
              <el-tag size="small" type="info">{{ relationTypeNames[node.relation] || node.relation }}</el-tag>
              <span>{{ node.data.year || '未知年份' }}</span>
              <span>{{ node.data.venue || '未知期刊' }}</span>
            </div>
          </el-card>
        </div>
        <el-empty v-else description="无关联论文" />
      </div>
    </el-drawer>

    <!-- 图例 -->
    <div class="legend-panel" v-if="relationTypes.length > 0">
      <div class="legend-title">关系类型</div>
      <div v-for="type in relationTypes" :key="type" class="legend-item">
        <span class="legend-color" :style="{ backgroundColor: getRelationColor(type) }"></span>
        <span class="legend-label">{{ relationTypeNames[type] || type }}</span>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-panel" v-if="!loading">
      <el-tag type="info">节点: {{ Object.keys(graphData.nodes).length }}</el-tag>
      <el-tag type="success" style="margin-left: 8px;">关系: {{ filteredEdges.length }}</el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
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

const emit = defineEmits(['build'])

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

// 关系类型颜色映射（支持中文和英文）
const relationColors = {
  // 中文关系类型 - 新增多种有价值关系
  '主题相似': '#E74C3C',      // 红色 - 内容相似
  '关键词共享': '#3498DB',    // 蓝色 - 关键词
  '同一会刊': '#9B59B6',      // 紫色 - 会刊
  '共同作者': '#F39C12',      // 橙色 - 作者
  '引用关系': '#27AE60',      // 绿色 - 引用
  '方法相似': '#1ABC9C',      // 青色 - 方法
  '研究脉络': '#E91E63',      // 粉色 - 演进
  // 英文关系类型（兼容旧数据）
  'cites': '#27AE60',
  'extends': '#3498DB',
  'improves': '#1ABC9C',
  'applies': '#F39C12',
  'contradicts': '#E74C3C',
  'related': '#9B59B6',
  'similar': '#E74C3C',
  'similar_topic': '#E74C3C',
  'shares_keywords': '#3498DB',
  'same_venue': '#9B59B6',
  'same_author': '#F39C12',
  'method_similar': '#1ABC9C',
  'evolution': '#E91E63'
}

// 关系类型中文映射
const relationTypeNames = {
  // 中文关系类型 - 新增关系
  '主题相似': '主题相似',
  '关键词共享': '关键词共享',
  '同一会刊': '同一会刊',
  '共同作者': '共同作者',
  '引用关系': '引用关系',
  '方法相似': '方法相似',
  '研究脉络': '研究脉络',
  // 英文关系类型映射为中文（兼容旧数据）
  'cites': '引用',
  'extends': '扩展',
  'improves': '改进',
  'applies': '应用',
  'contradicts': '矛盾',
  'related': '相关',
  'similar': '相似',
  'similar_topic': '主题相似',
  'shares_keywords': '关键词共享',
  'same_venue': '同一会刊',
  'same_author': '共同作者',
  'method_similar': '方法相似',
  'evolution': '研究脉络',

}

// 计算属性
const relationTypes = computed(() => {
  const types = new Set()
  graphData.value.edges.forEach(edge => {
    if (edge.type) types.add(edge.type)
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

  // 清除之前的SVG内容
  d3.select(svgElement.value).selectAll('*').remove()

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

  // 添加箭头标记 - 调整位置以适应更大的节点间距
  const defs = svg.append('defs')
  Object.keys(relationColors).forEach(type => {
    defs.append('marker')
      .attr('id', `arrow-${type}`)
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 35)  // 从25增加到35，适应更大的节点间距
      .attr('refY', 5)
      .attr('markerWidth', 8)  // 稍微增大箭头
      .attr('markerHeight', 8)
      .attr('orient', 'auto-start-reverse')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z')
      .attr('fill', relationColors[type])
  })
}

const updateGraph = () => {
  if (!g) return

  // 清除之前的内容
  g.selectAll('*').remove()

  // 准备节点数据
  const nodes = Object.entries(graphData.value.nodes).map(([id, data]) => ({
    id: parseInt(id),
    ...data
  }))

  // 检查是否有数据
  if (nodes.length === 0) {
    console.log('[DEBUG] 没有节点数据')
    return
  }

  console.log(`[DEBUG] 渲染图谱: ${nodes.length} 个节点, ${filteredEdges.value.length} 条边`)

  // 创建节点映射用于边的连接
  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  // 准备边数据 - 确保source和target引用节点对象
  const links = filteredEdges.value.map(edge => ({
    ...edge,
    source: nodeMap.get(edge.source),
    target: nodeMap.get(edge.target)
  })).filter(edge => edge.source && edge.target) // 过滤掉无效的边

  // 创建力导向布局 - 调整参数使节点间距更大
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id(d => d.id)
      .distance(250)  // 从150增加到250，连接节点距离更远
    )
    .force('charge', d3.forceManyBody()
      .strength(-800)  // 从-400增加到-800，斥力更强，节点更分散
      .distanceMin(50)  // 最小作用距离，防止节点过度聚集
      .distanceMax(800) // 最大作用距离
    )
    .force('center', d3.forceCenter(
      graphContainer.value.clientWidth / 2,
      graphContainer.value.clientHeight / 2
    ))
    .force('collision', d3.forceCollide().radius(d => {
      // 根据节点连接数动态调整碰撞半径
      const connectionCount = links.filter(l => l.source.id === d.id || l.target.id === d.id).length
      return 60 + Math.min(connectionCount * 5, 30)  // 基础60，根据连接数增加
    }))
    .force('x', d3.forceX(graphContainer.value.clientWidth / 2).strength(0.05))  // 添加水平方向弱引力
    .force('y', d3.forceY(graphContainer.value.clientHeight / 2).strength(0.05)) // 添加垂直方向弱引力

  // 绘制边 - 加粗线条以适应更大的间距
  const linkElements = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', d => relationColors[d.type] || '#999')
    .attr('stroke-width', d => Math.max(2.5, d.strength * 5 || 2.5))  // 加粗线条
    .attr('marker-end', d => `url(#arrow-${d.type})`)
    .attr('opacity', 0.75)

  // 绘制边标签 - 优化显示
  const linkLabels = g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(links)
    .join('text')
    .text(d => relationTypeNames[d.type] || d.type)
    .attr('font-size', '11px')  // 稍大字体
    .attr('fill', '#444')  // 更深的颜色
    .attr('text-anchor', 'middle')
    .attr('dy', -8)  // 离线条更远
    .attr('font-weight', '500')  // 加粗
    .style('text-shadow', '1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white')  // 添加白色描边

  // 绘制节点组
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

  // 节点圆形 - 增大节点大小以适应更大的间距
  nodeElements.append('circle')
    .attr('r', d => {
      const connectionCount = links.filter(l => l.source.id === d.id || l.target.id === d.id).length
      return 28 + Math.min(connectionCount * 4, 20)  // 从20增加到28，节点更大
    })
    .attr('fill', d => {
      const connectionCount = links.filter(l => l.source.id === d.id || l.target.id === d.id).length
      // 连接越多，颜色越深
      return d3.interpolateBlues(0.3 + Math.min(connectionCount * 0.1, 0.5))
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 3)  // 边框加粗
    .style('cursor', 'pointer')

  // 节点标签 - 调整位置，显示更多文字
  nodeElements.append('text')
    .text(d => {
      const title = d.title || d.data?.title || 'Paper'
      return title.length > 16 ? title.substring(0, 16) + '...' : title  // 从12增加到16
    })
    .attr('x', 0)
    .attr('y', 45)  // 从35增加到45，适应更大的节点
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')  // 字体稍大
    .attr('fill', '#333')
    .attr('font-weight', '500')

  // 更新位置
  simulation.on('tick', () => {
    linkElements
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    linkLabels
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2)

    nodeElements
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })
}

const showNodeDetail = (nodeData) => {
  selectedNode.value = { data: nodeData }

  // 查找关联节点
  connectedNodes.value = []
  filteredEdges.value.forEach(edge => {
    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source
    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target

    if (sourceId === nodeData.id) {
      const connected = graphData.value.nodes[targetId]
      if (connected) {
        connectedNodes.value.push({ data: connected, relation: edge.type })
      }
    } else if (targetId === nodeData.id) {
      const connected = graphData.value.nodes[sourceId]
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
      console.log('[DEBUG] 获取到图谱数据:', graphData.value)

      // 等待DOM更新后再初始化图谱
      await nextTick()
      initGraph()
      updateGraph()

      // 自适应缩放，使所有节点可见
      setTimeout(() => {
        fitGraphToView()
      }, 500)

      const nodeCount = Object.keys(graphData.value.nodes).length
      const edgeCount = graphData.value.edges.length

      if (nodeCount > 0) {
        ElMessage.success(`图谱加载成功: ${nodeCount} 个节点, ${edgeCount} 条边`)
      } else {
        ElMessage.info('暂无图谱数据，请先分析论文')
      }
    } else {
      ElMessage.error(response.error || '图谱加载失败')
    }
  } catch (error) {
    console.error('图谱加载失败:', error)
    ElMessage.error('图谱加载失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const fitGraphToView = () => {
  // 自适应缩放，使所有节点可见
  if (!g || !svg) return
  
  const nodeElements = g.selectAll('.node')
  if (nodeElements.empty()) return
  
  const containerWidth = graphContainer.value.clientWidth
  const containerHeight = graphContainer.value.clientHeight
  
  // 获取所有节点的位置范围
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  
  nodeElements.each(function(d) {
    if (d.x !== undefined && d.y !== undefined) {
      minX = Math.min(minX, d.x)
      maxX = Math.max(maxX, d.x)
      minY = Math.min(minY, d.y)
      maxY = Math.max(maxY, d.y)
    }
  })
  
  if (minX === Infinity) return
  
  // 添加边距
  const padding = 100
  minX -= padding
  maxX += padding
  minY -= padding
  maxY += padding
  
  const graphWidth = maxX - minX
  const graphHeight = maxY - minY
  
  if (graphWidth === 0 || graphHeight === 0) return
  
  // 计算合适的缩放比例
  const scaleX = containerWidth / graphWidth
  const scaleY = containerHeight / graphHeight
  const scale = Math.min(scaleX, scaleY, 1) * 0.9  // 最大缩放1，留10%边距
  
  // 计算平移量，使图谱居中
  const translateX = (containerWidth - (minX + maxX) * scale) / 2
  const translateY = (containerHeight - (minY + maxY) * scale) / 2
  
  const transform = d3.zoomIdentity
    .translate(translateX, translateY)
    .scale(scale)
  
  svg.transition()
    .duration(750)
    .call(zoom.transform, transform)
}

const resetZoom = () => {
  // 自适应重置，使所有节点可见
  fitGraphToView()
}

// 暴露方法给父组件
defineExpose({
  refreshGraph,
  fitGraphToView
})

// 生命周期
onMounted(async () => {
  await refreshGraph()

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

// 监听过滤器变化
watch(relationFilter, () => {
  updateGraph()
})
</script>

<style scoped>
.knowledge-graph-container {
  width: 100%;
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  background: white;
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
  overflow: hidden;
}

.graph-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.graph-info {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: auto;
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
  z-index: 10;
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
  max-height: 200px;
  overflow-y: auto;
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

.stats-panel {
  position: absolute;
  bottom: 20px;
  left: 20px;
}
</style>
