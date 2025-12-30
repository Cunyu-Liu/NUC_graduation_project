<template>
  <div class="analyze">
    <h2>单篇论文分析</h2>

    <el-card class="select-card" v-if="!currentFile">
      <h3>选择要分析的论文</h3>
      <el-table :data="files" style="width: 100%; margin-top: 20px">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="size" label="大小" :formatter="formatSize" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" size="small" @click="selectFile(scope.row)">
              分析此文件
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div v-else>
      <el-card class="file-card">
        <div class="file-info">
          <i class="el-icon-document file-icon"></i>
          <div>
            <h3>{{ currentFile.filename }}</h3>
            <p>文件大小: {{ formatSize(null, null, currentFile.size) }}</p>
          </div>
          <el-button @click="currentFile = null">选择其他文件</el-button>
        </div>
      </el-card>

      <el-card class="options-card">
        <h3>分析选项</h3>
        <el-checkbox-group v-model="selectedTasks">
          <el-checkbox label="summary">生成摘要</el-checkbox>
          <el-checkbox label="keypoints">提取要点</el-checkbox>
          <el-checkbox label="topic">主题分析</el-checkbox>
        </el-checkbox-group>

        <div style="margin-top: 20px">
          <el-button type="primary" size="large" @click="startAnalysis" :loading="analyzing">
            <i class="el-icon-video-play"></i> 开始分析
          </el-button>
        </div>
      </el-card>

      <el-card class="result-card" v-if="result">
        <h3>分析结果</h3>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="摘要" name="summary" v-if="result.summary">
            <div class="summary-content">{{ result.summary }}</div>
          </el-tab-pane>

          <el-tab-pane label="要点" name="keypoints" v-if="result.keypoints">
            <div class="keypoints-content">
              <div v-for="(items, category) in keypointsDisplay" :key="category" class="keypoint-category">
                <h4>{{ categoryNames[category] }}</h4>
                <ul>
                  <li v-for="(item, index) in items" :key="index">{{ item }}</li>
                </ul>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="主题分析" name="topic" v-if="result.topicAnalysis">
            <div class="topic-content">{{ result.topicAnalysis.analysis }}</div>
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
import { ElMessage } from 'element-plus'

export default {
  name: 'Analyze',
  setup() {
    const store = useStore()

    const files = computed(() => store.state.files)
    const currentFile = ref(null)
    const selectedTasks = ref(['summary', 'keypoints', 'topic'])
    const analyzing = ref(false)
    const result = ref(null)
    const activeTab = ref('summary')

    const categoryNames = {
      innovations: '核心创新点',
      methods: '主要方法',
      experiments: '实验设计',
      conclusions: '主要结论',
      contributions: '学术贡献',
      limitations: '局限性'
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

    const formatSize = (row, column, size) => {
      return (size / 1024 / 1024).toFixed(2) + ' MB'
    }

    const selectFile = (file) => {
      currentFile.value = file
      result.value = null
    }

    const startAnalysis = async () => {
      if (selectedTasks.value.length === 0) {
        ElMessage.warning('请至少选择一项分析任务')
        return
      }

      // 连接WebSocket
      connectSocket()
      store.commit('SHOW_PROGRESS_DIALOG', true)
      store.commit('SET_PROGRESS', { progress: 0, message: '开始分析...', step: '' })

      analyzing.value = true

      try {
        const response = await api.analyzePaper(
          `/uploads/${currentFile.value.filename}`,
          selectedTasks.value
        )

        if (response.success) {
          result.value = response.data
          store.commit('SET_PROGRESS', { progress: 100, message: '分析完成!' })
          ElMessage.success('分析完成!')
        } else {
          ElMessage.error(response.error || '分析失败')
        }
      } catch (error) {
        ElMessage.error('分析失败: ' + error.message)
      } finally {
        analyzing.value = false
      }
    }

    const downloadResult = () => {
      const filename = currentFile.value.filename.replace('.pdf', '')
      if (activeTab.value === 'summary') {
        api.downloadResult('summary', `${filename}_summary.txt`)
      } else if (activeTab.value === 'keypoints') {
        api.downloadResult('keypoints', `${filename}_keypoints.txt`)
      }
    }

    onMounted(() => {
      store.dispatch('fetchFiles')
    })

    return {
      files,
      currentFile,
      selectedTasks,
      analyzing,
      result,
      activeTab,
      categoryNames,
      keypointsDisplay,
      formatSize,
      selectFile,
      startAnalysis,
      downloadResult
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
.file-card,
.options-card,
.result-card {
  margin-bottom: 20px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.file-icon {
  font-size: 48px;
  color: #409eff;
}

.summary-content,
.topic-content {
  line-height: 1.8;
  color: #303133;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
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

.result-actions {
  margin-top: 20px;
  text-align: right;
}
</style>
