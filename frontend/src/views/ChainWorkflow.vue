<template>
  <div class="chain-workflow-container">
    <!-- 左侧：输入和配置面板 -->
    <div class="chain-input-panel">
      <div class="panel-header">
        <h2>输入内容</h2>
        <el-tooltip content="查看使用指南">
          <el-button circle size="small" @click="showGuide = true">
            <el-icon><QuestionFilled /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
      
      <div class="input-section">
        <div class="input-label">
          <span>输入要处理的内容：</span>
          <el-tag size="small" type="info">支持论文摘要、研究问题、代码等</el-tag>
        </div>
        <el-input
          v-model="workflowInput"
          type="textarea"
          :rows="10"
          placeholder="输入要处理的论文内容、研究问题或其他文本...&#10;例如：&#10;论文标题：基于深度学习的蛋白质结构预测&#10;摘要：本文提出了一种新的..."
          resize="none"
        />
      </div>
      
      <div class="templates-section">
        <h3>📋 快速模板</h3>
        <p class="section-hint">点击加载预设工作流模板，自动配置节点</p>
        <div class="template-buttons">
          <el-button size="small" type="primary" plain @click="loadTemplate('summary')">
            <el-icon><Document /></el-icon> 论文分析
          </el-button>
          <el-button size="small" type="success" plain @click="loadTemplate('review')">
            <el-icon><Reading /></el-icon> 文献综述
          </el-button>
          <el-button size="small" type="warning" plain @click="loadTemplate('code')">
            <el-icon><Cpu /></el-icon> 代码生成
          </el-button>
          <el-button size="small" type="info" plain @click="loadTemplate('topic')">
            <el-icon><DataAnalysis /></el-icon> 主题研究
          </el-button>
        </div>
      </div>

      <div class="quick-examples">
        <h3>💡 示例输入</h3>
        <el-collapse>
          <el-collapse-item title="论文摘要示例" name="1">
            <div class="example-text" @click="useExample('paper')">
              论文标题：基于Transformer的蛋白质结构预测方法研究
              摘要：本文提出了一种基于Transformer架构的新型蛋白质结构预测方法...
              [点击查看使用此示例]
            </div>
          </el-collapse-item>
          <el-collapse-item title="研究问题示例" name="2">
            <div class="example-text" @click="useExample('question')">
              问题：如何提高深度学习模型在小样本医学图像分类任务中的性能？
              [点击查看使用此示例]
            </div>
          </el-collapse-item>
          <el-collapse-item title="代码需求示例" name="3">
            <div class="example-text" @click="useExample('code')">
              需求：实现一个基于PyTorch的Transformer模型，用于时间序列预测任务。
              要求：包含位置编码、多头注意力机制、前馈网络。
              [点击查看使用此示例]
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <!-- 中间：链式配置面板 -->
    <div class="chain-config-panel">
      <div class="panel-header">
        <div class="header-title">
          <h2>链式工作流配置</h2>
          <el-tag size="small" type="info">{{ chainNodes.length }} 个节点</el-tag>
        </div>
        <el-tooltip content="添加节点">
          <el-button type="primary" circle @click="showAddNode = true">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
      </div>

      <!-- 节点列表 -->
      <div class="nodes-list" v-if="chainNodes.length > 0">
        <div class="nodes-hint">
          <el-alert
            title="节点按顺序执行，每个节点的输出可作为下一个节点的输入"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
        
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

        <!-- 连接箭头 -->
        <div class="chain-connections" v-if="chainNodes.length > 1">
          <div
            v-for="i in chainNodes.length - 1"
            :key="i"
            class="connection-line"
          >
            <el-icon><Bottom /></el-icon>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无节点，点击右上角添加或选择左侧模板">
        <el-button type="primary" @click="showAddNode = true">添加第一个节点</el-button>
      </el-empty>

      <!-- 执行按钮 -->
      <div class="panel-footer" v-if="chainNodes.length > 0">
        <el-button 
          type="primary" 
          size="large" 
          class="execute-btn"
          :loading="isExecuting"
          :disabled="chainNodes.length === 0 || !workflowInput.trim()"
          @click="executeChain"
        >
          <el-icon><VideoPlay /></el-icon>
          {{ isExecuting ? '执行中...' : '执行链式调用' }}
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
          <div class="form-hint">选择此节点的输入数据来源</div>
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
              <el-option label="方法分析" value="method_analysis" />
            </el-option-group>
            <el-option-group label="生成类">
              <el-option label="生成代码" value="code" />
              <el-option label="生成报告" value="report" />
              <el-option label="文献综述" value="review" />
              <el-option label="改进建议" value="improvement" />
            </el-option-group>
            <el-option-group label="评估类">
              <el-option label="质量评估" value="quality" />
              <el-option label="创新性评估" value="innovation" />
              <el-option label="方法评估" value="method" />
              <el-option label="实验设计评估" value="experiment" />
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- 自定义提示词 -->
        <el-form-item label="自定义提示">
          <el-input
            v-model="currentNode.prompt"
            type="textarea"
            :rows="8"
            placeholder="输入自定义提示词，使用 {{input}} 引用输入内容&#10;例如：&#10;请对以下内容进行深度分析：&#10;&#10;{{input}}&#10;&#10;要求：&#10;1. 提取核心观点&#10;2. 分析研究方法&#10;3. 指出创新点"
          />
          <div class="form-hint">使用 {{input}} 引用输入内容，支持Markdown格式</div>
        </el-form-item>

        <!-- 模型配置 -->
        <el-divider content-position="left">模型配置</el-divider>
        
        <el-form-item label="模型">
          <el-select v-model="currentNode.model" style="width: 100%">
            <el-option label="GLM-4-Plus（推荐）" value="glm-4-plus" />
            <el-option label="GLM-4-Flash（快速）" value="glm-4-flash" />
          </el-select>
        </el-form-item>

        <el-form-item label="温度">
          <el-slider v-model="currentNode.temperature" :min="0" :max="1" :step="0.1" show-stops />
          <div class="slider-hint">
            <span>确定性</span>
            <span style="float: right;">创造性</span>
          </div>
        </el-form-item>

        <el-form-item label="最大长度">
          <el-input-number v-model="currentNode.maxTokens" :min="500" :max="8000" :step="500" style="width: 100%" />
        </el-form-item>

        <!-- 输出处理 -->
        <el-divider content-position="left">输出配置</el-divider>
        
        <el-form-item label="输出格式">
          <el-radio-group v-model="currentNode.outputFormat">
            <el-radio label="text">纯文本</el-radio>
            <el-radio label="json">JSON</el-radio>
            <el-radio label="markdown">Markdown</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <!-- 变量预览 -->
      <div class="variables-preview">
        <div class="preview-title">可用变量</div>
        <div class="variable-list">
          <el-tag v-for="variable in availableVariables" :key="variable.name" size="small" class="variable-tag" effect="plain">
            {{ variable.name }}
          </el-tag>
        </div>
        <div class="variable-hint">点击复制变量到剪贴板</div>
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
        <el-empty v-if="executionResults.length === 0" description="尚未执行，请配置工作流并点击执行">
          <template #description>
            <div class="empty-hint">
              <p>尚未执行工作流</p>
              <p class="sub-hint">1. 在左侧输入内容</p>
              <p class="sub-hint">2. 添加工作流节点</p>
              <p class="sub-hint">3. 点击"执行链式调用"</p>
            </div>
          </template>
        </el-empty>
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
        <el-button type="primary" @click="addNode" :disabled="!newNode.name">确定</el-button>
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
        <el-button type="primary" @click="confirmSaveWorkflow" :disabled="!workflowName">保存</el-button>
      </template>
    </el-dialog>

    <!-- 使用指南对话框 -->
    <el-dialog v-model="showGuide" title="链式工作流使用指南" width="700px">
      <div class="guide-content">
        <h4>🚀 快速开始</h4>
        <ol>
          <li><strong>输入内容</strong> - 在左侧输入框中粘贴论文摘要、研究问题或其他文本</li>
          <li><strong>选择模板</strong> - 点击"快速模板"加载预设的工作流配置</li>
          <li><strong>调整节点</strong> - 在中间面板添加、删除或调整处理节点</li>
          <li><strong>执行</strong> - 点击"执行链式调用"按钮开始处理</li>
          <li><strong>查看结果</strong> - 在右侧面板查看每个步骤的输出</li>
        </ol>
        
        <h4>📊 节点类型说明</h4>
        <ul>
          <li><strong>分析类</strong> - 提取信息、识别模式、总结内容</li>
          <li><strong>生成类</strong> - 创建新内容，如代码、报告、综述</li>
          <li><strong>评估类</strong> - 评估质量、创新性、方法合理性</li>
          <li><strong>转换类</strong> - 格式转换、数据清洗、翻译</li>
        </ul>
        
        <h4>💡 使用技巧</h4>
        <ul>
          <li>使用 <code>{{input}}</code> 引用原始输入</li>
          <li>使用 <code>{{step1}}</code>、<code>{{step2}}</code> 等引用前面节点的输出</li>
          <li>节点按顺序执行，前一个节点的输出可作为后一个节点的输入</li>
          <li>可以保存常用的工作流配置，方便下次使用</li>
        </ul>
        
        <h4>🔧 高级配置</h4>
        <ul>
          <li><strong>温度参数</strong> - 较低值产生更确定的输出，较高值更具创造性</li>
          <li><strong>最大长度</strong> - 控制生成的最大token数量</li>
          <li><strong>输出格式</strong> - 可选择纯文本、JSON或Markdown格式</li>
        </ul>
      </div>
      <template #footer>
        <el-button type="primary" @click="showGuide = false">知道了</el-button>
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
  ArrowRight, QuestionFilled, Document, Reading, Cpu, DataAnalysis,
  Download, Save
} from '@element-plus/icons-vue'
import api from '@/api'

