<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">探索知识的边界</h1>
        <p class="hero-subtitle">
          上传论文，智能分析，发现研究空白，生成实验代码
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="handleQuickStart">
            <el-icon><Upload /></el-icon>
            <span>开始分析</span>
          </button>
          <button class="btn-secondary" @click="navigateTo('/chat')">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI 助手</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-item" v-for="stat in stats" :key="stat.title">
          <div class="stat-icon" :class="stat.class">
            <el-icon :size="24"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(stat.value) }}</div>
            <div class="stat-label">{{ stat.title }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">为科研人员打造的全流程智能分析工具</p>
      </div>
      
      <div class="features-grid">
        <div 
          v-for="feature in features" 
          :key="feature.title"
          class="feature-card"
          @click="navigateTo(feature.path)"
        >
          <div class="feature-icon-wrapper" :class="feature.class">
            <el-icon :size="28"><component :is="feature.icon" /></el-icon>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.description }}</p>
          <div class="feature-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- Workflow Section -->
    <section class="workflow-section">
      <div class="section-header">
        <h2 class="section-title">快速开始</h2>
        <p class="section-subtitle">四步完成从论文到代码的完整流程</p>
      </div>
      
      <div class="workflow-steps">
        <div 
          v-for="(step, index) in workflowSteps" 
          :key="step.title"
          class="workflow-step"
          :class="{ active: activeStep >= index }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <h4 class="step-title">{{ step.title }}</h4>
            <p class="step-desc">{{ step.description }}</p>
          </div>
          <div v-if="index < workflowSteps.length - 1" class="step-connector">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import {
  Document, DataAnalysis, Folder, Search, Share,
  Cpu, DocumentChecked, Upload, ChatDotRound, ArrowRight
} from '@element-plus/icons-vue'
import api from '@/api'

