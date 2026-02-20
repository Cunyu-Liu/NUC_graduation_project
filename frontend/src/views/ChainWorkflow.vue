<template>
  <div class="chain-workflow-container">
    <!-- 左侧：输入和配置面板 -->
    <div class="chain-input-panel">
      <div class="panel-header">
        <h2>输入内容</h2>
      </div>
      
      <div class="input-section">
        <el-input
          v-model="workflowInput"
          type="textarea"
          :rows="10"
          placeholder="输入要处理的论文内容、研究问题或其他文本..."
          resize="none"
        />
      </div>
      
      <div class="templates-section">
        <h3>快速加载模板</h3>
        <div class="template-buttons">
          <el-button size="small" @click="loadTemplate('summary')">论文分析</el-button>
          <el-button size="small" @click="loadTemplate('review')">文献综述</el-button>
          <el-button size="small" @click="loadTemplate('code')">代码生成</el-button>
          <el-button size="small" @click="loadTemplate('topic')">主题研究</el-button>
        </div>
      </div>
    </div>

    <!-- 中间：链式配置面板 -->
    <div class="chain-config-panel">
      <div class="panel-header">
        <h2>链式工作流配置</h2>
        <el-tooltip content="添加节点">
          <el-button type="primary" circle @click="showAddNode = true">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
      </div>

      <!-- 节点列表 -->
      <div class="nodes-list">
        <div
          v-for="(node, index) in chainNodes"
          :key="node.id"
          class="chain-node"
          :class="{ 
            'active': currentNode?.id === node.id,
            'completed': node.status === 'completed',
            'running': node.status === 'running',
            'error': node.status === 'error'
          }"
          @click="selectNode(node)"
        >
          <div class="node-index">{{ index + 1 }}</div>
          <div class="node-info">
            <div class="node-name">{{ node.name }}</div>
            <div class="node-type">{{ getNodeTypeLabel(node.type) }}</div>
          </div>
          <div class="node-status">
            <el-icon v-if="node.status === 'completed'" class="status-icon success"><CircleCheck /></el-icon>
            <el-icon v-else-if="node.status === 'running'" class="status-icon running"><Loading /></el-icon>
            <el-icon v-else-if="node.status === 'error'" class="status-icon error"><CircleClose /></el-icon>
            <el-icon v-else class="status-icon pending"><Timer /></el-icon>
          </div>
          <div class="node-actions">
            <el-icon class="action-btn" @click.stop="moveNode(index, -1)" v-if="index > 0"><ArrowUp /></el-icon>
            <el-icon class="action-btn" @click.stop="moveNode(index, 1)" v-if="index < chainNodes.length - 1"><ArrowDown /></el-icon>
            <el-icon class="action-btn delete" @click.stop="removeNode(index)"><Delete /></el-icon>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-if="chainNodes.length === 0" description="暂无节点，点击右上角添加" />
      </div>

      <!-- 连接箭头 -->
      <div v-if="chainNodes.length > 1" class="chain-connections">
        <div
          v-for="i in chainNodes.length - 1"
          :key="i"
          class="connection-line"
        >
          <el-icon><Bottom /></el-icon>
        </div>
      </div>

      <!-- 执行按钮 -->
      <div class="panel-footer">
        <el-button 
          type="primary" 
          size="large" 
          class="execute-btn"
          :loading="isExecuting"
          :disabled="chainNodes.length === 0"
          @click="executeChain"
        >
          <el-icon><VideoPlay /></el-icon>
          执行链式调用
        </el-button>
        <el-button size="large" @click="resetChain">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </div>

    <!-- 中间：节点配置详情 -->
    <div class="node-config-panel" v-if="currentNode">
      <div class="panel-header">
        <h3>{{ currentNode.name }}</h3>
        <el-tag :type="getNodeTypeTag(currentNode.type)">
          {{ getNodeTypeLabel(currentNode.type) }}
        </el-tag>
      </div>

      <el-form label-width="100px" class="node-form">
        <!-- 节点名称 -->
        <el-form-item label="节点名称">
          <el-input v-model="currentNode.name" placeholder="输入节点名称" />
        </el-form-item>

        <!-- 输入源 -->
        <el-form-item label="输入源">
          <el-select v-model="currentNode.inputSource" style="width: 100%">
            <el-option label="原始输入" value="original" />
            <el-option 
              v-for="(node, idx) in previousNodes" 
              :key="node.id"
              :label="`步骤 ${idx + 1}: ${node.name}`"
              :value="node.id"
            />
          </el-select>
        </el-form-item>

        <!-- 提示词模板 -->
        <el-form-item label="提示词模板">
          <el-select 
            v-model="currentNode.template" 
            placeholder="选择预设模板"
            style="width: 100%"
            @change="applyTemplate"
          >
            <el-option-group label="分析类">
              <el-option label="生成摘要" value="summary" />
              <el-option label="提取要点" value="keypoints" />
              <el-option label="识别研究空白" value="gaps" />
              <el-option label="主题分析" value="topic" />
            </el-option-group>
            <el-option-group label="生成类">
              <el-option label="生成代码" value="code" />
              <el-option label="生成报告" value="report" />
              <el-option label="文献综述" value="review" />
            </el-option-group>
            <el-option-group label="评估类">
              <el-option label="质量评估" value="quality" />
              <el-option label="创新性评估" value="innovation" />
              <el-option label="方法评估" value="method" />
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- 自定义提示词 -->
        <el-form-item label="自定义提示">
          <el-input
            v-model="currentNode.prompt"
            type="textarea"
            :rows="6"
            placeholder="输入自定义提示词，使用 {{input}} 引用输入内容"
          />
        </el-form-item>

        <!-- 模型配置 -->
        <el-form-item label="模型">
          <el-select v-model="currentNode.model" style="width: 100%">
            <el-option label="GLM-4-Plus" value="glm-4-plus" />
            <el-option label="GLM-4-Flash" value="glm-4-flash" />
          </el-select>
        </el-form-item>

        <el-form-item label="温度">
          <el-slider v-model="currentNode.temperature" :min="0" :max="1" :step="0.1" show-stops />
        </el-form-item>

        <el-form-item label="最大长度">
          <el-input-number v-model="currentNode.maxTokens" :min="500" :max="8000" :step="500" />
        </el-form-item>

        <!-- 输出处理 -->
        <el-form-item label="输出格式">
          <el-radio-group v-model="currentNode.outputFormat">
            <el-radio label="text">纯文本</el-radio>
            <el-radio label="json">JSON</el-radio>
            <el-radio label="markdown">Markdown</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 条件分支 -->
        <el-form-item label="条件执行">
          <el-switch v-model="currentNode.conditional" />
        </el-form-item>

        <el-form-item v-if="currentNode.conditional" label="条件表达式">
          <el-input
            v-model="currentNode.condition"
            placeholder="例如: input.score > 0.8"
          />
        </el-form-item>
      </el-form>

      <!-- 变量预览 -->
      <div class="variables-preview">
        <div class="preview-title">可用变量</div>
        <div class="variable-list">
          <el-tag v-for="variable in availableVariables" :key="variable.name" size="small" class="variable-tag">
            {{ variable.name }}: {{ variable.description }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 右侧：执行结果 -->
    <div class="execution-panel">
      <div class="panel-header">
        <h3>执行结果</h3>
        <div class="execution-stats" v-if="executionTime > 0">
          <el-tag size="small" type="info">
            <el-icon><Timer /></el-icon>
            {{ executionTime }}ms
          </el-tag>
        </div>
      </div>

      <!-- 进度条 -->
      <div v-if="isExecuting" class="execution-progress">
        <el-progress 
          :percentage="executionProgress" 
          :status="executionStatus"
          :stroke-width="8"
        />
        <div class="current-step">正在执行: {{ currentExecutingNode?.name }}</div>
      </div>

      <!-- 结果列表 -->
      <div class="results-list" v-else>
        <div
          v-for="(result, index) in executionResults"
          :key="index"
          class="result-item"
          :class="{ 'expanded': result.expanded }"
        >
          <div class="result-header" @click="result.expanded = !result.expanded">
            <div class="result-title">
              <span class="step-number">步骤 {{ index + 1 }}</span>
              <span class="node-name">{{ result.nodeName }}</span>
            </div>
            <div class="result-meta">
              <el-tag size="small" :type="result.success ? 'success' : 'danger'">
                {{ result.success ? '成功' : '失败' }}
              </el-tag>
              <el-icon class="expand-icon"><ArrowDown v-if="result.expanded" /><ArrowRight v-else /></el-icon>
            </div>
          </div>
          
          <div v-if="result.expanded" class="result-content">
            <div class="result-section">
              <div class="section-title">输入</div>
              <pre class="section-content input">{{ result.input }}</pre>
            </div>
            <div class="result-section">
              <div class="section-title">输出</div>
              <pre class="section-content output">{{ result.output }}</pre>
            </div>
            <div v-if="result.error" class="result-section">
              <div class="section-title">错误</div>
              <pre class="section-content error">{{ result.error }}</pre>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty v-if="executionResults.length === 0" description="尚未执行，请配置工作流并点击执行" />
      </div>

      <!-- 操作按钮 -->
      <div class="panel-footer" v-if="executionResults.length > 0">
        <el-button @click="exportResults">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
        <el-button type="primary" @click="saveWorkflow">
          <el-icon><Save /></el-icon>
          保存工作流
        </el-button>
      </div>
    </div>

    <!-- 添加节点对话框 -->
    <el-dialog v-model="showAddNode" title="添加节点" width="500px">
      <el-form label-width="80px">
        <el-form-item label="节点类型">
          <el-radio-group v-model="newNode.type">
            <el-radio-button label="analysis">分析</el-radio-button>
            <el-radio-button label="generation">生成</el-radio-button>
            <el-radio-button label="evaluation">评估</el-radio-button>
            <el-radio-button label="transform">转换</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="节点名称">
          <el-input v-model="newNode.name" placeholder="输入节点名称" />
        </el-form-item>

        <el-form-item label="模板">
          <el-select v-model="newNode.template" placeholder="选择预设模板" style="width: 100%">
            <el-option
              v-for="template in availableTemplates"
              :key="template.value"
              :label="template.label"
              :value="template.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddNode = false">取消</el-button>
        <el-button type="primary" @click="addNode">确定</el-button>
      </template>
    </el-dialog>

    <!-- 保存工作流对话框 -->
    <el-dialog v-model="showSaveWorkflow" title="保存工作流" width="400px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="workflowName" placeholder="输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="workflowDescription" type="textarea" :rows="3" placeholder="输入工作流描述" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSaveWorkflow = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveWorkflow">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus, VideoPlay, Refresh, ArrowUp, ArrowDown, Delete,
  CircleCheck, CircleClose, Loading, Timer, Bottom,
  ArrowRight,
  Download, Save
} from '@element-plus/icons-vue'
import api from '@/api'

