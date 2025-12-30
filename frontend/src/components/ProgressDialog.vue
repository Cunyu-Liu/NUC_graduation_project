<template>
  <el-dialog
    v-model="visible"
    title="处理中"
    width="400px"
    :close-on-click-modal="false"
    :show-close="false"
  >
    <div class="progress-content">
      <el-progress
        :percentage="progress"
        :status="progress === 100 ? 'success' : undefined"
      />
      <p class="message">{{ message }}</p>
      <p class="step" v-if="step">{{ step }}</p>
    </div>
  </el-dialog>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { getSocket } from '@/api'

export default {
  name: 'ProgressDialog',
  setup() {
    const store = useStore()

    const visible = computed({
      get: () => store.state.showProgressDialog,
      set: (val) => store.commit('SHOW_PROGRESS_DIALOG', val)
    })

    const progress = computed(() => store.state.progress)
    const message = computed(() => store.state.progressMessage)
    const step = computed(() => store.state.progressStep)

    // 监听WebSocket进度
    const socket = getSocket()
    socket.on('progress', (data) => {
      store.commit('SET_PROGRESS', {
        progress: data.progress,
        message: data.message,
        step: data.step
      })

      if (data.progress >= 100) {
        setTimeout(() => {
          store.commit('SHOW_PROGRESS_DIALOG', false)
        }, 1000)
      }
    })

    return {
      visible,
      progress,
      message,
      step
    }
  }
}
</script>

<style scoped>
.progress-content {
  padding: 20px 0;
  text-align: center;
}

.message {
  margin-top: 20px;
  font-size: 16px;
  color: #303133;
}

.step {
  margin-top: 10px;
  font-size: 14px;
  color: #909399;
}
</style>
