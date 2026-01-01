"""命令行入口 v4.0 - 院士级科研智能助手"""
import asyncio
import sys
from pathlib import Path
from typing import List
import click

from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from src.config import settings
from src.db_manager import DatabaseManager
from src.async_workflow import AsyncWorkflowEngine
from src.code_generator import CodeGenerator

console = Console()

# ============================================================================
# 数据库管理命令
# ============================================================================

@click.group()
def cli():
    """院士级科研智能助手 v4.0"""
    pass


@cli.command()
def init_db():
    """初始化数据库"""
    console.print("\n[bold blue]初始化数据库...[/bold blue]")
    db = DatabaseManager()
    db.create_tables()
    console.print("[green]✓ 数据库初始化成功[/green]")


@cli.command()
def stats():
    """显示统计信息"""
    db = DatabaseManager()
    stats = db.get_statistics()

    table = Table(title="系统统计信息")
    table.add_column("指标", style="cyan")
    table.add_column("数量", style="magenta")

    for key, value in stats.items():
        table.add_row(key, str(value))

    console.print(table)


# ============================================================================
# 论文管理命令
# ============================================================================

@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--tasks', '-t', multiple=True, default=['summary', 'keypoints', 'gaps', 'code'],
              help='要执行的任务')
@click.option('--no-code', is_flag=True, help='不自动生成代码')
def analyze(pdf_path: str, tasks: tuple, no_code: bool):
    """分析单篇论文"""
    console.print(f"\n[bold cyan]分析论文:[/bold cyan] {Path(pdf_path).name}")

    db = DatabaseManager()
    workflow = AsyncWorkflowEngine(db_manager=db)

    async def run():
        result = await workflow.execute_paper_workflow(
            pdf_path=pdf_path,
            tasks=list(tasks),
            auto_generate_code=not no_code
        )

        console.print("\n[green]✓ 分析完成[/green]")
        console.print(f"  状态: {result['status']}")
        console.print(f"  耗时: {result.get('duration', 0):.2f}秒")

        if 'paper_id' in result:
            console.print(f"  论文ID: {result['paper_id']}")

        if 'gaps_count' in result:
            console.print(f"  研究空白: {result['gaps_count']}个")

        if 'code_generated' in result:
            console.print(f"  生成代码: {result['code_generated']}个")

    asyncio.run(run())


@cli.command()
@click.argument('pdf_dir', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.pdf', help='文件匹配模式')
@click.option('--limit', '-n', default=10, help='最大并发数')
def batch(pdf_dir: str, pattern: str, limit: int):
    """批量分析论文"""
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.glob(pattern))

    console.print(f"\n[bold cyan]批量分析:[/bold cyan] {len(pdf_files)} 篇论文")

    if not pdf_files:
        console.print("[yellow]⚠ 未找到PDF文件[/yellow]")
        return

    db = DatabaseManager()
    workflow = AsyncWorkflowEngine(db_manager=db)

    async def run():
        summary = await workflow.batch_process_papers(
            pdf_paths=[str(f) for f in pdf_files],
            tasks=['summary', 'keypoints']
        )

        console.print("\n[green]✓ 批量分析完成[/green]")
        console.print(f"  总数: {summary['total']}")
        console.print(f"  成功: {summary['success']}")
        console.print(f"  失败: {summary['failed']}")
        console.print(f"  耗时: {summary['duration']:.2f}秒")
        console.print(f"  平均: {summary['avg_time']:.2f}秒/篇")

    asyncio.run(run())


# ============================================================================
# 数据库查询命令
# ============================================================================

@cli.command()
@click.option('--search', '-s', help='搜索关键词')
@click.option('--limit', '-n', default=20, help='显示数量')
def list(search: str, limit: int):
    """列出论文"""
    db = DatabaseManager()
    papers = db.get_papers(search=search or '', limit=limit)

    table = Table(title=f"论文列表 ({len(papers)} 篇)")
    table.add_column("ID", style="cyan")
    table.add_column("标题", style="white")
    table.add_column("年份", style="yellow")
    table.add_column("发表场所", style="green")

    for paper in papers:
        title = paper.title[:50] + "..." if len(paper.title) > 50 else paper.title
        table.add_row(str(paper.id), title, str(paper.year or 'N/A'), paper.venue or 'N/A')

    console.print(table)