// 状态
const showAddNode = ref(false)
const showSaveWorkflow = ref(false)
const workflowName = ref('')
const workflowDescription = ref('')
const currentNode = ref(null)
const isExecuting = ref(false)
const executionProgress = ref(0)
const executionStatus = ref('')
const executionTime = ref(0)
const currentExecutingNode = ref(null)
const executionResults = ref([])

// 链式节点
const chainNodes = ref([])

// 新节点配置
const newNode = ref({
  type: 'analysis',
  name: '',
  template: ''
})

// 可用模板
const availableTemplates = [
  { label: '生成摘要', value: 'summary', type: 'analysis' },
  { label: '提取要点', value: 'keypoints', type: 'analysis' },
  { label: '识别研究空白', value: 'gaps', type: 'analysis' },
  { label: '主题分析', value: 'topic', type: 'analysis' },
  { label: '生成代码', value: 'code', type: 'generation' },
  { label: '生成报告', value: 'report', type: 'generation' },
  { label: '文献综述', value: 'review', type: 'generation' },
  { label: '质量评估', value: 'quality', type: 'evaluation' },
  { label: '创新性评估', value: 'innovation', type: 'evaluation' },
  { label: '方法评估', value: 'method', type: 'evaluation' },
  { label: '数据清洗', value: 'clean', type: 'transform' },
  { label: '格式转换', value: 'format', type: 'transform' }
]

