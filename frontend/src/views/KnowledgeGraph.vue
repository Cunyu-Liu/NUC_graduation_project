<template>
  <div class="knowledge-graph-page">
    <el-card class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h2>
            <i class="el-icon-share"></i>
            知识图谱
          </h2>
          <p>可视化展示论文之间的引用和关联关系</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="buildGraph" :loading="building">
            <i class="el-icon-refresh"></i>
            重新构建
          </el-button>
          <el-button @click="exportGraph">
            <i class="el-icon-download"></i>
            导出
          </el-button>
        </div>
      </div>
    </el-card>

    <KnowledgeGraph ref="graphComponent" />
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import KnowledgeGraph from '@/components/KnowledgeGraph.vue'
import axios from 'axios'

export default {
  name: 'KnowledgeGraphView',
  components: {
    KnowledgeGraph
  },
  setup() {
    const graphComponent = ref(null)
    const building = ref(false)

    const buildGraph = async () => {
      try {
        building.value = true
        const response = await axios.post('/api/knowledge-graph/build', {
          paper_ids: []
        })

        if (response.data.success) {
          ElMessage.success('知识图谱构建成功')
          if (graphComponent.value) {
            graphComponent.value.refreshGraph()
          }
        }
      } catch (error) {
        console.error('构建知识图谱失败:', error)
        ElMessage.error('构建知识图谱失败: ' + (error.response?.data?.error || error.message))
      } finally {
        building.value = false
      }
    }

    const exportGraph = () => {
      ElMessage.info('导出功能开发中')
    }

    return {
      graphComponent,
      building,
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
