"""科研文献摘要提取系统 - 主程序入口"""
import sys
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from src.config import settings
from src.pdf_parser import PDFParser, ParsedPaper
from src.summary_generator import SummaryGenerator
from src.keypoint_extractor import KeypointExtractor
from src.topic_clustering import TopicClustering

# 初始化控制台
console = Console()


def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        科研文献摘要提取系统 v1.0                              ║
║        Research Paper Summary Extraction System               ║
║                                                              ║
║        基于 DeepSeek API 与 LangChain                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


@click.group()
def cli():
    """科研文献摘要提取系统 - 基于大语言模型的智能文献分析工具"""
    print_banner()


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.option('--no-save', is_flag=True, help='不保存到文件，只显示结果')
def parse(pdf_file: str, output: Optional[str], no_save: bool):
    """
    解析PDF文件并提取文本内容

    PDF_FILE: 要解析的PDF文件路径
    """
    try:
        with console.status("[bold green]正在解析PDF文件...", spinner="dots"):
            parser = PDFParser()
            paper = parser.parse_pdf(pdf_file)

        # 显示解析结果
        console.print(f"\n[bold green]✓[/bold green] 文件解析成功!")
        console.print(f"\n文件名: {paper.filename}")
        console.print(f"页数: {paper.page_count}")
        console.print(f"总字符数: {len(paper.full_text)}")

        # 显示元数据
        if paper.metadata.title:
            console.print(f"\n[bold]标题:[/bold] {paper.metadata.title}")

        if paper.metadata.abstract:
            console.print(f"\n[bold]摘要:[/bold]")
            console.print(paper.metadata.abstract[:300] + "..." if len(paper.metadata.abstract) > 300 else paper.metadata.abstract)

        if paper.metadata.keywords:
            console.print(f"\n[bold]关键词:[/bold] {', '.join(paper.metadata.keywords)}")

        if paper.metadata.sections:
            console.print(f"\n[bold]章节:[/bold]")
            for section_name in paper.metadata.sections.keys():
                console.print(f"  - {section_name}")

        # 保存结果
        if not no_save:
            output_path = Path(output) if output else settings.output_dir / f"{Path(pdf_file).stem}_parsed.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"文件名: {paper.filename}\n")
                f.write(f"页数: {paper.page_count}\n")
                f.write(f"\n{'='*60}\n\n")
                f.write(f"标题: {paper.metadata.title}\n")
                f.write(f"摘要: {paper.metadata.abstract}\n")
                f.write(f"关键词: {', '.join(paper.metadata.keywords)}\n")
                f.write(f"\n{'='*60}\n\n")
                f.write("完整文本:\n\n")
                f.write(paper.full_text)

            console.print(f"\n[bold green]✓[/bold green] 解析结果已保存到: {output_path}")

    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] 解析失败: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--model', '-m', help='使用的模型名称')
@click.option('--temperature', '-t', type=float, help='温度参数')
def summarize(pdf_file: str, output: Optional[str], model: Optional[str], temperature: Optional[float]):
    """
    生成论文摘要

    PDF_FILE: 要处理的PDF文件路径
    """
    try:
        # 步骤1: 解析PDF
        with console.status("[bold green]正在解析PDF文件...", spinner="dots"):
            parser = PDFParser()
            paper = parser.parse_pdf(pdf_file)
        console.print("[bold green]✓[/bold green] PDF解析完成")

        # 步骤2: 生成摘要
        console.print("[bold yellow]正在生成摘要...[/bold yellow]")
        generator = SummaryGenerator(model=model, temperature=temperature)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("调用LLM生成摘要...", total=None)
            summary = generator.generate_summary(
                paper,
                save=True,
                output_dir=Path(output) if output else None
            )

        # 显示摘要
        console.print(f"\n[bold green]✓[/bold green] 摘要生成成功!")
        console.print(Panel(summary, title="生成的摘要", border_style="green"))

        # 显示保存路径
        output_dir = Path(output) if output else settings.summary_output_dir
        output_path = output_dir / f"{Path(pdf_file).stem}_summary.txt"
        console.print(f"\n[bold]摘要已保存到:[/bold] {output_path}")

    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] 处理失败: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--model', '-m', help='使用的模型名称')
