"""LangGraph工作流模块 - 使用状态图管理文献分析流程"""
from typing import TypedDict, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.config import settings
from src.pdf_parser import PDFParser, ParsedPaper
from src.prompts import get_summary_prompt, get_keypoint_prompt, get_topic_prompt

# 尝试导入LangGraph，如果失败则提供简化版本
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("警告: LangGraph未安装，使用简化工作流")
    LANGGRAPH_AVAILABLE = False


# ============================================================================
# 定义状态类型
# ============================================================================

if LANGGRAPH_AVAILABLE:
    class PaperAnalysisState(TypedDict):
        """论文分析的状态"""
        # 输入
        pdf_path: str
        analysis_tasks: List[str]  # 要执行的任务列表：['parse', 'summary', 'keypoints', 'topic']

        # 中间状态
        parsed_paper: Optional[ParsedPaper]
        current_step: str

        # 输出结果
        summary: Optional[str]
        keypoints: Optional[Dict[str, List[str]]]
        topic_analysis: Optional[Dict[str, Any]]

        # 错误信息
        errors: List[str]
        status: str  # 'pending', 'processing', 'completed', 'failed'
else:
    # 如果LangGraph不可用，使用普通字典
    PaperAnalysisState = Dict[str, Any]


# ============================================================================
# 创建LLM实例
# ============================================================================

def create_llm(temperature: float = None, model: str = None):
    """创建LLM实例"""
    return ChatOpenAI(
        model=model or settings.default_model,
        api_key=settings.glm_api_key,
        base_url=settings.glm_base_url,
        temperature=temperature or settings.default_temperature,
        max_tokens=settings.max_tokens,
    )


# ============================================================================
# 定义节点函数
# ============================================================================

async def parse_pdf_node(state: PaperAnalysisState) -> PaperAnalysisState:
    """PDF解析节点"""
    print("🔍 步骤1: 解析PDF文件...")

    try:
        parser = PDFParser()
        paper = parser.parse_pdf(state["pdf_path"])

        state["parsed_paper"] = paper
        state["current_step"] = "parse_completed"
        state["status"] = "processing"

        print(f"✓ PDF解析完成: {paper.filename}")
        print(f"  - 标题: {paper.metadata.title}")
        print(f"  - 页数: {paper.page_count}")

    except Exception as e:
        error_msg = f"PDF解析失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        state["status"] = "failed"

    return state


async def generate_summary_node(state: PaperAnalysisState) -> PaperAnalysisState:
    """摘要生成节点"""
    print("\n📝 步骤2: 生成摘要...")

    if state.get("parsed_paper") is None:
        error_msg = "缺少解析的论文数据"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        return state

    try:
        paper = state["parsed_paper"]
        llm = create_llm(temperature=0.3)

        # 准备内容
        content = paper.full_text[:6000]  # 限制长度
        sections_text = "\n".join([
            f"{name}:\n{content[:500]}"
            for name, content in paper.metadata.sections.items()
        ])

        # 构建提示词
        prompt = get_summary_prompt(
            title=paper.metadata.title,
            abstract=paper.metadata.abstract,
            sections=sections_text,
            content=content
        )

        # 调用LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        summary = response.content

        state["summary"] = summary
        state["current_step"] = "summary_completed"

        print("✓ 摘要生成完成")
        print(f"\n{summary[:300]}...")

    except Exception as e:
        error_msg = f"摘要生成失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)

    return state


