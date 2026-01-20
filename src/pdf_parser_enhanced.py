"""增强版文献解析模块 - 深度解析PDF文档结构"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import fitz  # PyMuPDF
import json

# 尝试导入 pdfplumber，如果失败则使用备用方案
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("⚠️  pdfplumber 未安装，表格提取功能将受限。安装: pip install pdfplumber")


@dataclass
class PaperMetadata:
    """论文元数据 - 增强版"""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)

    # 新增字段
    publication_venue: str = ""  # 期刊或会议名称
    year: int = 0
    volume: str = ""
    number: str = ""
    pages: str = ""
    doi: str = ""
    references_count: int = 0

    # 表格和图片信息
    table_captions: List[Dict[str, str]] = field(default_factory=list)
    figure_captions: List[Dict[str, str]] = field(default_factory=list)

    # 数学公式信息
    formula_count: int = 0


@dataclass
class ParsedPaper:
    """解析后的论文数据 - 增强版"""
    filename: str
    full_text: str
    metadata: PaperMetadata
    page_count: int

    # 新增字段
    tables: List[str] = field(default_factory=list)
    figures: List[Dict[str, str]] = field(default_factory=list)
    section_structure: Dict[str, Any] = field(default_factory=dict)
    language: str = "unknown"  # zh, en, or mixed


class EnhancedPDFParser:
    """增强版PDF文档解析器"""

    def __init__(self, extract_tables: bool = True, extract_figures: bool = True):
        """
        初始化解析器

        Args:
            extract_tables: 是否提取表格
            extract_figures: 是否提取图片信息
        """
        self.extract_tables = extract_tables
        self.extract_figures = extract_figures

        # 加载停用词
        self.stopwords = self._load_stopwords()

        # 常见章节标题模式
        self.section_patterns = [
            (r'^(Abstract|摘要)\s*$', 'abstract'),
            (r'^(Introduction|引言)\s*$', 'introduction'),
            (r'^(Related Work|相关工作|Background|背景)\s*$', 'related_work'),
            (r'^(Method|Methodology|方法|系统设计|Proposed Method|提出方法)\s*$', 'method'),
            (r'^(Experiment|Experimental|Experiments|实验|结果|Evaluation|评估)\s*$', 'experiment'),
            (r'^(Result|Results|Discussion|讨论|结果分析)\s*$', 'result'),
            (r'^(Conclusion|Conclusions|结论|Future Work|未来工作)\s*$', 'conclusion'),
            (r'^(References|参考文献)\s*$', 'references'),
        ]

    def parse_pdf(self, pdf_path: str) -> ParsedPaper:
        """
        解析PDF文档 - 增强版

        Args:
            pdf_path: PDF文件路径

        Returns:
            ParsedPaper: 解析后的论文对象
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        print(f"正在解析: {pdf_path.name}")

        # 提取完整文本
        full_text = self._extract_full_text(pdf_path)

        # 提取元数据（增强版）
        metadata = self._extract_metadata_enhanced(pdf_path, full_text)

        # 获取页数
        page_count = self._get_page_count(pdf_path)

        # 提取表格
        tables = []
        if self.extract_tables:
            tables = self._extract_tables(pdf_path)

        # 提取图片信息
        figures = []
        if self.extract_figures:
            figures = self._extract_figures(pdf_path)

        # 分析章节结构
        section_structure = self._analyze_section_structure(full_text)

        # 检测语言
        language = self._detect_language(full_text)

        print(f"  ✓ 标题: {metadata.title[:60]}...")
        print(f"  ✓ 作者: {', '.join(metadata.authors[:3])}{'等' if len(metadata.authors) > 3 else ''}")
        print(f"  ✓ 摘要长度: {len(metadata.abstract)} 字符")
        print(f"  ✓ 章节数: {len(metadata.sections)}")
        print(f"  ✓ 参考文献数: {len(metadata.references)}")
        print(f"  ✓ 表格数: {len(tables)}")
        print(f"  ✓ 图片数: {len(figures)}")

        return ParsedPaper(
            filename=pdf_path.name,
            full_text=full_text,
            metadata=metadata,
            page_count=page_count,
            tables=tables,
            figures=figures,
            section_structure=section_structure,
            language=language
        )

    def _extract_full_text(self, pdf_path: Path) -> str:
        """
        提取PDF完整文本 - 增强版

        改进点:
        1. 处理双栏布局
        2. 过滤页眉页脚
        3. 保留段落结构
        """
        text_parts = []

        try:
            # 使用PyMuPDF处理双栏布局
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                # 获取文本块
                blocks = page.get_text("dict")["blocks"]

                # 过滤页眉页脚（通常在页面顶部和底部，且字体较小）
                page_height = page.rect.height
                filtered_blocks = []

                for block in blocks:
                    if "lines" not in block:
                        continue

                    # 检查块的位置，过滤页眉页脚
                    bbox = block["bbox"]  # (x0, y0, x1, y1)
                    block_height = bbox[3] - bbox[1]

                    # 过滤顶部5%和底部10%的内容（可能是页眉页脚）
                    if bbox[1] < page_height * 0.05 or bbox[3] > page_height * 0.9:
                        continue

                    # 过滤高度很小的块（可能是页码等）
                    if block_height < 10:
                        continue

                    filtered_blocks.append(block)

                # 提取文本
                for block in filtered_blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            for span in line["spans"]:
                                line_text += span["text"]
                            if line_text.strip():
                                text_parts.append(line_text.strip())

                # 页间分隔
                if page_num < len(doc) - 1:
                    text_parts.append("\n")

            doc.close()

        except Exception as e:
            # 降级方案：使用pdfplumber
            if not PDFPLUMBER_AVAILABLE:
                raise Exception(f"PDF文本提取失败且pdfplumber未安装: {e}")
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except Exception as e2:
                raise Exception(f"PDF文本提取失败: {e}, 降级方案也失败: {e2}")

        # 清理和合并文本
        full_text = "\n".join(text_parts)
        return self._clean_text_enhanced(full_text)

    def _clean_text_enhanced(self, text: str) -> str:
        """
        清理提取的文本 - 增强版
        """
        lines = text.split("\n")
        cleaned_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 移除空行
            if not stripped:
                continue

            # 移除页码（单独一行，只有数字）
            if stripped.isdigit() and len(stripped) < 5:
                continue

            # 移除常见的页眉页脚模式
            if re.match(r'^\d+\s+$', stripped):
                continue

            # 保留有意义的行
            if len(stripped) > 1 or any(c in stripped for c in "。.，,、;；:："):
                cleaned_lines.append(stripped)

        # 智能合并被断开的行
        merged_lines = []
        for line in cleaned_lines:
            # 如果当前行很短且不是以句号等结尾，可能是被断开的行
            if (len(line) < 50 and line and
                line[-1] not in "。.！!？?，,、;；:：" and
                merged_lines and
                not merged_lines[-1].endswith((".", "。", "!", "！", "?", "？"))):
                # 合并到上一行
                merged_lines[-1] += " " + line
            else:
                merged_lines.append(line)

        return "\n".join(merged_lines)

    def _extract_metadata_enhanced(self, pdf_path: Path, text: str) -> PaperMetadata:
        """
        提取元数据 - 增强版
        """
        metadata = PaperMetadata()

        # 使用PyMuPDF提取前几页的详细信息
        try:
            doc = fitz.open(pdf_path)

            # 提取第一页的文本块（标题和作者通常在第一页）
            first_page = doc[0]
            blocks = first_page.get_text("dict")["blocks"]

            # 提取标题（最大的字体，居中或靠上）- 改进版
            title_candidates = []
            seen_texts = set()  # 避免重复

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        # 获取整行文本
                        line_text = "".join([span["text"] for span in line["spans"]]).strip()

                        # 跳过过短或过长的文本，以及已知标题
                        if len(line_text) < 10 or len(line_text) > 300:
                            continue
                        if line_text in seen_texts:
                            continue

                        # 检查是否是标题的候选
                        # 1. 通常在前1/3的页面
                        bbox = block["bbox"]
                        page_height = first_page.rect.height
                        if bbox[1] > page_height * 0.35:  # 超过页面35%的位置
                            continue

                        # 2. 字体相对较大
                        avg_font_size = sum([span["size"] for span in line["spans"]]) / len(line["spans"])
                        if avg_font_size < 12:  # 字体太小
                            continue

                        # 3. 排除常见非标题文本
                        skip_patterns = [
                            r'^Abstract$', r'^摘要$', r'^Introduction$', r'^引言$',
                            r'^\d+\s*$',  # 纯数字
                            r'^[A-Z]\.$',  # 单字母
                            r'^http',  # URL
                        ]
                        if any(re.match(pattern, line_text, re.IGNORECASE) for pattern in skip_patterns):
                            continue

                        # 4. 计算标题得分
                        score = 0
                        score += avg_font_size * 2  # 字体越大得分越高
                        score += (page_height - bbox[1]) / page_height * 10  # 越靠上得分越高
                        if any(keyword in line_text.lower() for keyword in ['algorithm', 'method', 'system', 'approach', 'framework']):
                            score -= 5  # 这些词不太可能是标题
                        if len([w for w in line_text.split() if w[0].isupper()]) > len(line_text.split()) * 0.3:
                            score += 3  # 标题通常有较多大写字母

                        title_candidates.append({
                            "text": line_text,
                            "size": avg_font_size,
                            "y": bbox[1],
                            "score": score
                        })
                        seen_texts.add(line_text)

            # 选择得分最高的候选作为标题
            if title_candidates:
                title_candidates.sort(key=lambda x: x["score"], reverse=True)
                best_title = title_candidates[0]["text"]

                # 清理标题（去除多余空格、换行等）
                best_title = re.sub(r'\s+', ' ', best_title)
                best_title = best_title.strip()

                # 确保标题不以特定标点符号结尾
                if best_title and best_title[-1] in '.,:;':
                    best_title = best_title[:-1]

                metadata.title = best_title

            # 提取作者信息（通常在标题下方，字体较小）
            author_lines = []
            title_y = title_candidates[0]["y"] if title_candidates else 0

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]

                        # 只在标题下方查找作者
                        bbox = block["bbox"]
                        if bbox[1] < title_y + 50:  # 在标题下方50个单位内
                            # 检测作者行（通常包含@email或特殊符号）
                            if "@" in line_text or " and " in line_text or "，" in line_text or "University" in line_text:
                                author_lines.append(line_text.strip())

            # 解析作者
            if author_lines:
                all_authors = []
                for author_line in author_lines[:3]:  # 只看前3行
                    authors = self._parse_authors(author_line)
                    all_authors.extend(authors)
                # 去重
                metadata.authors = list(dict.fromkeys(all_authors))[:10]  # 最多10个

            # 提取机构信息
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = "".join([span["text"] for span in line["spans"]])
                        # 机构通常包含University, Institute, Lab等关键词
                        if any(keyword in line_text.lower() for keyword in
                               ["university", "institute", "lab", "laboratory", "大学", "研究所", "实验室"]):
                            if line_text.strip() and len(line_text.strip()) > 10:
                                metadata.affiliations.append(line_text.strip())
                                break
                    if metadata.affiliations:
                        break

            doc.close()

        except Exception as e:
            print(f"  警告: 无法使用PyMuPDF提取详细元数据: {e}")

        # 如果没有提取到标题，使用简单方法
        if not metadata.title or len(metadata.title) < 10:
            metadata.title = self._extract_title_simple(text)

        # 提取摘要（增强版）
        metadata.abstract = self._extract_abstract_enhanced(text)

        # 提取关键词
        metadata.keywords = self._extract_keywords_enhanced(text)

        # 提取章节
        metadata.sections = self._extract_sections_enhanced(text)

        # 提取参考文献
        metadata.references = self._extract_references_enhanced(text)

        # 提取发表信息
        self._extract_publication_info(text, metadata)

        # 提取表格和图片标题
        metadata.table_captions = self._extract_table_captions(text)
        metadata.figure_captions = self._extract_figure_captions(text)

        # 统计公式数量
        metadata.formula_count = text.count('$') // 2 + text.count(r'\[')

        return metadata

    def _extract_title_simple(self, text: str) -> str:
        """简单方法提取标题"""
        lines = text.split("\n")
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            if 10 < len(line) < 200 and not line.startswith(("Abstract", "摘要", "Introduction", "引言")):
                return line
        return ""

    def _parse_authors(self, author_text: str) -> List[str]:
        """解析作者信息"""
        authors = []

        # 移除email和数字
        author_text = re.sub(r'\S+@\S+', '', author_text)
        author_text = re.sub(r'\d+', '', author_text)

        # 分割作者
        if "," in author_text or "，" in author_text:
            authors = re.split(r'[，,]', author_text)
        elif " and " in author_text:
            authors = author_text.split(" and ")
        elif " and " in author_text.lower():
            authors = author_text.lower().split(" and ")
        else:
            authors = [author_text]

        # 清理作者名
        authors = [a.strip() for a in authors if a.strip() and len(a.strip()) > 1]

        return authors[:10]  # 最多返回10个作者

    def _extract_abstract_enhanced(self, text: str) -> str:
        """提取摘要 - 增强版"""
        # 更强大的模式匹配
        patterns = [
            r'(?:Abstract|摘要)\s*:?\s*(.*?)(?=\n\s*(?:Keywords?|关键词|Introduction|引言|1\.|1\s|引言))',
            r'(?:Abstract|ABSTRACT)\s*\n+(.*?)(?=\n\s*(?:Keywords?|KEYWORDS?|Introduction|引言))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # 清理多余的空白
                abstract = re.sub(r'\s+', ' ', abstract)
                if 50 < len(abstract) < 5000:
                    return abstract

        return ""

    def _extract_keywords_enhanced(self, text: str) -> List[str]:
        """提取关键词 - 增强版"""
        keywords = []

        patterns = [
            r'(?:Keywords?|关键词)\s*:?\s*(.*?)(?=\n\n|\n\s*(?:Introduction|引言|1\.|Abstract))',
            r'(?:Keywords?|KEYWORDS?)\s*:?\s*(.*?)(?=\n\n|\n\s*(?:Introduction|1\.))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                keyword_text = match.group(1)
                # 分割关键词
                kw_list = re.split(r'[;；,，、·]', keyword_text)

                # 过滤和清理关键词
                for kw in kw_list:
                    kw_clean = kw.strip()

                    # 严格过滤条件
                    # 1. 长度限制：2-50个字符
                    if len(kw_clean) < 2 or len(kw_clean) > 50:
                        continue

                    # 2. 不包含换行符（说明是整段文本）
                    if '\n' in kw_clean:
                        continue

                    # 3. 不包含图片/表格标记
                    skip_patterns = ['figure', 'table', 'fig.', 'eq.', 'equation', '图', '表', '式']
                    if any(pattern.lower() in kw_clean.lower() for pattern in skip_patterns):
                        continue

                    # 4. 不应该全是数字或特殊字符
                    if re.match(r'^[\d\W]+$', kw_clean):
                        continue

                    # 5. 限制单词数量（最多5个词）
                    words = kw_clean.split()
                    if len(words) > 5:
                        continue

                    keywords.append(kw_clean)

                # 也从摘要中提取关键词
                if not keywords:
                    keywords = self._extract_keywords_from_abstract(text)

                if keywords:
                    break

        # 限制关键词数量
        return keywords[:10]

    def _extract_keywords_from_abstract(self, text: str) -> List[str]:
        """从摘要中提取关键词（使用简单的TF-IDF思想）"""
        abstract = self._extract_abstract_enhanced(text)
        if not abstract:
            return []

        # 简单的词频统计
        words = re.findall(r'\b[a-zA-Z]{4,}\b', abstract.lower())
        from collections import Counter
        word_freq = Counter(words)

        # 过滤常见词
        stopwords = {'that', 'this', 'with', 'from', 'have', 'been', 'paper', 'propose'}
        keywords = [w for w, c in word_freq.most_common(10) if w not in stopwords]

        return keywords[:8]

    def _extract_sections_enhanced(self, text: str) -> Dict[str, str]:
        """提取章节 - 增强版"""
        sections = {}

        # 使用更灵活的模式
        section_pattern = r'^([A-Z][a-zA-Z\s]+|[\u4e00-\u9fa5]+)\s*$'

        lines = text.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            stripped = line.strip()

            # 检查是否是章节标题
            match = re.match(section_pattern, stripped)
            if match and len(stripped) < 50 and not stripped.endswith('.'):
                # 保存上一个章节
                if current_section and current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 50:
                        sections[current_section] = content[:4000]

                current_section = stripped
                current_content = []
            elif current_section:
                current_content.append(line)

        # 保存最后一个章节
        if current_section and current_content:
            content = "\n".join(current_content).strip()
            if len(content) > 50:
                sections[current_section] = content[:4000]

        return sections

    def _extract_references_enhanced(self, text: str) -> List[str]:
        """提取参考文献 - 增强版"""
        references = []

        # 查找References部分
        ref_pattern = r'(?:References?|参考文献)\s*:?\s*(.*?)(?=\Z|$)'
        match = re.search(ref_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            ref_text = match.group(1)

            # 按条目分割（通常以[1], [2]或数字开头）
            ref_entries = re.split(r'\n\s*(?:\[\d+\]|\d+\.)', ref_text)

            for ref in ref_entries:
                ref = ref.strip()
                if len(ref) > 20:  # 过滤太短的条目
                    # 清理
                    ref = re.sub(r'\s+', ' ', ref)
                    references.append(ref[:500])  # 限制长度

        return references[:200]  # 最多返回200条参考文献

    def _extract_publication_info(self, text: str, metadata: PaperMetadata):
        """提取发表信息 - 增强版"""
        # 查找会议/期刊名称模式 - 更全面
        venue_patterns = [
            # 会议
            r'Proceedings of\s+([^,\n]+?(?:Conference|Symposium|Workshop)[^,\n]*)',
            r'in\s+Proceedings of\s+([^,\n]+)',
            r'(?:Presented at|at)\s+([^,\n]+?(?:Conference|Symposium|Workshop)[^,\n]*)',
            r'([^,\n]*?(?:IEEE|ACM)[^,\n]*?(?:Conference|Symposium)[^,\n]*)',
            # 期刊
            r'([A-Z][a-zA-Z\s]*Journal[^,\n]*?(?:of\s+[A-Za-z]+[^,\n]*)?)',
            r'published in\s+([^,\n]+)',
            r'([A-Z][a-zA-Z\s]*Transactions[^,\n]*)',
            r'([A-Z][a-zA-Z\s]*Letters[^,\n]*)',
            # arXiv
            r'(arXiv:\d+\.\d+(?:v\d+)?)',
            # 中文期刊
            r'([^,\n]*?学报[^,\n]*)',
            r'([^,\n]*?期刊[^,\n]*)',
        ]

        # 提取期刊/会议（优先匹配更具体的模式）
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                venue = match.group(1).strip()
                # 清理venue
                venue = re.sub(r'\s+', ' ', venue)  # 合并多余空格
                venue = venue[:200]  # 限制长度
                if len(venue) > 5:  # 至少5个字符
                    metadata.publication_venue = venue
                    break

        # 提取年份 - 更智能的匹配
        year_patterns = [
            # 直接的4位年份
            r'\b(19|20)\d{2}\b',
            # Copyright后的年份
            r'(?:©|Copyright)\s*(19|20)\d{2}',
            # 会议日期中的年份
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(\d{1,2}),?\s*(19|20)\d{2}',
        ]

        all_years = []
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # 如果是元组，取最后一个数字
                    year_str = match[-1]
                    if len(year_str) == 4:
                        all_years.append(int(year_str))
                elif isinstance(match, str) and len(match) == 4:
                    all_years.append(int(match))

        # 选择最可能的年份（1990-2035之间，选择出现频率最高的）
        valid_years = [y for y in all_years if 1990 <= y <= 2035]
        if valid_years:
            # 统计频率，选择最常见的
            from collections import Counter
            year_counts = Counter(valid_years)
            # 如果有多个年份，选择出现次数最多的；如果次数相同，选择最近的
            if year_counts:
                most_common = year_counts.most_common(1)[0][0]
                metadata.year = most_common

        # 提取DOI - 更全面的模式
        doi_patterns = [
            r'(?:DOI|doi):\s*(10\.\d+/[^\s\n]+)',
            r'https?://doi\.org/(10\.\d+/[^\s\n]+)',
            r'DOI:\s*(10\.\d{4,}/[^\s\n]+)',
        ]

        for pattern in doi_patterns:
            doi_match = re.search(pattern, text, re.IGNORECASE)
            if doi_match:
                metadata.doi = doi_match.group(1).strip()
                break

        metadata.references_count = len(metadata.references)

    def _extract_table_captions(self, text: str) -> List[Dict[str, str]]:
        """提取表格标题"""
        captions = []
        pattern = r'(Table\s+\d+[:\.\s]+|表\s*\d+[:\.\s]+)(.*?)(?=\n\n|\n\s*(?:Figure|图|Table|表))'

        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            captions.append({
                "label": match.group(1).strip(),
                "caption": match.group(2).strip()
            })

        return captions[:50]

    def _extract_figure_captions(self, text: str) -> List[Dict[str, str]]:
        """提取图片标题"""
        captions = []
        pattern = r'(Figure\s+\d+[:\.\s]+|图\s*\d+[:\.\s]+)(.*?)(?=\n\n|\n\s*(?:Figure|图|Table|表))'

        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            captions.append({
                "label": match.group(1).strip(),
                "caption": match.group(2).strip()
            })

        return captions[:50]

    def _extract_tables(self, pdf_path: Path) -> List[str]:
        """提取表格内容"""
        tables = []

        if not PDFPLUMBER_AVAILABLE:
            print("  ⚠️  pdfplumber 未安装，跳过表格提取")
            return tables

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            # 转换表格为文本
                            table_text = self._table_to_text(table)
                            tables.append(table_text)
        except Exception as e:
            print(f"  警告: 表格提取失败: {e}")

        return tables

    def _table_to_text(self, table: List[List[str]]) -> str:
        """将表格转换为文本格式"""
        if not table or not table[0]:
            return ""

        # 简单的文本表格表示
        rows = []
        for row in table:
            if row:
                row_text = " | ".join([cell or "" for cell in row])
                rows.append(row_text)

        return "\n".join(rows)

    def _extract_figures(self, pdf_path: Path) -> List[Dict[str, str]]:
        """提取图片信息"""
        figures = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        figures.append({
                            "page": page_num + 1,
                            "index": img_index,
                            "format": base_image.get("ext", "unknown"),
                            "size": len(base_image.get("image", b""))
                        })

            doc.close()
        except Exception as e:
            print(f"  警告: 图片信息提取失败: {e}")

        return figures

    def _analyze_section_structure(self, text: str) -> Dict[str, Any]:
        """分析章节结构"""
        structure = {
            "total_sections": 0,
            "section_hierarchy": [],
            "section_titles": []
        }

        # 查找所有可能的章节标题
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            # 简单的章节标题检测（全大写英文或中文标题）
            if (stripped and
                len(stripped) < 80 and
                (stripped.isupper() or re.match(r'^[\u4e00-\u9fa5]+$', stripped)) and
                not stripped.endswith('.')):
                structure["section_titles"].append(stripped)

        structure["total_sections"] = len(structure["section_titles"])

        return structure

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        # 统计英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        total_chars = chinese_chars + english_words

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh"
        elif chinese_ratio < 0.1:
            return "en"
        else:
            return "mixed"

    def _get_page_count(self, pdf_path: Path) -> int:
        """获取PDF页数"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0

    def _load_stopwords(self) -> set:
        """加载停用词"""
        return {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "the", "a", "an", "and", "or", "but", "in", "on",
            "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were"
        }

    def batch_parse(self, pdf_paths: List[str]) -> List[ParsedPaper]:
        """批量解析PDF文件"""
        results = []

        for i, pdf_path in enumerate(pdf_paths, 1):
            print(f"\n[{i}/{len(pdf_paths)}] 解析: {Path(pdf_path).name}")
            try:
                paper = self.parse_pdf(pdf_path)
                results.append(paper)
            except Exception as e:
                print(f"✗ 解析失败: {e}")

        return results


def extract_text_from_pdf(pdf_path: str) -> str:
    """便捷函数：从PDF提取文本"""
    parser = EnhancedPDFParser()
    paper = parser.parse_pdf(pdf_path)
    return paper.full_text
