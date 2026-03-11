<template>
  <div class="kimi-chat-container">
    <!-- 左侧边栏 -->
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <!-- 新建对话按钮 -->
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewChat">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </button>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </button>
      </div>

      <!-- 对话历史列表 -->
      <div class="chat-history">
        <div
          v-for="chat in chatHistory"
          :key="chat.chat_id"
          class="chat-item"
          :class="{ active: currentChatId === chat.chat_id }"
          @click="switchChat(chat.chat_id)"
        >
          <el-icon class="chat-icon"><ChatLineRound /></el-icon>
          <span class="chat-title">{{ chat.preview || '新对话' }}</span>
          <div class="chat-actions" @click.stop>
            <el-dropdown trigger="click" :teleported="false">
              <el-icon class="more-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="renameChat(chat.chat_id)">
                    <el-icon><Edit /></el-icon> 重命名
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="deleteChat(chat.chat_id)" class="danger">
                    <el-icon><Delete /></el-icon> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 底部设置 -->
      <div class="sidebar-footer">
        <button class="footer-btn" @click="showSettings = true">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </button>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <!-- 顶部导航 -->
      <header class="chat-header">
        <div class="header-left">
          <h2 class="chat-title">{{ currentChatTitle }}</h2>
          <el-tag v-if="selectedPapers.length > 0" type="success" size="small">
            已关联 {{ selectedPapers.length }} 篇论文
          </el-tag>
        </div>
        <div class="header-right">
          <el-select v-model="currentModel" size="small" class="model-select">
            <el-option label="GLM-4-Plus" value="glm-4-plus" />
            <el-option label="GLM-4-Flash" value="glm-4-flash" />
          </el-select>
          <el-tooltip content="关联论文">
            <el-button circle size="small" @click="showPaperSelector = true">
              <el-icon><Document /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空对话">
            <el-button circle size="small" @click="clearCurrentChat">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </header>

      <!-- 消息列表区域 -->
      <div ref="messagesContainer" class="messages-area">
        <!-- 欢迎页面 -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-logo">
            <el-icon :size="80" color="#2d2d2d"><ChatDotRound /></el-icon>
          </div>
          <h1 class="welcome-title">AI <span class="accent">科研助手</span></h1>
          <p class="welcome-subtitle">
            基于您的论文库，提供深度文献分析、研究建议、代码生成等服务
          </p>

          <!-- 快捷功能卡片 -->
          <div class="quick-cards">
            <div
              v-for="card in quickCards"
              :key="card.key"
              class="quick-card"
              @click="sendQuickMessage(card.prompt)"
            >
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
              <span>{{ card.label }}</span>
            </div>
          </div>

          <!-- 示例问题 -->
          <div class="example-questions">
            <div class="section-title">你可以这样问我：</div>
            <div class="question-tags">
              <el-tag
                v-for="q in exampleQuestions"
                :key="q"
                class="question-tag"
                effect="plain"
                @click="sendMessage(q)"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <template v-else>
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message-wrapper"
            :class="{ 'user-message': message.role === 'user', 'ai-message': message.role === 'assistant' }"
          >
            <div class="message-avatar">
              <el-avatar
                v-if="message.role === 'user'"
                :size="36"
                :src="userAvatar"
              >
                {{ userInitial }}
              </el-avatar>
              <div v-else class="ai-avatar">
                <el-icon :size="20"><Cpu /></el-icon>
              </div>
            </div>

            <div class="message-content">
              <!-- 消息头部 -->
              <div class="message-header">
                <span class="message-role">{{ message.role === 'user' ? '我' : 'AI 助手' }}</span>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              </div>

              <!-- 消息体 -->
              <div class="message-body" v-html="renderMessage(message.content)"></div>

              <!-- 引用论文 -->
              <div v-if="message.references && message.references.length > 0" class="message-references">
                <div class="ref-title">引用文献：</div>
                <div class="ref-list">
                  <el-tag
                    v-for="ref in message.references"
                    :key="ref.paper_id"
                    size="small"
                    type="info"
                    class="ref-tag"
                    @click="viewPaper(ref.paper_id)"
                  >
                    {{ ref.title }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <!-- AI 正在输入 -->
          <div v-if="isTyping" class="message-wrapper ai-message typing">
            <div class="message-avatar">
              <div class="ai-avatar">
                <el-icon :size="20"><Cpu /></el-icon>
              </div>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入区域 -->
      <footer class="input-area">
        <div class="input-toolbar">
          <el-tooltip content="上传文件">
            <button class="tool-btn" @click="handleUpload">
              <el-icon><Paperclip /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="关联论文">
            <button class="tool-btn" @click="showPaperSelector = true" :class="{ active: selectedPapers.length > 0 }">
              <el-icon><Document /></el-icon>
              <span v-if="selectedPapers.length > 0" class="badge">{{ selectedPapers.length }}</span>
            </button>
          </el-tooltip>
          <el-tooltip content="使用 RAG">
            <button
              class="tool-btn"
              :class="{ active: useRag }"
              @click="useRag = !useRag"
            >
              <el-icon><Search /></el-icon>
              <span>RAG</span>
            </button>
          </el-tooltip>
        </div>

        <div class="input-box">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="inputRows"
            placeholder="输入您的问题，AI 将基于您的论文库进行回答..."
            resize="none"
            @keydown.enter.prevent="handleEnter"
            @input="handleInput"
          />
          <button
            class="send-btn"
            :disabled="!canSend"
            @click="sendMessage()"
          >
            <el-icon v-if="!isTyping"><Promotion /></el-icon>
            <el-icon v-else class="loading"><Loading /></el-icon>
          </button>
        </div>

        <!-- 已上传文件显示 -->
        <div v-if="uploadedFiles.length > 0" class="uploaded-files">
          <div class="uploaded-files-title">
            <el-icon><Document /></el-icon>
            <span>已上传 {{ uploadedFiles.length }} 个文件</span>
          </div>
          <div class="uploaded-files-list">
            <el-tag
              v-for="(file, index) in uploadedFiles"
              :key="file.hash"
              closable
              size="small"
              type="info"
              @close="removeFile(index)"
              class="uploaded-file-tag"
            >
              {{ file.name }}
            </el-tag>
          </div>
        </div>

        <div class="input-hint">
          <span>Enter 发送，Shift + Enter 换行</span>
          <span v-if="inputMessage.length > 0">{{ inputMessage.length }} 字符</span>
        </div>
      </footer>
    </main>

    <!-- 论文选择对话框 -->
    <el-dialog 
      v-model="showPaperSelector" 
      title="选择关联论文" 
      width="700px"
      :close-on-click-modal="false"
      class="paper-selector-dialog"
    >
      <div class="paper-selector">
        <!-- 关联论文功能说明 -->
        <el-alert
          title="关联论文功能说明"
          type="success"
          :closable="false"
          class="paper-help-alert"
          show-icon
        >
          <template #default>
            <div class="paper-help-content">
              <p><strong>什么是关联论文？</strong></p>
              <p>关联论文后，AI 助手将能够<strong>直接读取并理解</strong>这些论文的完整内容（标题、摘要、核心要点等），并基于这些内容回答您的问题。</p>
              <p style="margin-top: 8px;"><strong>如何使用？</strong></p>
              <ul>
                <li>选择您想要重点参考的论文（可多选）</li>
                <li>点击"确定"后，论文内容将被加载到当前对话中</li>
                <li>发送消息时，AI 会基于这些论文的内容进行深入分析和回答</li>
                <li>您可以随时更换关联的论文以适应不同的问题场景</li>
              </ul>
            </div>
          </template>
        </el-alert>

        <el-input
          v-model="paperSearch"
          placeholder="搜索论文..."
          clearable
          class="paper-search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="paper-table-wrapper">
          <el-table
            :data="filteredPapers"
            style="width: 100%"
            height="280"
            @selection-change="handlePaperSelectionChange"
            ref="paperTable"
            row-key="id"
            v-loading="loadingPapers"
            empty-text="暂无论文，请先上传"
          >
            <el-table-column type="selection" width="55" reserve-selection />
            <el-table-column prop="title" label="论文标题" show-overflow-tooltip min-width="250" />
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column prop="venue" label="期刊/会议" show-overflow-tooltip />
          </el-table>
        </div>
      </div>

      <template #footer>
        <div class="paper-dialog-footer">
          <span class="selected-count">已选择 <strong>{{ tempSelectedPapers.length }}</strong> 篇论文</span>
          <div class="dialog-actions">
            <el-button size="default" @click="showPaperSelector = false">取消</el-button>
            <el-button size="default" type="primary" @click="confirmPaperSelection" :loading="loadingPapers">
              确定
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="聊天设置" width="500px">
      <el-form label-width="100px">
        <el-form-item label="默认模型">
          <el-select v-model="settings.model" style="width: 100%">
            <el-option label="GLM-4-Plus" value="glm-4-plus" />
            <el-option label="GLM-4-Flash" value="glm-4-flash" />
          </el-select>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="settings.temperature" :min="0" :max="1" :step="0.1" show-stops />
          <div class="slider-hint">较低的值使输出更确定，较高的值使输出更随机</div>
        </el-form-item>
        <el-form-item label="最大长度">
          <el-input-number v-model="settings.maxTokens" :min="1000" :max="8000" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="启用 RAG">
          <el-switch v-model="settings.useRag" />
        </el-form-item>
        <el-form-item label="自动引用">
          <el-switch v-model="settings.autoReference" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">关闭</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog v-model="showRenameDialog" title="重命名对话" width="400px">
      <el-input v-model="renameValue" placeholder="输入新名称" />
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Fold, Expand, ChatLineRound, MoreFilled, Setting,
  Document, Delete, ChatDotRound, Cpu, Paperclip, Search,
  Promotion, Loading, Edit
} from '@element-plus/icons-vue'
import api from '@/api'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const store = useStore()

