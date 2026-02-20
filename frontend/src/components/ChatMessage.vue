<template>
  <div class="chat-message" :class="{ 'user-message': isUser, 'ai-message': !isUser }">
    <div class="message-avatar">
      <el-avatar v-if="!isUser" :size="36" :icon="ChatDotRound" class="ai-avatar" />
      <el-avatar v-else :size="36" class="user-avatar">{{ userInitial }}</el-avatar>
    </div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-author">{{ isUser ? '我' : 'AI 助手' }}</span>
        <span class="message-time">{{ formatTime(timestamp) }}</span>
      </div>
      <div class="message-body" v-html="renderedContent"></div>
      <div v-if="!isUser && references.length > 0" class="message-references">
        <div class="references-title">参考来源：</div>
        <div class="references-list">
          <el-tag
            v-for="(ref, index) in references"
            :key="index"
            size="small"
            type="info"
            class="reference-tag"
            @click="$emit('viewReference', ref)"
          >
            {{ ref.title || `论文 ${index + 1}` }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  isUser: {
    type: Boolean,
    default: false
  },
  timestamp: {
    type: Date,
    default: () => new Date()
  },
  references: {
    type: Array,
    default: () => []
  },
  userName: {
    type: String,
    default: ''
  }
})

defineEmits(['viewReference'])

const userInitial = computed(() => {
  return props.userName ? props.userName.charAt(0).toUpperCase() : 'U'
})

const renderedContent = computed(() => {
  // 使用 marked 渲染 markdown
  return marked.parse(props.content, { breaks: true })
})

const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  align-items: flex-end;
}

.user-message .message-body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.message-avatar {
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 500;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: calc(100% - 60px);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.user-message .message-header {
  flex-direction: row-reverse;
}

.message-author {
  font-weight: 500;
  color: #1f2937;
}

.message-time {
  color: #9ca3af;
  font-size: 12px;
}

.message-body {
  background: #f3f4f6;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
  color: #1f2937;
  line-height: 1.7;
  font-size: 14px;
  word-wrap: break-word;
}

.message-body :deep(p) {
  margin: 0 0 8px 0;
}

.message-body :deep(p:last-child) {
  margin-bottom: 0;
}

.message-body :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.message-body :deep(pre) {
  background: #1f2937;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-body :deep(pre code) {
  background: none;
  color: #e5e7eb;
  padding: 0;
}

.message-body :deep(ul), .message-body :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-body :deep(li) {
  margin: 4px 0;
}

.message-body :deep(blockquote) {
  border-left: 4px solid #10b981;
  margin: 8px 0;
  padding-left: 12px;
  color: #4b5563;
}

.message-references {
  margin-top: 8px;
}

.references-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.references-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.reference-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.reference-tag:hover {
  background: #10b981;
  color: white;
}
</style>
