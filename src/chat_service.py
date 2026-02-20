"""
AI 聊天服务 - v4.2院士级优化版

功能：
1. 基于论文库的智能问答
2. 上下文记忆
3. 引用溯源
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import re

# LangChain 导入
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[WARNING] LangChain 未安装，聊天功能将不可用")

from src.config import settings


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    references: List[Dict[str, Any]] = None


@dataclass
class ChatContext:
    """聊天上下文"""
    chat_id: str
    messages: List[ChatMessage]
    metadata: Dict[str, Any]


class AIChatService:
    """AI 聊天服务"""

    # 系统提示词
    SYSTEM_PROMPT = """你是一位资深的学术研究助手，专门帮助研究人员分析和理解学术论文。

你的能力包括：
1. 解释复杂的学术概念和方法
2. 对比不同论文的观点和方法
3. 识别研究趋势和模式
4. 提供研究建议和方向
5. 帮助撰写文献综述

在回答问题时，请：
1. 基于提供的论文内容给出准确的回答
2. 如果不确定，坦诚告知
3. 引用相关的论文作为依据
4. 使用学术规范的语言
5. 保持客观中立的态度

当前用户关联的论文：
{paper_context}
"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "glm-4-plus"
    ):
        """
        初始化聊天服务

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装，无法使用聊天功能")

        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model

        if not self.api_key:
            raise ValueError("请设置 GLM_API_KEY 环境变量")

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.7,
            max_tokens=4000
        )

        # 聊天历史存储（生产环境应使用 Redis 或数据库）
        self.chat_histories: Dict[str, ChatContext] = {}

    def _get_paper_context(self, paper_ids: List[int]) -> str:
        """
        获取论文上下文

        Args:
            paper_ids: 论文 ID 列表

        Returns:
            论文上下文文本
        """
        from src.db_manager import DatabaseManager
        db = DatabaseManager()
        
        context_parts = []
        for paper_id in paper_ids:
            paper = db.get_paper(paper_id)
            if paper:
                context_parts.append(f"""
论文标题：{paper.get('title', '未知')}
摘要：{paper.get('abstract', '无摘要')[:300]}...
关键词：{', '.join(paper.get('metadata', {}).get('keywords', []))}
---""")
        
        return "\n".join(context_parts) if context_parts else "未关联具体论文"

    def chat(
        self,
        message: str,
        chat_id: str = None,
        paper_ids: List[int] = None,
        model: str = None,
        settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        处理聊天请求

        Args:
            message: 用户消息
            chat_id: 对话 ID
            paper_ids: 关联的论文 ID 列表
            model: 模型名称
            settings: 其他设置

        Returns:
            包含回复和引用的字典
        """
        # 获取或创建聊天上下文
        if chat_id and chat_id in self.chat_histories:
            context = self.chat_histories[chat_id]
        else:
            chat_id = chat_id or f"chat_{datetime.now().timestamp()}"
            context = ChatContext(
                chat_id=chat_id,
                messages=[],
                metadata={}
            )
            self.chat_histories[chat_id] = context

        # 获取论文上下文
        paper_context = self._get_paper_context(paper_ids or [])

        # 构建消息列表
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT.format(paper_context=paper_context))
        ]

        # 添加历史消息（保留最近 10 条）
        for msg in context.messages[-10:]:
            if msg.role == 'user':
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                messages.append(AIMessage(content=msg.content))

        # 添加当前消息
        messages.append(HumanMessage(content=message))

        # 记录用户消息
        context.messages.append(ChatMessage(
            role='user',
            content=message,
            timestamp=datetime.now()
        ))

        try:
            # 调用 LLM
            response = self.llm.invoke(messages)
            content = response.content

            # 提取引用
            references = self._extract_references(content, paper_ids or [])

            # 记录助手回复
            context.messages.append(ChatMessage(
                role='assistant',
                content=content,
                timestamp=datetime.now(),
                references=references
            ))

            return {
                'chat_id': chat_id,
                'content': content,
                'references': references,
                'success': True
            }

        except Exception as e:
            print(f"[ERROR] 聊天请求失败: {e}")
            return {
                'chat_id': chat_id,
                'content': '抱歉，我暂时无法回答您的问题。请稍后再试。',
                'references': [],
                'success': False,
                'error': str(e)
            }

    def _extract_references(
        self,
        content: str,
        paper_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        从回复中提取引用的论文

        Args:
            content: 回复内容
            paper_ids: 论文 ID 列表

        Returns:
            引用列表
        """
        if not paper_ids:
            return []

        from src.db_manager import DatabaseManager
        db = DatabaseManager()

        references = []
        for paper_id in paper_ids:
            paper = db.get_paper(paper_id)
            if paper:
                # 检查是否引用了该论文
                title = paper.get('title', '')
                if title and len(title) > 10:
                    # 检查标题或关键词是否出现在回复中
                    keywords = paper.get('metadata', {}).get('keywords', [])
                    if any(kw.lower() in content.lower() for kw in keywords[:3]):
                        references.append({
                            'id': paper_id,
                            'title': title,
                            'year': paper.get('year'),
                            'venue': paper.get('venue')
                        })

        return references[:5]  # 最多返回 5 个引用

    def get_chat_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        获取聊天历史

        Args:
            chat_id: 对话 ID

        Returns:
            消息列表
        """
        if chat_id not in self.chat_histories:
            return []

        context = self.chat_histories[chat_id]
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'references': msg.references or []
            }
            for msg in context.messages
        ]

    def clear_chat(self, chat_id: str) -> bool:
        """
        清空聊天历史

        Args:
            chat_id: 对话 ID

        Returns:
            是否成功
        """
        if chat_id in self.chat_histories:
            del self.chat_histories[chat_id]
            return True
        return False


# 便捷函数
_chat_service = None

def get_chat_service() -> AIChatService:
    """获取聊天服务实例（单例）"""
    global _chat_service
    if _chat_service is None:
        _chat_service = AIChatService()
    return _chat_service
