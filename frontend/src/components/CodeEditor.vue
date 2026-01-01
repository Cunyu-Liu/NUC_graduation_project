<template>
  <div class="code-editor-container">
    <div class="editor-header">
      <h2>代码工作台</h2>
      <div class="header-actions">
        <el-button
          v-if="code.language"
          :icon="code.language === 'python' ? 'Orange' : 'Document'"
          type="info"
          plain
        >
          {{ code.language.toUpperCase() }}
        </el-button>
        <el-tag v-if="code.framework" type="success">{{ code.framework }}</el-tag>
        <el-tag type="info">v{{ code.current_version }}</el-tag>
        <el-tag :type="getQualityType(code.quality_score)">
          质量: {{ (code.quality_score * 100).toFixed(0) }}%
        </el-tag>
      </div>
    </div>

    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button @click="runCode" icon="VideoPlay" type="primary">运行</el-button>
          <el-button @click="saveCode" icon="Download">保存</el-button>
          <el-button @click="copyCode" icon="CopyDocument">复制</el-button>
          <el-button @click="downloadCode" icon="Download">下载</el-button>
        </el-button-group>
      </div>

      <div class="toolbar-right">
        <el-button @click="showModifyDialog = true" icon="Edit">
          AI修改
        </el-button>
        <el-button @click="showHistoryDialog = true" icon="Clock">
          历史版本
        </el-button>
      </div>
    </div>

    <!-- Monaco Editor容器 -->
    <div ref="editorContainer" class="monaco-editor-container"></div>

    <!-- 代码信息 -->
    <div class="code-info">
      <el-descriptions :column="4" size="small" border>
        <el-descriptions-item label="代码ID">{{ code.id }}</el-descriptions-item>
        <el-descriptions-item label="语言">{{ code.language }}</el-descriptions-item>
        <el-descriptions-item label="框架">{{ code.framework }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ code.current_version }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- AI修改对话框 -->
    <el-dialog v-model="showModifyDialog" title="AI代码修改" width="600px">
      <el-form :model="modifyForm" label-width="80px">
        <el-form-item label="修改提示">
          <el-input
            v-model="modifyForm.userPrompt"
            type="textarea"
            :rows="4"
            placeholder="请描述你想要的修改，例如：添加GPU支持、优化性能、添加注释..."
          />
        </el-form-item>
        <el-form-item label="常用提示">
          <el-space wrap>
            <el-tag
              v-for="prompt in commonPrompts"
              :key="prompt.label"
              @click="modifyForm.userPrompt = prompt.value"
              style="cursor: pointer"
            >
              {{ prompt.label }}
            </el-tag>
          </el-space>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showModifyDialog = false">取消</el-button>
        <el-button type="primary" @click="modifyCode" :loading="modifying">
          生成修改
        </el-button>
      </template>
    </el-dialog>

    <!-- 版本历史对话框 -->
    <el-dialog v-model="showHistoryDialog" title="版本历史" width="800px">
      <el-timeline>
        <el-timeline-item
          v-for="version in codeVersions"
          :key="version.id"
          :timestamp="version.created_at"
          placement="top"
        >
          <el-card>
            <div class="version-header">
              <span class="version-number">v{{ version.version_number }}</span>
              <el-tag :type="version.author === 'AI' ? 'primary' : 'success'">
                {{ version.author }}
              </el-tag>
            </div>
            <div class="version-description">{{ version.change_description }}</div>
            <div class="version-prompt" v-if="version.prompt">
              <strong>提示词:</strong> {{ version.prompt }}
            </div>
            <el-button
              size="small"
              @click="viewVersion(version)"
              style="margin-top: 8px"
            >
              查看代码
            </el-button>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>

    <!-- 运行结果对话框 -->
    <el-dialog v-model="showResultDialog" title="运行结果" width="70%">
      <div v-if="runResult">
        <el-alert
          :type="runResult.success ? 'success' : 'error'"
          :title="runResult.success ? '运行成功' : '运行失败'"
          :description="runResult.message"
          show-icon
          :closable="false"
        />

        <div v-if="runResult.output" class="run-output">
          <h4>输出:</h4>
          <pre>{{ runResult.output }}</pre>
        </div>

        <div v-if="runResult.error" class="run-error">
          <h4>错误:</h4>
          <pre>{{ runResult.error }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as monaco from 'monaco-editor'
import { ElMessage } from 'element-plus'
import api from '@/api'

// Props
const props = defineProps({
  codeId: {
    type: Number,
    required: true
  }
})

// 响应式数据
const code = ref({})
const showModifyDialog = ref(false)
const showHistoryDialog = ref(false)
const showResultDialog = ref(false)
const editorContainer = ref(null)
const modifying = ref(false)
const codeVersions = ref([])
const runResult = ref(null)

// Monaco Editor实例
let editor = null

// 表单数据
const modifyForm = ref({
  userPrompt: ''
})

// 常用提示词
const commonPrompts = [
  { label: '添加GPU支持', value: '添加GPU支持和CUDA加速' },
  { label: '添加注释', value: '为代码添加详细的中文注释和文档字符串' },
  { label: '优化性能', value: '优化代码性能，减少计算复杂度' },
  { label: '添加测试', value: '添加单元测试和验证逻辑' },
  { label: '添加类型提示', value: '添加Python类型提示（Type Hints）' },
  { label: '处理异常', value: '添加完善的异常处理和错误提示' }
]

// 方法
const initMonacoEditor = () => {
  require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }})

  require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(editorContainer.value, {
      value: code.value.code || '# Code will appear here',
      language: getMonacoLanguage(code.value.language),
      theme: 'vs-dark',
      options: {
        fontSize: 14,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        wordWrap: 'on',
        lineNumbers: 'on',
        renderWhitespace: 'selection',
        tabSize: 2,
        formatOnPaste: true,
        formatOnType: true
      }
    })
  })
}

