"""研究空白挖掘模块 - 自动识别潜在研究方向和机会"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from collections import Counter, defaultdict
import re

from src.config import settings
from src.pdf_parser import ParsedPaper
from src.prompts_doctoral import get_gap_mining_prompt


@dataclass
class ResearchGap:
    """研究空白"""
    gap_type: str  # methodological, theoretical, data, application, evaluation
    description: str
    importance: str  # high, medium, low
    difficulty: str  # low, medium, high
    potential_approach: str
    expected_impact: str
    related_papers: List[str]
    confidence: float  # 0-1


class ResearchGapMiner:
    """研究空白挖掘器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        初始化研究空白挖掘器

        Args:
            api_key: GLM-4 API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
        """
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else 0.3  # 降低温度以获得更确定的输出

        if not self.api_key:
            raise ValueError("请设置GLM_API_KEY环境变量")

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=4000,
        )

    def mine_gaps_from_papers(
        self,
        papers: List[ParsedPaper],
        use_llm: bool = True,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        从多篇论文中挖掘研究空白

        Args:
            papers: 论文列表
            use_llm: 是否使用LLM深度分析
            save: 是否保存结果
            output_dir: 输出目录

        Returns:
            Dict: 研究空白分析结果
        """
        print(f"\n{'='*80}")
        print(f"研究空白挖掘 - 分析 {len(papers)} 篇论文")
        print(f"{'='*80}\n")

        # 基于规则的初步分析
        rule_based_gaps = self._rule_based_gap_mining(papers)

        # 基于统计的关键词分析
        keyword_gaps = self._keyword_based_gap_mining(papers)

        # 基于参考文献的引文分析
        citation_gaps = self._citation_based_gap_mining(papers)

        # 使用LLM深度挖掘
        llm_gaps = []
        if use_llm and len(papers) >= 2:
            llm_gaps = self._llm_based_gap_mining(papers)

        # 合并和排序空白
        all_gaps = {
            "rule_based": rule_based_gaps,
            "keyword_based": keyword_gaps,
            "citation_based": citation_gaps,
            "llm_deep_analysis": llm_gaps
        }

        # 生成综合报告
        report = self._generate_gap_report(all_gaps, papers)

        # 保存结果
        if save:
            self._save_gap_report(report, output_dir)

        return report

    def _rule_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, List[str]]:
        """
        基于规则的空白挖掘

        规则：
        1. 检查"局限性"和"未来工作"部分
        2. 识别高频关键词但缺少的内容
        3. 分析方法论的多样性（多样性低 = 存在空白）
        """
        gaps = {
            "methodological": [],
            "theoretical": [],
            "data": [],
            "application": [],
            "evaluation": []
        }

        # 收集所有论文的局限性
        limitations_text = []
        for paper in papers:
            # 从结论部分提取局限性
            if "Conclusion" in paper.metadata.sections or "结论" in paper.metadata.sections:
                conclusion = paper.metadata.sections.get("Conclusion", "") or paper.metadata.sections.get("结论", "")
                limitations_text.append(conclusion)

            # 从摘要中提取局限性关键词
            if "limit" in paper.metadata.abstract.lower() or "局限" in paper.metadata.abstract:
                limitations_text.append(paper.metadata.abstract)

        # 分析局限性文本，提取空白
        all_text = " ".join(limitations_text)

        # 方法论空白模式
        method_patterns = [
            r'(?:目前|当前|现有)(?:方法|技术|算法)(?:无法|难以|不能)(?:处理|解决|应对)(.{10,50})",
            r'(?:需要|缺乏|缺少)(?:.{10,50})(?:方法|技术|算法)',
            r'(?:computational|time|space) (?:complexity|cost|overhead) (?:is|remains|becomes) (?:too )?(?:high|expensive|prohibitive)',
        ]

        for pattern in method_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5 and match not in gaps["methodological"]:
                    gaps["methodological"].append({
                        "description": f"方法局限: {match}",
                        "source": "limitation_analysis"
                    })

        # 数据空白模式
        data_patterns = [
            r'(?:缺乏|缺少|不足)(?:.{10,40})(?:数据|dataset|data)',
            r'(?:data|dataset) (?:scarcity|lack|unavailability)',
        ]

        for pattern in data_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5:
                    gaps["data"].append({
                        "description": f"数据局限: {match}",
                        "source": "limitation_analysis"
                    })

        # 应用空白模式
        app_patterns = [
            r'(?:尚未|未|有待)(?:.{10,40})(?:应用|部署|implement)',
            r'(?:real-world|practical) (?:application|deployment|use) (?:is|remains) (?:challenging|limited)',
        ]

        for pattern in app_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5:
                    gaps["application"].append({
                        "description": f"应用局限: {match}",
                        "source": "limitation_analysis"
                    })

        return gaps

    def _keyword_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, Any]:
        """
        基于关键词的空白挖掘

        思路：
        1. 分析所有关键词的频率分布
        2. 识别"稀有但重要"的关键词（可能是新兴方向）
        3. 识别"高频但缺乏"的内容（应该存在但实际不多的）
        """
        # 收集所有关键词
        all_keywords = []
        paper_keywords = {}

        for paper in papers:
            keywords = paper.metadata.keywords
            paper_keywords[paper.filename] = keywords
            all_keywords.extend(keywords)

        # 统计词频
        keyword_freq = Counter(all_keywords)

        # 识别稀有关键词（出现1-2次）
        rare_keywords = [kw for kw, freq in keyword_freq.items() if 1 <= freq <= 2]

        # 识别高频关键词（出现3次以上）
        common_keywords = [kw for kw, freq in keyword_freq.items() if freq >= 3]

        # 分析关键词的语义覆盖（简单版）
        semantic_clusters = self._cluster_keywords(all_keywords)

        # 查找语义空白（某些概念没有被充分研究）
        semantic_gaps = self._identify_semantic_gaps(semantic_clusters, keyword_freq)

        return {
            "keyword_frequency": dict(keyword_freq.most_common(20)),
            "rare_keywords": rare_keywords[:20],
            "emerging_topics": rare_keywords[:10],  # 稀有关键词可能是新兴方向
            "common_topics": common_keywords[:10],
            "semantic_clusters": semantic_clusters,
            "semantic_gaps": semantic_gaps
        }

    def _cluster_keywords(self, keywords: List[str]) -> Dict[str, List[str]]:
        """简单的关键词聚类（基于字符串相似性）"""
        # 这是一个简化的实现，实际应该使用词向量或语义相似度
        clusters = defaultdict(list)

        # 按词首字母分组
        for kw in keywords:
            if kw:
                first_char = kw[0].upper()
                clusters[first_char].append(kw)

        return dict(clusters)

    def _identify_semantic_gaps(
        self,
        clusters: Dict[str, List[str]],
        freq: Counter
    ) -> List[str]:
        """识别语义空白"""
        gaps = []

        # 简单规则：如果某个聚类只有很少的关键词，可能存在空白
        for letter, keywords in clusters.items():
            if len(keywords) <= 2:
                gaps.append(f"以'{letter}'开头的主题较少，可能存在研究空白")

        return gaps[:5]

    def _citation_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, Any]:
        """
        基于参考文献的引文分析

        思路：
        1. 分析参考文献的年份分布（识别经典 vs 最新文献）
        2. 识别被频繁引用的作者和会议
        3. 查找"重要但缺失"的引用（应该引用但未引用）
        """
        all_references = []
        ref_years = []
        ref_venues = Counter()

        for paper in papers:
            for ref in paper.metadata.references:
                all_references.append(ref)

                # 提取年份
                year_match = re.search(r'\b(19|20)\d{2}\b', ref)
                if year_match:
                    year = int(year_match.group())
                    if 1990 <= year <= 2030:
                        ref_years.append(year)

                # 提取发表场所（会议、期刊）
                venue_patterns = [
                    r'Proceedings of\s+([^,\n]+)',
                    r'([A-Z][a-zA-Z\s]+(?:Conference|Congress|Symposium))',
                    r'([A-Z][a-zA-Z\s]*Journal)',
                ]

                for pattern in venue_patterns:
                    match = re.search(pattern, ref)
                    if match:
                        ref_venues[match.group(1).strip()] += 1

        # 分析年份分布
        if ref_years:
            year_distribution = {
                "earliest": min(ref_years),
                "latest": max(ref_years),
                "average": sum(ref_years) / len(ref_years),
                "recent_5_years": len([y for y in ref_years if y >= 2020]),
            }
        else:
            year_distribution = {}

        return {
            "total_references": len(all_references),
            "year_distribution": year_distribution,
            "top_venues": dict(ref_venues.most_common(10)),
            "citation_agedness": self._analyze_citation_agedness(ref_years)
        }

    def _analyze_citation_agedness(self, years: List[int]) -> str:
        """分析引用的新旧程度"""
        if not years:
            return "无法分析"

        avg_year = sum(years) / len(years)

        if avg_year >= 2021:
            return "引用较新，关注前沿研究"
        elif avg_year >= 2018:
            return "引用适中，兼顾经典与前沿"
        else:
            return "引用较旧，可能需要关注最新进展"

    def _llm_based_gap_mining(self, papers: List[ParsedPaper]) -> List[Dict[str, Any]]:
        """
        使用LLM深度挖掘研究空白

        这是核心功能，利用大语言模型的推理能力
        """
        print("使用LLM深度分析研究空白...")

        # 准备论文信息
        papers_info = self._prepare_papers_info(papers)

        # 生成提示词
        prompt = get_gap_mining_prompt(papers_info)

        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content

            # 解析LLM响应
            gaps = self._parse_llm_gap_response(result, papers)

            return gaps

        except Exception as e:
            print(f"LLM分析失败: {e}")
            return []

    def _prepare_papers_info(self, papers: List[ParsedPaper]) -> str:
        """准备用于LLM分析的论文信息"""
        info_parts = []

        for i, paper in enumerate(papers, 1):
            info_parts.append(f"\n## 论文 {i}")
            info_parts.append(f"标题: {paper.metadata.title}")
            info_parts.append(f"摘要: {paper.metadata.abstract[:300]}...")
            info_parts.append(f"关键词: {', '.join(paper.metadata.keywords[:10])}")

            # 添加主要结论
            if "Conclusion" in paper.metadata.sections or "结论" in paper.metadata.sections:
                conclusion = paper.metadata.sections.get("Conclusion", "") or paper.metadata.sections.get("结论", "")
                info_parts.append(f"主要结论: {conclusion[:200]}...")

        return "\n".join(info_parts)

    def _parse_llm_gap_response(
        self,
        response: str,
        papers: List[ParsedPaper]
    ) -> List[Dict[str, Any]]:
        """解析LLM的响应，提取结构化的研究空白"""
        gaps = []

        try:
            # 尝试解析为JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                gaps_data = json.loads(json_str)

                # 转换为ResearchGap对象
                for gap_type, gap_list in gaps_data.items():
                    for gap in gap_list:
                        gaps.append({
                            "gap_type": gap_type,
                            "description": gap.get("description", ""),
                            "importance": gap.get("importance", "medium"),
                            "difficulty": gap.get("difficulty", "medium"),
                            "potential_approach": gap.get("potential_approach", ""),
                            "expected_impact": gap.get("expected_impact", ""),
                            "related_papers": [],  # LLM可能无法返回这个
                            "confidence": 0.7
                        })

            else:
                # 如果不是JSON，尝试从文本中提取
                # 这里可以添加更复杂的文本解析逻辑
                pass

        except Exception as e:
            print(f"解析LLM响应失败: {e}")

        return gaps

    def _generate_gap_report(
        self,
        all_gaps: Dict[str, Any],
        papers: List[ParsedPaper]
    ) -> Dict[str, Any]:
        """生成研究空白报告"""
        report = {
            "summary": {
                "total_papers_analyzed": len(papers),
                "total_gaps_identified": 0,
                "gap_categories": []
            },
            "gaps_by_category": all_gaps,
            "recommendations": [],
            "priority_gaps": []
        }

        # 统计各类空白数量
        for category, gaps in all_gaps.items():
            if isinstance(gaps, dict):
                count = sum(len(v) if isinstance(v, list) else 0 for v in gaps.values())
            elif isinstance(gaps, list):
                count = len(gaps)
            else:
                count = 0

            report["summary"]["total_gaps_identified"] += count

        # 生成优先级建议
        priority_gaps = []

        # 从LLM深度分析中提取高优先级空白
        llm_gaps = all_gaps.get("llm_deep_analysis", [])
        for gap in llm_gaps:
            if gap.get("importance") == "high" and gap.get("difficulty") in ["low", "medium"]:
                priority_gaps.append(gap)

        report["priority_gaps"] = priority_gaps[:5]

        # 生成建议
        report["recommendations"] = self._generate_recommendations(all_gaps)

        return report

    def _generate_recommendations(self, all_gaps: Dict[str, Any]) -> List[str]:
        """基于识别的空白生成建议"""
        recommendations = []

        # 基于方法论空白的建议
        method_gaps = all_gaps.get("rule_based", {}).get("methodological", [])
        if len(method_gaps) > 3:
            recommendations.append(
                "检测到多个方法论空白，建议重点关注算法优化和效率提升方向"
            )

        # 基于数据空白的建议
        data_gaps = all_gaps.get("rule_based", {}).get("data", [])
        if len(data_gaps) > 2:
            recommendations.append(
                "数据集是主要瓶颈，建议考虑新数据集构建或数据增强技术"
            )

        # 基于语义空白的建议
        semantic_gaps = all_gaps.get("keyword_based", {}).get("semantic_gaps", [])
        if semantic_gaps:
            recommendations.append(
                "存在未被充分探索的主题方向，这些可能是新兴机会"
            )

        # 基于引用分析的建议
        citation_info = all_gaps.get("citation_based", {})
        agedness = citation_info.get("citation_agedness", "")
        if "较旧" in agedness:
            recommendations.append(
                "引用文献较旧，建议加强对最新文献的追踪和引用"
            )

        return recommendations

    def _save_gap_report(self, report: Dict[str, Any], output_dir: Optional[Path] = None):
        """保存研究空白报告"""
        output_dir = output_dir or settings.cluster_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "research_gap_report.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("研究空白挖掘报告\n")
            f.write("=" * 80 + "\n\n")

            # 写入摘要
            f.write("## 分析摘要\n\n")
            f.write(f"分析论文数: {report['summary']['total_papers_analyzed']}\n")
            f.write(f"识别空白数: {report['summary']['total_gaps_identified']}\n\n")

            # 写入优先级空白
            f.write("## 优先级研究空白 (Top 5)\n\n")
            for i, gap in enumerate(report["priority_gaps"], 1):
                f.write(f"{i}. {gap['description']}\n")
                f.write(f"   重要性: {gap['importance']} | 难度: {gap['difficulty']}\n")
                f.write(f"   可能方法: {gap['potential_approach']}\n")
                f.write(f"   预期影响: {gap['expected_impact']}\n\n")

            # 写入建议
            f.write("## 研究建议\n\n")
            for i, rec in enumerate(report["recommendations"], 1):
                f.write(f"{i}. {rec}\n")

            # 写入详细分类
            f.write("\n## 详细分析\n\n")
            f.write("### 基于规则的空白识别\n\n")
            rule_based = report["gaps_by_category"].get("rule_based", {})
            for category, gaps in rule_based.items():
                f.write(f"{category}: {len(gaps)} 个空白\n")

            f.write("\n### 关键词分析\n\n")
            keyword_data = report["gaps_by_category"].get("keyword_based", {})
            f.write(f"新兴主题: {', '.join(keyword_data.get('emerging_topics', []))}\n")
            f.write(f"常见主题: {', '.join(keyword_data.get('common_topics', []))}\n")

        print(f"\n✓ 研究空白报告已保存到: {report_path}")


def mine_gaps_from_papers(pdf_paths: List[str]) -> Dict[str, Any]:
    """
    便捷函数：从PDF文件列表挖掘研究空白

    Args:
        pdf_paths: PDF文件路径列表

    Returns:
        Dict: 研究空白分析结果
    """
    from src.pdf_parser_enhanced import EnhancedPDFParser

    # 解析PDF
    print("正在解析PDF文件...")
    parser = EnhancedPDFParser()
    papers = []
    for pdf_path in pdf_paths:
        try:
            paper = parser.parse_pdf(pdf_path)
            papers.append(paper)
        except Exception as e:
            print(f"解析失败 {pdf_path}: {e}")

    # 挖掘研究空白
    miner = ResearchGapMiner()
    gaps = miner.mine_gaps_from_papers(papers, use_llm=True)

    return gaps
