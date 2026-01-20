"""异步工作流引擎 - v4.0院士版
支持异步、批量、智能调度的论文分析工作流
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import aiofiles
from pathlib import Path

from src.db_manager import DatabaseManager
from src.pdf_parser_enhanced import EnhancedPDFParser, ParsedPaper
from src.prompts_doctoral import get_summary_prompt_doctoral, get_keypoint_prompt_doctoral

# 尝试导入 langchain，如果没有安装则使用占位符
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("⚠️  langchain_openai 未安装，LLM功能将受限")
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    HumanMessage = None


class WorkflowState(Enum):
    """工作流状态"""
    UPLOADED = "uploaded"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GRAPH_BUILDING = "graph_building"
    INSIGHT_GENERATING = "insight_generating"
    CODE_GENERATING = "code_generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AsyncWorkflowEngine:
    """异步工作流引擎"""

    def __init__(self, db_manager: DatabaseManager, llm_config: Dict[str, Any] = None):
        """
        初始化工作流引擎

        Args:
            db_manager: 数据库管理器
            llm_config: LLM配置
        """
        self.db = db_manager

        # 初始化LLM（如果langchain可用）
        llm_config = llm_config or {}
        if LANGCHAIN_AVAILABLE and ChatOpenAI:
            self.llm = ChatOpenAI(
                model=llm_config.get('model', 'glm-4-plus'),
                api_key=llm_config.get('api_key'),
                base_url=llm_config.get('base_url'),
                temperature=0.3,
                max_tokens=8000,
                request_timeout=60
            )
        else:
            self.llm = None
            print("⚠️  LLM功能未启用（langchain未安装）")

        # PDF解析器
        self.pdf_parser = EnhancedPDFParser(extract_tables=True, extract_figures=True)

        # 并发控制 - 延迟初始化semaphore
        self.max_concurrent_analyses = llm_config.get('max_concurrent', 5)
        self._semaphore = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """获取或创建semaphore（延迟初始化）"""
        if self._semaphore is None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
                self._semaphore = asyncio.Semaphore(self.max_concurrent_analyses)
            except RuntimeError:
                # 如果没有运行中的事件循环，创建一个新的
                self._semaphore = asyncio.Semaphore(self.max_concurrent_analyses)
        return self._semaphore

    async def execute_paper_workflow(
        self,
        pdf_path: str,
        paper_id: int = None,
        tasks: List[str] = None,
        auto_generate_code: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的论文分析工作流

        Args:
            pdf_path: PDF文件路径
            paper_id: 已存在的论文ID（如果提供，则跳过解析和保存）
            tasks: 要执行的任务列表
            auto_generate_code: 是否自动生成代码

        Returns:
            Dict: 工作流执行结果
        """
        if tasks is None:
            tasks = ['summary', 'keypoints', 'topic', 'gaps', 'graph', 'code']

        result = {
            'pdf_path': pdf_path,
            'workflow_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'tasks_completed': [],
            'tasks_failed': [],
            'start_time': datetime.now().isoformat()
        }

        try:
            # 步骤1: 解析PDF（如果需要）
            if paper_id is None:
                print(f"\n[1/6] 解析PDF: {Path(pdf_path).name}")
                paper = await self._parse_pdf_async(pdf_path)

                # 保存到数据库（传递完整路径用于计算哈希）
                # create_paper返回字典，不是对象
                paper_record_dict = self._save_paper_to_db(paper, pdf_path)
                paper_id = paper_record_dict['id']
                result['paper_id'] = paper_id
            else:
                print(f"\n[1/6] 使用已存在的论文 ID: {paper_id}")
                result['paper_id'] = paper_id
                # 从数据库获取论文记录（get_paper返回字典，不是对象）
                paper_record_dict = self.db.get_paper(paper_id)
                if not paper_record_dict:
                    raise ValueError(f"论文 ID {paper_id} 不存在于数据库中")
                # 重新解析PDF用于分析
                paper = await self._parse_pdf_async(pdf_path)

            # 步骤2: 异步分析（并发执行多个任务）
            print(f"\n[2/6] 开始分析...")
            analysis_result = await self._analyze_paper_async(
                paper_id,  # 使用paper_id而不是paper_record.id
                paper,
                tasks=tasks
            )
            result['analysis_id'] = analysis_result['analysis_id']
            result['tasks_completed'].extend(analysis_result['completed'])
            result['tasks_failed'].extend(analysis_result['failed'])

            # 步骤3: 构建知识图谱
            if 'graph' in tasks:
                print(f"\n[3/6] 构建知识图谱...")
                await self._build_knowledge_graph_async(paper_id)

            # 步骤4: 生成洞察
            if 'gaps' in tasks:
                print(f"\n[4/6] 生成研究洞察...")
                gaps = await self._generate_insights_async(paper_id)
                result['gaps_count'] = len(gaps)

                # 步骤5: 自动生成代码
                if auto_generate_code and gaps:
                    print(f"\n[5/6] 自动生成代码...")
                    code_results = await self._generate_code_for_gaps_async(
                        paper_id, gaps[:3]  # 生成前3个空白的代码
                    )
                    result['code_generated'] = len(code_results)

            # 步骤6: 完成
            print(f"\n[6/6] ✓ 工作流完成！")
            result['status'] = 'completed'
            result['end_time'] = datetime.now().isoformat()

            # 计算耗时
            start = datetime.fromisoformat(result['start_time'])
            end = datetime.fromisoformat(result['end_time'])
            result['duration'] = (end - start).total_seconds()

        except Exception as e:
            print(f"\n✗ 工作流失败: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.now().isoformat()

        return result

    async def _parse_pdf_async(self, pdf_path: str) -> ParsedPaper:
        """异步解析PDF"""
        # 在线程池中执行阻塞的PDF解析
        loop = asyncio.get_event_loop()
        paper = await loop.run_in_executor(
            None,
            self.pdf_parser.parse_pdf,
            pdf_path
        )
        return paper

    def _save_paper_to_db(self, paper: ParsedPaper, pdf_path: str = None):
        """保存论文到数据库

        Args:
            paper: 解析后的论文对象
            pdf_path: PDF文件的完整路径（用于计算哈希），如果为None则使用paper.filename
        """
        # 使用传入的完整路径，或者使用paper.filename
        filepath_for_hash = pdf_path if pdf_path else paper.filename

        paper_data = {
            'title': paper.metadata.title,
            'abstract': paper.metadata.abstract,
            'pdf_path': paper.filename,  # 只保存文件名
            'pdf_hash': self._calculate_file_hash(filepath_for_hash),  # 使用完整路径计算哈希
            'year': paper.metadata.year,
            'venue': paper.metadata.publication_venue,
            'doi': paper.metadata.doi,
            'page_count': paper.page_count,
            'language': paper.language,
            'meta_data': {
                'authors': paper.metadata.authors,
                'keywords': paper.metadata.keywords,
                'sections_count': len(paper.metadata.sections),
                'references_count': len(paper.metadata.references),
                'tables_count': len(paper.tables),
                'figures_count': len(paper.figures)
            },
            'authors': [{'name': name} for name in paper.metadata.authors],
            'keywords': paper.metadata.keywords
        }

        return self.db.create_paper(paper_data)

    async def _analyze_paper_async(
        self,
        paper_id: int,
        paper: ParsedPaper,
        tasks: List[str]
    ) -> Dict[str, Any]:
        """异步分析论文"""
        # 创建分析记录 - 返回字典
        analysis_data = {
            'paper_id': paper_id,
            'status': 'analyzing'
        }
        analysis_dict = self.db.create_analysis(analysis_data)
        analysis_id = analysis_dict['id']

        completed = []
        failed = []

        # 并发执行分析任务
        async def run_task(task_name: str, task_func: Callable):
            async with self.semaphore:  # 限制并发数
                try:
                    print(f"  - 执行任务: {task_name}")
                    result = await task_func(paper)
                    print(f"    ✓ 完成: {task_name}")
                    return task_name, result, None
                except Exception as e:
                    print(f"    ✗ 失败: {task_name} - {e}")
                    return task_name, None, str(e)

        # 准备任务
        task_funcs = {}
        if 'summary' in tasks:
            task_funcs['summary'] = self._generate_summary_async
        if 'keypoints' in tasks:
            task_funcs['keypoints'] = self._extract_keypoints_async
        if 'topic' in tasks:
            task_funcs['topic'] = self._analyze_topic_async

        # 并发执行
        results = await asyncio.gather(
            *[run_task(name, func) for name, func in task_funcs.items()],
            return_exceptions=False
        )

        # 收集结果
        update_data = {
            'status': 'completed',
            'llm_calls': len(results),
            'tokens_used': 0
        }

        for task_name, task_result, error in results:
            if error:
                failed.append(task_name)
            else:
                completed.append(task_name)
                # 更新分析数据
                if task_name == 'summary' and task_result:
                    update_data['summary_text'] = task_result.get('summary', '')
                elif task_name == 'keypoints' and task_result:
                    update_data['keypoints'] = task_result
                elif task_name == 'topic' and task_result:
                    update_data['topic_analysis'] = task_result

        # 更新分析记录
        update_data['updated_at'] = datetime.utcnow()
        self.db.update_analysis(analysis_id, update_data)

        return {
            'analysis_id': analysis_id,
            'completed': completed,
            'failed': failed
        }

    async def _generate_summary_async(self, paper: ParsedPaper) -> Dict[str, str]:
        """异步生成摘要"""
        if not self.llm or not LANGCHAIN_AVAILABLE:
            print("⚠️  LLM未可用，无法生成摘要")
            return {
                'summary': "LLM功能未启用，无法生成摘要",
                'word_count': 0
            }

        prompt = self._prepare_summary_prompt(paper)

        # 在线程池中执行LLM调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.invoke,
            [HumanMessage(content=prompt)]
        )

        return {
            'summary': response.content,
            'word_count': len(response.content.split())
        }

    async def _extract_keypoints_async(self, paper: ParsedPaper) -> Dict[str, List[str]]:
        """异步提取要点"""
        if not self.llm or not LANGCHAIN_AVAILABLE:
            print("⚠️  LLM未可用，无法提取要点")
            return {field: [] for field in [
                "innovations", "research_gaps", "theoretical_framework",
                "methods", "experimental_design", "datasets",
                "conclusions", "statistical_analysis", "related_work_comparison",
                "reproducibility", "contributions", "limitations"
            ]}

        prompt = self._prepare_keypoint_prompt(paper)

        # 在线程池中执行LLM调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.invoke,
            [HumanMessage(content=prompt)]
        )

        # 解析JSON
        keypoints = self._parse_keypoints_json(response.content)

        return keypoints

    async def _analyze_topic_async(self, paper: ParsedPaper) -> Dict[str, Any]:
        """异步主题分析"""
        # 简化实现
        return {
            'topics': paper.metadata.keywords[:10],
            'field': self._infer_field(paper.metadata.keywords)
        }

    async def _build_knowledge_graph_async(self, paper_id: int):
        """异步构建知识图谱"""
        # 在实际实现中，这里应该：
        # 1. 分析参考文献，建立引用关系
        # 2. 使用相似度计算建立主题关联
        # 3. 检测方法继承关系
        pass  # 简化实现

    async def _generate_insights_async(self, analysis_id: int) -> List[Dict[str, Any]]:
        """异步生成研究洞察"""
        analysis_dict = self.db.get_analysis(analysis_id)
        if not analysis_dict:
            return []

        # 从分析结果中提取研究空白
        keypoints = analysis_dict.get('keypoints') or {}
        gaps_data = keypoints.get('research_gaps', [])

        gaps = []
        for gap_desc in gaps_data:
            # create_research_gap返回字典
            gap_dict = self.db.create_research_gap({
                'analysis_id': analysis_id,
                'gap_type': 'methodological',  # 简化
                'description': gap_desc,
                'importance': 'medium',
                'difficulty': 'medium',
                'status': 'identified'
            })
            gaps.append(gap_dict)

        return gaps

    async def _generate_code_for_gaps_async(
        self,
        paper_id: int,
        gaps: List,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """异步为研究空白生成代码"""
        from src.code_generator import CodeGenerator

        code_gen = CodeGenerator(llm=self.llm)

        async def generate_for_gap(gap_dict):
            try:
                # gap_dict是字典，不是对象
                print(f"    生成代码: {gap_dict.get('description', '')[:50]}...")
                code_data = await code_gen.generate_code_async(gap_dict)

                # 保存到数据库 - create_generated_code返回字典
                code_data['gap_id'] = gap_dict['id']
                generated_code_dict = self.db.create_generated_code(code_data)

                # 更新gap状态
                self.db.update_research_gap(gap_dict['id'], {'status': 'code_generated'})

                return {'gap_id': gap_dict['id'], 'code_id': generated_code_dict['id']}
            except Exception as e:
                print(f"      代码生成失败: {e}")
                return {'gap_id': gap_dict['id'], 'error': str(e)}

        # 并发生成（限制并发数）- 使用当前运行中的事件循环
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_generate(gap_dict):
            async with semaphore:
                return await generate_for_gap(gap_dict)

        results = await asyncio.gather(
            *[limited_generate(gap) for gap in gaps],
            return_exceptions=False
        )

        return results

    # ============================================================================
    # 批量处理
    # ============================================================================

    async def batch_process_papers(
        self,
        pdf_paths: List[str],
        tasks: List[str] = None
    ) -> Dict[str, Any]:
        """
        批量处理论文

        Args:
            pdf_paths: PDF文件路径列表
            tasks: 要执行的任务

        Returns:
            Dict: 批量处理结果
        """
        print(f"\n{'='*80}")
        print(f"批量处理 {len(pdf_paths)} 篇论文")
        print(f"{'='*80}\n")

        start_time = datetime.now()

        # 并发处理
        results = await asyncio.gather(
            *[self.execute_paper_workflow(pdf_path, tasks) for pdf_path in pdf_paths],
            return_exceptions=True
        )

        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'completed')
        failure_count = len(results) - success_count

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            'total': len(pdf_paths),
            'success': success_count,
            'failed': failure_count,
            'duration': duration,
            'avg_time': duration / len(pdf_paths) if pdf_paths else 0,
            'results': results
        }

        print(f"\n{'='*80}")
        print(f"批量处理完成: {success_count}/{len(pdf_paths)} 成功")
        print(f"总耗时: {duration:.2f}秒, 平均: {summary['avg_time']:.2f}秒/篇")
        print(f"{'='*80}\n")

        return summary

    # ============================================================================
    # 辅助方法
    # ============================================================================

    def _prepare_summary_prompt(self, paper: ParsedPaper) -> str:
        """准备摘要生成提示词"""
        content = self._prepare_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:800]}"
            for name, content_part in list(paper.metadata.sections.items())[:5]
        ])

        return get_summary_prompt_doctoral(
            title=paper.metadata.title or paper.filename,
            authors=", ".join(paper.metadata.authors[:5]),
            publication=f"{paper.metadata.publication_venue} ({paper.metadata.year})",
            abstract=paper.metadata.abstract or "未提取到摘要",
            keywords=", ".join(paper.metadata.keywords[:10]),
            sections=sections_text,
            content=content
        )

    def _prepare_keypoint_prompt(self, paper: ParsedPaper) -> str:
        """准备要点提取提示词"""
        content = self._prepare_content(paper)
        sections_text = "\n".join([
            f"### {name}\n{content_part[:800]}"
            for name, content_part in list(paper.metadata.sections.items())[:5]
        ])

        keywords_text = ", ".join(paper.metadata.keywords[:15]) if paper.metadata.keywords else "未提取到关键词"
        references_text = "\n".join(paper.metadata.references[:10]) if paper.metadata.references else "未提取参考文献"

        return get_keypoint_prompt_doctoral(
            title=paper.metadata.title or paper.filename,
            authors=", ".join(paper.metadata.authors[:5]),
            publication=f"{paper.metadata.publication_venue} ({paper.metadata.year})",
            abstract=paper.metadata.abstract or "未提取到摘要",
            keywords=keywords_text,
            sections=sections_text,
            content=content,
            references=references_text[:2000]
        )

    def _prepare_content(self, paper: ParsedPaper, max_chars: int = 10000) -> str:
        """准备论文内容"""
        content_parts = []

        if paper.metadata.title:
            content_parts.append(f"标题: {paper.metadata.title}")

        if paper.metadata.abstract:
            content_parts.append(f"摘要: {paper.metadata.abstract}")

        for section_name, section_content in list(paper.metadata.sections.items())[:5]:
            content_parts.append(f"\n{section_name}:\n{section_content[:1500]}")

        combined = "\n\n".join(content_parts)

        if len(combined) < max_chars:
            remaining = max_chars - len(combined)
            combined += f"\n\n正文片段:\n{paper.full_text[:remaining]}"

        return combined[:max_chars]

    def _parse_keypoints_json(self, response: str) -> Dict[str, List[str]]:
        """解析要点JSON"""
        import json

        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            keypoints = json.loads(json_str)

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
            return {field: [] for field in [
                "innovations", "research_gaps", "theoretical_framework",
                "methods", "experimental_design", "datasets",
                "conclusions", "statistical_analysis", "related_work_comparison",
                "reproducibility", "contributions", "limitations"
            ]}

    def _infer_field(self, keywords: List[str]) -> str:
        """推断研究领域"""
        keyword_text = " ".join(keywords).lower()

        field_keywords = {
            "Computer Science": ["learning", "algorithm", "network", "data"],
            "Medicine": ["clinical", "patient", "disease", "treatment"],
            "Biology": ["gene", "protein", "cell", "molecular"],
        }

        for field, kw_list in field_keywords.items():
            if any(kw in keyword_text for kw in kw_list):
                return field

        return "General"

    def _calculate_file_hash(self, filepath: str) -> str:
        """计算文件MD5哈希"""
        import hashlib

        md5_hash = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)

        return md5_hash.hexdigest()
