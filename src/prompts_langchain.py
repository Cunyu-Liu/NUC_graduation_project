"""
LangChain 提示词模板与输出解析器 - v4.2院士级优化版

功能：
1. 使用 LangChain Prompt Templates 管理提示词
2. 使用 Pydantic Output Parsers 实现结构化输出
3. 减少手动解析错误，提高代码可维护性
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate
)
from langchain.output_parsers import (
    PydanticOutputParser,
    CommaSeparatedListOutputParser
)


# ============================================================================
# Pydantic 输出模型定义（结构化输出）
# ============================================================================

class KeyPointItem(BaseModel):
    """单个要点"""
    content: str = Field(description="要点内容")
    importance: str = Field(description="重要性：high/medium/low", default="medium")


class KeyPointsOutput(BaseModel):
    """要点提取的结构化输出"""
    innovations: List[str] = Field(
        description="核心创新点列表，3-5个",
        default_factory=list
    )
    methods: List[str] = Field(
        description="主要方法与技术列表，3-5个",
        default_factory=list
    )
    experiments: List[str] = Field(
        description="实验设计与评估列表，2-4个",
        default_factory=list
    )
    conclusions: List[str] = Field(
        description="主要结论列表，3-5个",
        default_factory=list
    )
    contributions: List[str] = Field(
        description="学术贡献列表，2-4个",
        default_factory=list
    )
    limitations: List[str] = Field(
        description="研究局限性列表，1-3个",
        default_factory=list
    )


class ResearchGapItem(BaseModel):
    """单个研究空白"""
    description: str = Field(description="研究空白描述，简明扼要")
    gap_type: str = Field(
        description="空白类型：methodological(方法论)/theoretical(理论)/data(数据)/application(应用)/evaluation(评估)",
        default="methodological"
    )
    importance: str = Field(
        description="重要性：high(高)/medium(中)/low(低)",
        default="medium"
    )
    difficulty: str = Field(
        description="难度：high(高)/medium(中)/low(低)",
        default="medium"
    )
    potential_approach: str = Field(
        description="潜在解决方法",
        default=""
    )
    expected_impact: str = Field(
        description="预期影响",
        default=""
    )


class ResearchGapsOutput(BaseModel):
    """研究空白挖掘的结构化输出"""
    gaps: List[ResearchGapItem] = Field(
        description="识别的研究空白列表",
        default_factory=list
    )
    recommendations: List[str] = Field(
        description="研究建议列表",
        default_factory=list
    )


class TopicAnalysisOutput(BaseModel):
    """主题分析的结构化输出"""
    field: str = Field(description="研究领域")
    sub_field: str = Field(description="具体研究方向")
    core_themes: List[str] = Field(description="核心主题词，3-5个")
    research_question: str = Field(description="核心研究问题")
    methodology_type: str = Field(description="方法论类别")
    application_areas: List[str] = Field(description="应用领域列表")


class CodeGenerationOutput(BaseModel):
    """代码生成的结构化输出"""
    code: str = Field(description="完整的代码实现")
    language: str = Field(description="编程语言", default="python")
    framework: str = Field(description="使用的框架", default="pytorch")
    dependencies: List[str] = Field(description="依赖包列表", default_factory=list)
    explanation: str = Field(description="代码说明文档", default="")


# ============================================================================
# Output Parsers 实例
# ============================================================================

keypoints_parser = PydanticOutputParser(pydantic_object=KeyPointsOutput)
gaps_parser = PydanticOutputParser(pydantic_object=ResearchGapsOutput)
topic_parser = PydanticOutputParser(pydantic_object=TopicAnalysisOutput)
code_parser = PydanticOutputParser(pydantic_object=CodeGenerationOutput)
comma_list_parser = CommaSeparatedListOutputParser()


# ============================================================================
# Prompt Templates - 使用 LangChain 的 ChatPromptTemplate
# ============================================================================

# ----------------------------------------------------------------------------
# 摘要生成 Prompt Template
# ----------------------------------------------------------------------------
SUMMARY_SYSTEM_TEMPLATE = """你是一位资深的学术文献分析师，具有深厚的学术背景和研究经验。
你的任务是为科研论文撰写高质量的摘要。