// ==================== 状态 ====================
const sidebarCollapsed = ref(false)
const currentChatId = ref(null)
const chatHistory = ref([])
const messages = ref([])
const inputMessage = ref('')
const isTyping = ref(false)
const currentModel = ref('glm-4-plus')
const messagesContainer = ref(null)
const useRag = ref(true)
const selectedPapers = ref([])
const uploadedFiles = ref([])  // 已上传文件列表
const isUploading = ref(false)  // 上传中状态

// 论文选择
const showPaperSelector = ref(false)
const paperSearch = ref('')
const papers = ref([])
const tempSelectedPapers = ref([])
const paperTable = ref(null)
const loadingPapers = ref(false)

// 设置
const showSettings = ref(false)
const settings = ref({
  model: 'glm-4-plus',
  temperature: 0.7,
  maxTokens: 4000,
  useRag: true,
  autoReference: true
})

// 重命名
const showRenameDialog = ref(false)
const renameValue = ref('')
const renameChatId = ref(null)

// ==================== 计算属性 ====================
const userAvatar = computed(() => store.getters.currentUser?.avatar || '')
const userInitial = computed(() => {
  const name = store.getters.currentUser?.full_name || store.getters.currentUser?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const currentChatTitle = computed(() => {
  const chat = chatHistory.value.find(c => c.chat_id === currentChatId.value)
  return chat?.preview || '新对话'
})

const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && !isTyping.value
})

