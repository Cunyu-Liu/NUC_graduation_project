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
    progressStep: ''
  },

  mutations: {
    SET_FILES(state, files) {
      state.files = files
    },

    ADD_FILE(state, file) {
      state.files.unshift(file)
    },

    REMOVE_FILE(state, filename) {
      state.files = state.files.filter(f => f.filename !== filename)
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
    }
  },

  actions: {
    async fetchFiles({ commit }) {
      try {
        const response = await api.getFiles()
        if (response.success) {
          commit('SET_FILES', response.data.files)
        }
      } catch (error) {
        console.error('获取文件列表失败:', error)
      }
    },

    async deleteFile({ commit, dispatch }, filename) {
      try {
        const response = await api.deleteFile(filename)
        if (response.success) {
          commit('REMOVE_FILE', filename)
          return true
        }
      } catch (error) {
        console.error('删除文件失败:', error)
        return false
      }
    }
  },

  getters: {
    uploadedCount: state => state.files.length
  }
})