def extract(pdf_file: str, output: Optional[str], model: Optional[str]):
    """
    提取论文要点（创新点、方法、结论等）

    PDF_FILE: 要处理的PDF文件路径
    """
    try:
        # 步骤1: 解析PDF
        with console.status("[bold green]正在解析PDF文件...", spinner="dots"):
            parser = PDFParser()
            paper = parser.parse_pdf(pdf_file)
        console.print("[bold green]✓[/bold green] PDF解析完成")

        # 步骤2: 提取要点
        console.print("[bold yellow]正在提取核心要点...[/bold yellow]")
        extractor = KeypointExtractor(model=model)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("调用LLM提取要点...", total=None)
            keypoints = extractor.extract_keypoints(
                paper,
                save=True,
                output_dir=Path(output) if output else None
            )

        # 显示要点
        console.print(f"\n[bold green]✓[/bold green] 要点提取成功!")

        # 创建表格显示要点
        field_names = {
            "innovations": ("🔥", "核心创新点"),
            "methods": ("🔧", "主要方法"),
            "experiments": ("🧪", "实验设计"),
            "conclusions": ("💡", "主要结论"),
            "contributions": ("🎯", "学术贡献"),
            "limitations": ("⚠️", "局限性")
        }

        for field, (icon, name) in field_names.items():
            items = keypoints.get(field, [])
            if items:
                console.print(f"\n[bold]{icon} {name}[/bold]")
                for i, item in enumerate(items, 1):
                    console.print(f"  {i}. {item}")

        # 显示保存路径
        output_dir = Path(output) if output else settings.keypoints_output_dir
        output_path = output_dir / f"{Path(pdf_file).stem}_keypoints.txt"
        console.print(f"\n[bold]要点报告已保存到:[/bold] {output_path}")

    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] 处理失败: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('pdf_files', nargs=-1, type=click.Path(exists=True))
@click.option('--clusters', '-n', type=int, default=5, help='聚类数量')
@click.option('--method', '-m', type=click.Choice(['kmeans', 'dbscan', 'hierarchical']), default='kmeans', help='聚类方法')
@click.option('--language', '-l', type=click.Choice(['chinese', 'english']), default='chinese', help='论文语言')
def cluster(pdf_files: tuple, clusters: int, method: str, language: str):
    """
    对多篇论文进行主题聚类分析

    PDF_FILES: 要分析的PDF文件路径（可多个）
    """
    if len(pdf_files) < 2:
        console.print("[bold red]✗[/bold red] 至少需要2篇论文才能进行聚类分析", style="red")
        sys.exit(1)

    try:
        # 步骤1: 解析所有PDF
        console.print(f"[bold yellow]正在解析 {len(pdf_files)} 篇论文...[/bold yellow]")
        parser = PDFParser()
        papers = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("解析PDF文件...", total=len(pdf_files))
            for pdf_file in pdf_files:
                try:
                    paper = parser.parse_pdf(pdf_file)
                    papers.append(paper)
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"\n[bold yellow]⚠[/bold yellow] 跳过文件 {pdf_file}: {e}")

        console.print(f"[bold green]✓[/bold green] 成功解析 {len(papers)} 篇论文")

        if len(papers) < 2:
            console.print("[bold red]✗[/bold red] 成功解析的论文数量不足2篇", style="red")
            sys.exit(1)

        # 步骤2: 执行聚类
        console.print(f"[bold yellow]正在进行主题聚类 (方法={method}, 聚类数={clusters})...[/bold yellow]")
        clustering = TopicClustering(
            n_clusters=clusters,
            clustering_method=method,
            language=language
        )

        results = clustering.cluster_papers(papers)

        # 显示聚类结果
        console.print(f"\n[bold green]✓[/bold green] 聚类完成! 共发现 {results['unique_clusters']} 个主题类别")

        # 创建聚类信息表格
        table = Table(title="\n聚类结果概览", show_header=True, header_style="bold magenta")
        table.add_column("聚类ID", style="cyan", width=6)
        table.add_column("论文数量", justify="center", style="green")
        table.add_column("核心关键词", style="yellow")

        for cluster_id, info in results['cluster_analysis'].items():
            keywords_str = ", ".join(info['top_keywords'][:5])
            table.add_row(
                str(cluster_id),
                str(info['paper_count']),
                keywords_str
            )

        console.print(table)

        # 显示保存路径
        console.print(f"\n[bold]聚类可视化已保存到:[/bold] {settings.cluster_output_dir / 'cluster_visualization.png'}")
        console.print(f"[bold]聚类报告已保存到:[/bold] {settings.cluster_output_dir / 'cluster_report.txt'}")

    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] 聚类失败: {e}", style="red")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--model', '-m', help='使用的模型名称')
