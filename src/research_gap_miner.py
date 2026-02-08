"""研究空白挖掘模块 - v4.2 LangChain优化版

使用 LangChain Prompt Templates 和 Pydantic Output Parser
实现结构化输出，减少解析错误
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import Counter, defaultdict
import re

from src.config import settings
from src.pdf_parser import ParsedPaper

# v4.2: 使用新的 LangChain 辅助模块
try:
    from src.langchain_helpers import StructuredLLMHelper, get_structured_llm_helper
    from src.prompts_langchain import get_empty_gaps
    LANGCHAIN_V2_AVAILABLE = True
except ImportError:
    LANGCHAIN_V2_AVAILABLE = False
    print("[WARNING] 新的 LangChain 模块不可用，将使用降级模式")

# 保留旧版导入以确保兼容性
try:
    from langchain_openai import ChatOpenAI
    from src.prompts_doctoral import get_gap_mining_prompt
    LANGCHAIN_LEGACY_AVAILABLE = True
except ImportError:
    LANGCHAIN_LEGACY_AVAILABLE = False


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
    """研究空白挖掘器 - v4.2 LangChain优化版"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        use_langchain_v2: bool = True  # v4.2: 默认使用新的架构
    ):
        """
        初始化研究空白挖掘器

        Args:
            api_key: GLM-4 API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
            use_langchain_v2: 是否使用新的 LangChain 架构
        """
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else 0.3
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
                max_tokens=4000
            )
            self.llm = self.helper.llm
        # 否则使用旧的初始化方式
        elif LANGCHAIN_LEGACY_AVAILABLE:
            self.llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                max_tokens=4000,
            )
            self.helper = None
        else:
            raise ValueError("LangChain 不可用且未启用 v2 模式")

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

        # 汇总所有空白
        all_gaps = {
            "rule_based": rule_based_gaps,
            "keyword_based": keyword_gaps,
            "citation_based": citation_gaps,
            "llm_deep_analysis": llm_gaps
        }

        # 生成报告
        report = self._generate_gap_report(all_gaps, papers)

        # 保存报告
        if save:
            self._save_gap_report(report, output_dir)

        print(f"\n✓ 研究空白挖掘完成")
        print(f"  - 识别空白数: {report['summary']['total_gaps_identified']}")
        print(f"  - 高优先级空白: {len(report['priority_gaps'])}\n")

        return report

    async def amine_gaps_from_papers(
        self,
        papers: List[ParsedPaper],
        use_llm: bool = True,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        异步从多篇论文中挖掘研究空白

        Args:
            papers: 论文列表
            use_llm: 是否使用LLM深度分析
            save: 是否保存结果
            output_dir: 输出目录

        Returns:
            Dict: 研究空白分析结果
        """
        print(f"\n{'='*80}")
        print(f"研究空白挖掘 (异步) - 分析 {len(papers)} 篇论文")
        print(f"{'='*80}\n")

        # 基于规则的初步分析（同步）
        rule_based_gaps = self._rule_based_gap_mining(papers)

        # 基于统计的关键词分析（同步）
        keyword_gaps = self._keyword_based_gap_mining(papers)

        # 基于参考文献的引文分析（同步）
        citation_gaps = self._citation_based_gap_mining(papers)

        # 使用LLM深度挖掘（异步）
        llm_gaps = []
        if use_llm and len(papers) >= 2:
            llm_gaps = await self._allm_based_gap_mining(papers)

        # 汇总所有空白
        all_gaps = {
            "rule_based": rule_based_gaps,
            "keyword_based": keyword_gaps,
            "citation_based": citation_gaps,
            "llm_deep_analysis": llm_gaps
        }

        # 生成报告
        report = self._generate_gap_report(all_gaps, papers)

        # 保存报告
        if save:
            self._save_gap_report(report, output_dir)

        print(f"\n✓ 研究空白挖掘完成")
        print(f"  - 识别空白数: {report['summary']['total_gaps_identified']}")
        print(f"  - 高优先级空白: {len(report['priority_gaps'])}\n")

        return report

    def _rule_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, List[Dict]]:
        """
        基于规则的空白挖掘

        通过关键词匹配和模式识别识别潜在空白
        """
        print("进行基于规则的空白分析...")

        gaps = {
            "methodological": [],
            "theoretical": [],
            "data": [],
            "application": [],
            "evaluation": []
        }

        # 方法论模式
        method_patterns = [
            r'(?:computational|time|space) (?:complexity|cost|overhead)',
            r'(?:inefficient|slow|scalability issues?)',
            r'(?:limited|restrictive) (?:applicability|generalization)',
        ]

        # 数据模式
        data_patterns = [
            r'(?:lack|shortage|scarcity) of (?:data|datasets|samples)',
            r'(?:imbalanced|noisy|low-quality) data',
            r'(?:annotation|labeling) (?:cost|burden|challenge)',
        ]

        # 评估模式
        eval_patterns = [
            r'(?:lack|absence) of (?:benchmark|comparison|baseline)',
            r'(?:insufficient|inadequate) (?:evaluation|validation)',
            r'(?:limited|narrow) (?:evaluation|assessment) scope',
        ]

        # 分析每篇论文
        for paper in papers:
            text = paper.full_text.lower()

            # 检查方法论局限
            for pattern in method_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    match = re.search(pattern, text, re.IGNORECASE)
                    gaps["methodological"].append({
                        "description": f"检测到方法论局限: {match.group()}",
                        "source": f"{paper.metadata.title}",
                        "evidence": match.group()
                    })

            # 检查数据局限
            for pattern in data_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    match = re.search(pattern, text, re.IGNORECASE)
                    gaps["data"].append({
                        "description": f"检测到数据局限: {match.group()}",
                        "source": f"{paper.metadata.title}",
                        "evidence": match.group()
                    })

            # 检查评估局限
            for pattern in eval_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    match = re.search(pattern, text, re.IGNORECASE)
                    gaps["evaluation"].append({
                        "description": f"检测到评估局限: {match.group()}",
                        "source": f"{paper.metadata.title}",
                        "evidence": match.group()
                    })

        print(f"  - 方法论空白: {len(gaps['methodological'])}")
        print(f"  - 数据空白: {len(gaps['data'])}")
        print(f"  - 评估空白: {len(gaps['evaluation'])}")

        return gaps

    def _keyword_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, Any]:
        """
        基于关键词的空白挖掘

        分析关键词频率和共现，识别研究趋势和空白
        """
        print("进行基于关键词的空白分析...")

        # 收集所有关键词
        all_keywords = []
        for paper in papers:
            all_keywords.extend(paper.metadata.keywords)

        # 统计关键词频率
        keyword_freq = Counter(all_keywords)

        # 识别高频关键词（研究热点）
        hot_topics = keyword_freq.most_common(10)

        # 识别低频关键词（可能的空白）
        rare_keywords = [kw for kw, count in keyword_freq.items() if count == 1]

        # 分析关键词组合
        keyword_combinations = []
        for paper in papers:
            keywords = paper.metadata.keywords
            if len(keywords) >= 2:
                # 记录关键词对
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        keyword_combinations.append(tuple(sorted([keywords[i], keywords[j]])))

        combo_freq = Counter(keyword_combinations)
        rare_combinations = [combo for combo, count in combo_freq.items() if count == 1]

        gaps = {
            "hot_topics": [kw for kw, _ in hot_topics],
            "emerging_topics": rare_keywords[:10],
            "semantic_gaps": [f"{combo[0]}+{combo[1]}" for combo in rare_combinations[:5]],
            "keyword_frequency": dict(keyword_freq.most_common(20))
        }

        print(f"  - 研究热点: {len(hot_topics)} 个")
        print(f"  - 新兴主题: {len(rare_keywords)} 个")
        print(f"  - 语义空白: {len(rare_combinations)} 个")

        return gaps

    def _citation_based_gap_mining(self, papers: List[ParsedPaper]) -> Dict[str, Any]:
        """
        基于引文的空白挖掘

        分析引用模式，识别理论基础空白
        """
        print("进行基于引文的空白分析...")

        # 分析参考文献年份
        all_refs = []
        for paper in papers:
            all_refs.extend(paper.metadata.references)

        # 提取年份
        years = []
        for ref in all_refs:
            year_match = re.search(r'(19|20)\d{2}', ref)
            if year_match:
                year = int(year_match.group())
                if 1990 <= year <= 2025:
                    years.append(year)

        if years:
            avg_year = sum(years) / len(years)
            year_range = max(years) - min(years)

            citation_gaps = {
                "average_citation_year": avg_year,
                "citation_range": year_range,
                "oldest_citation": min(years),
                "newest_citation": max(years),
                "citation_agedness": self._assess_citation_agedness(avg_year)
            }
        else:
            citation_gaps = {
                "average_citation_year": None,
                "citation_range": 0,
                "citation_agedness": "无法评估"
            }

        print(f"  - 平均引用年份: {citation_gaps['average_citation_year']}")
        print(f"  - 引用时效性: {citation_gaps['citation_agedness']}")

        return citation_gaps

    def _assess_citation_agedness(self, avg_year: float) -> str:
        """评估引用的时效性"""
        from datetime import datetime
        current_year = datetime.now().year

        if avg_year >= current_year - 2:
            return "引用较新，关注前沿研究"
        elif avg_year >= 2018:
            return "引用适中，兼顾经典与前沿"
        else:
            return "引用较旧，可能需要关注最新进展"

    def _llm_based_gap_mining(self, papers: List[ParsedPaper]) -> List[Dict[str, Any]]:
        """
        使用LLM深度挖掘研究空白 - v4.2 使用 Pydantic Output Parser

        这是核心功能，利用大语言模型的推理能力
        """
        print("使用LLM深度分析研究空白...")

        # v4.2: 使用新的 helper 进行结构化输出
        if self.use_langchain_v2 and self.helper:
            papers_data = self._prepare_papers_data_for_v2(papers)
            result = self.helper.identify_gaps(papers_data)
            
            # 转换格式以兼容现有代码
            gaps = []
            for gap in result.get("gaps", []):
                gaps.append({
                    "gap_type": gap.get("gap_type", "methodological"),
                    "description": gap.get("description", ""),
                    "importance": gap.get("importance", "medium"),
                    "difficulty": gap.get("difficulty", "medium"),
                    "potential_approach": gap.get("potential_approach", ""),
                    "expected_impact": gap.get("expected_impact", ""),
                    "related_papers": [],
                    "confidence": 0.8
                })
            
            print(f"  - LLM识别空白: {len(gaps)} 个")
            return gaps
        else:
            # 旧版兼容模式
            papers_info = self._prepare_papers_info(papers)
            prompt = get_gap_mining_prompt(papers_info)

            try:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=prompt)])
                result = response.content
                gaps = self._parse_llm_gap_response(result, papers)
                print(f"  - LLM识别空白: {len(gaps)} 个")
                return gaps
            except Exception as e:
                print(f"LLM分析失败: {e}")
                return []

    async def _allm_based_gap_mining(self, papers: List[ParsedPaper]) -> List[Dict[str, Any]]:
        """
        异步使用LLM深度挖掘研究空白
        """
        print("使用LLM深度分析研究空白 (异步)...")

        # v4.2: 使用新的 helper 进行异步结构化输出
        if self.use_langchain_v2 and self.helper:
            papers_data = self._prepare_papers_data_for_v2(papers)
            result = await self.helper.aidentify_gaps(papers_data)
            
            # 转换格式以兼容现有代码
            gaps = []
            for gap in result.get("gaps", []):
                gaps.append({
                    "gap_type": gap.get("gap_type", "methodological"),
                    "description": gap.get("description", ""),
                    "importance": gap.get("importance", "medium"),
                    "difficulty": gap.get("difficulty", "medium"),
                    "potential_approach": gap.get("potential_approach", ""),
                    "expected_impact": gap.get("expected_impact", ""),
                    "related_papers": [],
                    "confidence": 0.8
                })
            
            print(f"  - LLM识别空白: {len(gaps)} 个")
            return gaps
        else:
            # 旧版兼容模式
            import asyncio
            papers_info = self._prepare_papers_info(papers)
            prompt = get_gap_mining_prompt(papers_info)

            try:
                from langchain_core.messages import HumanMessage
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.llm.invoke([HumanMessage(content=prompt)])
                )
                gaps = self._parse_llm_gap_response(response.content, papers)
                print(f"  - LLM识别空白: {len(gaps)} 个")
                return gaps
            except Exception as e:
                print(f"LLM分析失败: {e}")
                return []

    def _prepare_papers_data_for_v2(self, papers: List[ParsedPaper]) -> List[Dict[str, Any]]:
        """v4.2: 为新的 LangChain helper 准备论文数据"""
        papers_data = []
        for paper in papers:
            papers_data.append({
                "title": paper.metadata.title or "未命名",
                "abstract": paper.metadata.abstract or "无摘要",
                "keywords": paper.metadata.keywords or [],
                "sections": paper.metadata.sections or {}
            })
        return papers_data

    def _prepare_papers_info(self, papers: List[ParsedPaper]) -> str:
        """准备用于LLM分析的论文信息（旧版兼容）"""
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
        """解析LLM的响应，提取结构化的研究空白（旧版兼容）"""
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
                            "related_papers": [],
                            "confidence": 0.7
                        })

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

        from datetime import datetime
        report_path = output_dir / "research_gap_report.md"

        # 构建markdown格式内容
        md_content = f"""# 研究空白挖掘报告

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 分析摘要

| 指标 | 数值 |
|------|------|
| 分析论文数 | {report['summary']['total_papers_analyzed']} |
| 识别空白数 | {report['summary']['total_gaps_identified']} |

---

## 优先级研究空白 (Top 5)

"""

        for i, gap in enumerate(report["priority_gaps"], 1):
            md_content += f"""### {i}. {gap['description']}

- **重要性**: {gap['importance']}
- **难度**: {gap['difficulty']}
- **可能方法**: {gap['potential_approach']}
- **预期影响**: {gap['expected_impact']}

"""

        md_content += """---

## 研究建议

"""
        for i, rec in enumerate(report["recommendations"], 1):
            md_content += f"{i}. {rec}\n"

        md_content += """
---

## 详细分析

### 基于规则的空白识别

"""
        rule_based = report["gaps_by_category"].get("rule_based", {})
        for category, gaps in rule_based.items():
            md_content += f"- {category}: {len(gaps)} 个空白\n"

        md_content += """
### 关键词分析

"""
        keyword_data = report["gaps_by_category"].get("keyword_based", {})
        md_content += f"- **新兴主题**: {', '.join(keyword_data.get('emerging_topics', []))}\n"

        md_content += """
---

*此报告由院士级科研智能助手自动生成*
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"  报告已保存到: {report_path}")
