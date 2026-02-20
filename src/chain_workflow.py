"""LangChain 链式工作流引擎 - v4.2院士版
支持 SequentialChain、自定义链节点、条件分支
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# LangChain 导入
try:
    from langchain.chains import SequentialChain, LLMChain, TransformChain
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    PromptTemplate = None
    StrOutputParser = None
    print("⚠️  LangChain 未安装，链式工作流功能将受限")


class NodeType(Enum):
    """链节点类型"""
    ANALYSIS = "analysis"           # 分析节点
    GENERATION = "generation"       # 生成节点
    EVALUATION = "evaluation"       # 评估节点
    TRANSFORM = "transform"         # 转换节点
    CONDITIONAL = "conditional"     # 条件节点
    MERGE = "merge"                 # 合并节点
    SPLIT = "split"                 # 拆分节点


class NodeStatus(Enum):
    """节点执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ChainNode:
    """链节点定义"""
    id: str
    name: str
    type: NodeType
    prompt: str
    model: str = "glm-4-plus"
    temperature: float = 0.7
    max_tokens: int = 4000
    input_source: str = "previous"  # "original", "previous", or node_id
    output_format: str = "text"     # "text", "json", "markdown"
    conditional: bool = False
    condition: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    nodes_results: List[Dict[str, Any]] = field(default_factory=list)
    final_output: Optional[str] = None
    total_time: float = 0.0
    total_tokens: int = 0
    error: Optional[str] = None


# 预设提示词模板
PRESET_TEMPLATES = {
    # 分析类
    "summary": {
        "name": "生成摘要",
        "type": NodeType.ANALYSIS,
        "prompt": """请对以下论文内容生成一份学术摘要。
要求：
1. 简洁明了，200-300字
2. 包含研究背景、方法、主要结果
3. 突出创新点

论文内容：
{input}

请生成摘要："""
    },
    "keypoints": {
        "name": "提取要点",
        "type": NodeType.ANALYSIS,
        "prompt": """请从以下论文中提取关键要点，按以下分类整理：
1. 研究问题
2. 方法论创新
3. 主要贡献
4. 实验结果
5. 局限性
6. 未来工作

论文内容：
{input}

请以JSON格式输出要点。"""
    },
    "gaps": {
        "name": "识别研究空白",
        "type": NodeType.ANALYSIS,
        "prompt": """请分析以下论文，识别当前研究领域存在的研究空白（Research Gaps）。

请按以下类型分类：
- 方法论空白：现有方法的不足
- 理论空白：理论框架的缺失
- 数据空白：数据集的局限
- 应用空白：未探索的应用场景
- 评估空白：评估指标的不足

论文内容：
{input}

请列出发现的研究空白，并说明其重要性和潜在解决方向。"""
    },
    "topic": {
        "name": "主题分析",
        "type": NodeType.ANALYSIS,
        "prompt": """请分析以下论文的主题和领域分类。

要求：
1. 确定主要研究领域
2. 识别关键技术/方法
3. 分析与其他领域的交叉点
4. 评估该主题的研究热度

论文内容：
{input}

请提供详细分析。"""
    },
    # 生成类
    "code": {
        "name": "生成代码",
        "type": NodeType.GENERATION,
        "prompt": """请根据以下论文描述的方法，生成可执行的Python代码实现。

要求：
1. 代码结构清晰，包含必要的注释
2. 包含输入输出示例
3. 处理边界情况
4. 使用标准库和常用深度学习框架

论文描述：
{input}

请生成代码（包含必要的说明文档）："""
    },
    "report": {
        "name": "生成报告",
        "type": NodeType.GENERATION,
        "prompt": """请根据以下内容生成一份研究报告。

报告结构：
1. 执行摘要
2. 背景介绍
3. 详细分析
4. 关键发现
5. 建议与展望

内容：
{input}

请生成完整的Markdown格式报告。"""
    },
    "review": {
        "name": "文献综述",
        "type": NodeType.GENERATION,
        "prompt": """请根据以下多篇论文内容，生成一份文献综述。

综述结构：
1. 研究背景与动机
2. 相关方法分类与对比
3. 各方法优缺点分析
4. 发展趋势与挑战
5. 未来研究方向

论文内容：
{input}

请生成综合性文献综述。"""
    },
    # 评估类
    "quality": {
        "name": "质量评估",
        "type": NodeType.EVALUATION,
        "prompt": """请对以下研究内容进行质量评估。

评估维度（每项1-10分）：
1. 创新性：方法或理论的新颖程度
2. 严谨性：实验设计和论证的严谨性
3. 实用性：实际应用价值
4. 清晰度：写作和表达的清晰度
5. 完整性：研究的完整度

内容：
{input}

请提供详细评估报告，包括总分和各项得分。"""
    },
    "innovation": {
        "name": "创新性评估",
        "type": NodeType.EVALUATION,
        "prompt": """请评估以下研究内容的创新性。

评估要点：
1. 核心创新点识别
2. 与现有工作的差异
3. 创新程度评级（高/中/低）
4. 创新点的学术价值
5. 创新点的潜在影响

内容：
{input}

请提供创新性评估报告。"""
    },
    "method": {
        "name": "方法评估",
        "type": NodeType.EVALUATION,
        "prompt": """请评估以下研究方法的合理性。

评估维度：
1. 方法选择的合理性
2. 方法论的科学性
3. 实验设计的完整性
4. 对比实验的充分性
5. 评估指标的恰当性
6. 可复现性

方法描述：
{input}

请提供详细的方法论评估。"""
    },
    # 转换类
    "clean": {
        "name": "数据清洗",
        "type": NodeType.TRANSFORM,
        "prompt": """请清洗并结构化以下数据。

清洗要求：
1. 去除重复和冗余信息
2. 统一格式和单位
3. 修复明显的错误
4. 补充缺失的上下文
5. 按逻辑重新组织

原始数据：
{input}

请输出清洗后的结构化数据。"""
    },
    "format": {
        "name": "格式转换",
        "type": NodeType.TRANSFORM,
        "prompt": """请将以下内容转换为标准格式。

目标格式：结构化JSON
要求：
1. 提取关键字段
2. 统一数据类型
3. 保持信息完整性

内容：
{input}

请输出转换后的JSON格式数据。"""
    }
}


