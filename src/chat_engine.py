"""AI 聊天引擎 - v4.2院士版
支持流式输出、上下文管理、工具调用、多模态交互
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# LangChain 导入
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    HumanMessage = None
    AIMessage = None
    SystemMessage = None

# 向量存储导入
try:
    from src.vector_store import get_vector_store_manager
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    FILE = "file"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # "user", "assistant", "system"
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    references: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ChatContext:
    """聊天上下文"""
    chat_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    model: str = "glm-4-plus"
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: Optional[str] = None
    connected_papers: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: ChatMessage):
        """添加消息"""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # 限制历史消息数量（保留最近20轮）
        if len(self.messages) > 40:
            # 保留系统消息和最近消息
            system_msgs = [m for m in self.messages if m.role == "system"]
            recent_msgs = self.messages[-38:]
            self.messages = system_msgs + recent_msgs
    
    def to_langchain_messages(self) -> List:
        """转换为 LangChain 消息格式"""
        messages = []
        
        # 系统提示词
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        
        # 历史消息
        for msg in self.messages[-20:]:  # 只使用最近20条
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        return messages
    
    def clear(self):
        """清空上下文"""
        self.messages = []
        self.updated_at = datetime.now()


class ChatEngine:
    """AI 聊天引擎"""
    
    # 系统提示词模板
    DEFAULT_SYSTEM_PROMPT = """你是一位专业的科研助手，帮助研究人员进行文献分析、研究设计和学术写作。

你的能力包括：
1. 深度文献解读和分析
2. 研究空白识别和建议
3. 实验设计和方法论指导
4. 代码实现和算法解释
5. 学术写作和润色

请遵循以下原则：
- 回答要专业、准确、有深度
- 引用相关论文时要准确
- 对于不确定的内容要诚实说明
- 鼓励批判性思维和创新

