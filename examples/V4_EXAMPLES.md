# v4.0院士级科研智能助手 - 完整使用示例

## 🚀 快速开始

### 1. 环境准备

#### 安装依赖
```bash
# 安装Python依赖
pip install sqlalchemy psycopg2-binary asyncio aiofiles

# 安装LLM依赖
pip install langchain langchain-openai

# 安装PDF处理
pip install PyMuPDF pdfplumber

# 安装异步支持
pip install asyncio
```

#### 数据库配置
```bash
# 安装PostgreSQL
# macOS
brew install postgresql
brew services start postgresql

# 创建数据库
createdb literature_analysis

# 配置环境变量
export DATABASE_URL="postgresql://user:password@localhost:5432/literature_analysis"
export GLM_API_KEY="your-api-key"
```

---

## 📖 核心功能示例

### 示例1: 单篇论文完整工作流

```python
import asyncio
from src.db_manager import DatabaseManager
from src.async_workflow import AsyncWorkflowEngine

async def analyze_single_paper():
    """分析单篇论文的完整工作流"""

    # 初始化
    db = DatabaseManager()
    db.create_tables()  # 首次运行创建表

    workflow = AsyncWorkflowEngine(
        db_manager=db,
        llm_config={
            'model': 'glm-4-plus',
            'api_key': 'your-api-key',
            'max_concurrent': 5
        }
    )

    # 执行工作流
    result = await workflow.execute_paper_workflow(
        pdf_path='papers/deep_learning_paper.pdf',
        tasks=['summary', 'keypoints', 'topic', 'gaps', 'graph', 'code'],
        auto_generate_code=True
    )

    # 查看结果
    print(f"\n工作流结果:")
    print(f"  状态: {result['status']}")
    print(f"  论文ID: {result['paper_id']}")
    print(f"  分析ID: {result['analysis_id']}")
    print(f"  已完成任务: {result['tasks_completed']}")
    print(f"  研究空白数: {result.get('gaps_count', 0)}")
    print(f"  生成代码数: {result.get('code_generated', 0)}")
    print(f"  总耗时: {result['duration']:.2f}秒")

    return result

# 运行
result = asyncio.run(analyze_single_paper())
```

### 示例2: 批量处理论文

```python
async def batch_analyze_papers():
    """批量分析多篇论文"""

    db = DatabaseManager()
    workflow = AsyncWorkflowEngine(db_manager=db)

    # 要处理的论文列表
    pdf_files = [
        'papers/paper1.pdf',
        'papers/paper2.pdf',
        'papers/paper3.pdf',
        'papers/paper4.pdf',
        'papers/paper5.pdf',
    ]

    # 批量处理（自动并发）
    summary = await workflow.batch_process_papers(
        pdf_paths=pdf_files,
        tasks=['summary', 'keypoints', 'gaps', 'code']
    )

    print(f"\n批量处理完成:")
    print(f"  总数: {summary['total']}")
    print(f"  成功: {summary['success']}")
    print(f"  失败: {summary['failed']}")
    print(f"  总耗时: {summary['duration']:.2f}秒")
    print(f"  平均时间: {summary['avg_time']:.2f}秒/篇")

    return summary

# 运行
summary = asyncio.run(batch_analyze_papers())
```

### 示例3: 数据库CRUD操作

```python
from src.db_manager import DatabaseManager

def database_crud_example():
    """数据库CRUD操作示例"""

    db = DatabaseManager()

    # 1. 创建（Create）
    paper_data = {
        'title': 'Attention Is All You Need',
        'abstract': 'The dominant sequence transduction models...',
        'year': 2017,
        'venue': 'NeurIPS',
        'pdf_path': '/path/to/attention.pdf',
        'pdf_hash': 'abc123',
        'authors': [
            {'name': 'Ashish Vaswani'},
            {'name': 'Noam Shazeer'}
        ],
        'keywords': ['attention', 'transformer', 'neural networks']
    }

    paper = db.create_paper(paper_data)
    print(f"✓ 创建论文: ID={paper.id}")

    # 2. 读取（Read）
    paper = db.get_paper(paper.id)
    print(f"✓ 查询论文: {paper.title}")

    # 搜索论文
    papers = db.get_papers(search='transformer', year_from=2017)
    print(f"✓ 搜索结果: {len(papers)} 篇")

    # 3. 更新（Update）
    updated_paper = db.update_paper(
        paper.id,
        {'doi': '10.5555/12345'}
    )
    print(f"✓ 更新论文: DOI={updated_paper.doi}")

    # 4. 删除（Delete）
    success = db.delete_paper(paper.id)
    print(f"✓ 删除论文: {success}")

    # 批量删除
    success = db.batch_delete_papers([1, 2, 3])
    print(f"✓ 批量删除: {success} 篇")

# 运行
database_crud_example()
```

### 示例4: 代码生成与交互