// 状态
const showAddNode = ref(false)
const showSaveWorkflow = ref(false)
const showGuide = ref(false)
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

// 输入内容
const workflowInput = ref('')

// 可用模板
const availableTemplates = [
  { label: '生成摘要', value: 'summary', type: 'analysis' },
  { label: '提取要点', value: 'keypoints', type: 'analysis' },
  { label: '识别研究空白', value: 'gaps', type: 'analysis' },
  { label: '主题分析', value: 'topic', type: 'analysis' },
  { label: '方法分析', value: 'method_analysis', type: 'analysis' },
  { label: '生成代码', value: 'code', type: 'generation' },
  { label: '生成报告', value: 'report', type: 'generation' },
  { label: '文献综述', value: 'review', type: 'generation' },
  { label: '改进建议', value: 'improvement', type: 'generation' },
  { label: '质量评估', value: 'quality', type: 'evaluation' },
  { label: '创新性评估', value: 'innovation', type: 'evaluation' },
  { label: '方法评估', value: 'method', type: 'evaluation' },
  { label: '实验设计评估', value: 'experiment', type: 'evaluation' },
  { label: '数据清洗', value: 'clean', type: 'transform' },
  { label: '格式转换', value: 'format', type: 'transform' }
]

// 示例文本
const examples = {
  paper: `论文标题：基于Transformer的蛋白质结构预测方法研究

摘要：本文提出了一种基于Transformer架构的新型蛋白质结构预测方法。该方法利用自注意力机制捕获序列中的长程依赖关系，并通过多尺度特征融合策略整合不同层次的结构信息。实验结果表明，在CASP14数据集上，我们的方法相比现有最优方法将GDT-TS分数提高了2.3个百分点。`,
  question: `如何提高深度学习模型在小样本医学图像分类任务中的性能？

背景：现有方法在样本充足时表现良好，但在医学领域往往难以获取大量标注数据。
约束条件：
- 每类只有10-50个样本
- 需要高准确率
- 模型需要可解释`,
  code: `需求：实现一个基于PyTorch的Transformer模型，用于时间序列预测任务。

要求：
1. 包含位置编码
2. 多头注意力机制
3. 前馈网络
4. 残差连接和层归一化
5. 支持可变长度输入`
}

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
  
  ElMessage.success('节点添加成功')
}

