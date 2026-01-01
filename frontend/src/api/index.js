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
    // 使用环境变量或当前域名
    const wsUrl = import.meta.env.VITE_WS_URL || `${window.location.protocol}//${window.location.hostname}:${window.location.port || '5000'}`
    socket = io(wsUrl, {
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
  },

  // ============================================================================
  // v4.0 新增API - 论文管理
  // ============================================================================

  // 获取论文列表（新版本）
  getPapersList: (params = {}) => api.get('/papers', { params }),

  // 获取论文详情
  getPaper: (id) => api.get(`/papers/${id}`),

  // 更新论文
  updatePaper: (id, data) => api.put(`/papers/${id}`, data),

  // 删除论文
  deletePaper: (id) => api.delete(`/papers/${id}`),

  // 批量删除论文
  batchDeletePapers: (paperIds) => api.post('/papers/batch-delete', { paper_ids: paperIds }),

  // ============================================================================
  // v4.0 新增API - 分析和代码生成
  // ============================================================================

  // 分析论文
  analyzePaperV4: (paperId) => api.post(`/analyze/${paperId}`),

  // 获取研究空白列表
  getPriorityGaps: (limit = 50) => api.get('/gaps/priority', { params: { limit } }),

  // 获取研究空白详情
  getGapDetail: (gapId) => api.get(`/gaps/${gapId}`),

  // 生成代码
  generateCode: (gapId, strategy = 'method_improvement') =>
    api.post(`/gaps/${gapId}/generate-code`, { strategy }),

  // 获取生成的代码
  getCode: (codeId) => api.get(`/code/${codeId}`),

  // 修改代码
  modifyCode: (codeId, userPrompt) =>
    api.post(`/code/${codeId}/modify`, { user_prompt: userPrompt }),

  // 获取代码版本历史
  getCodeVersions: (codeId) => api.get(`/code/${codeId}/versions`),

  // ============================================================================
  // v4.0 新增API - 知识图谱
  // ============================================================================

  // 获取知识图谱数据
  getKnowledgeGraph: (paperIds = []) => {
    if (paperIds.length > 0) {
      return api.get('/knowledge-graph', { params: { paper_ids: paperIds.join(',') } })
    }
    return api.get('/knowledge-graph')
  },

  // 构建知识图谱
  buildKnowledgeGraph: (paperIds) => api.post('/knowledge-graph/build', { paper_ids: paperIds }),

  // 手动添加关系
  addRelation: (sourceId, targetId, relationType, strength = 0.5, evidence = '') =>
    api.post('/relations', {
      source_id: sourceId,
      target_id: targetId,
      relation_type: relationType,
      strength,
      evidence
    }),

  // ============================================================================
  // v4.0 新增API - 统计信息
  // ============================================================================

  // 获取统计信息
  getStatistics: () => api.get('/statistics')
}