要求：
1. 客观准确：严格基于论文内容，不添加主观臆断
2. 逻辑清晰：各部分内容连贯，层次分明
3. 简洁精炼：用最少的文字传达最多的信息
4. 专业规范：使用学术规范的语言表达
5. 长度控制：中文字数300-500字，英文200-400词

如果是中文论文，使用简体中文回答；如果是英文论文，使用英文回答。"""

SUMMARY_HUMAN_TEMPLATE = """请为以下论文生成专业摘要：

**论文标题**：{title}

**原始摘要**：{abstract}

**主要章节内容**：
{sections}

**论文正文（节选）**：
{content}

请直接输出摘要文本，不要添加任何额外说明或标记。摘要应该是一段连贯的文本，不需要分点或分段。"""

summary_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SUMMARY_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(SUMMARY_HUMAN_TEMPLATE)
])


# ----------------------------------------------------------------------------
# 要点提取 Prompt Template
# ----------------------------------------------------------------------------
KEYPOINTS_SYSTEM_TEMPLATE = """你是一位专业的学术文献分析专家，擅长从科研论文中提取关键信息。
你的任务是结构化地提取论文的核心要点。

所有要点必须是直接从论文中提取的事实，不要添加推测或外部知识。
请严格按照指定的JSON格式输出。"""

KEYPOINTS_HUMAN_TEMPLATE = """请分析以下论文并提取关键要点：

**论文标题**：{title}

**原始摘要**：{abstract}

**关键词**：{keywords}

**主要章节**：
{sections}

**论文正文（节选）**：
{content}

{format_instructions}

注意：
1. innovations（核心创新点）：3-5个，突出方法、算法、架构创新
2. methods（主要方法）：3-5个，包括核心方法、算法、技术
3. experiments（实验设计）：2-4个，说明实验目的、数据集、评估指标
4. conclusions（主要结论）：3-5个，包括定量和定性结论
5. contributions（学术贡献）：2-4个，阐明理论和实践贡献
6. limitations（局限性）：1-3个，诚实指出不足

每个要点应该简洁明了，一句话描述。"""

keypoints_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(KEYPOINTS_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(KEYPOINTS_HUMAN_TEMPLATE)
])


# ----------------------------------------------------------------------------
# 研究空白挖掘 Prompt Template
# ----------------------------------------------------------------------------
GAPS_SYSTEM_TEMPLATE = """你是一位学术研究战略专家，具有敏锐的研究洞察力。
你的任务是基于论文分析识别研究空白（Research Gaps）。

研究空白是指：
- 当前方法无法解决的问题
- 理论上的不足或缺失
- 数据或评估方面的局限
- 应用领域的未探索方向

请提供结构化的JSON输出。"""

GAPS_HUMAN_TEMPLATE = """请分析以下论文内容，识别研究空白：

**论文信息**：
{papers_info}

{format_instructions}

对于每个研究空白，请提供：
1. description：清晰描述空白是什么
2. gap_type：类型（methodological/theoretical/data/application/evaluation）
3. importance：重要性（high/medium/low）
4. difficulty：解决难度（high/medium/low）
5. potential_approach：可能的解决方法
6. expected_impact：预期影响和价值

同时提供2-3条研究建议。"""

gaps_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(GAPS_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(GAPS_HUMAN_TEMPLATE)
])


# ----------------------------------------------------------------------------
# 主题分析 Prompt Template
# ----------------------------------------------------------------------------
TOPIC_SYSTEM_TEMPLATE = """你是一位学术研究领域的专家，擅长分析文献的主题和研究方向。
你的任务是分析给定论文的研究主题和关键概念，并输出结构化结果。"""

TOPIC_HUMAN_TEMPLATE = """请分析以下论文的主题：

**论文标题**：{title}

**摘要**：{abstract}