// 计算属性
const previousNodes = computed(() => {
  if (!currentNode.value) return []
  const index = chainNodes.value.findIndex(n => n.id === currentNode.value.id)
  return chainNodes.value.slice(0, index)
})

const availableVariables = computed(() => {
  const vars = [
    { name: '{{input}}', description: '当前节点的输入内容' },
    { name: '{{original}}', description: '原始输入内容' }
  ]
  
  previousNodes.value.forEach((node, idx) => {
    vars.push({
      name: `{{step${idx + 1}}}`,
      description: `${node.name} 的输出`
    })
  })
  
  return vars
})

// 方法
const getNodeTypeLabel = (type) => {
  const labels = {
    analysis: '分析',
    generation: '生成',
    evaluation: '评估',
    transform: '转换'
  }
  return labels[type] || type
}

const getNodeTypeTag = (type) => {
  const tags = {
    analysis: 'primary',
    generation: 'success',
    evaluation: 'warning',
    transform: 'info'
  }
  return tags[type] || ''
}

const addNode = () => {
  if (!newNode.value.name) {
    ElMessage.warning('请输入节点名称')
    return
  }
  
  const template = availableTemplates.find(t => t.value === newNode.value.template)
  
  const node = {
    id: Date.now(),
    name: newNode.value.name,
    type: newNode.value.type,
    template: newNode.value.template,
    prompt: getDefaultPrompt(newNode.value.template),
    model: 'glm-4-plus',
    temperature: 0.7,
    maxTokens: 4000,
    inputSource: chainNodes.value.length === 0 ? 'original' : chainNodes.value[chainNodes.value.length - 1].id,
    outputFormat: 'text',
    conditional: false,
    condition: '',
    status: 'pending'
  }
  
  chainNodes.value.push(node)
  currentNode.value = node
  showAddNode.value = false
  
  // 重置新节点表单
  newNode.value = { type: 'analysis', name: '', template: '' }
}

