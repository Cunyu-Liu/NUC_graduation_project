"""增强版文献解析模块 - 深度解析PDF文档结构 - v3.0高精度版"""
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
    """增强版PDF文档解析器 - v3.0高精度版"""

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

        # 标题检测的关键词过滤列表 - 扩展版本
        self.title_stop_words = {
            'abstract', 'introduction', 'related work', 'background',
            'method', 'methodology', 'experiment', 'experiments',
            'results', 'discussion', 'conclusion', 'conclusions',
            'references', 'acknowledgments', 'acknowledgement',
            'figure', 'table', 'appendix', 'author', 'authors',
            '摘要', '引言', '方法', '实验', '结果', '讨论',
            '结论', '参考文献', '致谢', '图', '表', 'preprint',
            'arxiv', 'submitted', 'published', 'accepted'
        }
        
        # 标题前缀/后缀模式 - v3.3: 改进，避免匹配标题开头的数字
        self.title_prefix_patterns = [
            r'^\d+\s*\.\s+',  # v3.3: 章节编号（数字+点+空格）
            r'^Fig\.?\s*\d+',  # 图编号
            r'^Figure\s*\d+',  # Figure编号
            r'^Table\s*\d+',  # 表编号
            r'^\[\d+\]\s*',  # v3.3: 方括号数字编号 [1]
            r'^\(\d+\)\s*',  # 括号数字
            r'^\d+\s+',  # v3.3: 数字+空格（章节编号）
        ]

    def parse_pdf(self, pdf_path: str) -> ParsedPaper:
        """
        解析PDF文档 - 增强版 v3.0
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

        # 提取元数据（增强版 v3.0）
        metadata = self._extract_metadata_v3(pdf_path, full_text)

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
        """提取PDF完整文本 - 增强版 v3.0"""
        text_parts = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]

                # 过滤页眉页脚 - v3.0优化：不过滤顶部5%，保留标题区域
                page_height = page.rect.height
                filtered_blocks = []

                for block in blocks:
                    if "lines" not in block:
                        continue

                    bbox = block["bbox"]
                    block_height = bbox[3] - bbox[1]

                    # v3.0: 只过滤极顶部（可能是页眉）和底部（页码）
                    # 保留顶部区域以捕获标题
                    if bbox[1] < page_height * 0.02:  # 只过滤最顶部2%
                        continue
                    if bbox[3] > page_height * 0.95:  # 过滤底部5%
                        continue

                    # 过滤高度很小的块
                    if block_height < 5:
                        continue

                    filtered_blocks.append(block)

                # 提取文本并保留位置信息
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

            # 移除纯页码
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

    def _extract_metadata_v3(self, pdf_path: Path, text: str) -> PaperMetadata:
        """
        提取元数据 - v3.0高精度版
        重写标题和年份提取逻辑，大幅提高识别精度
        """
        metadata = PaperMetadata()
        filename_hint = self._extract_year_from_filename(pdf_path.name)

        # 首先尝试从PDF元数据中提取
        try:
            doc = fitz.open(pdf_path)
            pdf_metadata = doc.metadata

            # 提取标题 - 优先使用PDF元数据
            if pdf_metadata.get('title') and len(pdf_metadata['title']) > 5:
                metadata.title = self._clean_title(pdf_metadata['title'].strip())
                print(f"  ✓ 从PDF元数据获取标题: {metadata.title[:50]}...")

            # 提取作者
            if pdf_metadata.get('author'):
                authors = self._parse_authors(pdf_metadata['author'])
                if authors:
                    metadata.authors = authors[:10]

            # 提取关键词
            if pdf_metadata.get('keywords'):
                keywords = [kw.strip() for kw in pdf_metadata['keywords'].split(',') if kw.strip()]
                if keywords:
                    metadata.keywords = keywords[:10]
            
            # v3.0: 尝试从PDF元数据中提取年份
            if pdf_metadata.get('creationDate') or pdf_metadata.get('modDate'):
                date_str = pdf_metadata.get('creationDate') or pdf_metadata.get('modDate')
                year_match = re.search(r'(19|20)\d{2}', date_str)
                if year_match:
                    year = int(year_match.group(0))
                    if 1990 <= year <= 2035:
                        metadata.year = year
                        print(f"  ✓ 从PDF元数据获取年份: {year}")

            doc.close()
        except Exception as e:
            print(f"  警告: 无法读取PDF元数据: {e}")

        # v3.0: 高精度方法提取标题（如果元数据中没有）
        if not metadata.title or len(metadata.title) < 10:
            metadata.title = self._extract_title_precise_v3(pdf_path, text)

        # v3.0: 提取发表信息（高精度，带文件名提示）
        self._extract_publication_info_v3(text, metadata, filename_hint)

        # 提取摘要
        metadata.abstract = self._extract_abstract_enhanced(text)

        # 提取关键词（如果元数据中没有）
        if not metadata.keywords:
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

    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """v3.0: 从文件名中提取年份提示"""
        # 匹配常见的文件名年份模式
        patterns = [
            r'(?:19|20)\d{2}',  # 基本年份格式
            r'\(?(19|20)\d{2}\)?',  # 带括号的年份
            r'_(19|20)\d{2}_',  # 下划线分隔的年份
            r'-(19|20)\d{2}-',  # 横线分隔的年份
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, filename)
            for match in matches:
                year_str = match if len(match) == 4 else '20' + match if len(match) == 2 else match
                if len(year_str) == 4:
                    try:
                        year = int(year_str)
                        if 1990 <= year <= 2035:
                            return year
                    except ValueError:
                        continue
        return None

    def _extract_title_precise_v3(self, pdf_path: Path, text: str) -> str:
        """
        v3.1: 高精度标题提取方法
        使用多行合并、字体分析和位置信息综合判断
        改进：检测并跳过ResearchGate/Academia.edu等元数据页面
        """
        try:
            doc = fitz.open(pdf_path)
            
            # 分析前两页
            title_candidates = []
            
            for page_num in range(min(2, len(doc))):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                # v3.1: 检测是否是ResearchGate/Academia.edu等元数据页面
                page_text_sample = ""
                for block in blocks[:10]:  # 检查前10个块
                    if "lines" in block:
                        page_text_sample += "".join([span["text"] for line in block["lines"] for span in line["spans"]])
                
                is_metadata_page = self._is_metadata_page(page_text_sample)
                if is_metadata_page:
                    print(f"  ℹ️  第{page_num+1}页是元数据页，跳过")
                    continue
                
                # 收集所有文本块及其属性
                text_blocks = []
                for block in blocks:
                    if "lines" not in block:
                        continue
                    
                    for line in block["lines"]:
                        line_text = "".join([span["text"] for span in line["spans"]]).strip()
                        if not line_text:
                            continue
                            
                        # 计算字体属性
                        font_sizes = [span["size"] for span in line["spans"]]
                        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                        max_font_size = max(font_sizes) if font_sizes else 12
                        
                        # 获取位置
                        bbox = line["bbox"]
                        page_height = page.rect.height
                        y_position = bbox[1]
                        
                        # 检测是否粗体
                        is_bold = any(span.get("flags", 0) & 2 for span in line["spans"])
                        
                        text_blocks.append({
                            "text": line_text,
                            "avg_size": avg_font_size,
                            "max_size": max_font_size,
                            "y": y_position,
                            "is_bold": is_bold,
                            "bbox": bbox
                        })
                
                # 按垂直位置排序
                text_blocks.sort(key=lambda x: x["y"])
                
                # v3.1: 尝试合并多行标题
                merged_candidates = self._merge_title_lines(text_blocks, page_height, page_num)
                title_candidates.extend(merged_candidates)
            
            doc.close()
            
            # 排序并选择最佳标题
            if title_candidates:
                # 按得分排序
                title_candidates.sort(key=lambda x: x["score"], reverse=True)
                
                # v3.1: 过滤掉可能的作者行
                filtered_candidates = []
                for c in title_candidates:
                    text = c["text"]
                    # 排除明显的作者行特征
                    if self._is_likely_author_line(text):
                        continue
                    filtered_candidates.append(c)
                
                # 如果有过滤后的候选，使用它们；否则使用原始候选
                candidates_to_use = filtered_candidates if filtered_candidates else title_candidates
                
                # 优先选择第一页的高分候选
                first_page_candidates = [c for c in candidates_to_use if c["page"] == 0]
                if first_page_candidates and first_page_candidates[0]["score"] >= 50:
                    best_title = first_page_candidates[0]["text"]
                elif candidates_to_use:
                    best_title = candidates_to_use[0]["text"]
                else:
                    best_title = title_candidates[0]["text"]
                
                # 清理标题
                best_title = self._clean_title(best_title)
                
                if best_title and len(best_title) >= 10:
                    print(f"  ✓ 提取到标题: {best_title[:60]}...")
                    return best_title
                    
        except Exception as e:
            print(f"  警告: 高精度标题提取失败: {e}")
        
        # 降级方案
        return self._extract_title_simple(text)

    def _is_metadata_page(self, text_sample: str) -> bool:
        """
        v3.1: 检测是否是ResearchGate/Academia.edu等元数据页面
        """
        metadata_indicators = [
            'researchgate.net',
            'see discussions, stats',
            'author profiles',
            'publications',
            'citations',
            'reads',
            'academia.edu',
            'download file',
            'request full-text',
            'see profile',
        ]
        
        text_lower = text_sample.lower()
        indicator_count = sum(1 for indicator in metadata_indicators if indicator in text_lower)
        
        # 如果包含3个或以上指标，认为是元数据页面
        return indicator_count >= 3

    def _is_likely_author_line(self, text: str) -> bool:
        """
        v3.3: 检测文本是否可能是作者行而非标题
        """
        # v3.3: 首先检查明显的非标题特征
        # email地址
        if re.search(r'\S+@\S+\.\S+', text):
            return True
        
        # E-mail标签
        if re.search(r'\bE-?mail\b', text, re.IGNORECASE):
            return True
        
        # v3.3: 作者标记符号
        if '#,' in text or ',#' in text:  # 作者标记如 "Author1,#"
            return True
        if re.search(r'\w+\d+\s*,\s*#', text):  # "Author1,#"
            return True
        if re.search(r'\*\s*Equal\s+contribution', text, re.IGNORECASE):
            return True
        
        # 作者行特征
        author_indicators = [
            r'\w+\s+\w+\s*,\s*\w+\s+\w+',  # 多个作者名用逗号分隔
            r'\w+\s+\w+\s+and\s+\w+\s+\w+',  # 作者名用and连接
            r'University|Institute|College|Department|Laboratory|Lab',  # 机构名
            r'\d+\s+authors?\s*,\s*including',  # "15 authors, including"
            r'Corresponding\s+authors?',  # "Corresponding authors"
            r'#\s*Equivalent\s+authors?',  # 等效作者
            r'^\s*\d+\s*$',  # 单独的数字（作者标记）
        ]
        
        for pattern in author_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # v3.3: 检查是否是单独的人名（2-4个词，都是大写开头的常见人名）
        words = text.split()
        if 1 <= len(words) <= 4:
            # 检查是否符合 "名 姓" 或 "名 中名 姓" 模式
            # 移除可能的标记符号
            clean_words = [w.rstrip('*,#') for w in words]
            all_capitalized = all(w and len(w) > 0 and w[0].isupper() for w in clean_words if w)
            
            no_title_words = not any(tw in text.lower() for tw in 
                ['for', 'with', 'using', 'via', 'based', 'toward', 'approach', 
                 'method', 'algorithm', 'learning', 'network', 'model', 'system',
                 'analysis', 'prediction', 'generation', 'detection'])
            # 不包含标点符号（标题通常包含冒号或破折号）
            no_punctuation = not any(c in text for c in ':：-—–')
            
            if all_capitalized and no_title_words and no_punctuation:
                # 进一步检查：是否像人名（常见的英文名字特征）
                # 如果词很短，可能是人名
                avg_len = sum(len(w.rstrip('*,#')) for w in words) / len(words)
                if avg_len <= 8 and len(words) >= 2:
                    return True
        
        # 检查是否主要是人名（大写开头的短词）
        if len(words) >= 3:
            capitalized_short_words = [w for w in words if len(w) <= 15 and w and w[0].isupper()]
            # 如果超过70%是大写开头的短词，可能是作者列表
            if len(words) > 0 and len(capitalized_short_words) / len(words) > 0.7:
                # 进一步检查是否包含标题特征词
                title_words = ['for', 'with', 'using', 'via', 'based', 'toward', 'approach', 
                              'method', 'algorithm', 'learning', 'network', 'model']
                if not any(tw in text.lower() for tw in title_words):
                    return True
        
        return False

    def _merge_title_lines(self, text_blocks: List[Dict], page_height: float, page_num: int = 0) -> List[Dict]:
        """
        v3.3: 合并可能的多行标题
        改进：更好地处理字体大小变化，更早过滤作者行，更智能的合并
        """
        candidates = []
        i = 0
        
        # v3.1: 找到页面上的最大字体大小（用于相对评分）
        max_font_size = max((b["avg_size"] for b in text_blocks if "avg_size" in b), default=12)
        
        # v3.2: 跟踪已经处理过的行
        processed = set()
        
        while i < len(text_blocks):
            if i in processed:
                i += 1
                continue
                
            block = text_blocks[i]
            text = block["text"]
            
            # 基础过滤
            if len(text) < 5 or len(text) > 200:
                i += 1
                continue
            
            # v3.1: 更早排除作者行
            if self._is_likely_author_line(text):
                processed.add(i)
                i += 1
                continue
            
            # 排除明显的非标题
            lower_text = text.lower()
            if any(stop_word in lower_text for stop_word in self.title_stop_words):
                processed.add(i)
                i += 1
                continue
            
            # 排除纯数字、URL、email
            if re.match(r'^[\d\s\.]+$', text):
                processed.add(i)
                i += 1
                continue
            if text.startswith(('http://', 'https://', 'www.')):
                processed.add(i)
                i += 1
                continue
            if '@' in text:
                processed.add(i)
                i += 1
                continue
            
            # 排除章节编号等
            if any(re.match(p, text, re.IGNORECASE) for p in self.title_prefix_patterns):
                processed.add(i)
                i += 1
                continue
            
            # 计算当前行的得分
            score = self._calculate_title_score(block, page_height, max_font_size)
            
            # v3.1: 字体太小的直接跳过
            if block["avg_size"] < max_font_size * 0.8 and score < 40:
                processed.add(i)
                i += 1
                continue
            
            # v3.2: 尝试与下一行合并（如果可能是多行标题）
            merged_text = text
            merged_score = score
            j = i + 1
            
            while j < len(text_blocks):
                next_block = text_blocks[j]
                next_text = next_block["text"]
                
                # v3.2: 如果下一行是作者行或email，不要合并
                if self._is_likely_author_line(next_text):
                    break
                if '@' in next_text or 'E-mail' in next_text:
                    break
                if 'Corresponding' in next_text:
                    break
                
                # 检查是否应该合并
                # 条件：相邻、字体大小相似、下一行不是明显的新段落
                y_gap = next_block["y"] - block["y"]
                size_diff = abs(next_block["avg_size"] - block["avg_size"])
                
                # v3.2: 放宽合并条件
                should_merge = (
                    y_gap < 50 and  # v3.2: 增加垂直距离阈值
                    size_diff < 3 and  # v3.2: 稍微放宽字体大小差异
                    len(next_text) < 100 and  # 下一行不太长
                    not next_text.endswith(('.', '?', '!')) and  # 不是完整句子结尾
                    not any(stop in next_text.lower() for stop in self.title_stop_words) and
                    not any(re.match(p, next_text, re.IGNORECASE) for p in self.title_prefix_patterns)
                )
                
                if should_merge:
                    merged_text += " " + next_text
                    merged_score += self._calculate_title_score(next_block, page_height, max_font_size) * 0.8
                    processed.add(j)
                    j += 1
                else:
                    break
            
            # v3.2: 只考虑合理的合并结果
            if 15 <= len(merged_text) <= 300 and not self._is_likely_author_line(merged_text):
                candidates.append({
                    "text": merged_text,
                    "score": merged_score,
                    "page": page_num,  # v3.3: 使用实际的页面号
                    "y": block["y"]
                })
            
            processed.add(i)
            i = j if j > i + 1 else i + 1
        
        return candidates

    def _calculate_title_score(self, block: Dict, page_height: float, max_font_size: float = 12) -> float:
        """v3.1: 计算标题得分"""
        text = block["text"]
        score = 0
        font_size = block["avg_size"]
        
        # v3.1: 1. 字体大小得分（最重要）- 使用相对评分
        if max_font_size > 12:
            relative_size = font_size / max_font_size
            if relative_size >= 0.95:  # 最大或接近最大字体
                score += 70
            elif relative_size >= 0.85:
                score += 50
            elif relative_size >= 0.75:
                score += 30
            elif font_size >= 14:  # 绝对大小也考虑
                score += 25
            elif font_size >= 12:
                score += 10
        else:
            # 原始绝对评分（用于字体较小的PDF）
            if font_size >= 18:
                score += 60
            elif font_size >= 16:
                score += 45
            elif font_size >= 14:
                score += 30
            elif font_size >= 12:
                score += 15
        
        # 粗体额外加分
        if block["is_bold"]:
            score += 10
        
        # v3.1: 2. 位置得分（改进）
        y_ratio = block["y"] / page_height
        if 0.05 <= y_ratio <= 0.20:  # 理想区域：顶部5%-20%
            score += 30
        elif 0.20 < y_ratio <= 0.30:  # 可接受区域
            score += 20
        elif 0.30 < y_ratio <= 0.40:  # 边缘区域
            score += 10
        elif y_ratio < 0.05:  # 太靠上，可能是页眉
            score -= 20
        elif y_ratio > 0.50:  # 太靠下
            score -= 40
        
        # v3.1: 3. 长度得分（调整）
        length = len(text)
        if 40 <= length <= 150:  # 理想长度
            score += 20
        elif 20 <= length < 40:
            score += 10
        elif 15 <= length < 20:
            score += 5
        elif length > 200:  # 太长
            score -= 25
        
        # 4. 首字母大写特征（英文标题）
        words = text.split()
        if words:
            capitalized = sum(1 for w in words if w and w[0].isupper())
            if capitalized / len(words) > 0.6:
                score += 10
        
        # 5. 包含学术标题特征
        if ':' in text or '：' in text:  # 副标题
            score += 10
        if '-' in text and len(text) > 30:  # 带连接词的标题
            score += 5
        
        # v3.1: 标题关键词加分
        title_keywords = ['based', 'using', 'via', 'with', 'for', 'toward', 'approach', 
                         'method', 'algorithm', 'learning', 'network', 'model', 'system',
                         'generation', 'prediction', 'analysis', 'detection', 'recognition']
        if any(kw in text.lower() for kw in title_keywords):
            score += 8
        
        # 6. 中文论文标题特征
        if re.search(r'[\u4e00-\u9fa5]', text):
            score += 15
        
        # v3.1: 7. 减分：包含特定非标题模式（增强）
        if re.search(r'\b(University|Institute|College|Department|Laboratory|Lab)\b', text, re.IGNORECASE):
            score -= 50  # 可能是机构名
        if re.search(r'\b(email|E-mail|tel|phone|fax|address)\b', text, re.IGNORECASE):
            score -= 50  # 联系信息
        if re.search(r'\b(corresponding|author|affiliation)\b', text, re.IGNORECASE):
            score -= 30  # 作者相关信息
        if '#' in text and ',' in text:  # 作者标记
            score -= 40
        
        return score

    def _clean_title(self, title: str) -> str:
        """清理标题文本 - v3.3增强"""
        if not title:
            return ""
        
        # 合并多余空格
        title = re.sub(r'\s+', ' ', title)
        
        # 去除首尾标点和空格
        title = title.strip(' ,.，。：:;；!！?？')
        
        # v3.3: 移除常见的错误前缀（改进，避免匹配标题开头的数字）
        prefixes_to_remove = [
            r'^\d+\s*\.\s+',  # v3.3: 章节编号（数字+点+空格）
            r'^\[\d+\]\s*',  # v3.3: 方括号数字 [1]
            r'^Fig\.?\s*\d+[:\.\s]*',
            r'^Figure\s*\d+[:\.\s]*',
            r'^Table\s*\d+[:\.\s]*',
        ]
        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)
        
        # 限制长度
        if len(title) > 300:
            title = title[:300]
        
        return title.strip()

    def _extract_publication_info_v3(self, text: str, metadata: PaperMetadata, filename_hint: Optional[int] = None):
        """
        v3.0: 提取发表信息 - 高精度版
        改进期刊和会议识别逻辑，优化年份提取
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
        
        # 3. v3.0: 改进的年份提取
        self._extract_year_v3(text, metadata, filename_hint)
        
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

    def _extract_year_v3(self, text: str, metadata: PaperMetadata, filename_hint: Optional[int] = None):
        """
        v3.0: 改进的年份提取方法
        优先级：头部版权信息 > 会议/期刊信息 > 文件名 > 其他来源
        """
        # 获取文本的前3000字符（通常是第一页）
        first_page_text = text[:3000]
        
        # v3.0: 优先级1 - 版权/Copyright信息（最可靠）
        copyright_patterns = [
            r'(?:©|Copyright|\(c\))\s*["\']?(\d{4})["\']?',
            r'(?:©|Copyright|\(c\))\s*\d{4}["\']?\s*[-–]\s*["\']?(\d{4})["\']?',
            r'(?:©|Copyright|\(c\))\s*\d{4}\s+\w+\s+et\s+al\.?',
        ]
        
        for pattern in copyright_patterns:
            match = re.search(pattern, first_page_text, re.IGNORECASE)
            if match:
                year_str = match.group(1) if match.lastindex else re.search(r'(\d{4})', match.group(0))
                if year_str:
                    try:
                        year = int(year_str) if isinstance(year_str, str) else int(year_str.group(0))
                        if 1990 <= year <= 2035:
                            metadata.year = year
                            print(f"  ✓ 从Copyright提取到年份: {year}")
                            return
                    except (ValueError, AttributeError):
                        continue
        
        # v3.0: 优先级2 - 会议/期刊头部信息中的年份
        venue_year_patterns = [
            r'(?:Proceedings|Conference|Journal|Workshop|Symposium).{0,150}?(19|20)(\d{2})[^\d]',
            r'(?:Published|Accepted)\s+(?:in\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(\d{4})',
            r'\b(20\d{2})\b.{0,50}?(?:Proceedings|Conference|Journal)',
            r'\(?(\d{4})\)?\s+(?:IEEE|ACM|Springer|Elsevier)',
        ]
        
        for pattern in venue_year_patterns:
            match = re.search(pattern, first_page_text, re.IGNORECASE | re.DOTALL)
            if match:
                year_str = match.group(1) + match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                if len(year_str) == 2:  # 处理2位数年份
                    year_str = '20' + year_str
                try:
                    year = int(year_str)
                    if 1990 <= year <= 2035:
                        metadata.year = year
                        print(f"  ✓ 从会议/期刊信息提取到年份: {year}")
                        return
                except ValueError:
                    continue
        
        # v3.0: 优先级3 - 文件名中的年份提示
        if filename_hint and 1990 <= filename_hint <= 2035:
            metadata.year = filename_hint
            print(f"  ✓ 从文件名提取到年份: {filename_hint}")
            return
        
        # v3.0: 优先级4 - arXiv ID中的年份
        arxiv_pattern = r'arXiv[\s:]?(\d{2})(\d{2})\.\d+'
        arxiv_match = re.search(arxiv_pattern, first_page_text, re.IGNORECASE)
        if arxiv_match:
            year_prefix = arxiv_match.group(1)
            month = arxiv_match.group(2)
            try:
                year = 2000 + int(year_prefix)
                if 1990 <= year <= 2035 and 1 <= int(month) <= 12:
                    metadata.year = year
                    print(f"  ✓ 从arXiv ID提取到年份: {year}")
                    return
            except ValueError:
                pass
        
        # v3.0: 优先级5 - 在References之前的最近年份（引用年份通常是过去年份）
        # 获取References之前的文本
        refs_match = re.search(r'(?:References|参考文献)', text, re.IGNORECASE)
        pre_refs_text = text[:refs_match.start()] if refs_match else text[:5000]
        
        year_counts = {}
        for match in re.finditer(r'\b(19|20)(\d{2})\b', pre_refs_text):
            year_str = match.group(1) + match.group(2)
            year = int(year_str)
            if 1990 <= year <= 2035:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        if year_counts:
            # v3.0: 选择最近且出现频率合理的年份
            # 优先选择2015年之后的年份（现代论文）
            recent_years = {y: c for y, c in year_counts.items() if y >= 2015}
            
            if recent_years:
                # 在最近的年份中选择出现频率最高的
                best_year = max(recent_years.items(), key=lambda x: x[1])[0]
                metadata.year = best_year
                print(f"  ✓ 从文本分析提取到年份: {best_year}")
                return
            else:
                # 如果没有2015年之后的，选择出现频率最高的
                best_year = max(year_counts.items(), key=lambda x: x[1])[0]
                metadata.year = best_year
                print(f"  ✓ 从文本分析提取到年份: {best_year}")
                return
        
        print("  ⚠️  未能提取到年份")

    def _extract_title_simple(self, text: str) -> str:
        """简单方法提取标题（降级方案）- v3.3改进"""
        lines = text.split("\n")
        
        # v3.3: 收集前50行的候选
        candidates = []
        for i, line in enumerate(lines[:50]):
            line = line.strip()
            
            # 基础过滤
            if len(line) < 15 or len(line) > 200:
                continue
            
            # v3.3: 排除作者行
            if self._is_likely_author_line(line):
                continue
            
            lower_line = line.lower()
            
            # 排除常见的非标题
            if any(stop in lower_line for stop in self.title_stop_words):
                continue
            if line.isdigit():
                continue
            if '@' in line:
                continue
            if line.startswith(('http://', 'https://', 'www.')):
                continue
            if any(re.match(p, line, re.IGNORECASE) for p in self.title_prefix_patterns):
                continue
            
            # 评分
            score = 0
            if 40 <= len(line) <= 150:
                score += 20
            elif 30 <= len(line) < 40:
                score += 15
            elif 20 <= len(line) < 30:
                score += 10
            
            if ':' in line or '：' in line:
                score += 10
            if re.search(r'[\u4e00-\u9fa5]', line):
                score += 15
            
            # v3.3: 标题关键词加分
            title_keywords = ['based', 'using', 'via', 'with', 'for', 'toward', 'approach', 
                             'method', 'algorithm', 'learning', 'network', 'model', 'system']
            if any(kw in line.lower() for kw in title_keywords):
                score += 8
            
            # 位置权重（越靠前越好）
            score += max(0, 30 - i)
            
            candidates.append((line, score))
        
        if candidates:
            # 选择得分最高的
            candidates.sort(key=lambda x: x[1], reverse=True)
            return self._clean_title(candidates[0][0])
        
        return ""

    def _parse_authors(self, author_text: str) -> List[str]:
        """解析作者信息 - v3.0改进"""
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
        
        # v3.0: 过滤掉可能的非人名
        filtered_authors = []
        for author in authors:
            # 过滤掉机构名
            if re.search(r'\b(University|Institute|College|Department|Lab|Laboratory)\b', author, re.IGNORECASE):
                continue
            # 过滤掉太长的（可能是句子）
            if len(author) > 100:
                continue
            filtered_authors.append(author)
        
        return filtered_authors[:10] if filtered_authors else authors[:10]

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
        
        ref_pattern = r'(?:References?|参考文献)\s*:?\s*(.*)(?=\Z|$)'
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