export default {
  name: 'Home',
  components: {
    Document, DataAnalysis, Folder, Search, Share, 
    Cpu, DocumentChecked, Upload, ChatDotRound, ArrowRight
  },
  setup() {
    const router = useRouter()
    const store = useStore()
    const activeStep = ref(1)

    const features = ref([
      {
        title: '单篇论文分析',
        description: '上传单篇论文，生成结构化摘要，提取核心创新点与研究方法',
        icon: 'Document',
        path: '/analyze',
        class: 'primary'
      },
      {
        title: '多篇论文聚类',
        description: '分析多篇论文，发现研究趋势和主题关联，支持向量语义聚类',
        icon: 'DataAnalysis',
        path: '/cluster',
        class: 'secondary'
      },
      {
        title: '文件管理',
        description: '集中管理已上传的论文文件，支持批量操作与元数据编辑',
        icon: 'Folder',
        path: '/files',
        class: 'tertiary'
      },
      {
        title: '研究空白挖掘',
        description: '自动识别论文中的研究机会和未解决问题，评估重要性与难度',
        icon: 'Search',
        path: '/gaps',
        class: 'primary'
      },
      {
        title: '知识图谱',
        description: '可视化展示论文之间的引用和关联关系，构建学术知识网络',
        icon: 'Share',
        path: '/knowledge-graph',
        class: 'secondary'
      },
      {
        title: '智能代码生成',
        description: '基于研究空白自动生成实验代码，支持多种编程语言与框架',
        icon: 'Cpu',
        path: '/gaps',
        class: 'tertiary'
      }
    ])

    const stats = ref([
      { title: '已上传论文', value: 0, icon: 'Document', class: 'blue' },
      { title: '分析完成', value: 0, icon: 'DocumentChecked', class: 'green' },
      { title: '发现空白', value: 0, icon: 'Search', class: 'amber' },
      { title: '生成代码', value: 0, icon: 'Cpu', class: 'purple' }
    ])

    const workflowSteps = ref([
      { title: '上传论文', description: '支持PDF格式，自动提取元数据' },
      { title: '智能分析', description: '自动提取摘要、要点与研究空白' },
      { title: '发现空白', description: '挖掘研究机会与未解决问题' },
      { title: '生成代码', description: '辅助实验实现与验证' }
    ])

    const navigateTo = (path) => {
      router.push(path)
    }

    const handleQuickStart = () => {
      router.push('/analyze')
    }

    const formatNumber = (num) => {
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num.toString()
    }

    const fetchStats = async () => {
      try {
        const response = await api.getStatistics()
        if (response.success) {
          const data = response.data
          // 使用新数组确保响应式更新
          stats.value = [
            { title: '已上传论文', value: data.total_papers || 0, icon: 'Document', class: 'blue' },
            { title: '分析完成', value: data.completed_analyses || 0, icon: 'DocumentChecked', class: 'green' },
            { title: '发现空白', value: data.total_gaps || 0, icon: 'Search', class: 'amber' },
            { title: '生成代码', value: data.total_generated_code || 0, icon: 'Cpu', class: 'purple' }
          ]
          console.log('[Home] 统计数据已更新:', stats.value)
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
      features,
      stats,
      workflowSteps,
      activeStep,
      navigateTo,
      handleQuickStart,
      formatNumber
    }
  }
}
</script>

<style scoped>
@import '../styles/design-system.css';

.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* ============================================
   HERO SECTION
   ============================================ */
.hero-section {
  background: linear-gradient(135deg, var(--color-primary-800) 0%, var(--color-primary-900) 100%);
  border-radius: var(--radius-2xl);
  padding: var(--space-12) var(--space-10);
  margin-bottom: var(--space-8);
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(201, 162, 39, 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.hero-title {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: white;
  margin: 0 0 var(--space-4) 0;
  letter-spacing: var(--tracking-tight);
}

.hero-subtitle {
  font-size: var(--text-lg);
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 var(--space-8) 0;
  line-height: var(--leading-relaxed);
}

.hero-actions {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: white;
  color: var(--color-primary-800);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  background: var(--color-bg-primary);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

/* ============================================
   STATS SECTION
   ============================================ */
.stats-section {
  margin-bottom: var(--space-12);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-primary);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}

.stat-item:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.blue {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.stat-icon.green {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.stat-icon.amber {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.stat-icon.purple {
  background: #f3e8ff;
  color: #9333ea;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  line-height: 1;
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

/* ============================================
   FEATURES SECTION
   ============================================ */
.features-section {
  margin-bottom: var(--space-12);
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.section-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}

.section-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-tertiary);
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-5);
}

.feature-card {
  background: var(--color-bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--color-border-primary);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
}

.feature-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
  border-color: var(--color-border-focus);
}

.feature-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
}

.feature-icon-wrapper.primary {
  background: var(--color-primary-800);
  color: white;
}

.feature-icon-wrapper.secondary {
  background: var(--color-accent-100);
  color: var(--color-accent-600);
}

.feature-icon-wrapper.tertiary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.feature-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}

.feature-desc {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-4) 0;
}

.feature-arrow {
  position: absolute;
  bottom: var(--space-6);
  right: var(--space-6);
  width: 32px;
  height: 32px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.feature-card:hover .feature-arrow {
  background: var(--color-primary-800);
  color: white;
}

/* ============================================
   WORKFLOW SECTION
   ============================================ */
.workflow-section {
  background: var(--color-bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  border: 1px solid var(--color-border-primary);
}

.workflow-steps {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.workflow-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
}

.step-number {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: var(--color-bg-tertiary);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  margin-bottom: var(--space-4);
  transition: all var(--transition-fast);
}

.workflow-step.active .step-number {
  background: var(--color-primary-800);
  color: white;
}

.step-content {
  max-width: 160px;
}

.step-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
}

.step-desc {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

.step-connector {
  position: absolute;
  top: 24px;
  right: -50%;
  transform: translateX(50%);
  color: var(--color-border-primary);
  font-size: var(--text-lg);
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .workflow-steps {
    flex-wrap: wrap;
  }
  
  .workflow-step {
    flex: 0 0 calc(50% - var(--space-4));
    margin-bottom: var(--space-6);
  }
  
  .step-connector {
    display: none;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: var(--space-8) var(--space-5);
  }
  
  .hero-title {
    font-size: var(--text-3xl);
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }
  
  .stat-item {
    padding: var(--space-4);
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .workflow-step {
    flex: 0 0 100%;
  }
  
  .workflow-section {
    padding: var(--space-6);
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: var(--text-2xl);
  }
  
  .hero-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