const inputRows = computed(() => {
  const lines = inputMessage.value.split('\n').length
  return Math.min(Math.max(lines, 1), 5)
})

const filteredPapers = computed(() => {
  if (!paperSearch.value) return papers.value
  const query = paperSearch.value.toLowerCase()
  return papers.value.filter(p =>
    (p.title || '').toLowerCase().includes(query) ||
    (p.abstract || '').toLowerCase().includes(query)
  )
})

// ==================== 快捷功能卡片 ====================
const quickCards = [
  { key: 'summary', label: '文献综述', icon: 'Document', prompt: '请基于我的论文库生成一份文献综述' },
  { key: 'gaps', label: '研究空白', icon: 'Search', prompt: '请分析当前研究领域的主要空白' },
  { key: 'code', label: '代码生成', icon: 'Cpu', prompt: '请帮我生成实现XX算法的代码' },
  { key: 'trends', label: '趋势分析', icon: 'TrendCharts', prompt: '请分析该领域的研究趋势' },
]

const exampleQuestions = [
  '帮我总结这几篇论文的核心贡献',
  '这些论文中使用了哪些主要方法？',
  '这个领域的研究现状如何？',
  '有哪些潜在的研究方向值得探索？',
  '帮我比较论文A和论文B的方法差异',
  '请解释论文中的XX算法原理'
]