const getDefaultPrompt = (template) => {
  const prompts = {
    summary: '请对以下内容生成一份简洁的摘要：\n\n{{input}}',
    keypoints: '请从以下内容中提取核心要点：\n\n{{input}}',
    gaps: '请分析以下内容，识别研究空白：\n\n{{input}}',
    topic: '请分析以下内容的主题：\n\n{{input}}',
    code: '请根据以下需求生成代码：\n\n{{input}}',
    report: '请根据以下内容生成报告：\n\n{{input}}',
    review: '请对以下内容进行综述：\n\n{{input}}',
    quality: '请评估以下内容的质量：\n\n{{input}}',
    innovation: '请评估以下内容的创新性：\n\n{{input}}',
    method: '请评估以下方法的合理性：\n\n{{input}}',
    clean: '请清洗以下数据：\n\n{{input}}',
    format: '请将以下内容转换为标准格式：\n\n{{input}}'
  }
  return prompts[template] || '请处理以下内容：\n\n{{input}}'
}

const removeNode = (index) => {
  chainNodes.value.splice(index, 1)
  if (currentNode.value && chainNodes.value.findIndex(n => n.id === currentNode.value.id) === -1) {
    currentNode.value = chainNodes.value[0] || null
  }
}

const moveNode = (index, direction) => {
  const newIndex = index + direction
  if (newIndex >= 0 && newIndex < chainNodes.value.length) {
    const temp = chainNodes.value[index]
    chainNodes.value[index] = chainNodes.value[newIndex]
    chainNodes.value[newIndex] = temp
  }
}