**关键词**：{keywords}

**主要内容**：
{content}

{format_instructions}

请提供：
1. field：所属学科领域
2. sub_field：具体研究方向
3. core_themes：3-5个核心主题词，按重要性排序
4. research_question：核心研究问题
5. methodology_type：方法论类别
6. application_areas：可能的应用领域"""

topic_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TOPIC_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(TOPIC_HUMAN_TEMPLATE)
])


# ----------------------------------------------------------------------------
# 代码生成 Prompt Template
# ----------------------------------------------------------------------------
CODE_SYSTEM_TEMPLATE = """你是一位世界顶级的深度学习框架开发者和算法工程师。

专长：
1. 深度学习框架（PyTorch、TensorFlow、JAX）
2. 机器学习算法（经典到前沿）
3. 代码质量和最佳实践
4. 软件工程规范

代码要求：
1. 代码必须可以直接运行，无语法错误
2. 包含完整的文档字符串
3. 包含类型提示（Type Hints）
4. 包含单元测试
5. 遵循框架最佳实践
6. 代码结构清晰，模块化
7. 处理边界情况

直接输出可执行的代码，不要包含markdown代码块标记。"""

CODE_HUMAN_TEMPLATE = """请为以下研究空白生成代码实现：

**研究空白描述**：{gap_description}

**空白类型**：{gap_type}

**重要性**：{importance}

**难度**：{difficulty}

**潜在解决方法**：{potential_approach}

**预期影响**：{expected_impact}

**生成策略**：{strategy}

**编程语言**：{language}

**框架**：{framework}

{format_instructions}