const getDefaultPrompt = (template) => {
  const prompts = {
    summary: '请对以下内容生成一份简洁的摘要：\n\n{{input}}\n\n要求：\n1. 突出核心贡献\n2. 简明扼要，控制在200字以内\n3. 使用学术语言',
    keypoints: '请从以下内容中提取核心要点：\n\n{{input}}\n\n要求：\n1. 列出3-5个关键要点\n2. 每个要点一句话概括\n3. 按重要性排序',
    gaps: '请分析以下内容，识别研究空白：\n\n{{input}}\n\n要求：\n1. 指出现有研究的不足\n2. 提出可能的研究方向\n3. 说明每个方向的潜在价值',
    topic: '请分析以下内容的主题：\n\n{{input}}\n\n要求：\n1. 识别主要研究领域\n2. 提取核心关键词（5-10个）\n3. 说明与其他领域的关联',
    method_analysis: '请分析以下内容的研究方法：\n\n{{input}}\n\n要求：\n1. 描述使用的方法和技术\n2. 分析方法的优势和局限\n3. 与其他方法进行对比',
    code: '请根据以下需求生成代码：\n\n{{input}}\n\n要求：\n1. 代码结构清晰，注释完整\n2. 包含必要的错误处理\n3. 提供使用示例',
    report: '请根据以下内容生成报告：\n\n{{input}}\n\n要求：\n1. 结构完整，包含背景、方法、结果、结论\n2. 逻辑清晰，论证充分\n3. 使用学术写作规范',
    review: '请对以下内容进行综述：\n\n{{input}}\n\n要求：\n1. 系统回顾相关研究\n2. 比较不同方法的优缺点\n3. 指出未来研究方向',
    improvement: '请针对以下内容提出改进建议：\n\n{{input}}\n\n要求：\n1. 指出可改进的方面\n2. 提供具体的改进方案\n3. 分析改进后的预期效果',
    quality: '请评估以下内容的质量：\n\n{{input}}\n\n要求：\n1. 评估方法的科学性\n2. 分析实验设计的合理性\n3. 评价结论的可靠性\n4. 给出综合评分和改进建议',
    innovation: '请评估以下内容的创新性：\n\n{{input}}\n\n要求：\n1. 分析创新点和独特之处\n2. 与现有研究对比\n3. 评估创新程度和学术价值',
    method: '请评估以下方法的合理性：\n\n{{input}}\n\n要求：\n1. 分析方法的科学性\n2. 评估适用性和局限性\n3. 提出优化建议',
    experiment: '请评估以下实验设计：\n\n{{input}}\n\n要求：\n1. 分析实验设计的合理性\n2. 评估对照组设置\n3. 指出可能的混淆因素\n4. 提出改进建议',
    clean: '请清洗以下数据：\n\n{{input}}\n\n要求：\n1. 去除噪声和异常值\n2. 处理缺失值\n3. 标准化格式',
    format: '请将以下内容转换为标准格式：\n\n{{input}}\n\n要求：\n1. 统一格式规范\n2. 保持内容完整性\n3. 提高可读性'
  }
  return prompts[template] || '请处理以下内容：\n\n{{input}}'
}

