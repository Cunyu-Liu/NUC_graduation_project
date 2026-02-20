<template>
  <div class="ai-chat-container">
    <!-- 左侧边栏 - 对话历史 -->
    <div class="chat-sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <el-button type="primary" class="new-chat-btn" @click="createNewChat">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </el-button>
        <el-button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>
      
      <div class="chat-history">
        <div
          v-for="chat in chatHistory"
          :key="chat.id"
          class="chat-item"
          :class="{ active: currentChatId === chat.id }"
          @click="loadChat(chat.id)"
        >
          <el-icon class="chat-icon"><ChatLineRound /></el-icon>
          <span class="chat-title">{{ chat.title }}</span>
          <el-dropdown trigger="click" @command="handleChatCommand($event, chat.id)">
            <el-icon class="chat-more" @click.stop><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">重命名</el-dropdown-item>
                <el-dropdown-item command="delete" type="danger">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 顶部工具栏 -->
      <div class="chat-toolbar">
        <div class="toolbar-left">
          <h2 class="chat-title">{{ currentChatTitle }}</h2>
        </div>
        <div class="toolbar-right">
          <el-select v-model="selectedModel" size="small" class="model-select">
            <el-option label="GLM-4-Plus" value="glm-4-plus" />
            <el-option label="GLM-4-Flash" value="glm-4-flash" />
          </el-select>
          <el-button size="small" @click="showSettings = true">
            <el-icon><Setting /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messagesContainer" class="messages-container">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="welcome-icon">
            <el-icon :size="64" color="#10b981"><ChatDotRound /></el-icon>
          </div>
          <h1 class="welcome-title">AI 科研助手</h1>
          <p class="welcome-desc">基于您的论文库，为您提供智能问答、文献综述、研究建议等服务</p>
          
          <div class="quick-actions">
            <div class="quick-action-title">快捷功能：</div>
            <div class="quick-action-buttons">
              <el-button
                v-for="action in quickActions"
                :key="action.key"
                type="default"
                class="quick-action-btn"
                @click="sendQuickAction(action.prompt)"
              >
                <el-icon><component :is="action.icon" /></el-icon>
                {{ action.label }}
              </el-button>
            </div>
          </div>
        </div>

        <template v-else>
          <ChatMessage
            v-for="(message, index) in messages"
            :key="index"
            :content="message.content"
            :is-user="message.isUser"
            :timestamp="message.timestamp"
            :references="message.references || []"
            @view-reference="viewPaper"
          />
          
          <!-- 正在输入提示 -->
          <div v-if="isTyping" class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </template>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-toolbar">
          <el-tooltip content="上传文件">
            <el-button circle size="small" @click="handleUpload">
              <el-icon><Paperclip /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="关联论文">
            <el-button circle size="small" @click="showPaperSelector = true">
              <el-icon><Document /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空对话">
            <el-button circle size="small" @click="clearMessages">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
        
        <div class="input-box">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题，AI 将基于您的论文库进行回答..."
            resize="none"
            @keydown.enter.prevent="handleEnter"
          />
          <el-button
            type="primary"
            class="send-btn"
            :disabled="!inputMessage.trim() || isTyping"
            @click="sendMessage"
          >
            <el-icon><Position /></el-icon>
          </el-button>
        </div>
        
        <div class="input-hint">
          <span>Enter 发送，Shift + Enter 换行</span>
          <span v-if="selectedPapers.length > 0" class="selected-papers">
            已选择 {{ selectedPapers.length }} 篇论文
          </span>
        </div>
      </div>
    </div>

    <!-- 论文选择对话框 -->
    <el-dialog v-model="showPaperSelector" title="选择关联论文" width="60%">
      <div class="paper-selector">
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
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="title" label="论文标题" show-overflow-tooltip />
          <el-table-column prop="year" label="年份" width="80" />
          <el-table-column prop="venue" label="期刊/会议" show-overflow-tooltip />
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="showPaperSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmPaperSelection">确定</el-button>
      </template>
    </el-dialog>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="聊天设置" width="400px">
      <el-form label-width="100px">
        <el-form-item label="模型">
          <el-select v-model="settings.model" style="width: 100%">
            <el-option label="GLM-4-Plus" value="glm-4-plus" />
            <el-option label="GLM-4-Flash" value="glm-4-flash" />
          </el-select>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="settings.temperature" :min="0" :max="1" :step="0.1" />
        </el-form-item>
        <el-form-item label="最大长度">
          <el-input-number v-model="settings.maxTokens" :min="1000" :max="8000" :step="1000" />
        </el-form-item>
        <el-form-item label="引用论文">
          <el-switch v-model="settings.includeReferences" />
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Fold, Expand, ChatLineRound, MoreFilled,
  ChatDotRound, Setting, Paperclip, Document,
  Delete, Position, Search
} from '@element-plus/icons-vue'
import ChatMessage from '@/components/ChatMessage.vue'
import api from '@/api'

const store = useStore()

// 状态
const sidebarCollapsed = ref(false)
const currentChatId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isTyping = ref(false)
const selectedModel = ref('glm-4-plus')
const messagesContainer = ref(null)
const showPaperSelector = ref(false)
const showSettings = ref(false)
const paperSearch = ref('')
const selectedPapers = ref([])
const papers = ref([])

// 设置
const settings = ref({
  model: 'glm-4-plus',
  temperature: 0.7,
  maxTokens: 4000,
  includeReferences: true
})

// 聊天历史
const chatHistory = ref([
  { id: 1, title: '论文综述讨论', timestamp: Date.now() },
  { id: 2, title: '研究方法分析', timestamp: Date.now() - 86400000 },
])

