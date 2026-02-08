"""
LangChain 辅助工具 - 封装 LLM 调用和结构化输出处理

功能：
1. 封装 LLM 初始化配置
2. 提供结构化的 invoke 方法
3. 统一的错误处理和重试机制
4. 与 prompts_langchain 模块无缝集成
"""

import asyncio
from typing import Optional, Dict, Any, TypeVar, Generic, List
from datetime import datetime
import json

# 尝试导入 LangChain，如果失败则使用 mock
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain.output_parsers import OutputFixingParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    BaseMessage = None
    HumanMessage = None
    SystemMessage = None
    ChatPromptTemplate = None
    PydanticOutputParser = None
    OutputFixingParser = None
    print("[WARNING] LangChain 未安装，LLM功能将受限")

from src.config import settings
from src.prompts_langchain import (
    get_summary_messages,
    get_keypoints_messages,
    get_gaps_messages,
    get_topic_messages,
    get_code_messages,
    safe_parse_keypoints,
    safe_parse_gaps,
    safe_parse_topic,
    safe_parse_code,
    KeyPointsOutput,
    ResearchGapsOutput,
    TopicAnalysisOutput,
    CodeGenerationOutput,
    get_empty_keypoints,
    get_empty_gaps,
)

T = TypeVar('T')


