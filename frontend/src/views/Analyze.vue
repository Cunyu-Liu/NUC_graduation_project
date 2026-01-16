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
          <i class="el-icon-document paper-icon"></i>
          <div class="paper-details">
            <h3>{{ currentPaper.title || '未命名论文' }}</h3>
            <p>年份: {{ currentPaper.year || '未知' }} | 发表于: {{ currentPaper.venue || '未知' }}</p>
          </div>
          <el-button @click="currentPaper = null">选择其他论文</el-button>
        </div>
      </el-card>

      <el-card class="options-card">
        <h3>分析选项</h3>
        <el-checkbox-group v-model="selectedTasks">
          <el-checkbox label="summary">生成摘要</el-checkbox>
          <el-checkbox label="keypoints">提取要点</el-checkbox>
          <el-checkbox label="gaps">研究空白挖掘</el-checkbox>
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
                <h4>研究空白 #{{ index + 1 }}</h4>
                <p><strong>类型:</strong> {{ gap.gap_type }}</p>
                <p><strong>描述:</strong> {{ gap.description }}</p>
                <p><strong>重要性:</strong> {{ gap.importance }}/10</p>
                <p v-if="gap.potential_approach"><strong>潜在方案:</strong> {{ gap.potential_approach }}</p>
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
import { ElMessage } from 'element-plus'

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

    const selectPaper = (paper) => {
      currentPaper.value = paper
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
        const response = await api.analyzePaperV4(
          currentPaper.value.id,
          selectedTasks.value,
          true  // auto_generate_code
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
      categoryNames,
      keypointsDisplay,
      selectPaper,
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

.summary-content {
  line-height: 1.8;
  color: #303133;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
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

.gap-item h4 {
  color: #409eff;
  margin-bottom: 12px;
}

.gap-item p {
  margin: 8px 0;
  line-height: 1.6;
}

.result-actions {
  margin-top: 20px;
  text-align: right;
}
</style>
