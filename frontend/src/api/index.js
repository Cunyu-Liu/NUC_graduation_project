import axios from 'axios'
import { io } from 'socket.io-client'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 300000 // 5分钟超时
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API错误:', error)
    return Promise.reject(error)
  }
)

// WebSocket连接
let socket = null

export const connectSocket = () => {
  if (!socket) {
    socket = io('http://localhost:5000', {
      transports: ['websocket', 'polling']
    })

    socket.on('connect', () => {
      console.log('WebSocket已连接')
    })

    socket.on('disconnect', () => {
      console.log('WebSocket已断开')
    })

    socket.on('progress', (data) => {
      console.log('进度更新:', data)
    })
  }
  return socket
}

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export const getSocket = () => {
  if (!socket) {
    return connectSocket()
  }
  return socket
}

// API接口
export default {
  // 健康检查
  healthCheck: () => api.get('/health'),

  // 获取配置
  getConfig: () => api.get('/config'),

  // 文件上传
  uploadFile: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取文件列表
  getFiles: () => api.get('/files'),

  // 删除文件
  deleteFile: (filename) => api.delete(`/files/${filename}`),

  // 解析PDF
  parsePDF: (filepath) => api.post('/parse', { filepath }),

  // 生成摘要
  generateSummary: (filepath, model, temperature) =>
    api.post('/summarize', { filepath, model, temperature }),

  // 提取要点
  extractKeypoints: (filepath, model) =>
    api.post('/extract', { filepath, model }),

  // 完整分析
  analyzePaper: (filepath, tasks) =>
    api.post('/analyze', { filepath, tasks }),

  // 主题聚类
  clusterPapers: (filepaths, nClusters, method, language) =>
    api.post('/cluster', { filepaths, nClusters, method, language }),

  // 下载结果
  downloadResult: (type, filename) => {
    const url = `/api/download/${type}/${filename}`
    window.open(url, '_blank')
  }
}