请生成完整、可直接运行的代码，包含：
1. 所有必要的import语句
2. 完整的类/函数实现
3. 文档字符串
4. 类型提示
5. 单元测试
6. 使用示例"""

code_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(CODE_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(CODE_HUMAN_TEMPLATE)
])


# ============================================================================
# 便捷函数 - 封装 Prompt 和 Parser 的调用
# ============================================================================

def format_papers_for_gaps(papers_data: List[Dict[str, Any]]) -> str:
    """将论文数据格式化为 gaps prompt 需要的格式"""
    info_parts = []
    for i, paper in enumerate(papers_data, 1):
        info_parts.append(f"\n## 论文 {i}")
        info_parts.append(f"标题: {paper.get('title', '未命名')}")
        info_parts.append(f"摘要: {paper.get('abstract', '无摘要')[:300]}...")
        info_parts.append(f"关键词: {', '.join(paper.get('keywords', []))}")
    return "\n".join(info_parts)


def get_summary_messages(
    title: str,
    abstract: str,
    sections: str,
    content: str
) -> List[Any]:
    """
    获取摘要生成的消息列表
    
    Args:
        title: 论文标题
        abstract: 论文摘要
        sections: 章节内容
        content: 正文内容
    
    Returns:
        List[BaseMessage]: LangChain 消息列表
    """
    return summary_prompt_template.format_messages(
        title=title or "未提取标题",
        abstract=abstract or "未提取摘要",
        sections=sections or "未提取章节",
        content=content or ""
    )


def get_keypoints_messages(
    title: str,
    abstract: str,
    keywords: str,
    sections: str,
    content: str
) -> tuple[List[Any], PydanticOutputParser]:
    """
    获取要点提取的消息列表和解析器
    
    Returns:
        tuple: (消息列表, output_parser)
    """
    parser = keypoints_parser
    messages = keypoints_prompt_template.format_messages(
        title=title or "未提取标题",
        abstract=abstract or "未提取摘要",
        keywords=keywords or "未提取关键词",
        sections=sections or "未提取章节",
        content=content or "",
        format_instructions=parser.get_format_instructions()
    )
    return messages, parser


def get_gaps_messages(
    papers_data: List[Dict[str, Any]]
) -> tuple[List[Any], PydanticOutputParser]:
    """
    获取研究空白挖掘的消息列表和解析器
    
    Returns:
        tuple: (消息列表, output_parser)
    """
    parser = gaps_parser
    papers_info = format_papers_for_gaps(papers_data)
    messages = gaps_prompt_template.format_messages(
        papers_info=papers_info,
        format_instructions=parser.get_format_instructions()
    )
    return messages, parser


def get_topic_messages(
    title: str,
    abstract: str,
    keywords: str,
    content: str
) -> tuple[List[Any], PydanticOutputParser]:
    """
    获取主题分析的消息列表和解析器
    
    Returns:
        tuple: (消息列表, output_parser)
    """
    parser = topic_parser
    messages = topic_prompt_template.format_messages(
        title=title or "未提取标题",
        abstract=abstract or "未提取摘要",
        keywords=keywords or "未提取关键词",
        content=content or "",
        format_instructions=parser.get_format_instructions()
    )
    return messages, parser


def get_code_messages(
    gap_description: str,
    gap_type: str,
    importance: str,
    difficulty: str,
    potential_approach: str,
    expected_impact: str,
    strategy: str = "method_improvement",
    language: str = "python",
    framework: str = "pytorch"
) -> tuple[List[Any], PydanticOutputParser]:
    """
    获取代码生成的消息列表和解析器
    
    Returns:
        tuple: (消息列表, output_parser)
    """
    parser = code_parser
    messages = code_prompt_template.format_messages(
        gap_description=gap_description,
        gap_type=gap_type,
        importance=importance,
        difficulty=difficulty,
        potential_approach=potential_approach,
        expected_impact=expected_impact,
        strategy=strategy,
        language=language,
        framework=framework,
        format_instructions=parser.get_format_instructions()
    )
    return messages, parser


# ============================================================================
# 后处理函数 - 处理解析失败的情况
# ============================================================================

def parse_with_fallback(parser: PydanticOutputParser, text: str, default_value: Any = None) -> Any:
    """
    带fallback的解析函数
    
    Args:
        parser: PydanticOutputParser 实例
        text: 要解析的文本
        default_value: 解析失败时的默认值
    
    Returns:
        解析结果或默认值
    """
    try:
        return parser.parse(text)
    except Exception as e:
        print(f"[WARNING] 解析失败: {e}")
        print(f"[WARNING] 原始文本: {text[:200]}...")
        if default_value is not None:
            return default_value
        # 返回对应类型的空对象
        model_class = parser.pydantic_object
        return model_class()


def safe_parse_keypoints(text: str) -> KeyPointsOutput:
    """安全解析要点输出"""
    return parse_with_fallback(
        keypoints_parser,
        text,
        KeyPointsOutput(
            innovations=[],
            methods=[],
            experiments=[],
            conclusions=[],
            contributions=[],
            limitations=[]
        )
    )


def safe_parse_gaps(text: str) -> ResearchGapsOutput:
    """安全解析研究空白输出"""
    return parse_with_fallback(
        gaps_parser,
        text,
        ResearchGapsOutput(gaps=[], recommendations=[])
    )


def safe_parse_topic(text: str) -> TopicAnalysisOutput:
    """安全解析主题分析输出"""
    return parse_with_fallback(
        topic_parser,
        text,
        TopicAnalysisOutput(
            field="",
            sub_field="",
            core_themes=[],
            research_question="",
            methodology_type="",
            application_areas=[]
        )
    )


def safe_parse_code(text: str) -> CodeGenerationOutput:
    """安全解析代码生成输出"""
    return parse_with_fallback(
        code_parser,
        text,
        CodeGenerationOutput(code="", language="python", framework="pytorch")
    )


# ============================================================================
# 空结果工厂函数
# ============================================================================

def get_empty_keypoints() -> Dict[str, List[str]]:
    """获取空的要点结构"""
    return {
        "innovations": [],
        "methods": [],
        "experiments": [],
        "conclusions": [],
        "contributions": [],
        "limitations": []
    }


def get_empty_gaps() -> Dict[str, List[Any]]:
    """获取空的研究空白结构"""
    return {
        "gaps": [],
        "recommendations": []
    }
