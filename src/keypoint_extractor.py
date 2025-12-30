"""要点提取模块 - 识别论文核心创新、实验方法与结论"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI

from src.config import settings
from src.pdf_parser import ParsedPaper
from src.prompts import get_keypoint_prompt


class KeypointExtractor:
    """论文要点提取器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        初始化要点提取器

        Args:
            api_key: GLM-4 API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
        """
        self.api_key = api_key or settings.glm_api_key
        self.base_url = base_url or settings.glm_base_url
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else settings.default_temperature
        self.max_tokens = max_tokens or settings.max_tokens

        if not self.api_key:
            raise ValueError("请设置GLM_API_KEY环境变量")

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def extract_keypoints(
        self,
        paper: ParsedPaper,
        save: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, List[str]]:
        """
        提取论文要点

        Args:
            paper: 解析后的论文对象
            save: 是否保存要点到文件
            output_dir: 输出目录

        Returns:
            Dict[str, List[str]]: 提取的要点字典
        """
        # 准备内容
        content = self._prepare_paper_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:500]}"
            for name, content_part in paper.metadata.sections.items()
        ])
        keywords_text = ", ".join(paper.metadata.keywords) if paper.metadata.keywords else "未提取到关键词"

        # 使用专业提示词
        prompt = get_keypoint_prompt(
            title=paper.metadata.title or paper.filename,
            abstract=paper.metadata.abstract or "未提取到摘要",
            keywords=keywords_text,
            sections=sections_text,
            content=content
        )

        # 生成要点
        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content
            keypoints = self._parse_response(result)
        except Exception as e:
            print(f"要点提取失败: {e}")
            keypoints = self._get_empty_keypoints()

        # 保存要点
        if save:
            self._save_keypoints(paper, keypoints, output_dir)

        return keypoints

    def _prepare_paper_content(self, paper: ParsedPaper, max_chars: int = 8000) -> str:
        """
        准备论文内容

        Args:
            paper: 论文对象
            max_chars: 最大字符数

        Returns:
            str: 处理后的论文内容
        """
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
                content_parts.append(f"\n{section_name}:\n{section_content[:1500]}")

        # 组合内容
        combined_content = "\n\n".join(content_parts)

        if len(combined_content) < max_chars:
            remaining_chars = max_chars - len(combined_content)
            full_text_sample = paper.full_text[:remaining_chars]
            combined_content += f"\n\n论文正文:\n{full_text_sample}"

        return combined_content[:max_chars]

    def _parse_response(self, response: str) -> Dict[str, List[str]]:
        """
        解析LLM响应，提取JSON数据

        Args:
            response: LLM响应文本

        Returns:
            Dict[str, List[str]]: 解析后的要点字典
        """
        # 尝试提取JSON部分
        try:
            # 查找JSON代码块
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # 尝试直接解析整个响应
                json_str = response.strip()

            # 解析JSON
            keypoints = json.loads(json_str)

            # 验证并确保所有字段都存在
            required_fields = ["innovations", "methods", "experiments", "conclusions", "contributions", "limitations"]
            for field in required_fields:
                if field not in keypoints:
                    keypoints[field] = []
                elif not isinstance(keypoints[field], list):
                    keypoints[field] = [str(keypoints[field])]

            return keypoints

        except Exception as e:
            print(f"JSON解析失败: {e}")
            print(f"原始响应: {response}")
            return self._get_empty_keypoints()

    def _get_empty_keypoints(self) -> Dict[str, List[str]]:
        """返回空的要点结构"""
        return {
            "innovations": [],
            "methods": [],
            "experiments": [],
            "conclusions": [],
            "contributions": [],
            "limitations": []
        }

    def _save_keypoints(
        self,
        paper: ParsedPaper,
        keypoints: Dict[str, List[str]],
        output_dir: Optional[Path] = None
    ):
        """
        保存要点到文件

        Args:
            paper: 论文对象
            keypoints: 提取的要点
            output_dir: 输出目录
        """
        output_dir = output_dir or settings.keypoints_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用原文件名（去掉.pdf）作为输出文件名
        output_filename = Path(paper.filename).stem + "_keypoints.txt"
        output_path = output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"论文标题: {paper.metadata.title or paper.filename}\n")
            f.write(f"文件名: {paper.filename}\n")
            f.write(f"页数: {paper.page_count}\n")
            f.write(f"\n{'='*60}\n\n")
            f.write("核心要点报告\n\n")

            # 写入各个类别
            field_names = {
                "innovations": "🔥 核心创新点",
                "methods": "🔧 主要方法与技术",
                "experiments": "🧪 实验设计与评估",
                "conclusions": "💡 主要结论",
                "contributions": "🎯 学术贡献",
                "limitations": "⚠️ 局限性"
            }

            for field, display_name in field_names.items():
                f.write(f"{display_name}\n")
                items = keypoints.get(field, [])
                if items:
                    for i, item in enumerate(items, 1):
                        f.write(f"  {i}. {item}\n")
                else:
                    f.write("  (未提取到)\n")
                f.write("\n")

            f.write(f"{'='*60}\n")

    def batch_extract_keypoints(
        self,
        papers: List[ParsedPaper],
        output_dir: Optional[Path] = None
    ) -> List[Dict[str, List[str]]]:
        """
        批量提取要点

        Args:
            papers: 论文列表
            output_dir: 输出目录

        Returns:
            List[Dict[str, List[str]]]: 要点列表
        """
        all_keypoints = []

        for i, paper in enumerate(papers, 1):
            print(f"正在提取第 {i}/{len(papers)} 篇论文的要点...")
            try:
                keypoints = self.extract_keypoints(paper, save=True, output_dir=output_dir)
                all_keypoints.append(keypoints)
                print(f"✓ 完成: {paper.filename}")
            except Exception as e:
                print(f"✗ 失败: {paper.filename} - {e}")
                all_keypoints.append(self._get_empty_keypoints())

        return all_keypoints

    def generate_summary_report(
        self,
        keypoints: Dict[str, List[str]],
        paper_title: str
    ) -> str:
        """
        生成要点摘要报告

        Args:
            keypoints: 提取的要点
            paper_title: 论文标题

        Returns:
            str: 摘要报告
        """
        report_lines = [
            f"# {paper_title}",
            "",
            "## 核心创新点"
        ]

        for item in keypoints.get("innovations", []):
            report_lines.append(f"- {item}")

        report_lines.extend([
            "",
            "## 主要方法"
        ])

        for item in keypoints.get("methods", []):
            report_lines.append(f"- {item}")

        report_lines.extend([
            "",
            "## 主要结论"
        ])

        for item in keypoints.get("conclusions", []):
            report_lines.append(f"- {item}")

        return "\n".join(report_lines)


def extract_keypoints_from_pdf(pdf_path: str) -> Dict[str, List[str]]:
    """
    便捷函数：从PDF文件提取要点

    Args:
        pdf_path: PDF文件路径

    Returns:
        Dict[str, List[str]]: 提取的要点
    """
    from src.pdf_parser import PDFParser

    # 解析PDF
    parser = PDFParser()
    paper = parser.parse_pdf(pdf_path)

    # 提取要点
    extractor = KeypointExtractor()
    keypoints = extractor.extract_keypoints(paper)

    return keypoints
