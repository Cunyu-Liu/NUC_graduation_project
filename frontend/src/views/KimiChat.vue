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
            <el-icon :size="80" color="#10b981"><ChatDotRound /></el-icon>
          </div>
          <h1 class="welcome-title">AI 科研助手</h1>
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
          <el-tooltip content="网络搜索">
            <button
              class="tool-btn"
              :class="{ active: useWebSearch }"
              @click="useWebSearch = !useWebSearch"
            >
              <el-icon><Globe /></el-icon>
              <span>联网</span>
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
    <el-dialog v-model="showPaperSelector" title="选择关联论文" width="700px">
      <div class="paper-selector">
        <!-- 关联论文功能说明 -->
        <el-alert
          title="💡 关联论文功能说明"
          type="info"
          :closable="false"
          class="paper-help-alert"
        >
          <template #default>
            <div class="paper-help-content">
              <p><strong>什么是关联论文？</strong></p>
              <p>关联论文是指在AI回答您的问题时，<strong>优先参考</strong>的论文。这可以让AI的回答更贴合您的研究内容。</p>
              <p style="margin-top: 8px;"><strong>如何使用？</strong></p>
              <ul>
                <li>选择您想要重点参考的论文（可多选）</li>
                <li>点击"确定"后，这些论文会在RAG检索时被优先搜索</li>
                <li>发送消息时，AI会优先分析这些论文的内容来回答您的问题</li>
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

        <el-table
          :data="filteredPapers"
          style="width: 100%"
          max-height="400"
          @selection-change="handlePaperSelectionChange"
          ref="paperTable"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="title" label="论文标题" show-overflow-tooltip min-width="250" />
          <el-table-column prop="year" label="年份" width="80" />
          <el-table-column prop="venue" label="期刊/会议" show-overflow-tooltip />
        </el-table>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <span>已选择 {{ tempSelectedPapers.length }} 篇论文</span>
          <div>
            <el-button @click="showPaperSelector = false">取消</el-button>
            <el-button type="primary" @click="confirmPaperSelection">确定</el-button>
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
  Globe, Promotion, Loading, Edit
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
const useWebSearch = ref(false)
const selectedPapers = ref([])
const uploadedFiles = ref([])  // 已上传文件列表
const isUploading = ref(false)  // 上传中状态

// 论文选择
const showPaperSelector = ref(false)
const paperSearch = ref('')
const papers = ref([])
const tempSelectedPapers = ref([])
const paperTable = ref(null)

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
        useWebSearch: useWebSearch.value,
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
  background: #f9fafb;
}

/* ==================== 侧边栏 ==================== */
.sidebar {
  width: 260px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
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
  border-bottom: 1px solid #e5e7eb;
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.collapse-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: #e5e7eb;
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
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s;
  position: relative;
}

.chat-item:hover {
  background: #f3f4f6;
}

.chat-item.active {
  background: #d1fae5;
}

.chat-item.active .chat-title {
  color: #059669;
  font-weight: 500;
}

.chat-icon {
  font-size: 16px;
  color: #6b7280;
  flex-shrink: 0;
}

.chat-item.active .chat-icon {
  color: #059669;
}

.chat-title {
  flex: 1;
  font-size: 14px;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-item:hover .chat-actions {
  opacity: 1;
}

.more-icon {
  padding: 4px;
  border-radius: 4px;
  color: #6b7280;
  cursor: pointer;
}

.more-icon:hover {
  background: #e5e7eb;
  color: #374151;
}

.sidebar.collapsed .chat-title,
.sidebar.collapsed .chat-actions {
  display: none;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.footer-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.footer-btn:hover {
  background: #f3f4f6;
  color: #374151;
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
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
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
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 16px;
  color: #6b7280;
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-card:hover {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
  transform: translateY(-2px);
}

.quick-card span {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.quick-card:hover span {
  color: #059669;
}

/* 示例问题 */
.example-questions {
  max-width: 600px;
}

.section-title {
  font-size: 14px;
  color: #9ca3af;
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
  transition: all 0.2s;
}

.question-tag:hover {
  background: #d1fae5;
  border-color: #10b981;
  color: #059669;
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  color: white;
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
  font-weight: 600;
  color: #374151;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
}

.message-body {
  padding: 14px 18px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.7;
  color: #374151;
}

.user-message .message-body {
  background: #10b981;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-body {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.ai-message .message-body :deep(p) {
  margin: 0 0 12px 0;
}

.ai-message .message-body :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-message .message-body :deep(pre) {
  background: #1f2937;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.ai-message .message-body :deep(code) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.ai-message .message-body :deep(:not(pre) > code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  color: #ec4899;
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
  color: #111827;
}

.ai-message .message-body :deep(blockquote) {
  border-left: 4px solid #10b981;
  margin: 12px 0;
  padding: 8px 16px;
  background: #f0fdf4;
  border-radius: 0 8px 8px 0;
}

/* 引用文献 */
.message-references {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}

.ref-title {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.ref-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ref-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.ref-tag:hover {
  background: #d1fae5;
  border-color: #10b981;
  color: #059669;
}

/* 正在输入动画 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 18px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #10b981;
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
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
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
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tool-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.tool-btn.active {
  background: #d1fae5;
  border-color: #10b981;
  color: #059669;
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
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px 16px;
  transition: all 0.2s;
}

.input-box:focus-within {
  background: #ffffff;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.send-btn:disabled {
  background: #d1d5db;
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
  color: #9ca3af;
}

/* ==================== 对话框样式 ==================== */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.paper-selector {
  max-height: 500px;
}

.paper-search {
  margin-bottom: 16px;
}

.slider-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

/* 关联论文帮助提示 */
.paper-help-alert {
  margin-bottom: 16px;
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
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
}

.uploaded-files-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #166534;
  font-weight: 500;
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
  color: #ef4444;
}

:deep(.el-dropdown-menu__item.danger:hover) {
  background: #fef2f2;
  color: #dc2626;
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