def analyze(pdf_file: str, output: Optional[str], model: Optional[str]):
    """
    完整分析：生成摘要 + 提取要点

    PDF_FILE: 要处理的PDF文件路径
    """
    try:
        # 步骤1: 解析PDF
        with console.status("[bold green]正在解析PDF文件...", spinner="dots"):
            parser = PDFParser()
            paper = parser.parse_pdf(pdf_file)
        console.print("[bold green]✓[/bold green] PDF解析完成")

        # 步骤2: 生成摘要
        console.print("[bold yellow]步骤 1/2: 正在生成摘要...[/bold yellow]")
        generator = SummaryGenerator(model=model)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("调用LLM生成摘要...", total=None)
            summary = generator.generate_summary(
                paper,
                save=True,
                output_dir=Path(output) if output else None
            )

        console.print("[bold green]✓[/bold green] 摘要生成完成")

        # 步骤3: 提取要点
        console.print("[bold yellow]步骤 2/2: 正在提取要点...[/bold yellow]")
        extractor = KeypointExtractor(model=model)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("调用LLM提取要点...", total=None)
            keypoints = extractor.extract_keypoints(
                paper,
                save=True,
                output_dir=Path(output) if output else None
            )

        console.print("[bold green]✓[/bold green] 要点提取完成")

        # 显示结果摘要
        console.print(f"\n[bold green]✓[/bold green] 完整分析成功!")
        console.print(Panel(summary[:400] + "..." if len(summary) > 400 else summary, title="生成的摘要", border_style="green"))

        # 显示要点概览
        console.print("\n[bold]核心要点:[/bold]")
        console.print(f"  • 创新点: {len(keypoints.get('innovations', []))} 个")
        console.print(f"  • 方法: {len(keypoints.get('methods', []))} 个")
        console.print(f"  • 结论: {len(keypoints.get('conclusions', []))} 个")

        # 显示保存路径
        output_dir = Path(output) if output else None
        if output_dir:
            console.print(f"\n[bold]结果已保存到:[/bold] {output_dir}")
        else:
            console.print(f"\n[bold]摘要已保存到:[/bold] {settings.summary_output_dir}")
            console.print(f"[bold]要点已保存到:[/bold] {settings.keypoints_output_dir}")

    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] 处理失败: {e}", style="red")
        sys.exit(1)


@cli.command()
def config():
    """显示当前配置"""
    config_table = Table(title="系统配置", show_header=True, header_style="bold magenta")
    config_table.add_column("配置项", style="cyan")
    config_table.add_column("值", style="yellow")

    config_table.add_row("DeepSeek API Key", f"{settings.deepseek_api_key[:10]}..." if settings.deepseek_api_key else "未设置")
    config_table.add_row("Base URL", settings.deepseek_base_url)
    config_table.add_row("模型", settings.default_model)
    config_table.add_row("温度", str(settings.default_temperature))
    config_table.add_row("最大Tokens", str(settings.max_tokens))
    config_table.add_row("输出目录", str(settings.output_dir))

    console.print(config_table)

    # 检查API Key
    if not settings.deepseek_api_key:
        console.print("\n[bold red]⚠ 警告: 未设置DEEPSEEK_API_KEY环境变量[/bold red]")
        console.print("请在 .env 文件中设置 DEEPSEEK_API_KEY")
    else:
        console.print("\n[bold green]✓[/bold green] 系统配置正常")


def main():
    """主函数"""
    cli()


if __name__ == "__main__":
    main()
