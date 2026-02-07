"""增强版文献解析模块 - 深度解析PDF文档结构 - v2.0高精度版"""
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
    """增强版PDF文档解析器 - v2.0高精度版"""

    # 顶级会议和期刊的精确匹配模式（优先级最高）
    TOP_VENUES = {
        # AI/ML顶级会议
        'AAAI': r'AAAI\s+(?:Conference\s+on\s+)?(?:Artificial\s+Intelligence)?',
        'IJCAI': r'IJCAI(?:\s*-\s*\d{1,2})?',
        'NeurIPS': r'NeurIPS|NIPS(?:\s*\d{4})?',
        'ICML': r'ICML(?:\s*\d{4})?',
        'ICLR': r'ICLR(?:\s*\d{4})?',
        'ACL': r'ACL(?:\s*\d{4})?',
        'EMNLP': r'EMNLP(?:\s*\d{4})?',
        'NAACL': r'NAACL(?:\s*\d{4})?',
        'CVPR': r'CVPR(?:\s*\d{4})?',
        'ICCV': r'ICCV(?:\s*\d{4})?',
        'ECCV': r'ECCV(?:\s*\d{4})?',
        'KDD': r'KDD(?:\s*\d{4})?',
        'WWW': r'WWW(?:\s*\d{4})?',
        'SIGIR': r'SIGIR(?:\s*\d{4})?',
        # 系统/软件工程
        'ICSE': r'ICSE(?:\s*\d{4})?',
        'FSE': r'FSE|ESEC/FSE(?:\s*\d{4})?',
        'ASE': r'ASE(?:\s*\d{4})?',
        'OSDI': r'OSDI(?:\s*\d{4})?',
        'SOSP': r'SOSP(?:\s*\d{4})?',
        'PLDI': r'PLDI(?:\s*\d{4})?',
        # 数据库
        'SIGMOD': r'SIGMOD(?:\s*\d{4})?',
        'VLDB': r'VLDB(?:\s*\d{4})?',
        'ICDE': r'ICDE(?:\s*\d{4})?',
        'CIKM': r'CIKM(?:\s*\d{4})?',
        # 网络
        'SIGCOMM': r'SIGCOMM(?:\s*\d{4})?',
        'NSDI': r'NSDI(?:\s*\d{4})?',
        'INFOCOM': r'INFOCOM(?:\s*\d{4})?',
        # 安全
        'S&P': r'IEEE\s+(?:Symposium\s+on\s+)?Security\s+and\s+Privacy',
        'CCS': r'CCS(?:\s*\d{4})?',
        'USENIX Security': r'USENIX\s+Security(?:\s*\d{4})?',
        'NDSS': r'NDSS(?:\s*\d{4})?',
        # 自然语言处理期刊
        'TACL': r'TACL|Transactions\s+of\s+the\s+Association\s+for\s+Computational\s+Linguistics',
        'CL': r'Computational\s+Linguistics',
        # 顶级期刊
        'Nature': r'Nature(?:\s*\d{4})?',
        'Science': r'Science(?:\s*\d{4})?',
        'TPAMI': r'TPAMI|IEEE\s+Transactions\s+on\s+Pattern\s+Analysis\s+and\s+Machine\s+Intelligence',
        'IJCV': r'IJCV|International\s+Journal\s+of\s+Computer\s+Vision',
        'JMLR': r'JMLR|Journal\s+of\s+Machine\s+Learning\s+Research',
        'TOSEM': r'TOSEM|ACM\s+Transactions\s+on\s+Software\s+Engineering\s+and\s+Methodology',
        'TSE': r'TSE|IEEE\s+Transactions\s+on\s+Software\s+Engineering',
    }

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

        # 标题检测的关键词过滤列表
        self.title_stop_words = {
            'abstract', 'introduction', 'related work', 'background',
            'method', 'methodology', 'experiment', 'experiments',
            'results', 'discussion', 'conclusion', 'conclusions',
            'references', 'acknowledgments', 'acknowledgement',
            'figure', 'table', 'appendix', 'author', 'authors',
            '摘要', '引言', '方法', '实验', '结果', '讨论',
            '结论', '参考文献', '致谢', '图', '表'
        }

    def parse_pdf(self, pdf_path: str) -> ParsedPaper:
        """
        解析PDF文档 - 增强版 v2.0
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 检查文件大小
        file_size = pdf_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"PDF文件为空: {pdf_path.name}")

        if file_size < 1024:
            print(f"  ⚠️  警告: PDF文件过小 ({file_size} bytes)")

        print(f"正在解析: {pdf_path.name} (大小: {file_size / 1024:.1f} KB)")

        # 提取完整文本
        full_text = self._extract_full_text(pdf_path)

        # 提取元数据（增强版 v2.0）
        metadata = self._extract_metadata_v2(pdf_path, full_text)

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
        print(f"  ✓ 期刊/会议: {metadata.publication_venue}")
        print(f"  ✓ 年份: {metadata.year}")
        print(f"  ✓ 作者: {', '.join(metadata.authors[:3])}{'等' if len(metadata.authors) > 3 else ''}")
        print(f"  ✓ 摘要长度: {len(metadata.abstract)} 字符")

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
        """提取PDF完整文本 - 增强版"""
        text_parts = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]

                # 过滤页眉页脚
                page_height = page.rect.height
                filtered_blocks = []

                for block in blocks:
                    if "lines" not in block:
                        continue

                    bbox = block["bbox"]
                    block_height = bbox[3] - bbox[1]

                    # 过滤顶部5%和底部10%
                    if bbox[1] < page_height * 0.05 or bbox[3] > page_height * 0.92:
                        continue

                    # 过滤高度很小的块
                    if block_height < 8:
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
            if not PDFPLUMBER_AVAILABLE:
                raise Exception(f"PDF文本提取失败: {e}")
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except Exception as e2:
                raise Exception(f"PDF文本提取失败: {e}, 降级方案也失败: {e2}")

        full_text = "\n".join(text_parts)
        return self._clean_text_enhanced(full_text)

    def _clean_text_enhanced(self, text: str) -> str:
        """清理提取的文本 - 增强版"""
        lines = text.split("\n")
        cleaned_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 移除空行
            if not stripped:
                continue

            # 移除页码
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
            if (len(line) < 50 and line and
                line[-1] not in "。.！!？?，,、;；:：" and
                merged_lines and
                not merged_lines[-1].endswith((".", "。", "!", "！", "?", "？"))):
                merged_lines[-1] += " " + line
            else:
                merged_lines.append(line)

        return "\n".join(merged_lines)

    def _extract_metadata_v2(self, pdf_path: Path, text: str) -> PaperMetadata:
        """
        提取元数据 - v2.0高精度版
        重写标题和期刊提取逻辑，大幅提高识别精度
        """
        metadata = PaperMetadata()

        # 首先尝试从PDF元数据中提取
        try:
            doc = fitz.open(pdf_path)
            pdf_metadata = doc.metadata

            if pdf_metadata.get('title') and len(pdf_metadata['title']) > 5:
                metadata.title = self._clean_title(pdf_metadata['title'].strip())
                print(f"  ✓ 从PDF元数据获取标题: {metadata.title[:50]}...")

            if pdf_metadata.get('author'):
                authors = self._parse_authors(pdf_metadata['author'])
                if authors:
                    metadata.authors = authors[:10]

            if pdf_metadata.get('keywords'):
                keywords = [kw.strip() for kw in pdf_metadata['keywords'].split(',') if kw.strip()]
                if keywords:
                    metadata.keywords = keywords[:10]

            doc.close()
        except Exception as e:
            print(f"  警告: 无法读取PDF元数据: {e}")

        # 使用高精度方法提取标题
        if not metadata.title or len(metadata.title) < 10:
            metadata.title = self._extract_title_precise(pdf_path, text)

        # 提取发表信息（高精度）
        self._extract_publication_info_v2(text, metadata)

        # 提取摘要
        metadata.abstract = self._extract_abstract_enhanced(text)

        # 提取关键词
        metadata.keywords = self._extract_keywords_enhanced(text)

        # 提取章节
        metadata.sections = self._extract_sections_enhanced(text)

        # 提取参考文献
        metadata.references = self._extract_references_enhanced(text)

        # 提取表格和图片标题
        metadata.table_captions = self._extract_table_captions(text)
        metadata.figure_captions = self._extract_figure_captions(text)

        # 统计公式数量
        metadata.formula_count = text.count('$') // 2 + text.count(r'\[')

        return metadata

    def _extract_title_precise(self, pdf_path: Path, text: str) -> str:
        """
        高精度标题提取方法
        使用多种策略综合判断，大幅提高准确性
        """
        try:
            doc = fitz.open(pdf_path)
            
            # 分析前3页（标题可能在第一页，也可能在后续页）
            title_candidates = []
            
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                    
                    for line in block["lines"]:
                        line_text = "".join([span["text"] for span in line["spans"]]).strip()
                        
                        # 基础过滤
                        if len(line_text) < 10 or len(line_text) > 300:
                            continue
                        
                        # 计算平均字体大小
                        font_sizes = [span["size"] for span in line["spans"]]
                        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                        
                        # 获取位置信息
                        bbox = block["bbox"]
                        page_height = page.rect.height
                        y_position = bbox[1]
                        
                        # 标题通常在页面顶部1/3区域
                        if y_position > page_height * 0.4:
                            continue
                        
                        # 排除常见的非标题文本
                        lower_text = line_text.lower()
                        if any(stop_word in lower_text for stop_word in self.title_stop_words):
                            continue
                        
                        # 排除纯数字、URL、email
                        if re.match(r'^[\d\s\.]+$', line_text):
                            continue
                        if line_text.startswith(('http://', 'https://', 'www.')):
                            continue
                        if '@' in line_text:
                            continue
                        
                        # 计算标题得分
                        score = 0
                        
                        # 1. 字体大小得分（最重要）
                        if avg_font_size >= 16:
                            score += 50
                        elif avg_font_size >= 14:
                            score += 35
                        elif avg_font_size >= 12:
                            score += 20
                        
                        # 2. 位置得分（越靠上越好）
                        score += (1 - y_position / page_height) * 20
                        
                        # 3. 长度得分（标题通常在40-150字符之间）
                        if 40 <= len(line_text) <= 150:
                            score += 15
                        elif 20 <= len(line_text) < 40:
                            score += 10
                        
                        # 4. 首字母大写特征（英文标题）
                        words = line_text.split()
                        capitalized_words = [w for w in words if w and w[0].isupper()]
                        if words and len(capitalized_words) / len(words) > 0.5:
                            score += 10
                        
                        # 5. 包含冒号或破折号（学术论文标题特征）
                        if ':' in line_text or '：' in line_text or '-' in line_text:
                            score += 5
                        
                        # 6. 中文论文标题特征
                        if re.search(r'[\u4e00-\u9fa5]', line_text):
                            score += 10
                        
                        # 7. 排除含有特定关键词（这些通常不是标题）
                        exclude_patterns = [
                            r'^\d+\s*\.\s*',  # 章节编号
                            r'^Fig\.?\s*\d+',  # 图编号
                            r'^Table\s*\d+',  # 表编号
                            r'^[\(\[]?\d+[\)\]]?',  # 数字编号
                        ]
                        if any(re.match(p, line_text, re.IGNORECASE) for p in exclude_patterns):
                            score -= 50
                        
                        title_candidates.append({
                            "text": line_text,
                            "size": avg_font_size,
                            "y": y_position,
                            "score": score,
                            "page": page_num
                        })
            
            doc.close()
            
            # 排序并选择最佳标题
            if title_candidates:
                # 按得分排序
                title_candidates.sort(key=lambda x: x["score"], reverse=True)
                
                # 选择得分最高的，但如果第一页有高分候选，优先第一页
                first_page_high_score = [c for c in title_candidates if c["page"] == 0 and c["score"] >= 60]
                
                if first_page_high_score:
                    best_title = first_page_high_score[0]["text"]
                else:
                    best_title = title_candidates[0]["text"]
                
                # 清理标题
                best_title = self._clean_title(best_title)
                
                if best_title:
                    print(f"  ✓ 提取到标题: {best_title[:60]}...")
                    return best_title
                    
        except Exception as e:
            print(f"  警告: 高精度标题提取失败: {e}")
        
        # 降级方案：使用简单方法
        return self._extract_title_simple(text)

    def _clean_title(self, title: str) -> str:
        """清理标题文本"""
        if not title:
            return ""
        
        # 合并多余空格
        title = re.sub(r'\s+', ' ', title)
        
        # 去除首尾标点和空格
        title = title.strip(' ,.，。：:;；!！?？')
        
        # 限制长度
        if len(title) > 300:
            title = title[:300]
        
        return title

    def _extract_publication_info_v2(self, text: str, metadata: PaperMetadata):
        """
        提取发表信息 - v2.0高精度版
        改进期刊和会议识别逻辑
        """
        # 1. 首先尝试匹配顶级会议和期刊（最高优先级）
        venue_found = False
        
        for venue_name, pattern in self.TOP_VENUES.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                venue = match.group(0).strip()
                # 清理venue
                venue = re.sub(r'\s+', ' ', venue)
                venue = venue.strip(' ,.')
                
                if len(venue) > 3:
                    metadata.publication_venue = venue
                    print(f"  ✓ 提取到顶级会议/期刊: {venue}")
                    venue_found = True
                    break
            if venue_found:
                break
        
        # 2. 如果没有匹配到顶级会议，尝试通用模式
        if not venue_found:
            general_patterns = [
                # IEEE会议/期刊
                r'IEEE(?:\s+\w+)?\s+(?:Transactions\s+on\s+\w+|Conference\s+on\s+[^,\n]+|Journal\s+of\s+[^,\n]+)',
                # ACM会议
                r'ACM\s+(?:SIG\w+|\w+)\s+(?:\d{4}\s+)?Conference\s+on\s+[^,\n]+',
                # Springer期刊
                r'Springer[^,\n]*?(?:Journal|Proceedings)',
                # Elsevier期刊
                r'Elsevier[^,\n]*?(?:Journal)',
                # arXiv
                r'arXiv(?::\s*\d+\.\d+(?:v\d+)?)?',
                # 通用会议模式
                r'Proceedings\s+of\s+(?:the\s+)?(?:\d{1,4}(?:st|nd|rd|th)?\s+)?([^,\n]{10,100}?(?:Conference|Symposium|Workshop)[^,\n]{0,50})',
                # 通用期刊模式
                r'([A-Z][a-zA-Z\s]{5,80}Journal\s+(?:of|on)\s+[A-Z][^,\n]{0,60})',
                # 中文期刊
                r'([^,\n]{5,40}学报[^,\n]{0,30})',
                r'([^,\n]{5,40}期刊[^,\n]{0,30})',
            ]
            
            for pattern in general_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    venue = match.group(1) if match.lastindex else match.group(0)
                    venue = venue.strip()
                    venue = re.sub(r'\s+', ' ', venue)
                    venue = venue.strip(' ,.')
                    
                    # 过滤掉太短的
                    if len(venue) > 10:
                        metadata.publication_venue = venue
                        print(f"  ✓ 提取到发表信息: {venue}")
                        venue_found = True
                        break
        
        # 3. 从PDF第一页提取年份（通常年份在第一页的会议/期刊信息中）
        try:
            # 获取文本的前2000字符（通常是第一页）
            first_page_text = text[:2000]
            
            # 优先从Copyright或会议信息中提取年份
            year_patterns_priority = [
                r'(?:©|Copyright|\(c\))\s*(?:19|20)\d{2}',
                r'(?:Proceedings|Conference|Journal).{0,100}?(19|20)\d{2}',
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(19|20)\d{2}',
            ]
            
            for pattern in year_patterns_priority:
                match = re.search(pattern, first_page_text, re.IGNORECASE)
                if match:
                    year_str = re.search(r'(19|20)\d{2}', match.group(0))
                    if year_str:
                        year = int(year_str.group(0))
                        if 1990 <= year <= 2035:
                            metadata.year = year
                            print(f"  ✓ 提取到年份: {year}")
                            break
            
            # 如果没找到，再在整个文本中找最常见的年份
            if not metadata.year:
                year_counts = {}
                for match in re.finditer(r'\b(19|20)\d{2}\b', text):
                    year = int(match.group(0))
                    if 1990 <= year <= 2035:
                        year_counts[year] = year_counts.get(year, 0) + 1
                
                if year_counts:
                    # 选择出现频率最高的年份
                    metadata.year = max(year_counts.items(), key=lambda x: x[1])[0]
                    print(f"  ✓ 提取到年份: {metadata.year}")
                    
        except Exception as e:
            print(f"  警告: 年份提取失败: {e}")
        
        # 4. 提取DOI
        doi_patterns = [
            r'(?:DOI|doi)[:\s]*(10\.\d{4,}/[^\s\n\)]+)',
            r'https?://doi\.org/(10\.\d{4,}/[^\s\n\)]+)',
        ]
        
        for pattern in doi_patterns:
            doi_match = re.search(pattern, text, re.IGNORECASE)
            if doi_match:
                metadata.doi = doi_match.group(1).strip()
                print(f"  ✓ 提取到DOI: {metadata.doi}")
                break
        
        metadata.references_count = len(metadata.references)

    def _extract_title_simple(self, text: str) -> str:
        """简单方法提取标题（降级方案）"""
        lines = text.split("\n")
        for i, line in enumerate(lines[:30]):
            line = line.strip()
            # 更严格的标题判断
            if (15 <= len(line) <= 200 and 
                not line.startswith(("Abstract", "摘要", "Introduction", "引言")) and
                not line.isdigit() and
                '@' not in line and
                not line.startswith('http')):
                # 检查是否包含标题关键词
                lower_line = line.lower()
                if not any(stop in lower_line for stop in self.title_stop_words):
                    return self._clean_title(line)
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
        
        return authors[:10]

    def _extract_abstract_enhanced(self, text: str) -> str:
        """提取摘要 - 增强版"""
        patterns = [
            r'(?:Abstract|摘要)\s*:?\s*(.*?)(?=\n\s*(?:Keywords?|关键词|Introduction|引言|1\.|1\s|引言))',
            r'(?:Abstract|ABSTRACT)\s*\n+(.*?)(?=\n\s*(?:Keywords?|KEYWORDS?|Introduction|引言))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
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
                kw_list = re.split(r'[;；,，、·]', keyword_text)
                
                for kw in kw_list:
                    kw_clean = kw.strip()
                    
                    if len(kw_clean) < 2 or len(kw_clean) > 50:
                        continue
                    if '\n' in kw_clean:
                        continue
                    
                    skip_patterns = ['figure', 'table', 'fig.', 'eq.', 'equation', '图', '表', '式']
                    if any(pattern.lower() in kw_clean.lower() for pattern in skip_patterns):
                        continue
                    
                    if re.match(r'^[\d\W]+$', kw_clean):
                        continue
                    
                    words = kw_clean.split()
                    if len(words) > 5:
                        continue
                    
                    keywords.append(kw_clean)
                
                if keywords:
                    break
        
        return keywords[:10]

    def _extract_sections_enhanced(self, text: str) -> Dict[str, str]:
        """提取章节 - 增强版"""
        sections = {}
        section_pattern = r'^([A-Z][a-zA-Z\s]+|[\u4e00-\u9fa5]+)\s*$'
        
        lines = text.split("\n")
        current_section = None
        current_content = []
        
        for line in lines:
            stripped = line.strip()
            
            match = re.match(section_pattern, stripped)
            if match and len(stripped) < 50 and not stripped.endswith('.'):
                if current_section and current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 50:
                        sections[current_section] = content[:4000]
                
                current_section = stripped
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section and current_content:
            content = "\n".join(current_content).strip()
            if len(content) > 50:
                sections[current_section] = content[:4000]
        
        return sections

    def _extract_references_enhanced(self, text: str) -> List[str]:
        """提取参考文献 - 增强版"""
        references = []
        
        ref_pattern = r'(?:References?|参考文献)\s*:?\s*(.*?)(?=\Z|$)'
        match = re.search(ref_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            ref_text = match.group(1)
            ref_entries = re.split(r'\n\s*(?:\[\d+\]|\d+\.)', ref_text)
            
            for ref in ref_entries:
                ref = ref.strip()
                if len(ref) > 20:
                    ref = re.sub(r'\s+', ' ', ref)
                    references.append(ref[:500])
        
        return references[:200]

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

    def _get_page_count(self, pdf_path: Path) -> int:
        """获取PDF页数"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0

    def _extract_tables(self, pdf_path: Path) -> List[str]:
        """提取表格内容"""
        tables = []
        
        if not PDFPLUMBER_AVAILABLE:
            return tables
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            table_text = "\n".join([" | ".join([str(cell or "") for cell in row]) for row in table])
                            if len(table_text) > 20:
                                tables.append(table_text[:2000])
        except Exception as e:
            print(f"  警告: 表格提取失败: {e}")
        
        return tables[:20]

    def _extract_figures(self, pdf_path: Path) -> List[Dict[str, str]]:
        """提取图片信息"""
        figures = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                images = page.get_images()
                for img_index, img in enumerate(images):
                    figures.append({
                        "page": page_num + 1,
                        "index": img_index + 1,
                        "type": "image"
                    })
            
            doc.close()
        except Exception as e:
            print(f"  警告: 图片提取失败: {e}")
        
        return figures[:50]

    def _analyze_section_structure(self, text: str) -> Dict[str, Any]:
        """分析章节结构"""
        structure = {
            "sections": [],
            "abstract_present": False,
            "introduction_present": False,
            "conclusion_present": False,
            "references_present": False
        }
        
        text_lower = text.lower()
        
        structure["abstract_present"] = bool(re.search(r'\babstract\b|\b摘要\b', text_lower))
        structure["introduction_present"] = bool(re.search(r'\bintroduction\b|\b引言\b', text_lower))
        structure["conclusion_present"] = bool(re.search(r'\bconclusion\b|\bconclusions\b|\b结论\b', text_lower))
        structure["references_present"] = bool(re.search(r'\breferences\b|\b参考文献\b', text_lower))
        
        return structure

    def _detect_language(self, text: str) -> str:
        """检测文档语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.1:
            return "zh"
        elif chinese_ratio > 0.01:
            return "mixed"
        else:
            return "en"

    def _load_stopwords(self) -> set:
        """加载停用词"""
        common_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'dare', 'ought', 'used', 'this', 'that', 'these', 'those', 'i',
            'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us',
            'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', '的',
            '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会',
            '着', '没有', '看', '好', '自己', '这', '那', '这些', '那些'
        }
        return common_stopwords