// ==================== 方法 ====================
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const renderMessage = (content) => {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// ==================== 聊天操作 ====================
const loadChatHistory = async () => {
  try {
    // 这里可以调用后端 API 获取会话列表
    // 目前使用本地存储
    const saved = localStorage.getItem('kimi_chat_history')
    if (saved) {
      chatHistory.value = JSON.parse(saved)
    }
  } catch (e) {
    console.error('加载聊天历史失败:', e)
  }
}

const saveChatHistory = () => {
  try {
    localStorage.setItem('kimi_chat_history', JSON.stringify(chatHistory.value))
  } catch (e) {
    console.error('保存聊天历史失败:', e)
  }
}

const createNewChat = () => {
  const newChatId = `chat_${Date.now()}`
  currentChatId.value = newChatId
  messages.value = []
  selectedPapers.value = []

  // 添加到历史
  chatHistory.value.unshift({
    chat_id: newChatId,
    preview: '新对话',
    created_at: new Date().toISOString(),
    message_count: 0
  })

  saveChatHistory()
}

const switchChat = async (chatId) => {
  if (currentChatId.value === chatId) return

  currentChatId.value = chatId

  // 加载该会话的消息历史
  try {
    const response = await api.getChatHistory(chatId)
    if (response.success) {
      messages.value = response.data || []
    }
  } catch (e) {
    console.error('加载消息历史失败:', e)
    messages.value = []
  }

  scrollToBottom()
}

const renameChat = (chatId) => {
  renameChatId.value = chatId
  renameValue.value = ''
  showRenameDialog.value = true
}

const confirmRename = () => {
  if (!renameValue.value.trim()) {
    ElMessage.warning('请输入新名称')
    return
  }

  const chat = chatHistory.value.find(c => c.chat_id === renameChatId.value)
  if (chat) {
    chat.preview = renameValue.value
    saveChatHistory()
    ElMessage.success('重命名成功')
  }

  showRenameDialog.value = false
}

const deleteChat = async (chatId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 调用后端 API 删除
    await api.deleteChat({ chatId })

    // 从列表中移除
    chatHistory.value = chatHistory.value.filter(c => c.chat_id !== chatId)

    // 如果删除的是当前会话，切换到第一个或新建
    if (currentChatId.value === chatId) {
      if (chatHistory.value.length > 0) {
        switchChat(chatHistory.value[0].chat_id)
      } else {
        createNewChat()
      }
    }

    saveChatHistory()
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
    }
  }
}

const clearCurrentChat = async () => {
  if (messages.value.length === 0) return

  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.clearChat({ chatId: currentChatId.value })
    messages.value = []

    // 更新预览
    const chat = chatHistory.value.find(c => c.chat_id === currentChatId.value)
    if (chat) {
      chat.preview = '新对话'
      chat.message_count = 0
      saveChatHistory()
    }

    ElMessage.success('已清空')
  } catch (e) {
    if (e !== 'cancel') {
      console.error('清空失败:', e)
    }
  }
}

// ==================== 消息发送 ====================
const handleEnter = (e) => {
  if (e.shiftKey) {
    // Shift+Enter 换行
    return
  }
  e.preventDefault()
  sendMessage()
}

const handleInput = () => {
  // 可以在这里实现输入提示等功能
}

const sendQuickMessage = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}