const removeNode = (index) => {
  chainNodes.value.splice(index, 1)
  if (currentNode.value && chainNodes.value.findIndex(n => n.id === currentNode.value.id) === -1) {
    currentNode.value = chainNodes.value[0] || null
  }
  ElMessage.success('节点已删除')
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
    ElMessage.success('模板已应用')
  }
}

const useExample = (type) => {
  workflowInput.value = examples[type]
  ElMessage.success('示例已加载，您可以根据需要修改')
}

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
    
    // 更新进度
    executionProgress.value = 10
    
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
    const templates = {
      summary: {
        name: '论文分析',
        nodes: [
          { name: '提取要点', type: 'analysis', template: 'keypoints', model: 'glm-4-plus' },
          { name: '生成摘要', type: 'analysis', template: 'summary', model: 'glm-4-plus' },
          { name: '识别研究空白', type: 'analysis', template: 'gaps', model: 'glm-4-plus' }
        ]
      },
      review: {
        name: '文献综述',
        nodes: [
          { name: '主题分析', type: 'analysis', template: 'topic', model: 'glm-4-plus' },
          { name: '生成综述', type: 'generation', template: 'review', model: 'glm-4-plus' },
          { name: '质量评估', type: 'evaluation', template: 'quality', model: 'glm-4-plus' }
        ]
      },
      code: {
        name: '代码生成',
        nodes: [
          { name: '需求分析', type: 'analysis', template: 'method_analysis', model: 'glm-4-plus' },
          { name: '生成代码', type: 'generation', template: 'code', model: 'glm-4-plus' },
          { name: '代码评估', type: 'evaluation', template: 'quality', model: 'glm-4-plus' }
        ]
      },
      topic: {
        name: '主题研究',
        nodes: [
          { name: '主题识别', type: 'analysis', template: 'topic', model: 'glm-4-plus' },
          { name: '方法分析', type: 'analysis', template: 'method_analysis', model: 'glm-4-plus' },
          { name: '创新评估', type: 'evaluation', template: 'innovation', model: 'glm-4-plus' }
        ]
      }
    }
    
    const template = templates[templateId]
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
      
      // 自动选择第一个节点
      if (chainNodes.value.length > 0) {
        currentNode.value = chainNodes.value[0]
      }
      
      ElMessage.success(`已加载模板: ${template.name}，包含 ${template.nodes.length} 个节点`)
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
  ElMessage.success('已重置工作流状态')
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
  // 加载默认模板
  loadTemplate('summary')
  
  // 显示欢迎提示
  setTimeout(() => {
    if (chainNodes.value.length === 0) {
      ElMessage.info('欢迎使用链式工作流！点击左侧模板快速开始，或点击右上角 + 添加节点')
    }
  }, 500)
})
</script>