class LLMHelper:
    """
    LangChain LLM 辅助类
    
    封装 LLM 初始化和调用逻辑，提供统一接口
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "glm-4-plus",
        temperature: float = 0.3,
        max_tokens: int = 8000,
        timeout: int = 60
    ):
        """
        初始化 LLM Helper
        
        Args:
            api_key: API 密钥，默认从 settings 读取
            base_url: API 基础 URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间（秒）
        """
        if not LANGCHAIN_AVAILABLE:
            self.llm = None
            print("[WARNING] LangChain 不可用，LLMHelper 将以降级模式运行")
            return
        
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        if not self.api_key:
            print("[WARNING] API 密钥未设置，LLM 功能将不可用")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                request_timeout=self.timeout
            )
    
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self.llm is not None and LANGCHAIN_AVAILABLE
    
    def invoke(
        self,
        messages: List[BaseMessage],
        max_retries: int = 2
    ) -> Optional[str]:
        """
        同步调用 LLM
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
        
        Returns:
            响应文本或 None
        """
        if not self.is_available():
            return None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                print(f"[ERROR] LLM 调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(1)
                continue
        
        return None
    
    async def ainvoke(
        self,
        messages: List[BaseMessage],
        max_retries: int = 2
    ) -> Optional[str]:
        """
        异步调用 LLM
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
        
        Returns:
            响应文本或 None
        """
        if not self.is_available():
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.invoke,
            messages,
            max_retries
        )


class StructuredLLMHelper(LLMHelper):
    """
    结构化输出的 LLM Helper
    
    自动处理 Prompt 和 Output Parser 的调用
    """
    
    def generate_summary(
        self,
        title: str,
        abstract: str,
        sections: str,
        content: str
    ) -> str:
        """
        生成论文摘要
        
        Returns:
            摘要文本
        """
        messages = get_summary_messages(title, abstract, sections, content)
        result = self.invoke(messages)
        return result or "摘要生成失败"
    
    async def agenerate_summary(
        self,
        title: str,
        abstract: str,
        sections: str,
        content: str
    ) -> str:
        """异步生成摘要"""
        messages = get_summary_messages(title, abstract, sections, content)
        result = await self.ainvoke(messages)
        return result or "摘要生成失败"
    
    def extract_keypoints(
        self,
        title: str,
        abstract: str,
        keywords: str,
        sections: str,
        content: str
    ) -> Dict[str, List[str]]:
        """
        提取论文要点
        
        Returns:
            结构化要点字典
        """
        if not self.is_available():
            return get_empty_keypoints()
        
        messages, parser = get_keypoints_messages(title, abstract, keywords, sections, content)
        result = self.invoke(messages)
        
        if not result:
            return get_empty_keypoints()
        
        try:
            parsed = safe_parse_keypoints(result)
            return {
                "innovations": parsed.innovations,
                "methods": parsed.methods,
                "experiments": parsed.experiments,
                "conclusions": parsed.conclusions,
                "contributions": parsed.contributions,
                "limitations": parsed.limitations
            }
        except Exception as e:
            print(f"[ERROR] 要点解析失败: {e}")
            return get_empty_keypoints()
    
    async def aextract_keypoints(
        self,
        title: str,
        abstract: str,
        keywords: str,
        sections: str,
        content: str
    ) -> Dict[str, List[str]]:
        """异步提取要点"""
        if not self.is_available():
            return get_empty_keypoints()
        
        messages, parser = get_keypoints_messages(title, abstract, keywords, sections, content)
        result = await self.ainvoke(messages)
        
        if not result:
            return get_empty_keypoints()
        
        try:
            parsed = safe_parse_keypoints(result)
            return {
                "innovations": parsed.innovations,
                "methods": parsed.methods,
                "experiments": parsed.experiments,
                "conclusions": parsed.conclusions,
                "contributions": parsed.contributions,
                "limitations": parsed.limitations
            }
        except Exception as e:
            print(f"[ERROR] 要点解析失败: {e}")
            return get_empty_keypoints()
    
    def identify_gaps(
        self,
        papers_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Any]]:
        """
        识别研究空白
        
        Returns:
            包含 gaps 和 recommendations 的字典
        """
        if not self.is_available():
            return get_empty_gaps()
        
        messages, parser = get_gaps_messages(papers_data)
        result = self.invoke(messages)
        
        if not result:
            return get_empty_gaps()
        
        try:
            parsed = safe_parse_gaps(result)
            return {
                "gaps": [
                    {
                        "description": gap.description,
                        "gap_type": gap.gap_type,
                        "importance": gap.importance,
                        "difficulty": gap.difficulty,
                        "potential_approach": gap.potential_approach,
                        "expected_impact": gap.expected_impact
                    }
                    for gap in parsed.gaps
                ],
                "recommendations": parsed.recommendations
            }
        except Exception as e:
            print(f"[ERROR] 研究空白解析失败: {e}")
            return get_empty_gaps()
    
    async def aidentify_gaps(
        self,
        papers_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Any]]:
        """异步识别研究空白"""
        if not self.is_available():
            return get_empty_gaps()
        
        messages, parser = get_gaps_messages(papers_data)
        result = await self.ainvoke(messages)
        
        if not result:
            return get_empty_gaps()
        
        try:
            parsed = safe_parse_gaps(result)
            return {
                "gaps": [
                    {
                        "description": gap.description,
                        "gap_type": gap.gap_type,
                        "importance": gap.importance,
                        "difficulty": gap.difficulty,
                        "potential_approach": gap.potential_approach,
                        "expected_impact": gap.expected_impact
                    }
                    for gap in parsed.gaps
                ],
                "recommendations": parsed.recommendations
            }
        except Exception as e:
            print(f"[ERROR] 研究空白解析失败: {e}")
            return get_empty_gaps()
    
    def analyze_topic(
        self,
        title: str,
        abstract: str,
        keywords: str,
        content: str
    ) -> Dict[str, Any]:
        """
        分析论文主题
        
        Returns:
            主题分析结果字典
        """
        if not self.is_available():
            return {
                "field": "",
                "sub_field": "",
                "core_themes": [],
                "research_question": "",
                "methodology_type": "",
                "application_areas": []
            }
        
        messages, parser = get_topic_messages(title, abstract, keywords, content)
        result = self.invoke(messages)
        
        if not result:
            return {
                "field": "",
                "sub_field": "",
                "core_themes": [],
                "research_question": "",
                "methodology_type": "",
                "application_areas": []
            }
        
        try:
            parsed = safe_parse_topic(result)
            return {
                "field": parsed.field,
                "sub_field": parsed.sub_field,
                "core_themes": parsed.core_themes,
                "research_question": parsed.research_question,
                "methodology_type": parsed.methodology_type,
                "application_areas": parsed.application_areas
            }
        except Exception as e:
            print(f"[ERROR] 主题分析解析失败: {e}")
            return {
                "field": "",
                "sub_field": "",
                "core_themes": [],
                "research_question": "",
                "methodology_type": "",
                "application_areas": []
            }
    
    def generate_code(
        self,
        gap_description: str,
        gap_type: str,
        importance: str,
        difficulty: str,
        potential_approach: str,
        expected_impact: str,
        strategy: str = "method_improvement",
        language: str = "python",
        framework: str = "pytorch"
    ) -> Dict[str, Any]:
        """
        生成代码
        
        Returns:
            代码生成结果字典
        """
        if not self.is_available():
            return {
                "code": "",
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }
        
        messages, parser = get_code_messages(
            gap_description=gap_description,
            gap_type=gap_type,
            importance=importance,
            difficulty=difficulty,
            potential_approach=potential_approach,
            expected_impact=expected_impact,
            strategy=strategy,
            language=language,
            framework=framework
        )
        result = self.invoke(messages)
        
        if not result:
            return {
                "code": "",
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }
        
        try:
            parsed = safe_parse_code(result)
            return {
                "code": parsed.code,
                "language": parsed.language,
                "framework": parsed.framework,
                "dependencies": parsed.dependencies,
                "explanation": parsed.explanation
            }
        except Exception as e:
            print(f"[ERROR] 代码生成解析失败: {e}")
            # 如果解析失败，直接返回原始代码
            return {
                "code": result,
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }
    
    async def agenerate_code(
        self,
        gap_description: str,
        gap_type: str,
        importance: str,
        difficulty: str,
        potential_approach: str,
        expected_impact: str,
        strategy: str = "method_improvement",
        language: str = "python",
        framework: str = "pytorch"
    ) -> Dict[str, Any]:
        """异步生成代码"""
        if not self.is_available():
            return {
                "code": "",
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }
        
        messages, parser = get_code_messages(
            gap_description=gap_description,
            gap_type=gap_type,
            importance=importance,
            difficulty=difficulty,
            potential_approach=potential_approach,
            expected_impact=expected_impact,
            strategy=strategy,
            language=language,
            framework=framework
        )
        result = await self.ainvoke(messages)
        
        if not result:
            return {
                "code": "",
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }
        
        try:
            parsed = safe_parse_code(result)
            return {
                "code": parsed.code,
                "language": parsed.language,
                "framework": parsed.framework,
                "dependencies": parsed.dependencies,
                "explanation": parsed.explanation
            }
        except Exception as e:
            print(f"[ERROR] 代码生成解析失败: {e}")
            return {
                "code": result,
                "language": language,
                "framework": framework,
                "dependencies": [],
                "explanation": ""
            }


# ============================================================================
# 便捷函数 - 全局实例
# ============================================================================

_helpler_instance = None

def get_structured_llm_helper(
    api_key: Optional[str] = None,
    model: str = "glm-4-plus",
    **kwargs
) -> StructuredLLMHelper:
    """
    获取或创建全局 StructuredLLMHelper 实例
    
    Args:
        api_key: API 密钥
        model: 模型名称
        **kwargs: 其他参数
    
    Returns:
        StructuredLLMHelper 实例
    """
    global _helpler_instance
    if _helpler_instance is None:
        _helpler_instance = StructuredLLMHelper(
            api_key=api_key,
            model=model,
            **kwargs
        )
    return _helpler_instance


def reset_helper():
    """重置全局实例（用于测试或重新配置）"""
    global _helpler_instance
    _helpler_instance = None