const sendMessage = async (content = null) => {
  const message = content || inputMessage.value.trim()
  if (!message || isTyping.value) return

  // 清空输入框
  if (!content) {
    inputMessage.value = ''
  }

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString(),
    references: []
  })

  scrollToBottom()
  isTyping.value = true

  try {
    // 准备上传的文件内容
    const filesData = uploadedFiles.value.map(file => ({
      filename: file.name,
      content: file.content,
      content_type: file.content_type,
      size: file.size
    }))

    // 调用流式 API
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        message,
        chatId: currentChatId.value,
        papers: selectedPapers.value.map(p => p.id),
        model: currentModel.value,
        temperature: settings.value.temperature,
        useRag: useRag.value,
        files: filesData.length > 0 ? filesData : undefined
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''

    // 添加 AI 消息占位
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      references: []
    })

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.done) {
              isTyping.value = false
            } else if (data.content) {
              fullContent += data.content
              messages.value[messages.value.length - 1].content = fullContent
              scrollToBottom()
            }
          } catch (e) {
            console.error('解析 SSE 数据失败:', e)
          }
        }
      }
    }

    // 更新会话预览
    const chat = chatHistory.value.find(c => c.chat_id === currentChatId.value)
    if (chat) {
      chat.preview = message.slice(0, 30) + (message.length > 30 ? '...' : '')
      chat.message_count = messages.value.length
      saveChatHistory()
    }

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')
    isTyping.value = false
  }
}

// ==================== 论文选择 ====================
const loadPapers = async () => {
  try {
    const response = await api.getPapersList({ limit: 1000 })
    if (response.success) {
      // API 返回的 data 直接是数组，不是 { items: [...] }
      papers.value = Array.isArray(response.data) ? response.data : (response.data.items || [])
      console.log(`[DEBUG] 加载了 ${papers.value.length} 篇论文`)
    } else {
      console.error('[ERROR] 加载论文失败:', response.error)
      papers.value = []
    }
  } catch (error) {
    console.error('[ERROR] 加载论文失败:', error)
    papers.value = []
  }
}

const handlePaperSelectionChange = (selection) => {
  tempSelectedPapers.value = selection
}

const confirmPaperSelection = () => {
  selectedPapers.value = [...tempSelectedPapers.value]
  showPaperSelector.value = false
  
  // 将关联论文保存到当前会话上下文
  const chat = chatHistory.value.find(c => c.chat_id === currentChatId.value)
  if (chat) {
    chat.connected_papers = selectedPapers.value.map(p => p.id)
    saveChatHistory()
  }
  
  ElMessage.success(`已关联 ${selectedPapers.value.length} 篇论文，RAG将优先检索这些论文`)
}

const viewPaper = (paperId) => {
  window.open(`#/papers/${paperId}`, '_blank')
}

// ==================== 设置 ====================
const saveSettings = () => {
  localStorage.setItem('kimi_chat_settings', JSON.stringify(settings.value))
  showSettings.value = false
  ElMessage.success('设置已保存')
}

const loadSettings = () => {
  try {
    const saved = localStorage.getItem('kimi_chat_settings')
    if (saved) {
      settings.value = { ...settings.value, ...JSON.parse(saved) }
    }
  } catch (e) {
    console.error('加载设置失败:', e)
  }
}

// ==================== 文件上传 ====================
const handleUpload = () => {
  // 创建隐藏的文件输入
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.txt,.pdf,.doc,.docx,.md,.py,.js,.json,.java,.c,.cpp,.html,.css'
  input.multiple = true
  input.style.display = 'none'
  input.onchange = (e) => {
    handleFileSelect(e)
    // 清理创建的input元素
    document.body.removeChild(input)
  }
  document.body.appendChild(input)
  input.click()
}

const handleFileSelect = async (event) => {
  const files = event.target.files
  if (!files || files.length === 0) return
  
  isUploading.value = true
  
  for (const file of files) {
    // 检查文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.warning(`${file.name} 超过 10MB，已跳过`)
      continue
    }
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      ElMessage.info(`正在上传 ${file.name}...`)
      
      const response = await fetch('/api/chat/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      })
      
      const result = await response.json()
      
      if (result.success) {
        uploadedFiles.value.push({
          name: result.data.filename,
          hash: result.data.file_hash,
          content: result.data.content,
          content_type: result.data.content_type,
          size: result.data.size
        })
        ElMessage.success(`${file.name} 上传成功`)
      } else {
        ElMessage.error(`${file.name} 上传失败: ${result.error || '未知错误'}`)
      }
    } catch (error) {
      console.error('上传错误:', error)
      ElMessage.error(`${file.name} 上传失败: ${error.message || '网络错误'}`)
    }
  }
  
  isUploading.value = false
}