class ChainWorkflowEngine:
    """链式工作流引擎"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        初始化链式工作流引擎
        
        Args:
            llm_config: LLM配置
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装，无法使用链式工作流")
        
        self.llm_config = llm_config or {}
        self.llm = self._create_llm()
    
    def _create_llm(self, model: Optional[str] = None, 
                   temperature: Optional[float] = None) -> ChatOpenAI:
        """创建 LLM 实例"""
        return ChatOpenAI(
            model=model or self.llm_config.get('model', 'glm-4-plus'),
            api_key=self.llm_config.get('api_key') or os.getenv('GLM_API_KEY'),
            base_url=self.llm_config.get('base_url') or os.getenv('GLM_BASE_URL'),
            temperature=temperature or self.llm_config.get('temperature', 0.7),
            max_tokens=self.llm_config.get('max_tokens', 4000),
            request_timeout=120
        )
    
    def create_node(self, template_key: str, custom_prompt: Optional[str] = None,
                   model: str = "glm-4-plus", temperature: float = 0.7) -> ChainNode:
        """
        根据模板创建链节点
        
        Args:
            template_key: 模板键
            custom_prompt: 自定义提示词（可选）
            model: 模型名称
            temperature: 温度参数
            
        Returns:
            ChainNode 实例
        """
        if template_key not in PRESET_TEMPLATES:
            raise ValueError(f"未知模板: {template_key}")
        
        template = PRESET_TEMPLATES[template_key]
        
        return ChainNode(
            id=f"node_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            name=template["name"],
            type=template["type"],
            prompt=custom_prompt or template["prompt"],
            model=model,
            temperature=temperature
        )
    
    async def execute_node(self, node: ChainNode, input_text: str) -> Dict[str, Any]:
        """
        执行单个链节点
        
        Args:
            node: 链节点
            input_text: 输入文本
            
        Returns:
            执行结果
        """
        import time
        
        start_time = time.time()
        node.status = NodeStatus.RUNNING
        
        try:
            # 创建 LLM 实例
            llm = self._create_llm(node.model, node.temperature)
            
            # 创建提示词模板
            prompt_template = PromptTemplate(
                input_variables=["input"],
                template=node.prompt
            )
            
            # 创建链
            chain = prompt_template | llm | StrOutputParser()
            
            # 执行
            result = await asyncio.to_thread(chain.invoke, {"input": input_text})
            
            # 更新节点状态
            node.status = NodeStatus.COMPLETED
            node.output = result
            node.execution_time = time.time() - start_time
            
            return {
                "success": True,
                "output": result,
                "execution_time": node.execution_time,
                "tokens": node.tokens_used
            }
            
        except Exception as e:
            node.status = NodeStatus.ERROR
            node.error = str(e)
            node.execution_time = time.time() - start_time
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": node.execution_time
            }
    
    async def execute_workflow(self, nodes: List[ChainNode], 
                              initial_input: str,
                              progress_callback: Optional[Callable] = None) -> WorkflowResult:
        """
        执行完整的工作流
        
        Args:
            nodes: 链节点列表
            initial_input: 初始输入
            progress_callback: 进度回调函数
            
        Returns:
            工作流执行结果
        """
        import time
        
        start_time = time.time()
        results = []
        current_input = initial_input
        
        total_nodes = len(nodes)
        
        for idx, node in enumerate(nodes):
            # 检查条件执行
            if node.conditional and node.condition:
                # 简化条件判断（实际应使用更复杂的表达式解析）
                if "score" in node.condition and "< 0.5" in node.condition:
                    # 示例：如果条件不满足则跳过
                    node.status = NodeStatus.SKIPPED
                    results.append({
                        "node_id": node.id,
                        "node_name": node.name,
                        "status": "skipped",
                        "reason": "条件不满足"
                    })
                    continue
            
            # 更新进度
            if progress_callback:
                progress_callback({
                    "current": idx + 1,
                    "total": total_nodes,
                    "node_name": node.name,
                    "progress": int((idx / total_nodes) * 100)
                })
            
            # 确定输入源
            if node.input_source == "original":
                current_input = initial_input
            elif node.input_source != "previous" and node.input_source:
                # 从指定节点获取输出
                for prev_result in results:
                    if prev_result.get("node_id") == node.input_source:
                        current_input = prev_result.get("output", current_input)
                        break
            
            # 执行节点
            result = await self.execute_node(node, current_input)
            
            result_info = {
                "node_id": node.id,
                "node_name": node.name,
                "node_type": node.type.value,
                "status": node.status.value,
                "input_preview": current_input[:200] + "..." if len(current_input) > 200 else current_input,
                "output_preview": (node.output[:200] + "...") if node.output and len(node.output) > 200 else node.output,
                "full_output": node.output,
                "execution_time": node.execution_time,
                "error": node.error
            }
            
            results.append(result_info)
            
            # 如果出错，停止执行
            if not result["success"]:
                return WorkflowResult(
                    success=False,
                    nodes_results=results,
                    error=node.error,
                    total_time=time.time() - start_time
                )
            
            # 更新当前输入为当前节点的输出
            if node.output:
                current_input = node.output
        
        total_time = time.time() - start_time
        
        return WorkflowResult(
            success=True,
            nodes_results=results,
            final_output=current_input,
            total_time=total_time,
            total_tokens=sum(node.tokens_used for node in nodes)
        )
    
    def create_analysis_chain(self, paper_content: str) -> List[ChainNode]:
        """
        创建标准分析链
        
        Args:
            paper_content: 论文内容
            
        Returns:
            链节点列表
        """
        return [
            self.create_node("summary", model="glm-4-flash"),
            self.create_node("keypoints", model="glm-4-plus"),
            self.create_node("gaps", model="glm-4-plus")
        ]
    
    def create_code_generation_chain(self, gap_description: str) -> List[ChainNode]:
        """
        创建代码生成链
        
        Args:
            gap_description: 研究空白描述
            
        Returns:
            链节点列表
        """
        return [
            self.create_node("code", model="glm-4-plus", temperature=0.3),
            self.create_node("quality", model="glm-4-flash")
        ]
    
    def create_review_chain(self, papers_content: List[str]) -> List[ChainNode]:
        """
        创建文献综述链
        
        Args:
            papers_content: 多篇论文内容
            
        Returns:
            链节点列表
        """
        combined_content = "\n\n=== 论文分隔 ===\n\n".join(papers_content)
        
        return [
            self.create_node("clean", model="glm-4-flash"),
            self.create_node("review", model="glm-4-plus"),
            self.create_node("innovation", model="glm-4-plus")
        ]
    
    @staticmethod
    def get_preset_templates() -> Dict[str, Dict[str, Any]]:
        """获取所有预设模板"""
        return {
            key: {
                "name": value["name"],
                "type": value["type"].value
            }
            for key, value in PRESET_TEMPLATES.items()
        }


# 全局引擎实例
_workflow_engine = None

def get_workflow_engine(llm_config: Optional[Dict[str, Any]] = None) -> ChainWorkflowEngine:
    """获取工作流引擎实例"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = ChainWorkflowEngine(llm_config=llm_config)
    return _workflow_engine
