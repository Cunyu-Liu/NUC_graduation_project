"""摘要生成模块 - v4.2 LangChain优化版

使用 LangChain Prompt Templates 和 StructuredLLMHelper
提供更优雅的提示词管理和结构化输出
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.config import settings
from src.pdf_parser import ParsedPaper

# v4.2: 使用新的 LangChain 辅助模块
try:
    from src.langchain_helpers import StructuredLLMHelper, get_structured_llm_helper
    LANGCHAIN_V2_AVAILABLE = True
except ImportError:
    LANGCHAIN_V2_AVAILABLE = False
    print("[WARNING] 新的 LangChain 模块不可用，将使用降级模式")

# 保留旧版导入以确保兼容性
try:
    from langchain_openai import ChatOpenAI
    from src.prompts import get_summary_prompt
    LANGCHAIN_LEGACY_AVAILABLE = True
except ImportError:
    LANGCHAIN_LEGACY_AVAILABLE = False


class SummaryGenerator:
    """论文摘要生成器 - v4.2 LangChain优化版"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_langchain_v2: bool = True  # v4.2: 默认使用新的 LangChain 架构
    ):
        """
        初始化摘要生成器

        Args:
            api_key: GLM-4 API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            use_langchain_v2: 是否使用新的 LangChain 架构
        """
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else settings.default_temperature
        self.max_tokens = max_tokens or settings.max_tokens
        self.use_langchain_v2 = use_langchain_v2 and LANGCHAIN_V2_AVAILABLE

        if not self.api_key:
            raise ValueError("请设置GLM_API_KEY环境变量")

        # v4.2: 初始化新的 LangChain helper
        if self.use_langchain_v2:
            self.helper = get_structured_llm_helper(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            self.llm = self.helper.llm
        # 否则使用旧的初始化方式
        elif LANGCHAIN_LEGACY_AVAILABLE:
            self.llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            self.helper = None
        else:
            raise ValueError("LangChain 不可用且未启用 v2 模式")

    def generate_summary(
        self,
        paper: ParsedPaper,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> str:
        """
        生成单篇论文的摘要

        Args:
            paper: 解析后的论文对象
            save: 是否保存摘要到文件
            output_dir: 输出目录

        Returns:
            str: 生成的摘要
        """
        # 准备内容
        content = self._prepare_paper_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:500]}"
            for name, content_part in paper.metadata.sections.items()
        ])

        # v4.2: 使用新的 helper 生成摘要
        if self.use_langchain_v2 and self.helper:
            summary = self.helper.generate_summary(
                title=paper.metadata.title or paper.filename,
                abstract=paper.metadata.abstract or "未提取到摘要",
                sections=sections_text,
                content=content
            )
        else:
            # 旧版兼容模式
            from langchain_core.messages import HumanMessage
            prompt = get_summary_prompt(
                title=paper.metadata.title or paper.filename,
                abstract=paper.metadata.abstract or "未提取到摘要",
                sections=sections_text,
                content=content
            )
            response = self.llm.invoke([HumanMessage(content=prompt)])
            summary = response.content

        # 保存摘要
        if save:
            self._save_summary(paper, summary, output_dir)

        return summary

    async def agenerate_summary(
        self,
        paper: ParsedPaper,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> str:
        """
        异步生成单篇论文的摘要

        Args:
            paper: 解析后的论文对象
            save: 是否保存摘要到文件
            output_dir: 输出目录

        Returns:
            str: 生成的摘要
        """
        # 准备内容
        content = self._prepare_paper_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:500]}"
            for name, content_part in paper.metadata.sections.items()
        ])

        # v4.2: 使用新的 helper 异步生成摘要
        if self.use_langchain_v2 and self.helper:
            summary = await self.helper.agenerate_summary(
                title=paper.metadata.title or paper.filename,
                abstract=paper.metadata.abstract or "未提取到摘要",
                sections=sections_text,
                content=content
            )
        else:
            # 旧版兼容模式
            import asyncio
            from langchain_core.messages import HumanMessage
            prompt = get_summary_prompt(
                title=paper.metadata.title or paper.filename,
                abstract=paper.metadata.abstract or "未提取到摘要",
                sections=sections_text,
                content=content
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.invoke([HumanMessage(content=prompt)])
            )
            summary = response.content

        # 保存摘要
        if save:
            self._save_summary(paper, summary, output_dir)

        return summary

    def _prepare_paper_content(self, paper: ParsedPaper, max_chars: int = 8000) -> str:
        """
        准备论文内容，避免超出token限制

        Args:
            paper: 论文对象
            max_chars: 最大字符数

        Returns:
            str: 处理后的论文内容
        """
        # 优先使用摘要和主要章节
        content_parts = []

        # 添加标题
        if paper.metadata.title:
            content_parts.append(f"标题: {paper.metadata.title}")

        # 添加摘要
        if paper.metadata.abstract:
            content_parts.append(f"摘要: {paper.metadata.abstract}")

        # 添加主要章节
        if paper.metadata.sections:
            content_parts.append("\n主要章节:")
            for section_name, section_content in paper.metadata.sections.items():
                content_parts.append(f"\n{section_name}:\n{section_content[:1000]}")

        # 如果内容仍然不够，添加全文的部分内容
        combined_content = "\n\n".join(content_parts)

        if len(combined_content) < max_chars:
            # 可以添加更多全文内容
            remaining_chars = max_chars - len(combined_content)
            full_text_sample = paper.full_text[:remaining_chars]
            combined_content += f"\n\n论文正文:\n{full_text_sample}"

        return combined_content[:max_chars]

    def _save_summary(
        self,
        paper: ParsedPaper,
        summary: str,
        output_dir: Optional[Path] = None
    ):
        """
        保存摘要到文件

        Args:
            paper: 论文对象
            summary: 生成的摘要
            output_dir: 输出目录
        """
        output_dir = output_dir or settings.summary_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用原文件名（去掉.pdf）作为输出文件名，保存为markdown格式
        output_filename = Path(paper.filename).stem + "_summary.md"
        output_path = output_dir / output_filename

        # 构建markdown格式内容
        md_content = f"""# 论文摘要报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 论文标题 | {paper.metadata.title or paper.filename} |
| 文件名 | `{paper.filename}` |
| 页数 | {paper.page_count} |
| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

---

## AI生成的摘要

{summary}

---

*此报告由院士级科研智能助手自动生成*
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def batch_generate_summaries(
        self,
        papers: List[ParsedPaper],
        output_dir: Optional[Path] = None
    ) -> List[str]:
        """
        批量生成摘要

        Args:
            papers: 论文列表
            output_dir: 输出目录

        Returns:
            List[str]: 摘要列表
        """
        summaries = []

        for i, paper in enumerate(papers, 1):
            print(f"正在生成第 {i}/{len(papers)} 篇论文的摘要...")
            try:
                summary = self.generate_summary(paper, save=True, output_dir=output_dir)
                summaries.append(summary)
                print(f"✓ 完成: {paper.filename}")
            except Exception as e:
                print(f"✗ 失败: {paper.filename} - {e}")
                summaries.append("")

        return summaries

    def generate_custom_summary(
        self,
        paper_content: str,
        custom_prompt: str
    ) -> str:
        """
        使用自定义提示生成摘要

        Args:
            paper_content: 论文内容
            custom_prompt: 自定义提示词

        Returns:
            str: 生成的摘要
        """
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt = ChatPromptTemplate.from_template(custom_prompt)
        chain = prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"paper_content": paper_content})
            return result
        except Exception as e:
            raise Exception(f"自定义摘要生成失败: {e}")


def generate_summary_for_pdf(pdf_path: str) -> str:
    """
    便捷函数：为PDF文件生成摘要

    Args:
        pdf_path: PDF文件路径

    Returns:
        str: 生成的摘要
    """
    from src.pdf_parser import PDFParser

    # 解析PDF
    parser = PDFParser()
    paper = parser.parse_pdf(pdf_path)

    # 生成摘要
    generator = SummaryGenerator()
    summary = generator.generate_summary(paper)

    return summary