const removeFile = (index) => {
  uploadedFiles.value.splice(index, 1)
}

// 监听论文选择对话框打开
watch(showPaperSelector, async (newVal) => {
  if (newVal) {
    // 对话框打开时加载论文列表
    await loadPapers()
    
    // 初始化已选择的论文
    await nextTick()
    if (paperTable.value && selectedPapers.value.length > 0) {
      // 清空当前选择
      paperTable.value.clearSelection()
      
      // 重新选中已关联的论文
      selectedPapers.value.forEach(paper => {
        const row = papers.value.find(p => p.id === paper.id)
        if (row) {
          paperTable.value.toggleRowSelection(row, true)
        }
      })
    }
    
    // 同步tempSelectedPapers
    tempSelectedPapers.value = [...selectedPapers.value]
  }
})

// ==================== 生命周期 ====================
onMounted(() => {
  loadChatHistory()
  loadPapers()
  loadSettings()

  // 如果没有会话，创建一个新的
  if (chatHistory.value.length === 0) {
    createNewChat()
  } else {
    // 切换到第一个会话
    switchChat(chatHistory.value[0].chat_id)
  }
  
  // 检查上传按钮可用性
  console.log('[DEBUG] KimiChat 已挂载，上传功能已就绪')
})
</script>

<style scoped>
.kimi-chat-container {
  display: flex;
  height: calc(100vh - 64px);
  background: var(--color-bg-secondary);
}

/* ==================== 侧边栏 ==================== */
.sidebar {
  width: 260px;
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border-primary);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--color-border-primary);
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--color-primary-800);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.new-chat-btn:hover {
  background: var(--color-primary-900);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.collapse-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-muted);
}

.collapse-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.sidebar.collapsed .new-chat-btn span {
  display: none;
}

/* 对话历史 */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  margin-bottom: 4px;
  transition: all var(--transition-fast);
  position: relative;
}

.chat-item:hover {
  background: var(--color-bg-tertiary);
}

.chat-item.active {
  background: var(--color-primary-800);
}

.chat-item.active .chat-title {
  color: var(--color-text-inverse);
  font-weight: var(--font-medium);
}

.chat-icon {
  font-size: 16px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.chat-item.active .chat-icon {
  color: var(--color-text-inverse);
}

.chat-title {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-item.active .chat-title {
  color: var(--color-text-inverse);
}

.chat-actions {
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.chat-item:hover .chat-actions {
  opacity: 1;
}

.more-icon {
  padding: 4px;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
}

.more-icon:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.chat-item.active .more-icon {
  color: var(--color-text-inverse);
}

.sidebar.collapsed .chat-title,
.sidebar.collapsed .chat-actions {
  display: none;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border-primary);
}

.footer-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.footer-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.sidebar.collapsed .footer-btn span {
  display: none;
}

/* ==================== 主聊天区域 ==================== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-select {
  width: 140px;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 欢迎页面 */
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  text-align: center;
  padding: 40px 20px;
}

.welcome-logo {
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.welcome-title .accent {
  color: var(--color-accent-500);
}

.welcome-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  max-width: 500px;
  margin-bottom: 40px;
}

/* 快捷卡片 */
.quick-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 600px;
  margin-bottom: 48px;
}

.quick-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-card:hover {
  border-color: var(--color-primary-400);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.quick-card span {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
}

.quick-card:hover span {
  color: var(--color-text-primary);
}

/* 示例问题 */
.example-questions {
  max-width: 600px;
}

.section-title {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

.question-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.question-tag {
  cursor: pointer;
  transition: all var(--transition-fast);
}

.question-tag:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary-400);
  color: var(--color-text-primary);
}

/* 消息样式 */
.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 90%;
}

.message-wrapper.user-message {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-wrapper.ai-message {
  margin-right: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-800);
  border-radius: 50%;
  color: var(--color-text-inverse);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.user-message .message-header {
  justify-content: flex-end;
}

.message-role {
  font-size: 13px;
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.message-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.message-body {
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text-primary);
}

.user-message .message-body {
  background: var(--color-primary-800);
  color: var(--color-text-inverse);
  border-bottom-right-radius: 4px;
}

.ai-message .message-body {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-primary);
  border-bottom-left-radius: 4px;
}