<style scoped>
.chain-workflow-container {
  display: flex;
  height: calc(100vh - 64px);
  background: #f5f7fa;
  overflow: hidden;
}

/* 左侧输入面板 */
.chain-input-panel {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
}

.chain-input-panel .panel-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chain-input-panel .panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.input-section {
  margin-bottom: 16px;
}

.input-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.input-section :deep(.el-textarea__inner) {
  min-height: 200px;
}

.templates-section h3,
.quick-examples h3 {
  font-size: 14px;
  color: #303133;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-hint {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

.template-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.template-buttons .el-button {
  flex: 1;
  min-width: calc(50% - 4px);
}

.quick-examples {
  margin-top: 20px;
}

.example-text {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  white-space: pre-wrap;
  line-height: 1.6;
}

.example-text:hover {
  background: #e6f7ff;
  color: #1890ff;
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

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
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

.nodes-hint {
  margin-bottom: 12px;
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
  top: 80px;
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
  width: 380px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.node-form {
  padding: 20px;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.slider-hint {
  font-size: 12px;
  color: #909399;
  margin-top: -8px;
}

.variables-preview {
  padding: 0 20px 20px;
}

.preview-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.variable-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.variable-tag:hover {
  background-color: #409eff;
  color: white;
}

.variable-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
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
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
  text-align: center;
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
  gap: 10px;
}

.step-number {
  font-size: 13px;
  color: #909399;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.expand-icon {
  color: #909399;
  transition: transform 0.2s;
}

.result-item.expanded .expand-icon {
  transform: rotate(180deg);
}

.result-content {
  padding: 16px;
  background: #fff;
}

.result-section {
  margin-bottom: 16px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.section-content {
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.section-content.input {
  background: #f5f7fa;
  color: #606266;
}

.section-content.output {
  background: #f0f9ff;
  color: #1890ff;
  border: 1px solid #bae7ff;
}

.section-content.error {
  background: #fff1f0;
  color: #cf1322;
  border: 1px solid #ffa39e;
}

/* 空状态 */
.empty-hint {
  text-align: left;
  color: #606266;
}

.empty-hint p {
  margin: 4px 0;
}

.sub-hint {
  font-size: 13px;
  color: #909399;
  padding-left: 16px;
}

/* 指南内容 */
.guide-content {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 16px;
}

.guide-content h4 {
  color: #1890ff;
  margin: 20px 0 12px 0;
  font-size: 15px;
}

.guide-content h4:first-child {
  margin-top: 0;
}

.guide-content ol,
.guide-content ul {
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}

.guide-content li {
  margin-bottom: 8px;
}

.guide-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #1890ff;
}

/* 响应式 */
@media (max-width: 1400px) {
  .chain-workflow-container {
    flex-wrap: wrap;
  }
  
  .chain-input-panel,
  .chain-config-panel,
  .node-config-panel {
    width: 50%;
    min-width: 300px;
  }
  
  .execution-panel {
    width: 100%;
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .chain-input-panel,
  .chain-config-panel,
  .node-config-panel {
    width: 100%;
  }
}
</style>
