"""数据库索引优化 - v4.1性能优化版"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings


def create_optimized_indexes():
    """创建优化的数据库索引"""

    index_sql = """

    -- ============================================================================
    -- 论文表索引优化
    -- ============================================================================

    -- 复合索引：年份 + 发表场所（常用查询组合）
    CREATE INDEX IF NOT EXISTS idx_papers_year_venue
    ON papers(year, venue)
    WHERE year IS NOT NULL AND venue IS NOT NULL;

    -- 全文搜索索引（标题和摘要）
    CREATE INDEX IF NOT EXISTS idx_papers_title_gin
    ON papers USING gin(to_tsq('english', title));

    CREATE INDEX IF NOT EXISTS idx_papers_abstract_gin
    ON papers USING gin(to_tsq('english', abstract));

    -- 哈希索引（用于精确查找）
    CREATE INDEX IF NOT EXISTS idx_papers_pdf_hash
    ON papers(pdf_hash)
    WHERE pdf_hash IS NOT NULL;

    -- 时间范围查询索引
    CREATE INDEX IF NOT EXISTS idx_papers_created_at
    ON papers(created_at DESC);

    -- ============================================================================
    -- 作者表索引优化
    -- ============================================================================

    -- 论文数量索引（用于排序热门作者）
    CREATE INDEX IF NOT EXISTS idx_authors_paper_count
    ON authors(paper_count DESC);

    -- H指数索引
    CREATE INDEX IF NOT EXISTS idx_authors_h_index
    ON authors(h_index DESC);

    -- ============================================================================
    -- 关键词表索引优化
    -- ============================================================================

    -- 热度分数索引
    CREATE INDEX IF NOT EXISTS idx_keywords_trending
    ON keywords(trending_score DESC, paper_count DESC);

    -- ============================================================================
    -- 分析表索引优化
    -- ============================================================================

    -- 复合索引：论文ID + 状态
    CREATE INDEX IF NOT EXISTS idx_analyses_paper_status
    ON analyses(paper_id, status);

    -- 状态索引（用于查询待处理任务）
    CREATE INDEX IF NOT EXISTS idx_analyses_status
    ON analyses(status)
    WHERE status != 'completed';

    -- 创建时间索引
    CREATE INDEX IF NOT EXISTS idx_analyses_created_at
    ON analyses(created_at DESC);

    -- ============================================================================
    -- 研究空白表索引优化
    -- ============================================================================

    -- 复合索引：重要性 + 难度 + 状态
    CREATE INDEX IF NOT EXISTS idx_gaps_priority_status
    ON research_gaps(importance, difficulty, status);

    -- 优先级索引（高优先级且未完成）
    CREATE INDEX IF NOT EXISTS idx_gaps_priority_unfinished
    ON research_gaps(importance, created_at DESC)
    WHERE status = 'identified';

    -- ============================================================================
    -- 关系表索引优化
    -- ============================================================================

    -- 源节点索引（用于查找出边）
    CREATE INDEX IF NOT EXISTS idx_relations_source_type
    ON relations(source_id, relation_type);

    -- 目标节点索引（用于查找入边）
    CREATE INDEX IF NOT EXISTS idx_relations_target_type
    ON relations(target_id, relation_type);

    -- 关系强度索引（用于查找强关系）
    CREATE INDEX IF NOT EXISTS idx_relations_strength
    ON relations(strength DESC)
    WHERE strength >= 0.7;

    -- ============================================================================
    -- 任务表索引优化
    -- ============================================================================

    -- 状态索引（用于查询运行中的任务）
    CREATE INDEX IF NOT EXISTS idx_tasks_status
    ON tasks(status)
    WHERE status != 'completed';

    -- 类型 + 状态索引
    CREATE INDEX IF NOT EXISTS idx_tasks_type_status
    ON tasks(task_type, status);

    -- 创建时间索引
    CREATE INDEX IF NOT EXISTS idx_tasks_created_at
    ON tasks(created_at DESC);

    -- ============================================================================
    -- 代码表索引优化
    -- ============================================================================

    -- 质量分数索引
    CREATE INDEX IF NOT EXISTS idx_code_quality
    ON generated_code(quality_score DESC);

    -- 状态索引
    CREATE INDEX IF NOT EXISTS idx_code_status
    ON generated_code(status);

    -- 版本索引
    CREATE INDEX IF NOT EXISTS idx_code_version
    ON generated_code(current_version DESC);

    -- ============================================================================
    -- 实验表索引优化
    -- ============================================================================

    -- 代码ID + 状态索引
    CREATE INDEX IF NOT EXISTS idx_experiments_code_status
    ON experiments(code_id, status);

    -- 完成时间索引
    CREATE INDEX IF NOT EXISTS idx_experiments_completed_at
    ON experiments(completed_at DESC)
    WHERE completed_at IS NOT NULL;

    -- ============================================================================
    -- 部分索引（仅对符合条件的行建索引，节省空间）
    -- ============================================================================

    -- 仅索引已完成的分析
    CREATE INDEX IF NOT EXISTS idx_analyses_completed
    ON analyses(paper_id, created_at DESC)
    WHERE status = 'completed';

    -- 仅索引重要的研究空白
    CREATE INDEX IF NOT EXISTS idx_gaps_important
    ON research_gaps(analysis_id, created_at DESC)
    WHERE importance = 'high';

    """

    return index_sql


def analyze_table_performance():
    """分析表性能（统计信息更新）"""

    analyze_sql = """

    -- 更新统计信息
    ANALYZE papers;
    ANALYZE authors;
    ANALYZE keywords;
    ANALYZE analyses;
    ANALYZE research_gaps;
    ANALYZE generated_code;
    ANALYZE relations;
    ANALYZE tasks;
    ANALYZE experiments;

    -- 真空分析（找出存储膨胀的表）
    VACUUM ANALYZE papers;
    VACUUM ANALYZE analyses;

    """

    return analyze_sql


def drop_unused_indexes():
    """删除未使用的索引（在应用新索引前执行）"""

    drop_sql = """

    -- 检查并删除未使用的索引
    -- 注意：在生产环境谨慎操作

    """

    return drop_sql


def run_optimization():
    """执行数据库优化"""
    from src.db_manager import DatabaseManager

    db = DatabaseManager()

    print("\n" + "="*80)
    print("数据库性能优化")
    print("="*80 + "\n")

    # 创建优化索引
    print("[1/2] 创建优化索引...")
    try:
        with db.get_session() as session:
            index_sql = create_optimized_indexes()

            # 执行索引创建
            for statement in index_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        session.execute(text(statement))
                    except Exception as e:
                        if "already exists" not in str(e):
                            print(f"  警告: {e}")

            session.commit()
            print("✓ 索引优化完成")
    except Exception as e:
        print(f"✗ 索引优化失败: {e}")

    # 更新统计信息
    print("\n[2/2] 更新统计信息...")
    try:
        with db.get_session() as session:
            analyze_sql = analyze_table_performance()

            for statement in analyze_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    session.execute(text(statement))

            session.commit()
            print("✓ 统计信息更新完成")
    except Exception as e:
        print(f"✗ 统计更新失败: {e}")

    print("\n" + "="*80)
    print("✓ 数据库优化完成")
    print("="*80 + "\n")


if __name__ == '__main__':
    run_optimization()