当前时间：{current_time}"""

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        初始化聊天引擎
        
        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config or {}
        self.contexts: Dict[str, ChatContext] = {}
        self.db_manager = None
        
        # 初始化 LLM
        if LANGCHAIN_AVAILABLE:
            self.llm = self._create_llm()
        else:
            self.llm = None
        
        # 初始化向量存储
        if VECTOR_STORE_AVAILABLE:
            self.vector_store = get_vector_store_manager()
        else:
            self.vector_store = None
    
    def _create_llm(self, model: Optional[str] = None) -> ChatOpenAI:
        """创建 LLM 实例"""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        return ChatOpenAI(
            model=model or self.llm_config.get('model', 'glm-4-plus'),
            api_key=self.llm_config.get('api_key') or os.getenv('GLM_API_KEY'),
            base_url=self.llm_config.get('base_url') or os.getenv('GLM_BASE_URL'),
            temperature=self.llm_config.get('temperature', 0.7),
            max_tokens=self.llm_config.get('max_tokens', 4000),
            streaming=True,
            request_timeout=120
        )
    
    def create_context(self, 
                      chat_id: Optional[str] = None,
                      model: str = "glm-4-plus",
                      temperature: float = 0.7,
                      system_prompt: Optional[str] = None,
                      connected_papers: Optional[List[int]] = None) -> ChatContext:
        """
        创建新的聊天上下文
        
        Args:
            chat_id: 聊天ID（可选）
            model: 模型名称
            temperature: 温度参数
            system_prompt: 系统提示词
            connected_papers: 关联的论文ID列表
            
        Returns:
            ChatContext 实例
        """
        if chat_id is None:
            chat_id = f"chat_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # 生成系统提示词
        if system_prompt is None:
            system_prompt = self.DEFAULT_SYSTEM_PROMPT.format(
                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        
        context = ChatContext(
            chat_id=chat_id,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
            connected_papers=connected_papers or []
        )
        
        self.contexts[chat_id] = context
        return context
    
    def get_context(self, chat_id: str) -> Optional[ChatContext]:
        """获取聊天上下文"""
        return self.contexts.get(chat_id)
    
    def delete_context(self, chat_id: str) -> bool:
        """删除聊天上下文"""
        if chat_id in self.contexts:
            del self.contexts[chat_id]
            return True
        return False
    
    def clear_context(self, chat_id: str) -> bool:
        """清空聊天上下文中的消息"""
        context = self.contexts.get(chat_id)
        if context:
            context.clear()
            return True
        return False
    
    async def chat_stream(self, 
                         chat_id: str,
                         message: str,
                         use_rag: bool = True,
                         search_papers: bool = True) -> AsyncGenerator[str, None]:
        """
        流式聊天
        
        Args:
            chat_id: 聊天ID
            message: 用户消息
            use_rag: 是否使用 RAG
            search_papers: 是否搜索相关论文
            
        Yields:
            流式响应片段
        """
        if not LANGCHAIN_AVAILABLE or not self.llm:
            yield "抱歉，聊天功能当前不可用。"
            return
        
        # 获取或创建上下文
        context = self.get_context(chat_id)
        if not context:
            context = self.create_context(chat_id)
        
        # 构建增强提示词
        enhanced_message = message
        references = []
        
        # RAG：检索相关论文
        if use_rag and self.vector_store and self.vector_store.is_available():
            try:
                search_results = self.vector_store.search(message, top_k=3)
                if search_results:
                    context_text = "\n\n".join([
                        f"论文 {i+1}: {r.title}\n{r.abstract[:500]}..."
                        for i, r in enumerate(search_results)
                    ])
                    enhanced_message = f"基于以下相关论文回答问题：\n\n{context_text}\n\n用户问题：{message}"
                    
                    references = [
                        {"paper_id": r.paper_id, "title": r.title, "distance": r.distance}
                        for r in search_results
                    ]
            except Exception as e:
                print(f"RAG 搜索失败: {e}")
        
        # 添加用户消息
        user_msg = ChatMessage(
            role="user",
            content=message,
            references=references
        )
        context.add_message(user_msg)
        
        # 准备消息
        messages = context.to_langchain_messages()
        messages.append(HumanMessage(content=enhanced_message))
        
        # 流式生成
        full_response = ""
        try:
            async for chunk in self.llm.astream(messages):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                yield content
        except Exception as e:
            yield f"\n\n[错误: {str(e)}]"
            return
        
        # 添加助手消息
        assistant_msg = ChatMessage(
            role="assistant",
            content=full_response,
            references=references
        )
        context.add_message(assistant_msg)
    
    async def chat(self, 
                  chat_id: str,
                  message: str,
                  use_rag: bool = True) -> Dict[str, Any]:
        """
        非流式聊天
        
        Args:
            chat_id: 聊天ID
            message: 用户消息
            use_rag: 是否使用 RAG
            
        Returns:
            完整响应
        """
        full_response = ""
        async for chunk in self.chat_stream(chat_id, message, use_rag):
            full_response += chunk
        
        return {
            "content": full_response,
            "chat_id": chat_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_chat_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        获取聊天历史
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            消息列表
        """
        context = self.get_context(chat_id)
        if not context:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "references": msg.references
            }
            for msg in context.messages
        ]
    
    def list_chats(self) -> List[Dict[str, Any]]:
        """
        列出所有聊天会话
        
        Returns:
            聊天会话列表
        """
        return [
            {
                "chat_id": chat_id,
                "message_count": len(context.messages),
                "model": context.model,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "preview": context.messages[-1].content[:50] + "..." if context.messages else ""
            }
            for chat_id, context in self.contexts.items()
        ]
    
    def generate_chat_title(self, first_message: str) -> str:
        """
        根据第一条消息生成聊天标题
        
        Args:
            first_message: 第一条消息
            
        Returns:
            生成的标题
        """
        # 简单规则生成标题
        title = first_message[:30] if len(first_message) <= 30 else first_message[:27] + "..."
        return title
    
    async def analyze_papers(self, 
                            chat_id: str,
                            paper_ids: List[int],
                            analysis_type: str = "summary") -> AsyncGenerator[str, None]:
        """
        分析指定论文
        
        Args:
            chat_id: 聊天ID
            paper_ids: 论文ID列表
            analysis_type: 分析类型
            
        Yields:
            流式响应
        """
        if not self.db_manager:
            yield "错误：数据库管理器未配置"
            return
        
        # 获取论文数据
        papers = []
        for pid in paper_ids:
            paper = self.db_manager.get_paper(pid)
            if paper:
                papers.append(paper)
        
        if not papers:
            yield "未找到指定的论文"
            return
        
        # 构建分析提示词
        if analysis_type == "summary":
            prompt = f"请对以下 {len(papers)} 篇论文进行综合分析和总结：\n\n"
        elif analysis_type == "compare":
            prompt = f"请对比分析以下 {len(papers)} 篇论文的方法和结果：\n\n"
        elif analysis_type == "gaps":
            prompt = f"请基于以下 {len(papers)} 篇论文识别研究空白：\n\n"
        else:
            prompt = f"请分析以下 {len(papers)} 篇论文：\n\n"
        
        for i, paper in enumerate(papers, 1):
            prompt += f"论文 {i}:\n"
            prompt += f"标题: {paper.get('title', '未知')}\n"
            prompt += f"摘要: {paper.get('abstract', '无摘要')[:500]}...\n\n"
        
        async for chunk in self.chat_stream(chat_id, prompt, use_rag=False):
            yield chunk
    
    async def generate_literature_review(self, 
                                        chat_id: str,
                                        topic: str,
                                        paper_ids: Optional[List[int]] = None) -> AsyncGenerator[str, None]:
        """
        生成文献综述
        
        Args:
            chat_id: 聊天ID
            topic: 研究主题
            paper_ids: 可选的论文ID列表
            
        Yields:
            流式响应
        """
        prompt = f"请针对主题「{topic}」生成一份详细的文献综述。"
        
        if paper_ids and self.db_manager:
            prompt += "\n\n基于以下论文：\n"
            for pid in paper_ids:
                paper = self.db_manager.get_paper(pid)
                if paper:
                    prompt += f"- {paper.get('title', '未知')}\n"
        
        prompt += """

文献综述结构：
1. 研究背景与意义
2. 相关工作的系统回顾
3. 方法论的演进
4. 现有研究的不足
5. 未来研究方向

请生成综述："""
        
        async for chunk in self.chat_stream(chat_id, prompt, use_rag=True):
            yield chunk


# 全局引擎实例
_chat_engine = None

def get_chat_engine(llm_config: Optional[Dict[str, Any]] = None, 
                   db_manager=None) -> ChatEngine:
    """获取聊天引擎实例"""
    global _chat_engine
    if _chat_engine is None:
        _chat_engine = ChatEngine(llm_config=llm_config)
        _chat_engine.db_manager = db_manager
    return _chat_engine
