<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in cards" :key="card.title">
        <el-card class="feature-card" @click="navigateTo(card.path)">
          <div class="card-icon">
            <i :class="card.icon"></i>
          </div>
          <h3>{{ card.title }}</h3>
          <p>{{ card.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-divider />

    <div class="stats">
      <h2>系统统计</h2>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="8">
          <el-statistic title="已上传论文" :value="stats.fileCount" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="已生成摘要" :value="stats.summaryCount" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="已提取要点" :value="stats.keypointCount" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const store = useStore()

    const cards = ref([
      {
        title: '单篇论文分析',
        description: '上传单篇论文，生成摘要并提取要点',
        icon: 'el-icon-document',
        path: '/analyze'
      },
      {
        title: '多篇论文聚类',
        description: '分析多篇论文，发现研究趋势和主题',
        icon: 'el-icon-data-analysis',
        path: '/cluster'
      },
      {
        title: '文件管理',
        description: '查看和管理已上传的论文文件',
        icon: 'el-icon-folder',
        path: '/files'
      }
    ])

    const stats = ref({
      fileCount: 0,
      summaryCount: 0,
      keypointCount: 0
    })

    const navigateTo = (path) => {
      router.push(path)
    }

    onMounted(async () => {
      await store.dispatch('fetchFiles')
      stats.value.fileCount = store.getters.uploadedCount
    })

    return {
      cards,
      stats,
      navigateTo
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 15px 0;
  font-size: 18px;
  color: #303133;
}

.feature-card p {
  color: #909399;
  font-size: 14px;
  line-height: 1.5;
}

.stats {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stats h2 {
  margin-bottom: 20px;
  color: #303133;
}
</style>