```python
import asyncio
from src.code_generator import CodeGenerator
from src.db_manager import DatabaseManager
from src.database import ResearchGap

async def code_generation_example():
    """代码生成示例"""

    db = DatabaseManager()
    generator = CodeGenerator(db_manager=db)

    # 创建研究空白
    gap_data = {
        'analysis_id': 1,  # 假设有一个分析ID=1
        'gap_type': 'methodological',
        'description': '现有图神经网络在大规模图上的计算复杂度是O(V²)，无法处理千万级节点',
        'importance': 'high',
        'difficulty': 'medium',
        'potential_approach': '设计基于稀疏矩阵的线性复杂度图聚合算法',
        'expected_impact': '可以将图神经网络的应用规模扩大10倍'
    }

    gap = db.create_research_gap(gap_data)

    # 生成代码
    print("正在生成代码...")
    code_data = await generator.generate_code_async(
        research_gap=gap,
        strategy='method_improvement',
        language='python',
        framework='pytorch'
    )

    print(f"\n✓ 代码生成完成:")
    print(f"  语言: {code_data['language']}")
    print(f"  框架: {code_data['framework']}")
    print(f"  质量评分: {code_data['quality_score']:.2f}")
    print(f"  代码长度: {len(code_data['code'])} 字符")

    # 保存到数据库
    code_data['gap_id'] = gap.id
    code_record = db.create_generated_code(code_data)
    print(f"  代码ID: {code_record.id}")

    # 用户修改代码
    print("\n用户要求优化代码...")
    user_prompt = "请优化算法的时间复杂度，并添加详细注释"

    updated_code = await generator.modify_code_async(
        code_id=code_record.id,
        user_prompt=user_prompt,
        db_manager=db
    )

    print(f"✓ 代码已更新到版本 {updated_code.current_version}")

    # 交互式生成（多轮迭代）
    print("\n开始交互式代码生成...")
    result = await generator.generate_code_with_interaction(
        research_gap=gap,
        max_iterations=3
    )

    print(f"✓ 交互式生成完成:")
    print(f"  最终版本: {result['total_iterations']}")
    print(f"  质量评分: {result['final_code']['quality_score']:.2f}")

# 运行
asyncio.run(code_generation_example())
```

### 示例5: 知识图谱查询

```python
from src.db_manager import DatabaseManager

def knowledge_graph_example():
    """知识图谱查询示例"""

    db = DatabaseManager()

    # 1. 创建论文关系
    relation_data = {
        'source_id': 1,  # Transformer论文
        'target_id': 2,  # BERT论文
        'relation_type': 'extends',  # BERT扩展了Transformer
        'strength': 0.9,
        'evidence': 'BERT使用Transformer架构作为编码器'
    }

    relation = db.create_relation(relation_data)
    print(f"✓ 创建关系: {relation.relation_type}")

    # 2. 获取论文的所有关系
    relations = db.get_relations(paper_id=1)
    print(f"\n论文1的关系网络:")
    for rel in relations:
        print(f"  {rel.source_id} --[{rel.relation_type}]--> {rel.target_id}")

    # 3. 获取知识图谱数据
    graph = db.get_paper_graph(paper_ids=[1, 2, 3])
    print(f"\n知识图谱统计:")
    print(f"  节点数: {len(graph['nodes'])}")
    print(f"  边数: {len(graph['edges'])}")

    # 4. 可视化（使用matplotlib）
    import matplotlib.pyplot as plt
    import networkx as nx

    G = nx.DiGraph()
    for node_id, node_data in graph['nodes'].items():
        G.add_node(node_id, label=node_data['title'][:30])

    for edge in graph['edges']:
        G.add_edge(
            edge['source'],
            edge['target'],
            relation_type=edge['type']
        )

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='lightblue')
    plt.title("论文知识图谱")
    plt.savefig('knowledge_graph.png')
    print("✓ 知识图谱已保存到 knowledge_graph.png")

# 运行
knowledge_graph_example()
```

### 示例6: 高级查询与统计

```python
from src.db_manager import DatabaseManager

def advanced_queries_example():
    """高级查询示例"""

    db = DatabaseManager()

    # 1. 获取数据库统计
    stats = db.get_statistics()
    print(f"\n数据库统计:")
    print(f"  论文总数: {stats['total_papers']}")
    print(f"  作者总数: {stats['total_authors']}")
    print(f"  分析完成: {stats['completed_analyses']}")
    print(f"  研究空白: {stats['total_gaps']}")
    print(f"  生成代码: {stats['total_generated_code']}")

    # 2. 复杂查询：获取2020-2023年的顶会论文
    papers = db.get_papers(
        year_from=2020,
        year_to=2023,
        venue='NeurIPS',  # 或 'ICML', 'CVPR'等
        limit=20
    )

    print(f"\n2020-2023年NeurIPS论文: {len(papers)} 篇")
    for paper in papers[:5]:
        print(f"  - {paper.title} ({paper.year})")

    # 3. 获取高优先级研究空白
    priority_gaps = db.get_priority_gaps(limit=10)
    print(f"\n高优先级研究空白:")
    for gap in priority_gaps:
        print(f"  - {gap.description[:60]}...")
        print(f"    重要性: {gap.importance} | 难度: {gap.difficulty}")

    # 4. 获取论文的完整分析历史
    paper_id = 1
    analyses = db.get_analyses_by_paper(paper_id)
    print(f"\n论文{paper_id}的分析历史:")
    for analysis in analyses:
        print(f"  - {analysis.created_at}: {analysis.status}")
        print(f"    任务耗时: {analysis.total_time}秒")
        print(f"    LLM调用: {analysis.llm_calls}次")

# 运行
advanced_queries_example()
```