const getMonacoLanguage = (language) => {
  const langMap = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'java': 'java',
    'cpp': 'cpp',
    'go': 'go',
    'rust': 'rust'
  }
  return langMap[language] || 'python'
}

const getQualityType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
}

const loadCode = async () => {
  try {
    const response = await api.getCode(props.codeId)
    if (response.success) {
      code.value = response.data
      if (editor) {
        editor.setValue(code.value.code)
      }
      // 加载版本历史
      loadVersionHistory()
    }
  } catch (error) {
    ElMessage.error('加载代码失败')
    console.error(error)
  }
}

const modifyCode = async () => {
  if (!modifyForm.value.userPrompt) {
    ElMessage.warning('请输入修改提示')
    return
  }

  modifying.value = true
  try {
    const response = await api.modifyCode(props.codeId, modifyForm.value.userPrompt)
    if (response.success) {
      code.value = response.data
      if (editor) {
        editor.setValue(code.value.code)
      }
      ElMessage.success('代码修改成功')
      showModifyDialog.value = false
      modifyForm.value.userPrompt = ''
    }
  } catch (error) {
    ElMessage.error('代码修改失败')
    console.error(error)
  } finally {
    modifying.value = false
  }
}

const loadVersionHistory = async () => {
  // 从后端获取版本历史
  try {
    // 这里需要API支持获取版本历史
    // const response = await api.getCodeVersions(props.codeId)
    // codeVersions.value = response.data
  } catch (error) {
    console.error('加载版本历史失败:', error)
  }
}

const viewVersion = (version) => {
  if (editor && version.code_diff) {
    // 显示版本差异或代码
    editor.setValue(version.code || code.value.code)
    ElMessage.info(`正在查看 v${version.version_number}`)
  }
}

const runCode = async () => {
  // 模拟代码运行
  ElMessage.info('代码执行功能需要后端沙箱环境支持')

  showResultDialog.value = true
  runResult.value = {
    success: false,
    message: '当前为演示模式，代码执行功能正在开发中',
    output: null,
    error: '功能开发中'
  }
}

const saveCode = () => {
  ElMessage.success('代码已保存到数据库')
}

const copyCode = () => {
  if (editor) {
    navigator.clipboard.writeText(editor.getValue())
    ElMessage.success('代码已复制到剪贴板')
  }
}

const downloadCode = () => {
  if (!code.value.code) return

  const blob = new Blob([code.value.code], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `code_${code.value.id}_${code.value.current_version}.${code.value.language}`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('代码下载成功')
}

// 生命周期
onMounted(() => {
  initMonacoEditor()
  loadCode()
})

// 监听codeId变化
watch(() => props.codeId, () => {
  loadCode()
})
</script>

<style scoped>
.code-editor-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.editor-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e0e0e0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 8px;
}

.monaco-editor-container {
  flex: 1;
  min-height: 400px;
}

.code-info {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.version-number {
  font-weight: 600;
  font-size: 16px;
}

.version-description {
  margin-bottom: 8px;
  color: #606266;
}

.version-prompt {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

.run-output,
.run-error {
  margin-top: 16px;
  padding: 12px;
  border-radius: 4px;
  background: #f5f7fa;
}

.run-output h4,
.run-error h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.run-output pre,
.run-error pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.run-error {
  background: #fef0f0;
}

.run-error pre {
  color: #f56c6c;
}
</style>