.ai-message .message-body :deep(p) {
  margin: 0 0 12px 0;
}

.ai-message .message-body :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-message .message-body :deep(pre) {
  background: var(--color-primary-900);
  border-radius: var(--radius-md);
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.ai-message .message-body :deep(code) {
  font-family: var(--font-family-mono);
  font-size: 13px;
}

.ai-message .message-body :deep(:not(pre) > code) {
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  color: var(--color-accent-600);
}

.ai-message .message-body :deep(ul), .ai-message .message-body :deep(ol) {
  padding-left: 20px;
  margin: 12px 0;
}

.ai-message .message-body :deep(li) {
  margin: 6px 0;
}

.ai-message .message-body :deep(h1), .ai-message .message-body :deep(h2), .ai-message .message-body :deep(h3) {
  margin: 20px 0 12px 0;
  color: var(--color-text-primary);
}

.ai-message .message-body :deep(blockquote) {
  border-left: 4px solid var(--color-primary-400);
  margin: 12px 0;
  padding: 8px 16px;
  background: var(--color-bg-tertiary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

/* 引用文献 */
.message-references {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--color-border-primary);
}

.ref-title {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.ref-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ref-tag {
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ref-tag:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary-400);
  color: var(--color-text-primary);
}

/* 正在输入动画 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 18px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-primary-500);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* ==================== 输入区域 ==================== */
.input-area {
  background: var(--color-bg-primary);
  border-top: 1px solid var(--color-border-primary);
  padding: 16px 24px;
}

.input-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.tool-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.tool-btn.active {
  background: var(--color-primary-100);
  border-color: var(--color-primary-400);
  color: var(--color-primary-700);
}

.tool-btn .badge {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ef4444;
  color: white;
  font-size: 11px;
  border-radius: 50%;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  transition: all var(--transition-fast);
}

.input-box:focus-within {
  background: var(--color-bg-primary);
  border-color: var(--color-primary-400);
  box-shadow: 0 0 0 3px rgba(45, 45, 45, 0.1);
}

.input-box :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  padding: 0;
  font-size: 15px;
  resize: none;
  box-shadow: none;
}

.input-box :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-800);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-inverse);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--color-primary-900);
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
}

.send-btn:disabled {
  background: var(--color-primary-200);
  cursor: not-allowed;
}

.send-btn .loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-hint {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ==================== 对话框样式 ==================== */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-footer > div {
  display: flex;
  gap: 12px;
}

/* 论文选择对话框样式 */
.paper-selector-dialog :deep(.el-dialog) {
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.paper-selector-dialog :deep(.el-dialog__body) {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.paper-selector-dialog :deep(.el-dialog__footer) {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-primary);
  background: var(--color-bg-primary);
  flex-shrink: 0;
}

.paper-selector {
  display: flex;
  flex-direction: column;
}

.paper-table-wrapper {
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.paper-search {
  margin-bottom: 16px;
}

.slider-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

/* 关联论文帮助提示 */
.paper-help-alert {
  margin-bottom: 16px;
}

/* 论文对话框底部 */
.paper-dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.selected-count {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.selected-count strong {
  color: var(--color-primary-800);
}

.dialog-actions {
  display: flex;
  gap: var(--space-3);
}

.paper-help-content {
  font-size: 13px;
  line-height: 1.6;
}

.paper-help-content p {
  margin: 4px 0;
}

.paper-help-content ul {
  margin: 4px 0;
  padding-left: 20px;
}

.paper-help-content li {
  margin: 2px 0;
}

/* 已上传文件显示 */
.uploaded-files {
  margin-bottom: 12px;
  padding: 12px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
}

.uploaded-files-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
  margin-bottom: 8px;
}

.uploaded-files-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.uploaded-file-tag {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 下拉菜单危险项 */
:deep(.el-dropdown-menu__item.danger) {
  color: var(--color-error);
}

:deep(.el-dropdown-menu__item.danger:hover) {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 100;
    height: 100%;
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
  }

  .quick-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .message-wrapper {
    max-width: 100%;
  }
}
</style>