@cli.command()
@click.argument('paper_id', type=int)
def show(paper_id: int):
    """显示论文详情"""
    db = DatabaseManager()
    paper = db.get_paper(paper_id)

    if not paper:
        console.print("[red]✗ 论文不存在[/red]")
        return

    console.print(f"\n[bold cyan]ID:[/bold cyan] {paper.id}")
    console.print(f"[bold cyan]标题:[/bold cyan] {paper.title}")
    console.print(f"[bold cyan]作者:[/bold cyan] {', '.join(paper.metadata.get('authors', [])[:5])}")
    console.print(f"[bold cyan]年份:[/bold cyan] {paper.year}")
    console.print(f"[bold cyan]发表场所:[/bold cyan] {paper.venue}")
    console.print(f"[bold cyan]摘要:[/bold cyan]\n{paper.abstract[:300]}...")

    # 显示分析历史
    analyses = db.get_analyses_by_paper(paper_id)
    if analyses:
        console.print(f"\n[bold yellow]分析历史:[/bold yellow] {len(analyses)} 次")
        for analysis in analyses:
            console.print(f"  - {analysis.created_at}: {analysis.status}")


@cli.command()
@click.argument('paper_id', type=int)
def delete(paper_id: int):
    """删除论文"""
    db = DatabaseManager()
    success = db.delete_paper(paper_id)

    if success:
        console.print(f"[green]✓ 论文 {paper_id} 已删除[/green]")
    else:
        console.print(f"[red]✗ 论文 {paper_id} 不存在[/red]")


# ============================================================================
# 代码生成命令
# ============================================================================

@cli.command()
@click.argument('gap_id', type=int)
@click.option('--strategy', '-s', default='method_improvement', help='代码生成策略')
@click.option('--prompt', '-p', help='用户自定义提示')
def generate_code(gap_id: int, strategy: str, prompt: str):
    """生成代码"""
    from src.database import ResearchGap

    db = DatabaseManager()

    gap = db.db_manager.query(ResearchGap).filter(
        ResearchGap.id == gap_id
    ).first()

    if not gap:
        console.print("[red]✗ 研究空白不存在[/red]")
        return

    console.print(f"\n[cyan]生成代码:[/cyan] {gap.description[:50]}...")

    async def run():
        generator = CodeGenerator(db_manager=db)
        code_data = await generator.generate_code_async(
            research_gap=gap,
            strategy=strategy,
            user_prompt=prompt
        )

        code_record = db.create_generated_code({
            **code_data,
            'gap_id': gap_id
        })

        console.print(f"[green]✓ 代码生成完成[/green]")
        console.print(f"  代码ID: {code_record.id}")
        console.print(f"  语言: {code_record.language}")
        console.print(f"  框架: {code_record.framework}")
        console.print(f"  质量评分: {code_record.quality_score:.2f}")
        console.print(f"\n[bold]代码预览:[/bold]")
        console.print(code_record.code[:500] + "...")

    asyncio.run(run())


@cli.command()
@click.argument('code_id', type=int)
@click.argument('prompt', type=str)
def modify_code(code_id: int, prompt: str):
    """修改代码"""
    db = DatabaseManager()
    generator = CodeGenerator(db_manager=db)

    console.print(f"\n[cyan]修改代码:[/cyan] ID={code_id}")
    console.print(f"[cyan]提示:[/cyan] {prompt}")

    async def run():
        updated = await generator.modify_code_async(
            code_id=code_id,
            user_prompt=prompt,
            db_manager=db
        )

        console.print(f"[green]✓ 代码已更新到版本 {updated.current_version}[/green]")

    asyncio.run(run())


# ============================================================================
# 知识图谱命令
# ============================================================================

@cli.command()
@click.option('--paper-ids', '-p', help='论文ID列表（逗号分隔）')
def graph(paper_ids: str):
    """显示知识图谱"""
    db = DatabaseManager()

    if paper_ids:
        ids = [int(id) for id in paper_ids.split(',')]
        graph_data = db.get_paper_graph(paper_ids=ids)
    else:
        graph_data = db.get_paper_graph()

    console.print(f"\n[bold cyan]知识图谱统计:[/bold cyan]")
    console.print(f"  节点数: {len(graph_data['nodes'])}")
    console.print(f"  边数: {len(graph_data['edges'])}")

    # 显示关系类型
    relation_types = {}
    for edge in graph_data['edges']:
        rel_type = edge['type']
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

    console.print(f"\n[bold yellow]关系类型:[/bold yellow]")
    for rel_type, count in relation_types.items():
        console.print(f"  {rel_type}: {count}")


if __name__ == '__main__':
    cli()
