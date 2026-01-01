"""博士级论文分析器 - 统一入口
整合所有增强功能,提供一站式深度论文分析服务
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from src.config import settings
from src.pdf_parser_enhanced import EnhancedPDFParser, ParsedPaper
from src.prompts_doctoral import (
    get_summary_prompt_doctoral,
    get_keypoint_prompt_doctoral,
    get_topic_prompt_doctoral
)
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


class DoctoralAnalyzer:
    """
    博士级论文分析器

    功能：
    1. 增强PDF解析（表格、参考文献、结构识别）
    2. 博士级摘要生成
    3. 深度要点提取（12+类别）
    4. 主题聚类分析
    5. 研究空白挖掘
    6. 趋势预测
    7. 多论文对比分析
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "glm-4-plus",
        cache_enabled: bool = True
    ):
        """
        初始化分析器

        Args:
            api_key: GLM-4 API密钥
            base_url: API基础URL
            model: 模型名称（默认使用plus以获得最佳质量）
            cache_enabled: 是否启用缓存
        """
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model
        self.cache_enabled = cache_enabled

        if not self.api_key:
            raise ValueError("请设置GLM_API_KEY环境变量")

        # 初始化组件
        self.pdf_parser = EnhancedPDFParser(extract_tables=True, extract_figures=True)
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.3,
            max_tokens=8000,
        )

        # 缓存
        self.cache = {} if cache_enabled else None

        # 统计信息
        self.stats = {
            "papers_analyzed": 0,
            "summaries_generated": 0,
            "keypoints_extracted": 0,
            "gaps_identified": 0,
            "total_tokens_used": 0
        }

    def analyze_single_paper(
        self,
        pdf_path: str,
        tasks: List[str] = None,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        分析单篇论文 - 完整功能

        Args:
            pdf_path: PDF文件路径
            tasks: 要执行的任务列表，默认全部
                - "summary": 生成摘要
                - "keypoints": 提取要点
                - "topic": 主题分析
            save: 是否保存结果
            output_dir: 输出目录

        Returns:
            Dict: 完整的分析结果
        """
        if tasks is None:
            tasks = ["summary", "keypoints", "topic"]

        print(f"\n{'='*80}")
        print(f"博士级论文分析 - {Path(pdf_path).name}")
        print(f"{'='*80}\n")

        results = {
            "filename": Path(pdf_path).name,
            "analysis_time": datetime.now().isoformat(),
            "tasks_performed": tasks
        }

        try:
            # 1. 解析PDF（增强版）
            print("[1/5] 增强PDF解析...")
            paper = self.pdf_parser.parse_pdf(pdf_path)
            results["parsing"] = {
                "page_count": paper.page_count,
                "language": paper.language,
                "title": paper.metadata.title,
                "authors": paper.metadata.authors,
                "abstract_length": len(paper.metadata.abstract),
                "sections_count": len(paper.metadata.sections),
                "references_count": len(paper.metadata.references),
                "tables_count": len(paper.tables),
                "figures_count": len(paper.figures)
            }

            # 2. 生成摘要（博士级）
            if "summary" in tasks:
                print("[2/5] 生成博士级摘要...")
                summary = self._generate_doctoral_summary(paper)
                results["summary"] = summary
                self.stats["summaries_generated"] += 1

            # 3. 提取要点（12+类别深度分析）
            if "keypoints" in tasks:
                print("[3/5] 深度要点提取...")
                keypoints = self._extract_doctoral_keypoints(paper)
                results["keypoints"] = keypoints
                self.stats["keypoints_extracted"] += 1

            # 4. 主题分析
            if "topic" in tasks:
                print("[4/5] 主题分析...")
                topic = self._analyze_topic_doctoral(paper)
                results["topic_analysis"] = topic

            # 5. 保存结果
            if save:
                print("[5/5] 保存结果...")
                self._save_analysis_results(results, output_dir)

            self.stats["papers_analyzed"] += 1

            print(f"\n✓ 分析完成: {paper.metadata.title[:60]}...")

        except Exception as e:
            print(f"\n✗ 分析失败: {e}")
            results["error"] = str(e)

        return results

    def analyze_multiple_papers(
        self,
        pdf_paths: List[str],
        enable_clustering: bool = True,
        enable_gap_mining: bool = True,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        分析多篇论文 - 高级功能

        Args:
            pdf_paths: PDF文件路径列表
            enable_clustering: 是否启用主题聚类
            enable_gap_mining: 是否启用研究空白挖掘
            save: 是否保存结果
            output_dir: 输出目录

        Returns:
            Dict: 多篇论文的综合分析结果
        """
        print(f"\n{'='*80}")
        print(f"博士级多篇论文分析 - {len(pdf_paths)} 篇论文")
        print(f"{'='*80}\n")

        results = {
            "analysis_time": datetime.now().isoformat(),
            "paper_count": len(pdf_paths),
            "features_enabled": {
                "clustering": enable_clustering,
                "gap_mining": enable_gap_mining
            }
        }

        # 1. 批量解析PDF
        print("\n[阶段 1/4] 批量解析PDF...")
        papers = self.pdf_parser.batch_parse(pdf_paths)
        results["papers"] = [
            {
                "filename": p.filename,
                "title": p.metadata.title,
                "authors": p.metadata.authors,
                "year": p.metadata.year
            }
            for p in papers
        ]

        # 2. 单篇论文分析（并行）
        print("\n[阶段 2/4] 并行分析各篇论文...")
        individual_results = self._parallel_analyze(papers)
        results["individual_analyses"] = individual_results

        # 3. 主题聚类
        if enable_clustering and len(papers) >= 2:
            print("\n[阶段 3/4] 主题聚类分析...")
            from src.topic_clustering_enhanced import EnhancedTopicClustering

            clustering = EnhancedTopicClustering(n_clusters=min(5, len(papers)))
            cluster_results = clustering.analyze_with_llm(papers)
            results["clustering"] = cluster_results

        # 4. 研究空白挖掘
        if enable_gap_mining and len(papers) >= 2:
            print("\n[阶段 4/4] 研究空白挖掘...")
            from src.research_gap_miner import ResearchGapMiner

            gap_miner = ResearchGapMiner(model=self.model)
            gap_results = gap_miner.mine_gaps_from_papers(papers, use_llm=True)
            results["research_gaps"] = gap_results
            self.stats["gaps_identified"] += gap_results["summary"]["total_gaps_identified"]

        # 5. 保存综合报告
        if save:
            self._save_multi_paper_report(results, output_dir)

        return results

    def compare_papers(
        self,
        pdf_paths: List[str],
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        对比分析多篇论文

        Args:
            pdf_paths: PDF文件路径列表
            save: 是否保存结果
            output_dir: 输出目录

        Returns:
            Dict: 对比分析结果
        """
        print(f"\n{'='*80}")
        print(f"论文对比分析 - {len(pdf_paths)} 篇论文")
        print(f"{'='*80}\n")

        # 解析所有论文
        papers = self.pdf_parser.batch_parse(pdf_paths)

        comparison = {
            "paper_count": len(papers),
            "comparison_time": datetime.now().isoformat(),
            "papers": [
                {
                    "filename": p.filename,
                    "title": p.metadata.title,
                    "authors": p.metadata.authors,
                    "year": p.metadata.year,
                    "venue": p.metadata.publication_venue
                }
                for p in papers
            ]
        }

        # 对比维度
        comparison["comparisons"] = {
            "methodology": self._compare_methodology(papers),
            "datasets": self._compare_datasets(papers),
            "performance": self._compare_performance(papers),
            "innovations": self._compare_innovations(papers),
            "limitations": self._compare_limitations(papers)
        }

        # 生成对比表
        comparison["comparison_table"] = self._generate_comparison_table(papers)

        # 保存
        if save:
            self._save_comparison_report(comparison, output_dir)

        return comparison

    def _generate_doctoral_summary(self, paper: ParsedPaper) -> Dict[str, str]:
        """生成博士级摘要"""
        # 准备内容
        content = self._prepare_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:800]}"
            for name, content_part in list(paper.metadata.sections.items())[:5]
        ])

        # 构建提示词
        prompt = get_summary_prompt_doctoral(
            title=paper.metadata.title or paper.filename,
            authors=", ".join(paper.metadata.authors[:5]),
            publication=f"{paper.metadata.publication_venue} ({paper.metadata.year})",
            abstract=paper.metadata.abstract or "未提取到摘要",
            keywords=", ".join(paper.metadata.keywords[:10]),
            sections=sections_text,
            content=content
        )

        # 生成摘要
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            summary = response.content

            return {
                "summary_text": summary,
                "word_count": len(summary.split()),
                "language": paper.language
            }
        except Exception as e:
            return {
                "summary_text": f"摘要生成失败: {e}",
                "word_count": 0,
                "language": "unknown"
            }

    def _extract_doctoral_keypoints(self, paper: ParsedPaper) -> Dict[str, List[str]]:
        """提取博士级要点（12+类别）"""
        content = self._prepare_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:800]}"
            for name, content_part in list(paper.metadata.sections.items())[:5]
        ])

        keywords_text = ", ".join(paper.metadata.keywords[:15]) if paper.metadata.keywords else "未提取到关键词"
        references_text = "\n".join(paper.metadata.references[:10]) if paper.metadata.references else "未提取参考文献"

        # 构建提示词
        prompt = get_keypoint_prompt_doctoral(
            title=paper.metadata.title or paper.filename,
            authors=", ".join(paper.metadata.authors[:5]),
            publication=f"{paper.metadata.publication_venue} ({paper.metadata.year})",
            abstract=paper.metadata.abstract or "未提取到摘要",
            keywords=keywords_text,
            sections=sections_text,
            content=content,
            references=references_text[:2000]
        )

        # 生成要点
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content
            keypoints = self._parse_keypoints_json(result)
        except Exception as e:
            print(f"  要点提取失败: {e}")
            keypoints = self._get_empty_keypoints()

        return keypoints

    def _analyze_topic_doctoral(self, paper: ParsedPaper) -> Dict[str, Any]:
        """博士级主题分析"""
        prompt = get_topic_prompt_doctoral(
            title=paper.metadata.title,
            authors=", ".join(paper.metadata.authors),
            abstract=paper.metadata.abstract,
            keywords=", ".join(paper.metadata.keywords),
            content=paper.metadata.abstract[:3000]
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            analysis = response.content

            return {
                "analysis_text": analysis,
                "keywords": paper.metadata.keywords[:10],
                "field": self._infer_field(paper.metadata.keywords)
            }
        except Exception as e:
            return {
                "analysis_text": f"主题分析失败: {e}",
                "keywords": paper.metadata.keywords[:10],
                "field": "unknown"
            }

    def _prepare_content(self, paper: ParsedPaper, max_chars: int = 10000) -> str:
        """准备论文内容"""
        content_parts = []

        if paper.metadata.title:
            content_parts.append(f"标题: {paper.metadata.title}")

        if paper.metadata.abstract:
            content_parts.append(f"摘要: {paper.metadata.abstract}")

        # 添加主要章节
        for section_name, section_content in list(paper.metadata.sections.items())[:5]:
            content_parts.append(f"\n{section_name}:\n{section_content[:1500]}")

        combined = "\n\n".join(content_parts)

        if len(combined) < max_chars:
            remaining = max_chars - len(combined)
            combined += f"\n\n正文片段:\n{paper.full_text[:remaining]}"

        return combined[:max_chars]

    def _parse_keypoints_json(self, response: str) -> Dict[str, List[str]]:
        """解析要点JSON"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            keypoints = json.loads(json_str)

            # 确保所有字段存在
            required_fields = [
                "innovations", "research_gaps", "theoretical_framework",
                "methods", "experimental_design", "datasets",
                "conclusions", "statistical_analysis", "related_work_comparison",
                "reproducibility", "contributions", "limitations"
            ]

            for field in required_fields:
                if field not in keypoints:
                    keypoints[field] = []

            return keypoints

        except Exception as e:
            print(f"  JSON解析失败: {e}")
            return self._get_empty_keypoints()

    def _get_empty_keypoints(self) -> Dict[str, List[str]]:
        """返回空的要点结构"""
        return {
            "innovations": [],
            "research_gaps": [],
            "theoretical_framework": [],
            "methods": [],
            "experimental_design": [],
            "datasets": [],
            "conclusions": [],
            "statistical_analysis": [],
            "related_work_comparison": [],
            "reproducibility": [],
            "contributions": [],
            "limitations": []
        }

    def _parallel_analyze(self, papers: List[ParsedPaper]) -> List[Dict[str, Any]]:
        """并行分析多篇论文"""
        results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_paper = {
                executor.submit(self._analyze_single_paper_cached, paper): paper
                for paper in papers
            }

            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  ✓ 完成: {paper.filename}")
                except Exception as e:
                    print(f"  ✗ 失败: {paper.filename} - {e}")
                    results.append({"error": str(e), "filename": paper.filename})

        return results

    def _analyze_single_paper_cached(self, paper: ParsedPaper) -> Dict[str, Any]:
        """带缓存的单篇论文分析"""
        # 生成缓存键
        cache_key = self._generate_cache_key(paper)

        if self.cache_enabled and cache_key in self.cache:
            print(f"  [缓存命中] {paper.filename}")
            return self.cache[cache_key]

        # 执行分析
        result = {
            "filename": paper.filename,
            "title": paper.metadata.title,
            "summary": self._generate_doctoral_summary(paper),
            "keypoints": self._extract_doctoral_keypoints(paper)
        }

        # 存入缓存
        if self.cache_enabled:
            self.cache[cache_key] = result

        return result

    def _generate_cache_key(self, paper: ParsedPaper) -> str:
        """生成缓存键"""
        content = f"{paper.filename}_{len(paper.full_text)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _infer_field(self, keywords: List[str]) -> str:
        """推断研究领域"""
        keyword_text = " ".join(keywords).lower()

        field_keywords = {
            "Computer Science": ["learning", "algorithm", "network", "data", "computing"],
            "Medicine": ["clinical", "patient", "disease", "treatment", "medical"],
            "Biology": ["gene", "protein", "cell", "molecular", "biological"],
            "Physics": ["quantum", "particle", "energy", "field", "wave"],
            "Chemistry": ["molecule", "reaction", "chemical", "synthesis", "catalyst"]
        }

        for field, kw_list in field_keywords.items():
            if any(kw in keyword_text for kw in kw_list):
                return field

        return "General"

    def _compare_methodology(self, papers: List[ParsedPaper]) -> List[str]:
        """对比方法论"""
        comparisons = []
        for p in papers:
            methods = p.metadata.sections.get("Method", "")
            if methods:
                comparisons.append(f"{p.metadata.title}: 使用方法见Method部分")
        return comparisons

    def _compare_datasets(self, papers: List[ParsedPaper]) -> List[str]:
        """对比数据集"""
        datasets = []
        for p in papers:
            # 简单实现：从摘要中提取数据集信息
            abstract = p.metadata.abstract
            if "dataset" in abstract.lower() or "数据集" in abstract:
                datasets.append(f"{p.metadata.title}: 提到数据集")
        return datasets

    def _compare_performance(self, papers: List[ParsedPaper]) -> List[str]:
        """对比性能"""
        return ["性能对比分析需要进一步细化实现"]

    def _compare_innovations(self, papers: List[ParsedPaper]) -> List[str]:
        """对比创新点"""
        return ["创新点对比分析需要进一步细化实现"]

    def _compare_limitations(self, papers: List[ParsedPaper]) -> List[str]:
        """对比局限性"""
        return ["局限性对比分析需要进一步细化实现"]

    def _generate_comparison_table(self, papers: List[ParsedPaper]) -> str:
        """生成对比表"""
        lines = ["\n论文对比表:\n"]
        lines.append(f"{'序号':<5}{'标题':<40}{'作者':<30}{'年份':<10}")
        lines.append("-" * 95)

        for i, p in enumerate(papers, 1):
            title = p.metadata.title[:37] + "..." if len(p.metadata.title) > 40 else p.metadata.title
            authors = ", ".join(p.metadata.authors[:2]) + ("..." if len(p.metadata.authors) > 2 else "")
            lines.append(f"{i:<5}{title:<40}{authors:<30}{p.metadata.year or 'N/A':<10}")

        return "\n".join(lines)

    def _save_analysis_results(self, results: Dict[str, Any], output_dir: Optional[Path]):
        """保存分析结果"""
        output_dir = output_dir or settings.summary_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(results["filename"]).stem
        save_path = output_dir / f"{filename}_doctoral_analysis.json"

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 结果已保存: {save_path}")

    def _save_multi_paper_report(self, results: Dict[str, Any], output_dir: Optional[Path]):
        """保存多篇论文综合报告"""
        output_dir = output_dir or settings.cluster_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        save_path = output_dir / f"multi_paper_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 综合报告已保存: {save_path}")

    def _save_comparison_report(self, comparison: Dict[str, Any], output_dir: Optional[Path]):
        """保存对比报告"""
        output_dir = output_dir or settings.cluster_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        save_path = output_dir / "paper_comparison_report.json"

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 对比报告已保存: {save_path}")

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()


# 便捷函数
def analyze_paper(
    pdf_path: str,
    api_key: Optional[str] = None,
    model: str = "glm-4-plus"
) -> Dict[str, Any]:
    """
    便捷函数：分析单篇论文

    Args:
        pdf_path: PDF文件路径
        api_key: API密钥
        model: 模型名称

    Returns:
        Dict: 分析结果
    """
    analyzer = DoctoralAnalyzer(api_key=api_key, model=model)
    return analyzer.analyze_single_paper(pdf_path)


def analyze_papers(
    pdf_paths: List[str],
    api_key: Optional[str] = None,
    model: str = "glm-4-plus"
) -> Dict[str, Any]:
    """
    便捷函数：分析多篇论文

    Args:
        pdf_paths: PDF文件路径列表
        api_key: API密钥
        model: 模型名称

    Returns:
        Dict: 分析结果
    """
    analyzer = DoctoralAnalyzer(api_key=api_key, model=model)
    return analyzer.analyze_multiple_papers(pdf_paths)
