<template>
  <div class="cluster">
    <h2>多篇论文主题聚类分析</h2>

    <el-card class="select-card">
      <h3>选择要分析的论文（至少2篇）</h3>
      <el-table
        :data="files"
        style="width: 100%; margin-top: 20px"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="size" label="大小" :formatter="formatSize" />
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
        <i class="el-icon-data-analysis"></i> 开始聚类分析
      </el-button>
    </el-card>

    <el-card class="result-card" v-if="result">
      <h3>聚类结果</h3>

      <el-alert
        :title="`共发现 ${result.clusterCount} 个主题类别`"
        type="success"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-collapse v-model="activeClusters">
        <el-collapse-item
          v-for="(cluster, index) in Object.entries(result.clusterAnalysis)"
          :key="cluster[0]"
          :name="cluster[0]"
        >
          <template #title>
            <strong>聚类 {{ cluster[0] }}</strong>
            <el-tag style="margin-left: 10px">{{ cluster[1].paperCount }} 篇论文</el-tag>
          </template>

          <div class="cluster-content">
            <h4>核心关键词</h4>
            <el-space wrap>
              <el-tag
                v-for="(keyword, kIndex) in cluster[1].topKeywords.slice(0, 10)"
                :key="kIndex"
                type="success"
              >
                {{ keyword }}
              </el-tag>
            </el-space>

            <h4 style="margin-top: 20px">包含论文</h4>
            <ul>
              <li v-for="(paper, pIndex) in cluster[1].papers" :key="pIndex">
                {{ paper }}
              </li>
            </ul>

            <h4 style="margin-top: 20px">代表性论文</h4>
            <div
              v-for="(rep, rIndex) in cluster[1].representativePapers"
              :key="rIndex"
              class="rep-paper"
            >
              <p><strong>{{ rep.title }}</strong></p>
              <p class="rep-abstract">{{ rep.abstract }}</p>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div class="result-actions">
        <el-button @click="downloadVisualization">
          <i class="el-icon-picture"></i> 下载可视化图
        </el-button>
        <el-button @click="downloadReport">
          <i class="el-icon-document"></i> 下载聚类报告
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import api, { connectSocket } from '@/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'Cluster',
  setup() {
    const store = useStore()

    const files = computed(() => store.state.files)
    const selectedFiles = ref([])
    const options = ref({
      nClusters: 5,
      method: 'kmeans',
      language: 'chinese'
    })
    const clustering = ref(false)
    const result = ref(null)
    const activeClusters = ref(['0', '1', '2'])

    const formatSize = (row, column, size) => {
      return (size / 1024 / 1024).toFixed(2) + ' MB'
    }

    const handleSelectionChange = (selection) => {
      selectedFiles.value = selection
    }

    const startCluster = async () => {
      if (selectedFiles.value.length < 2) {
        ElMessage.warning('请至少选择2篇论文')
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
        const response = await api.clusterPapers(
          paperIds,
          options.value.nClusters,
          options.value.method,
          options.value.language
        )

        if (response.success) {
          // 格式化结果
          result.value = {
            clusterCount: response.data.n_clusters,
            clusterAnalysis: response.data.cluster_analysis
          }
          store.commit('SET_PROGRESS', { progress: 100, message: '聚类完成!' })
          ElMessage.success('聚类分析完成!')
        } else {
          ElMessage.error(response.error || '聚类失败')
        }
      } catch (error) {
        console.error('聚类错误:', error)
        ElMessage.error('聚类失败: ' + (error.message || '未知错误'))
      } finally {
        clustering.value = false
        store.commit('SHOW_PROGRESS_DIALOG', false)
      }
    }

    const downloadVisualization = () => {
      api.downloadResult('cluster', 'cluster_visualization.png')
    }

    const downloadReport = () => {
      api.downloadResult('cluster', 'cluster_report.txt')
    }

    onMounted(() => {
      store.dispatch('fetchFiles')
    })

    return {
      files,
      selectedFiles,
      options,
      clustering,
      result,
      activeClusters,
      formatSize,
      handleSelectionChange,
      startCluster,
      downloadVisualization,
      downloadReport
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
.result-card {
  margin-bottom: 20px;
}

.cluster-content h4 {
  color: #409eff;
  margin: 20px 0 10px 0;
}

.cluster-content ul {
  list-style: none;
  padding: 0;
}

.cluster-content ul li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
}

.cluster-content ul li:before {
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
  text-align: right;
}
</style>
