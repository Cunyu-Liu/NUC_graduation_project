<template>
  <div class="profile">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h2>个人信息</h2>
          <el-button type="primary" @click="editMode = !editMode">
            {{ editMode ? '取消编辑' : '编辑资料' }}
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form
            v-if="editMode"
            :model="editForm"
            :rules="rules"
            ref="editFormRef"
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="editForm.username" disabled />
            </el-form-item>

            <el-form-item label="姓名" prop="full_name">
              <el-input v-model="editForm.full_name" placeholder="请输入真实姓名" />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="editForm.email" type="email" placeholder="请输入邮箱地址" />
            </el-form-item>

            <el-form-item label="单位" prop="organization">
              <el-input v-model="editForm.organization" placeholder="请输入所在单位" />
            </el-form-item>

            <el-form-item label="研究方向" prop="research_interests">
              <el-input
                v-model="editForm.research_interests"
                type="textarea"
                :rows="3"
                placeholder="请输入您的研究方向和兴趣"
              />
            </el-form-item>

            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="editForm.bio"
                type="textarea"
                :rows="4"
                placeholder="请输入个人简介"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveProfile" :loading="saving">
                保存
              </el-button>
              <el-button @click="cancelEdit">取消</el-button>
            </el-form-item>
          </el-form>

          <el-descriptions v-else :column="2" border class="profile-info">
            <el-descriptions-item label="用户名">
              {{ userInfo.username }}
            </el-descriptions-item>
            <el-descriptions-item label="姓名">
              {{ userInfo.full_name || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ userInfo.email || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="单位">
              {{ userInfo.organization || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="研究方向" :span="2">
              {{ userInfo.research_interests || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="个人简介" :span="2">
              {{ userInfo.bio || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">
              {{ formatDate(userInfo.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后登录">
              {{ formatDate(userInfo.last_login) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            label-width="120px"
            class="password-form"
            style="max-width: 600px"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPassword">
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 统计信息 -->
        <el-tab-pane label="统计信息" name="stats">
          <div class="stats-header">
            <h3>数据统计</h3>
            <el-button size="small" @click="refreshStatistics" :icon="Refresh">
              刷新
            </el-button>
          </div>
          <el-row :gutter="20" class="stats-row">
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-content">
                  <el-icon class="stat-icon" color="#409eff" :size="40"><Document /></el-icon>
                  <div class="stat-details">
                    <div class="stat-number">{{ stats.total_papers }}</div>
                    <div class="stat-label">上传论文</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-content">
                  <el-icon class="stat-icon" color="#67c23a" :size="40"><DataAnalysis /></el-icon>
                  <div class="stat-details">
                    <div class="stat-number">{{ stats.total_analyses }}</div>
                    <div class="stat-label">分析次数</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-content">
                  <el-icon class="stat-icon" color="#e6a23c" :size="40"><Star /></el-icon>
                  <div class="stat-details">
                    <div class="stat-number">{{ stats.total_gaps }}</div>
                    <div class="stat-label">发现空白</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-card class="recent-activity" style="margin-top: 20px">
            <template #header>
              <h3>最近活动</h3>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in recentActivities"
                :key="index"
                :timestamp="activity.timestamp"
                :color="activity.color"
              >
                {{ activity.description }}
              </el-timeline-item>
              <el-timeline-item v-if="recentActivities.length === 0" timestamp="暂无数据">
                暂无活动记录
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Document, DataAnalysis, Star, Refresh } from '@element-plus/icons-vue'

const store = useStore()
const activeTab = ref('basic')
const editMode = ref(false)
const saving = ref(false)
const changingPassword = ref(false)

// 用户信息
const userInfo = computed(() => store.state.user || {})

// 编辑表单
const editFormRef = ref(null)
const editForm = reactive({
  username: '',
  full_name: '',
  email: '',
  organization: '',
  research_interests: '',
  bio: ''
})

const rules = {
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 密码表单
const passwordFormRef = ref(null)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 统计信息
const stats = ref({
  total_papers: 0,
  total_analyses: 0,
  total_gaps: 0
})

const recentActivities = ref([])

// 方法
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadUserProfile = async () => {
  try {
    const response = await api.getCurrentUser()
    if (response.success) {
      Object.assign(editForm, response.data)
      store.commit('SET_USER', response.data)
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
  }
}

const saveProfile = async () => {
  try {
    await editFormRef.value.validate()
    saving.value = true

    const response = await api.updateUser(editForm)

    if (response.success) {
      ElMessage.success('个人信息更新成功')
      editMode.value = false
      store.commit('SET_USER', response.data)
    } else {
      ElMessage.error(response.error || '更新失败')
    }
  } catch (error) {
    if (error !== false) { // 表单验证错误时会返回false
      console.error('保存失败:', error)
      ElMessage.error('保存失败: ' + (error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  editMode.value = false
  // 重置表单为当前用户信息
  Object.assign(editForm, userInfo.value)
}

const changePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true

    const response = await api.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })

    if (response.success) {
      ElMessage.success('密码修改成功，请重新登录')
      resetPasswordForm()
      // 延迟退出登录，让用户看到成功提示
      setTimeout(() => {
        store.dispatch('logout')
      }, 1500)
    } else {
      ElMessage.error(response.error || '密码修改失败')
    }
  } catch (error) {
    if (error !== false) {
      console.error('修改密码失败:', error)
      ElMessage.error('修改密码失败: ' + (error.message || '未知错误'))
    }
  } finally {
    changingPassword.value = false
  }
}

const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
}

const loadStatistics = async () => {
  try {
    const response = await api.getStatistics()
    if (response.success) {
      // 优先使用用户统计，如果没有则计算总数
      const userStats = response.data.user_stats
      const overview = response.data.overview
      
      stats.value = {
        total_papers: userStats?.total_papers ?? overview?.total_papers ?? 0,
        total_analyses: userStats?.total_analyses ?? overview?.total_analyses ?? 0,
        total_gaps: userStats?.total_gaps ?? overview?.total_gaps ?? 0
      }
      
      console.log('[DEBUG] 统计信息已更新:', stats.value)
    } else {
      // 如果API返回不成功，尝试从store获取
      const storeStats = store.state.statistics
      if (storeStats) {
        stats.value = {
          total_papers: storeStats.total_papers || 0,
          total_analyses: storeStats.total_analyses || 0,
          total_gaps: storeStats.total_gaps || 0
        }
      }
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
    // 尝试从store获取
    const storeStats = store.state.statistics
    if (storeStats) {
      stats.value = {
        total_papers: storeStats.total_papers || 0,
        total_analyses: storeStats.total_analyses || 0,
        total_gaps: storeStats.total_gaps || 0
      }
    }
  }
}

// 刷新统计数据
const refreshStatistics = async () => {
  await loadStatistics()
  ElMessage.success('统计信息已刷新')
}

// 监听标签页切换，切换到统计标签时刷新数据
watch(activeTab, (newVal) => {
  if (newVal === 'stats') {
    loadStatistics()
  }
})

// 生命周期
onMounted(() => {
  // 初始化编辑表单
  Object.assign(editForm, userInfo.value)
  loadUserProfile()
  loadStatistics()
  
  // 定时刷新统计信息（每30秒）
  setInterval(() => {
    if (activeTab.value === 'stats') {
      loadStatistics()
    }
  }, 30000)
})
</script>

<style scoped>
.profile {
  max-width: 1200px;
  margin: 0 auto;
}

.profile-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #303133;
}

.profile-form,
.password-form {
  padding: 20px;
  max-width: 800px;
}

.profile-info {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.stat-icon {
  flex-shrink: 0;
}

.stat-details {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.recent-activity h3 {
  margin: 0;
  color: #303133;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
</style>
