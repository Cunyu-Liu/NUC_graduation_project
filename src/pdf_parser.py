"""文献解析模块 - PDF文档文本提取与结构化处理"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from dataclasses import dataclass

# 尝试导入 pdfplumber
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


@dataclass
class PaperMetadata:
    """论文元数据"""
    title: str = ""
    authors: List[str] = None
    abstract: str = ""
    keywords: List[str] = None
    sections: Dict[str, str] = None

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []
        if self.sections is None:
            self.sections = {}


@dataclass
class ParsedPaper:
    """解析后的论文数据"""
    filename: str
    full_text: str
    metadata: PaperMetadata
    page_count: int


class PDFParser:
    """PDF文档解析器"""

    def __init__(self):
        """初始化解析器"""
        pass

    def parse_pdf(self, pdf_path: str) -> ParsedPaper:
        """
        解析PDF文档

        Args:
            pdf_path: PDF文件路径

        Returns:
            ParsedPaper: 解析后的论文对象
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 提取完整文本
        full_text = self._extract_full_text(pdf_path)

        # 提取元数据
        metadata = self._extract_metadata(full_text)

        # 获取页数
        page_count = self._get_page_count(pdf_path)

        return ParsedPaper(
            filename=pdf_path.name,
            full_text=full_text,
            metadata=metadata,
            page_count=page_count
        )

    def _extract_full_text(self, pdf_path: Path) -> str:
        """
        提取PDF完整文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            str: 提取的文本内容
        """
        text_parts = []

        # 首先尝试使用 PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
        except Exception as e:
            # 如果PyMuPDF失败，尝试pdfplumber（如果可用）
            if PDFPLUMBER_AVAILABLE:
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                except Exception as e2:
                    raise Exception(f"PDF文本提取失败: {e}, pdfplumber备选方案也失败: {e2}")
            else:
                raise Exception(f"PDF文本提取失败: {e}")

        full_text = "\n\n".join(text_parts)
        return self._clean_text(full_text)

    def _clean_text(self, text: str) -> str:
        """
        清理提取的文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 移除过短的行
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            # 保留有意义的行（长度大于1，或者包含常见标点）
            if len(stripped) > 1 or any(c in stripped for c in "。.，,、;；:："):
                cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines)

    def _extract_metadata(self, text: str) -> PaperMetadata:
        """
        从文本中提取元数据

        Args:
            text: 论文全文

        Returns:
            PaperMetadata: 论文元数据
        """
        metadata = PaperMetadata()

        # 提取标题（通常是第一行较长的文本）
        lines = text.split("\n")
        for i, line in enumerate(lines[:20]):  # 只检查前20行
            line = line.strip()
            if 10 < len(line) < 200 and not line.startswith(("Abstract", "摘要", "Introduction", "引言")):
                metadata.title = line
                break

        # 提取摘要
        abstract = self._extract_abstract(text)
        metadata.abstract = abstract

        # 提取章节
        metadata.sections = self._extract_sections(text)

        # 提取关键词
        metadata.keywords = self._extract_keywords(text)

        return metadata

    def _extract_abstract(self, text: str) -> str:
        """
        提取摘要部分

        Args:
            text: 论文全文

        Returns:
            str: 摘要内容
        """
        # 中英文摘要模式
        patterns = [
            r"Abstract\s*:?\s*(.*?)(?=\n\s*(Keywords|Introduction|1\.|引言|关键词|1\s))",
            r"摘\s*要\s*:?\s*(.*?)(?=\n\s*(关键词|引言|1\.|1\s|Abstract))",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # 限制摘要长度
                if len(abstract) > 50 and len(abstract) < 2000:
                    return abstract[:2000]  # 限制最大长度

        return ""

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        提取主要章节

        Args:
            text: 论文全文

        Returns:
            Dict[str, str]: 章节名称与内容的映射
        """
        sections = {}

        # 常见章节标题模式
        section_patterns = [
            r"(Introduction|引言)\s*:?\s*(.*?)(?=\n\s*(Related Work|Method|2\.|相关工作|方法|参考文献))",
            r"(Related Work|相关工作)\s*:?\s*(.*?)(?=\n\s*(Method|Methodology|3\.|方法|系统设计))",
            r"(Method|Methodology|方法|系统设计)\s*:?\s*(.*?)(?=\n\s*(Experiment|Result|4\.|实验|结果|Evaluation))",
            r"(Experiment|Experimental|Experiments|实验|结果|评估)\s*:?\s*(.*?)(?=\n\s*(Conclusion|Discussion|5\.|结论|讨论|参考文献|Reference))",
            r"(Conclusion|Discussion|结论|讨论)\s*:?\s*(.*?)(?=\n\s*(Reference|参考文献|\Z))",
        ]

        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section_name = match.group(1).strip()
                section_content = match.group(2).strip()
                # 只保存有内容的章节
                if len(section_content) > 50:
                    sections[section_name] = section_content[:3000]  # 限制长度

        return sections

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词

        Args:
            text: 论文全文

        Returns:
            List[str]: 关键词列表
        """
        keywords = []

        # 关键词提取模式
        patterns = [
            r"Keywords?\s*:?\s*([^\n]+)",
            r"关键词\s*:?\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                keyword_text = match.group(1)
                # 分割关键词（支持中英文分隔符）
                kw_list = re.split(r"[;；,，、]", keyword_text)
                keywords = [kw.strip() for kw in kw_list if kw.strip()]
                if keywords:
                    break

        return keywords[:10]  # 最多返回10个关键词

    def _get_page_count(self, pdf_path: Path) -> int:
        """
        获取PDF页数

        Args:
            pdf_path: PDF文件路径

        Returns:
            int: 页数
        """
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0

    def batch_parse(self, pdf_paths: List[str]) -> List[ParsedPaper]:
        """
        批量解析PDF文件

        Args:
            pdf_paths: PDF文件路径列表

        Returns:
            List[ParsedPaper]: 解析后的论文列表
        """
        results = []

        for pdf_path in pdf_paths:
            try:
                paper = self.parse_pdf(pdf_path)
                results.append(paper)
            except Exception as e:
                print(f"解析文件失败 {pdf_path}: {e}")

        return results


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    便捷函数：从PDF提取文本

    Args:
        pdf_path: PDF文件路径

    Returns:
        str: 提取的文本
    """
    parser = PDFParser()
    paper = parser.parse_pdf(pdf_path)
    return paper.full_text