async def extract_keypoints_node(state: PaperAnalysisState) -> PaperAnalysisState:
    """要点提取节点"""
    print("\n🎯 步骤3: 提取要点...")

    if state.get("parsed_paper") is None:
        error_msg = "缺少解析的论文数据"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        return state

    try:
        paper = state["parsed_paper"]
        llm = create_llm(temperature=0.2)

        # 准备内容
        content = paper.full_text[:6000]
        sections_text = "\n".join([
            f"{name}:\n{content[:500]}"
            for name, content in paper.metadata.sections.items()
        ])
        keywords_text = ", ".join(paper.metadata.keywords) if paper.metadata.keywords else "未提取"

        # 构建提示词
        prompt = get_keypoint_prompt(
            title=paper.metadata.title,
            abstract=paper.metadata.abstract,
            keywords=keywords_text,
            sections=sections_text,
            content=content
        )

        # 调用LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        result = response.content

        # 解析JSON结果 - 增强版，支持修复不完整的JSON
        import json
        import re

        def extract_json_str(resp: str) -> str:
            """从响应中提取JSON字符串"""
            json_match = re.search(r'```json\s*(.*?)\s*```', resp, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
            
            json_match = re.search(r'```\s*(.*?)\s*```', resp, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
            
            start = resp.find('{')
            if start == -1:
                return resp.strip()
            
            brace_count = 0
            end = start
            for i, char in enumerate(resp[start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = start + i + 1
                        break
            return resp[start:end].strip()

        def fix_json(json_str: str) -> str:
            """修复常见的JSON格式问题"""
            json_str = json_str.replace('\n', '\\n').replace('\r', '\\r')
            
            quote_count = json_str.count('"')
            if quote_count % 2 != 0:
                json_str += '"'
            
            open_braces = json_str.count('{') - json_str.count('}')
            open_brackets = json_str.count('[') - json_str.count(']')
            json_str += '}' * max(0, open_braces)
            json_str += ']' * max(0, open_brackets)
            
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            return json_str

        # 提取JSON
        json_str = extract_json_str(result)
        
        # 尝试解析
        try:
            keypoints = json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试修复JSON
            fixed_json = fix_json(json_str)
            keypoints = json.loads(fixed_json)

        # 验证结构
        required_fields = ["innovations", "methods", "experiments",
                          "conclusions", "contributions", "limitations"]
        for field in required_fields:
            if field not in keypoints:
                keypoints[field] = []

        state["keypoints"] = keypoints
        state["current_step"] = "keypoints_completed"

        print("✓ 要点提取完成")
        for category, items in keypoints.items():
            if items:
                print(f"  - {category}: {len(items)} 个")

    except Exception as e:
        error_msg = f"要点提取失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        import traceback
        traceback.print_exc()

    return state


async def analyze_topic_node(state: PaperAnalysisState) -> PaperAnalysisState:
    """主题分析节点"""
    print("\n🔬 步骤4: 分析主题...")

    if state.get("parsed_paper") is None:
        error_msg = "缺少解析的论文数据"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)
        return state

    try:
        paper = state["parsed_paper"]
        llm = create_llm(temperature=0.4)

        # 准备内容
        content = paper.full_text[:5000]
        keywords_text = ", ".join(paper.metadata.keywords) if paper.metadata.keywords else "未提取"

        # 构建提示词
        prompt = get_topic_prompt(
            title=paper.metadata.title,
            abstract=paper.metadata.abstract,
            keywords=keywords_text,
            content=content
        )

        # 调用LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        topic_analysis = response.content

        state["topic_analysis"] = {
            "analysis": topic_analysis,
            "keywords": paper.metadata.keywords,
            "title": paper.metadata.title
        }
        state["current_step"] = "topic_completed"

        print("✓ 主题分析完成")
        print(f"\n{topic_analysis[:300]}...")

    except Exception as e:
        error_msg = f"主题分析失败: {str(e)}"
        print(f"✗ {error_msg}")
        state["errors"].append(error_msg)

    return state


def should_generate_summary(state: PaperAnalysisState) -> str:
    """判断是否需要生成摘要"""
    return "summary" in state.get("analysis_tasks", [])


def should_extract_keypoints(state: PaperAnalysisState) -> str:
    """判断是否需要提取要点"""
    return "keypoints" in state.get("analysis_tasks", [])


def should_analyze_topic(state: PaperAnalysisState) -> str:
    """判断是否需要分析主题"""
    return "topic" in state.get("analysis_tasks", [])


def finalize_node(state: PaperAnalysisState) -> PaperAnalysisState:
    """完成节点"""
    state["status"] = "completed"
    print("\n✓ 所有分析任务完成！")
    return state


# ============================================================================
# 构建工作流图
# ============================================================================

def create_analysis_workflow():
    """创建论文分析工作流"""

    if not LANGGRAPH_AVAILABLE:
        return None

    # 创建状态图
    workflow = StateGraph(PaperAnalysisState)

    # 添加节点
    workflow.add_node("parse_pdf", parse_pdf_node)
    workflow.add_node("generate_summary", generate_summary_node)
    workflow.add_node("extract_keypoints", extract_keypoints_node)
    workflow.add_node("analyze_topic", analyze_topic_node)
    workflow.add_node("finalize", finalize_node)

    # 设置入口点
    workflow.set_entry_point("parse_pdf")

    # 添加条件边
    workflow.add_conditional_edges(
        "parse_pdf",
        should_generate_summary,
        {
            True: "generate_summary",
            False: "extract_keypoints"
        }
    )

    workflow.add_conditional_edges(
        "generate_summary",
        should_extract_keypoints,
        {
            True: "extract_keypoints",
            False: "analyze_topic" if should_analyze_topic({"analysis_tasks": []}) else "finalize"
        }
    )

    workflow.add_conditional_edges(
        "extract_keypoints",
        should_analyze_topic,
        {
            True: "analyze_topic",
            False: "finalize"
        }
    )

    workflow.add_conditional_edges(
        "analyze_topic",
        lambda state: "finalize",
        {
            "finalize": "finalize"
        }
    )

    # 添加结束边
    workflow.add_edge("finalize", END)

    # 编译图
    app = workflow.compile()

    return app


# ============================================================================
# 主要执行函数
# ============================================================================

class PaperAnalysisWorkflow:
    """论文分析工作流包装类"""

    def __init__(self):
        """初始化工作流"""
        self.app = create_analysis_workflow()
        self.use_langgraph = LANGGRAPH_AVAILABLE

    async def analyze(
        self,
        pdf_path: str,
        tasks: List[str] = None
    ) -> PaperAnalysisState:
        """
        执行完整的论文分析流程

        Args:
            pdf_path: PDF文件路径
            tasks: 要执行的任务列表，默认执行所有任务

        Returns:
            PaperAnalysisState: 分析结果状态
        """
        if tasks is None:
            tasks = ["summary", "keypoints", "topic"]

        # 初始化状态
        initial_state: PaperAnalysisState = {
            "pdf_path": pdf_path,
            "analysis_tasks": tasks,
            "parsed_paper": None,
            "current_step": "initialized",
            "summary": None,
            "keypoints": None,
            "topic_analysis": None,
            "errors": [],
            "status": "pending"
        }

        # 执行工作流
        print("=" * 60)
        print("开始执行论文分析工作流")
        print("=" * 60)

        try:
            if self.app is not None:
                # 使用LangGraph
                final_state = await self.app.ainvoke(initial_state)
            else:
                # 使用简化版本
                final_state = await self._run_simple_workflow(initial_state)
            return final_state

        except Exception as e:
            print(f"\n✗ 工作流执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            initial_state["status"] = "failed"
            initial_state["errors"].append(str(e))
            return initial_state

    async def _run_simple_workflow(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """简化的工作流执行（当LangGraph不可用时）"""
        # 步骤1: 解析PDF
        state = await parse_pdf_node(state)
        if state["status"] == "failed":
            return state

        # 步骤2: 生成摘要
        if "summary" in state.get("analysis_tasks", []):
            state = await generate_summary_node(state)

        # 步骤3: 提取要点
        if "keypoints" in state.get("analysis_tasks", []):
            state = await extract_keypoints_node(state)

        # 步骤4: 主题分析
        if "topic" in state.get("analysis_tasks", []):
            state = await analyze_topic_node(state)

        # 完成
        state = finalize_node(state)
        return state

    def analyze_sync(
        self,
        pdf_path: str,
        tasks: List[str] = None
    ) -> PaperAnalysisState:
        """
        同步执行论文分析（兼容性接口）

        Args:
            pdf_path: PDF文件路径
            tasks: 要执行的任务列表

        Returns:
            PaperAnalysisState: 分析结果状态
        """
        import asyncio
        return asyncio.run(self.analyze(pdf_path, tasks))


# ============================================================================
# 便捷函数
# ============================================================================

async def analyze_paper_async(
    pdf_path: str,
    tasks: List[str] = None
) -> PaperAnalysisState:
    """
    异步分析论文

    Args:
        pdf_path: PDF文件路径
        tasks: 任务列表

    Returns:
        分析结果
    """
    workflow = PaperAnalysisWorkflow()
    return await workflow.analyze(pdf_path, tasks)


def analyze_paper(
    pdf_path: str,
    tasks: List[str] = None
) -> PaperAnalysisState:
    """
    分析论文（同步接口）

    Args:
        pdf_path: PDF文件路径
        tasks: 任务列表，如 ["summary", "keypoints", "topic"]

    Returns:
        分析结果
    """
    workflow = PaperAnalysisWorkflow()
    return workflow.analyze_sync(pdf_path, tasks)