const selectNode = (node) => {
  currentNode.value = node
}

const applyTemplate = (template) => {
  if (currentNode.value && template) {
    currentNode.value.prompt = getDefaultPrompt(template)
  }
}

const workflowInput = ref('')

const executeChain = async () => {
  if (chainNodes.value.length === 0) {
    ElMessage.warning('请先添加工作流节点')
    return
  }
  
  // 如果没有输入内容，提示用户
  if (!workflowInput.value.trim()) {
    ElMessage.warning('请输入工作流处理内容')
    return
  }
  
  isExecuting.value = true
  executionProgress.value = 0
  executionStatus.value = ''
  executionResults.value = []
  
  const startTime = Date.now()
  
  try {
    // 重置所有节点状态
    chainNodes.value.forEach(node => {
      node.status = 'pending'
      node.output = null
      node.error = null
    })
    
    // 准备节点配置
    const nodesConfig = chainNodes.value.map(node => ({
      id: node.id,
      name: node.name,
      type: node.type,
      prompt: node.prompt,
      model: node.model,
      temperature: node.temperature,
      maxTokens: node.maxTokens,
      inputSource: node.inputSource,
      outputFormat: node.outputFormat,
      conditional: node.conditional,
      condition: node.condition
    }))
    
    // 调用后端 API
    const response = await api.executeWorkflow(nodesConfig, {
      content: workflowInput.value
    })
    
    if (response.success) {
      // 更新执行结果
      executionResults.value = response.data.results.map((result, index) => ({
        nodeName: result.node_name,
        nodeType: result.node_type,
        input: result.input_preview || '',
        output: result.full_output || result.output_preview || '',
        success: result.status === 'completed',
        error: result.error,
        expanded: index === response.data.results.length - 1
      }))
      
      // 更新节点状态
      response.data.results.forEach((result, index) => {
        if (chainNodes.value[index]) {
          chainNodes.value[index].status = result.status
          chainNodes.value[index].output = result.full_output
          chainNodes.value[index].error = result.error
        }
      })
      
      executionProgress.value = 100
      executionStatus.value = 'success'
      executionTime.value = response.data.total_time * 1000
      
      ElMessage.success(`工作流执行完成，耗时 ${response.data.total_time.toFixed(2)}s`)
    } else {
      throw new Error(response.error || '执行失败')
    }
    
  } catch (error) {
    console.error('工作流执行错误:', error)
    executionStatus.value = 'exception'
    ElMessage.error(`执行失败: ${error.message}`)
    
    // 标记当前运行的节点为错误状态
    const runningNode = chainNodes.value.find(n => n.status === 'running')
    if (runningNode) {
      runningNode.status = 'error'
      runningNode.error = error.message
    }
  } finally {
    isExecuting.value = false
    currentExecutingNode.value = null
  }
}

