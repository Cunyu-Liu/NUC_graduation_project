<template>
  <div class="home">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <h1>欢迎使用科研文献智能分析系统</h1>
      <p>上传论文，智能分析，发现研究空白</p>
    </div>

    <!-- 功能卡片 -->
    <h2 class="section-title">核心功能</h2>
    <el-row :gutter="20">
      <el-col :span="8" v-for="card in cards" :key="card.title">
        <el-card class="feature-card" @click="navigateTo(card.path)" shadow="hover">
          <div class="card-icon" :style="{ backgroundColor: card.color }">
            <el-icon :size="36" color="#fff"><component :is="card.icon" /></el-icon>
          </div>
          <h3>{{ card.title }}</h3>
          <p>{{ card.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统统计 -->
    <div class="stats-section">
      <h2 class="section-title">系统统计</h2>
      <el-row :gutter="20">
        <el-col :span="6" v-for="stat in stats" :key="stat.title">
          <el-card class="stat-card">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="28" color="#fff"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 快速开始 -->
    <div class="quick-start">
      <h2 class="section-title">快速开始</h2>
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="上传论文" description="支持PDF格式"></el-step>
        <el-step title="智能分析" description="自动提取摘要和要点"></el-step>
        <el-step title="发现空白" description="挖掘研究机会"></el-step>
        <el-step title="生成代码" description="辅助实验实现"></el-step>
      </el-steps>
      <div style="text-align: center; margin-top: 30px">
        <el-button type="primary" size="large" @click="handleQuickStart">
          立即开始
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import {
  Document, DataAnalysis, Folder, Search, Share,
  Cpu, DocumentChecked
} from '@element-plus/icons-vue'
import api from '@/api'

export default {
  name: 'Home',
  components: {
    Document, DataAnalysis, Folder, Search, Share, Cpu, DocumentChecked
  },
  setup() {
    const router = useRouter()
    const store = useStore()

    const cards = ref([
      {
        title: '单篇论文分析',
        description: '上传单篇论文，生成摘要并提取要点',
        icon: 'Document',
        path: '/analyze',
        color: '#1890ff'
      },
      {
        title: '多篇论文聚类',
        description: '分析多篇论文，发现研究趋势和主题',
        icon: 'DataAnalysis',
        path: '/cluster',
        color: '#52c41a'
      },
      {
        title: '文件管理',
        description: '查看和管理已上传的论文文件',
        icon: 'Folder',
        path: '/files',
        color: '#faad14'
      },
      {
        title: '研究空白挖掘',
        description: '发现论文中的研究机会和未解决问题',
        icon: 'Search',
        path: '/gaps',
        color: '#722ed1'
      },
      {
        title: '知识图谱',
        description: '可视化论文之间的关系网络',
        icon: 'Share',
        path: '/knowledge-graph',
        color: '#eb2f96'
      }
    ])

    const stats = ref([
      { title: '已上传论文', value: 0, icon: 'Document', color: '#1890ff' },
      { title: '分析完成', value: 0, icon: 'DocumentChecked', color: '#52c41a' },
      { title: '发现空白', value: 0, icon: 'Search', color: '#722ed1' },
      { title: '生成代码', value: 0, icon: 'Cpu', color: '#faad14' }
    ])

    const activeStep = ref(0)

    const navigateTo = (path) => {
      router.push(path)
    }

    const handleQuickStart = () => {
      router.push('/analyze')
    }

    const fetchStats = async () => {
      try {
        const response = await api.getStatistics()
        if (response.success) {
          const data = response.data
          stats.value[0].value = data.total_papers || 0
          stats.value[1].value = data.completed_analyses || 0
          stats.value[2].value = data.total_gaps || 0
          stats.value[3].value = data.total_generated_code || 0
        }
      } catch (error) {
        console.error('获取统计数据失败:', error)
      }
    }

    onMounted(async () => {
      await store.dispatch('fetchFiles')
      await fetchStats()
    })

    return {
      cards,
      stats,
      activeStep,
      navigateTo,
      handleQuickStart
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-banner {
  background-color: #1890ff;
  color: white;
  padding: 48px 40px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 40px;
}

.welcome-banner h1 {
  font-size: 28px;
  margin-bottom: 12px;
  font-weight: 500;
}

.welcome-banner p {
  font-size: 16px;
  opacity: 0.85;
  font-weight: 400;
}

.section-title {
  font-size: 20px;
  color: #262626;
  margin-bottom: 20px;
  font-weight: 500;
  padding-left: 12px;
  border-left: 4px solid #1890ff;
}

.feature-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  border: none;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 8px auto 16px;
}

.feature-card h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #262626;
  font-weight: 500;
}

.feature-card p {
  color: #8c8c8c;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.stats-section {
  margin-top: 40px;
  margin-bottom: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  border: none;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
  line-height: 1;
}

.stat-title {
  font-size: 14px;
  color: #8c8c8c;
}

.quick-start {
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
</style>
