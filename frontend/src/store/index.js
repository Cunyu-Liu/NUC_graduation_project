import { createStore } from 'vuex'
import api from '@/api'

export default createStore({
  state: {
    files: [],
    currentFile: null,
    showUploadDialog: false,
    showProgressDialog: false,
    progress: 0,
    progressMessage: '',
    progressStep: '',

    // 认证相关状态
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    isAuthenticated: !!localStorage.getItem('token')
  },

  mutations: {
    SET_FILES(state, files) {
      state.files = files
    },

    ADD_FILE(state, file) {
      state.files.unshift(file)
    },

    REMOVE_FILE(state, paperId) {
      state.files = state.files.filter(f => f.id !== paperId)
    },

    SET_CURRENT_FILE(state, file) {
      state.currentFile = file
    },

    SHOW_UPLOAD_DIALOG(state, show) {
      state.showUploadDialog = show
    },

    SHOW_PROGRESS_DIALOG(state, show) {
      state.showProgressDialog = show
    },

    SET_PROGRESS(state, { progress, message, step }) {
      if (progress !== undefined) state.progress = progress
      if (message !== undefined) state.progressMessage = message
      if (step !== undefined) state.progressStep = step
    },

    // 认证相关mutations
    SET_TOKEN(state, token) {
      state.token = token
      state.isAuthenticated = !!token
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    },

    SET_USER(state, user) {
      state.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        localStorage.removeItem('user')
      }
    },

    CLEAR_AUTH(state) {
      state.token = null
      state.user = null
      state.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  },

  actions: {
    async fetchFiles({ commit }) {
      try {
        const response = await api.getPapersList()
        if (response.success) {
          commit('SET_FILES', response.data)
        }
      } catch (error) {
        console.error('获取论文列表失败:', error)
      }
    },

    async deleteFile({ commit, dispatch }, paperId) {
      try {
        const response = await api.deletePaper(paperId)
        if (response.success) {
          commit('REMOVE_FILE', paperId)
          return true
        }
      } catch (error) {
        console.error('删除论文失败:', error)
        return false
      }
    },

    // 认证相关actions
    async login({ commit }, credentials) {
      try {
        const response = await api.login(credentials)

        if (response.success) {
          commit('SET_TOKEN', response.data.token)
          commit('SET_USER', response.data.user)
          return response
        }
        return response
      } catch (error) {
        console.error('登录失败:', error)
        return { success: false, error: error.message || '登录失败' }
      }
    },

    async register({ commit }, userData) {
      try {
        const response = await api.register(userData)

        if (response.success) {
          commit('SET_TOKEN', response.data.token)
          commit('SET_USER', response.data.user)
          return response
        }
        return response
      } catch (error) {
        console.error('注册失败:', error)
        return { success: false, error: error.message || '注册失败' }
      }
    },

    async logout({ commit }) {
      commit('CLEAR_AUTH')
    },

    async fetchCurrentUser({ commit, state }) {
      if (!state.token) {
        return { success: false, error: '未登录' }
      }

      try {
        const response = await api.getCurrentUser()

        if (response.success) {
          commit('SET_USER', response.data)
          return response
        }
        return response
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果token无效，清除认证状态
        if (error.response && error.response.status === 401) {
          commit('CLEAR_AUTH')
        }
        return { success: false, error: error.message || '获取用户信息失败' }
      }
    },

    async updateUser({ commit }, userData) {
      try {
        const response = await api.updateUser(userData)

        if (response.success) {
          commit('SET_USER', response.data)
          return response
        }
        return response
      } catch (error) {
        console.error('更新用户信息失败:', error)
        return { success: false, error: error.message || '更新失败' }
      }
    }
  },

  getters: {
    uploadedCount: state => state.files.length,

    // 认证相关getters
    isAuthenticated: state => state.isAuthenticated,
    currentUser: state => state.user,
    token: state => state.token
  }
})
