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
          <div class="card-icon" :style="{ background: card.color }">
            <i :class="card.icon"></i>
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
            <div class="stat-icon" :style="{ background: stat.color }">
              <i :class="stat.icon"></i>
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import axios from 'axios'

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
        path: '/analyze',
        color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      },
      {
        title: '多篇论文聚类',
        description: '分析多篇论文，发现研究趋势和主题',
        icon: 'el-icon-data-analysis',
        path: '/cluster',
        color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
      },
      {
        title: '文件管理',
        description: '查看和管理已上传的论文文件',
        icon: 'el-icon-folder',
        path: '/files',
        color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
      },
      {
        title: '研究空白挖掘',
        description: '发现论文中的研究机会和未解决问题',
        icon: 'el-icon-search',
        path: '/gaps',
        color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
      },
      {
        title: '知识图谱',
        description: '可视化论文之间的关系网络',
        icon: 'el-icon-share',
        path: '/knowledge-graph',
        color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
      }
    ])

    const stats = ref([
      { title: '已上传论文', value: 0, icon: 'el-icon-document', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
      { title: '分析完成', value: 0, icon: 'el-icon-data-analysis', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
      { title: '发现空白', value: 0, icon: 'el-icon-search', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
      { title: '生成代码', value: 0, icon: 'el-icon-cpu', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }
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
        const response = await axios.get('/api/statistics')
        if (response.data.success) {
          const data = response.data.data
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
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.welcome-banner h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.welcome-banner p {
  font-size: 16px;
  opacity: 0.9;
}

.section-title {
  font-size: 24px;
  color: #303133;
  margin-bottom: 20px;
  font-weight: 600;
}

.feature-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.card-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: white;
  font-size: 36px;
}

.feature-card h3 {
  margin: 15px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.feature-card p {
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}

.stats-section {
  margin-top: 40px;
  margin-bottom: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  overflow: hidden;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  margin-right: 15px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 5px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
}

.quick-start {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>