# 批量解析功能
class BatchPDFParser:
    """批量PDF解析器"""
    
    def __init__(self, parser: Optional[EnhancedPDFParser] = None):
        self.parser = parser or EnhancedPDFParser()
    
    def parse_directory(self, directory: str, pattern: str = "*.pdf") -> List[ParsedPaper]:
        """解析目录中的所有PDF文件"""
        directory = Path(directory)
        pdf_files = list(directory.glob(pattern))
        
        results = []
        for pdf_file in pdf_files:
            try:
                paper = self.parser.parse_pdf(str(pdf_file))
                results.append(paper)
            except Exception as e:
                print(f"  ❌ 解析失败 {pdf_file.name}: {e}")
        
        return results
    
    def parse_files(self, file_paths: List[str]) -> Tuple[List[ParsedPaper], List[Tuple[str, str]]]:
        """解析多个PDF文件，返回成功和失败的结果"""
        success = []
        failed = []
        
        for path in file_paths:
            try:
                paper = self.parser.parse_pdf(path)
                success.append(paper)
            except Exception as e:
                failed.append((path, str(e)))
        
        return success, failed


# 兼容性保持
PDFParser = EnhancedPDFParser


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        parser = EnhancedPDFParser()
        
        try:
            paper = parser.parse_pdf(pdf_path)
            print("\n" + "="*60)
            print("解析结果:")
            print(f"  标题: {paper.metadata.title}")
            print(f"  作者: {', '.join(paper.metadata.authors)}")
            print(f"  年份: {paper.metadata.year}")
            print(f"  期刊/会议: {paper.metadata.publication_venue}")
            print(f"  DOI: {paper.metadata.doi}")
            print(f"  页数: {paper.page_count}")
            print(f"  语言: {paper.language}")
            print(f"  摘要长度: {len(paper.metadata.abstract)} 字符")
            print(f"  关键词: {', '.join(paper.metadata.keywords[:5])}")
            print("="*60)
        except Exception as e:
            print(f"解析失败: {e}")
    else:
        print("用法: python pdf_parser_enhanced.py <pdf文件路径>")