// 当前聊天标题
const currentChatTitle = computed(() => {
  const chat = chatHistory.value.find(c => c.id === currentChatId.value)
  return chat?.title || '新对话'
})

// 快捷功能
const quickActions = [
  { key: 'summary', label: '生成文献综述', icon: 'Document', prompt: '请基于我的论文库生成一份文献综述' },
  { key: 'gaps', label: '分析研究空白', icon: 'Search', prompt: '请分析当前研究领域的主要空白' },
  { key: 'trends', label: '研究趋势分析', icon: 'TrendCharts', prompt: '请分析该领域的研究趋势' },
  { key: 'methods', label: '方法论对比', icon: 'DataAnalysis', prompt: '请对比不同研究方法的优缺点' },
]

// 过滤后的论文
const filteredPapers = computed(() => {
  if (!paperSearch.value) return papers.value
  const query = paperSearch.value.toLowerCase()
  return papers.value.filter(p => 
    (p.title || '').toLowerCase().includes(query) ||
    (p.abstract || '').toLowerCase().includes(query)
  )
})

// 加载论文列表
const loadPapers = async () => {
  try {
    const response = await api.getPapersList({ limit: 100 })
    if (response.success) {
      papers.value = response.data.items || []
    }
  } catch (error) {
    console.error('加载论文失败:', error)
  }
}

// 发送消息
const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isTyping.value) return

  // 添加用户消息
  messages.value.push({
    content: message,
    isUser: true,
    timestamp: new Date()
  })

  inputMessage.value = ''
  isTyping.value = true
  scrollToBottom()

  try {
    // 调用 API
    const response = await api.chatWithAI({
      message,
      chatId: currentChatId.value,
      model: selectedModel.value,
      papers: selectedPapers.value.map(p => p.id),
      settings: settings.value
    })

    if (response.success) {
      messages.value.push({
        content: response.data.content,
        isUser: false,
        timestamp: new Date(),
        references: response.data.references || []
      })
    } else {
      throw new Error(response.error || '请求失败')
    }
  } catch (error) {
    ElMessage.error('AI 响应失败: ' + error.message)
    messages.value.push({
      content: '抱歉，我暂时无法回答您的问题。请稍后再试。',
      isUser: false,
      timestamp: new Date()
    })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

// 处理 Enter 键
const handleEnter = (e) => {
  if (!e.shiftKey) {
    sendMessage()
  }
}

// 快捷功能
const sendQuickAction = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 新建对话
const createNewChat = () => {
  const newId = Date.now()
  chatHistory.value.unshift({
    id: newId,
    title: '新对话',
    timestamp: Date.now()
  })
  currentChatId.value = newId
  messages.value = []
}

// 加载对话
const loadChat = (chatId) => {
  currentChatId.value = chatId
  // TODO: 从后端加载历史消息
  messages.value = []
}

// 处理对话命令
const handleChatCommand = async (command, chatId) => {
  if (command === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      chatHistory.value = chatHistory.value.filter(c => c.id !== chatId)
      if (currentChatId.value === chatId) {
        currentChatId.value = null
        messages.value = []
      }
    } catch {
      // 取消
    }
  } else if (command === 'rename') {
    // TODO: 重命名对话框
  }
}

// 清空消息
const clearMessages = () => {
  messages.value = []
}

// 处理论文选择
const handleSelectionChange = (selection) => {
  selectedPapers.value = selection
}

// 确认论文选择
const confirmPaperSelection = () => {
  showPaperSelector.value = false
  ElMessage.success(`已选择 ${selectedPapers.value.length} 篇论文`)
}

// 查看论文
const viewPaper = (paper) => {
  if (paper.id) {
    window.open(`#/papers/${paper.id}`, '_blank')
  }
}

// 处理上传
const handleUpload = () => {
  ElMessage.info('文件上传功能开发中')
}

onMounted(() => {
  loadPapers()
})
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  height: calc(100vh - 64px);
  background: #f8fafc;
}

/* 侧边栏 */
.chat-sidebar {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.chat-sidebar.collapsed {
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
}

.collapsed .new-chat-btn span {
  display: none;
}

.collapse-btn {
  padding: 8px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.chat-item:hover {
  background: #f3f4f6;
}

.chat-item.active {
  background: #dbeafe;
  color: #1d4ed8;
}

.chat-icon {
  font-size: 16px;
}

.chat-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-more {
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-item:hover .chat-more {
  opacity: 1;
}

.collapsed .chat-title,
.collapsed .chat-more {
  display: none;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-left h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.model-select {
  width: 140px;
}

/* 消息区域 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 40px;
}

.welcome-icon {
  margin-bottom: 24px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.welcome-desc {
  font-size: 15px;
  color: #6b7280;
  max-width: 500px;
  margin-bottom: 32px;
}

.quick-actions {
  width: 100%;
  max-width: 600px;
}

.quick-action-title {
  font-size: 14px;
  color: #9ca3af;
  margin-bottom: 12px;
}

.quick-action-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-action-btn {
  justify-content: flex-start;
  padding: 16px;
  height: auto;
  border: 1px solid #e5e7eb;
}

.quick-action-btn:hover {
  border-color: #10b981;
  color: #10b981;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px 20px;
  align-items: center;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.input-area {
  background: #fff;
  border-top: 1px solid #e5e7eb;
  padding: 16px 24px;
}

.input-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-box :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  resize: none;
}

.send-btn {
  height: 44px;
  width: 44px;
  border-radius: 12px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-hint {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.selected-papers {
  color: #10b981;
}

/* 论文选择器 */
.paper-selector {
  max-height: 500px;
}

.paper-search {
  margin-bottom: 16px;
}
</style>