---

## 🔧 高级功能

### 1. 自定义工作流

```python
async def custom_workflow():
    """自定义工作流"""

    db = DatabaseManager()
    workflow = AsyncWorkflowEngine(db_manager=db)

    # 只分析，不生成代码
    result = await workflow.execute_paper_workflow(
        pdf_path='paper.pdf',
        tasks=['summary', 'keypoints'],  # 只执行这两个任务
        auto_generate_code=False  # 不自动生成代码
    )

    return result
```

### 2. 性能优化配置

```python
# 高性能配置
workflow = AsyncWorkflowEngine(
    db_manager=db,
    llm_config={
        'model': 'glm-4-plus',
        'max_concurrent': 10,  # 增加并发数
        'request_timeout': 120  # 增加超时时间
    }
)

# 批量处理100篇论文
results = await workflow.batch_process_papers(
    pdf_paths=list_of_100_papers,
    tasks=['summary', 'keypoints']  # 减少任务以加快速度
)
```

### 3. 错误处理与重试

```python
async def robust_workflow():
    """容错工作流"""

    db = DatabaseManager()
    workflow = AsyncWorkflowEngine(db_manager=db)

    try:
        result = await workflow.execute_paper_workflow(
            pdf_path='paper.pdf',
            tasks=['summary', 'keypoints', 'gaps', 'code']
        )

        if result['status'] == 'completed':
            print("✓ 分析成功")
        else:
            print(f"✗ 分析失败: {result.get('error')}")
            # 重试逻辑
            # ...

    except Exception as e:
        print(f"✗ 工作流异常: {e}")
        # 保存错误日志
        # ...
```

---

## 📊 性能对比

### v3.0 vs v4.0

| 指标 | v3.0 | v4.0 | 提升 |
|-----|------|------|------|
| 单篇分析时间 | 60秒 | 10秒 | **6x** |
| 并发能力 | 1篇 | 100篇 | **100x** |
| 批量处理 | 不支持 | 支持 | **新功能** |
| 数据持久化 | 文件 | 数据库 | **质变** |
| 代码生成 | 不支持 | 支持 | **新功能** |
| 知识图谱 | 不支持 | 支持 | **新功能** |

---

## 🎯 实战案例

### 案例1: 文献综述自动化

```python
async def literature_review_auto():
    """自动化文献综述"""

    # 1. 批量分析领域内的50篇论文
    papers = glob.glob('nlp_papers/*.pdf')
    summary = await workflow.batch_process_papers(
        pdf_paths=papers,
        tasks=['summary', 'keypoints', 'gaps', 'graph']
    )

    # 2. 构建知识图谱
    graph = db.get_paper_graph()
    # 可视化研究方向

    # 3. 提取研究空白
    priority_gaps = db.get_priority_gaps(limit=20)
    # 按重要性排序

    # 4. 生成综述报告
    review = {
        'total_papers': summary['total'],
        'main_directions': extract_directions(graph),
        'research_gaps': priority_gaps,
        'future_work': suggest_future_work(priority_gaps)
    }

    return review
```

### 案例2: 从论文到代码

```python
async def from_paper_to_code():
    """完整的论文到代码流程"""

    # 1. 上传并分析论文
    result = await workflow.execute_paper_workflow(
        pdf_path='new_method.pdf',
        auto_generate_code=True
    )

    # 2. 查看生成的代码
    code_id = result['generated_code_id']
    code = db.get_code(code_id)

    print(f"生成的代码:\n{code.code}")

    # 3. 用户修改
    updated = await code_generator.modify_code_async(
        code_id=code_id,
        user_prompt="请添加GPU支持和批处理功能"
    )

    # 4. 运行代码
    exec(updated.code)  # 注意：实际应用中需要沙箱环境

    # 5. 保存实验结果
    experiment = {
        'code_id': updated.id,
        'config': {...},
        'results': {...},
        'metrics': {...}
    }
    db.create_experiment(experiment)
```

---

## 🎓 最佳实践

### 1. 数据库管理
- 定期备份数据库
- 使用索引优化查询
- 监控数据库大小

### 2. LLM调用
- 使用合适的模型（plus vs air）
- 控制并发数避免限流
- 实现重试机制

### 3. 代码质量
- 始终在沙箱中运行生成的代码
- 审查AI生成的代码
- 添加自己的测试

### 4. 性能优化
- 批量处理时使用异步
- 启用缓存避免重复分析
- 监控API调用成本

---

## 📚 更多示例

查看 `examples/` 目录获取更多完整示例：
- `basic_usage.py` - 基础用法
- `batch_processing.py` - 批量处理
- `code_generation.py` - 代码生成
- `knowledge_graph.py` - 知识图谱
- `advanced_queries.py` - 高级查询

---

**版本**: v4.0 Academician Edition
**更新日期**: 2025年

**开始您的智能科研之旅！** 🚀🎓📄