// 加载工作流模板
const loadTemplate = async (templateId) => {
  try {
    const response = await api.getWorkflowTemplates()
    if (response.success) {
      const template = response.data.find(t => t.id === templateId)
      if (template) {
        // 清空现有节点
        chainNodes.value = []
        
        // 根据模板创建节点
        template.nodes.forEach((nodeConfig, index) => {
          const newNode = {
            id: `node_${Date.now()}_${index}`,
            name: nodeConfig.name,
            type: nodeConfig.type,
            template: nodeConfig.template,
            prompt: getDefaultPrompt(nodeConfig.template),
            model: nodeConfig.model || 'glm-4-plus',
            temperature: 0.7,
            maxTokens: 4000,
            inputSource: index === 0 ? 'original' : chainNodes.value[index - 1]?.id || 'original',
            outputFormat: 'text',
            conditional: false,
            condition: '',
            status: 'pending'
          }
          chainNodes.value.push(newNode)
        })
        
        ElMessage.success(`已加载模板: ${template.name}`)
      }
    }
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

const resetChain = () => {
  chainNodes.value.forEach(node => {
    node.status = 'pending'
  })
  executionResults.value = []
  executionProgress.value = 0
  executionTime.value = 0
  ElMessage.success('已重置工作流')
}

const exportResults = () => {
  const data = JSON.stringify(executionResults.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow-results-${Date.now()}.json`
  a.click()
  ElMessage.success('结果已导出')
}

const saveWorkflow = () => {
  showSaveWorkflow.value = true
}

const confirmSaveWorkflow = async () => {
  if (!workflowName.value) {
    ElMessage.warning('请输入工作流名称')
    return
  }
  
  try {
    // 调用 API 保存工作流
    await api.saveWorkflow({
      name: workflowName.value,
      description: workflowDescription.value,
      nodes: chainNodes.value
    })
    
    ElMessage.success('工作流保存成功')
    showSaveWorkflow.value = false
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

onMounted(() => {
  // 加载模板列表
  loadTemplate('summary')
})
</script>

<style scoped>
.chain-workflow-container {
  display: flex;
  height: calc(100vh - 64px);
  background: #f5f7fa;
}

/* 左侧输入面板 */
.chain-input-panel {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.chain-input-panel .panel-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 12px;
}

.chain-input-panel .panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.input-section {
  flex: 1;
  margin-bottom: 16px;
}

.input-section :deep(.el-textarea__inner) {
  height: 100%;
  min-height: 200px;
}

.templates-section h3 {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.template-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 中间配置面板 */
.chain-config-panel {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
}

.nodes-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  position: relative;
}

.chain-node {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.chain-node:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.chain-node.active {
  border-color: #409eff;
  background: #f0f9ff;
}

.chain-node.completed {
  border-color: #67c23a;
}

.chain-node.running {
  border-color: #e6a23c;
  animation: pulse 1.5s infinite;
}

.chain-node.error {
  border-color: #f56c6c;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.node-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-type {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.node-status {
  display: flex;
  align-items: center;
}

.status-icon {
  font-size: 18px;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.running {
  color: #e6a23c;
}

.status-icon.error {
  color: #f56c6c;
}

.status-icon.pending {
  color: #c0c4cc;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chain-node:hover .node-actions {
  opacity: 1;
}

.action-btn {
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f5f7fa;
  color: #409eff;
}

.action-btn.delete:hover {
  color: #f56c6c;
}

.chain-connections {
  position: absolute;
  left: 32px;
  top: 40px;
  display: flex;
  flex-direction: column;
  gap: 44px;
  pointer-events: none;
  color: #c0c4cc;
}

.connection-line {
  font-size: 16px;
}

.panel-footer {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
}

.execute-btn {
  flex: 1;
}

/* 中间配置面板 */
.node-config-panel {
  width: 400px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.node-form {
  padding: 20px;
}

.variables-preview {
  padding: 0 20px 20px;
}

.preview-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.variable-tag {
  cursor: help;
}

/* 右侧执行面板 */
.execution-panel {
  flex: 1;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.execution-stats {
  display: flex;
  gap: 8px;
}

.execution-progress {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.current-step {
  text-align: center;
  margin-top: 8px;
  color: #606266;
  font-size: 13px;
}

.results-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.result-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  cursor: pointer;
  transition: background 0.2s;
}

.result-header:hover {
  background: #e4e7ed;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  font-size: 12px;
  color: #909399;
  background: #fff;
  padding: 2px 8px;
  border-radius: 4px;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-icon {
  color: #909399;
  transition: transform 0.2s;
}

.result-content {
  padding: 16px;
}

.result-section {
  margin-bottom: 16px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-content {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Monaco', 'Menlo', monospace;
  max-height: 200px;
  overflow-y: auto;
}

.section-content.input {
  background: #ecf5ff;
  color: #409eff;
}

.section-content.output {
  background: #f0f9ff;
  color: #303133;
}

.section-content.error {
  background: #fef0f0;
  color: #f56c6c;
}
</style>
