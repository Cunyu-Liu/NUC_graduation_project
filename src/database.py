"""数据库模型与ORM - v4.0院士版
使用SQLAlchemy ORM，支持PostgreSQL
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON, Enum, Index,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()


# ============================================================================
# 论文相关模型
# ============================================================================

class Paper(Base):
    """论文表"""
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(Text)
    pdf_path = Column(String(1000))
    pdf_hash = Column(String(64), unique=True, index=True)  # MD5去重

    # 元数据
    year = Column(Integer, index=True)
    venue = Column(String(500), index=True)
    doi = Column(String(200))
    page_count = Column(Integer)
    language = Column(String(10), default='unknown')

    # 灵活存储所有元数据
    metadata = Column(JSONB, default={})

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("PaperKeyword", back_populates="paper", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="paper", cascade="all, delete-orphan")
    outgoing_relations = relationship(
        "Relation",
        foreign_keys="Relation.source_id",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    incoming_relations = relationship(
        "Relation",
        foreign_keys="Relation.target_id",
        back_populates="target",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Paper(id={self.id}, title='{self.title[:50]}...')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'year': self.year,
            'venue': self.venue,
            'doi': self.doi,
            'page_count': self.page_count,
            'language': self.language,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Author(Base):
    """作者表（去重）"""
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    affiliation = Column(String(500))
    email = Column(String(200))

    # 统计信息
    paper_count = Column(Integer, default=0)
    h_index = Column(Integer, default=0)  # 可以后续计算

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    papers = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"


class PaperAuthor(Base):
    """论文-作者关联表"""
    __tablename__ = 'paper_authors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('authors.id', ondelete='CASCADE'), nullable=False)
    author_order = Column(Integer)  # 作者顺序
    is_corresponding = Column(Boolean, default=False)  # 是否通讯作者

    # 关系
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")

    # 联合唯一索引
    __table_args__ = (
        UniqueConstraint('paper_id', 'author_id', name='unique_paper_author'),
    )

    def __repr__(self):
        return f"<PaperAuthor(paper_id={self.paper_id}, author_id={self.author_id})>"


class Keyword(Base):
    """关键词表（去重）"""
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, unique=True, index=True)
    category = Column(String(100))  # 方法、任务、数据集等分类

    # 统计
    paper_count = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0)  # 热度分数

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    papers = relationship("PaperKeyword", back_populates="keyword", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"


class PaperKeyword(Base):
    """论文-关键词关联表"""
    __tablename__ = 'paper_keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id', ondelete='CASCADE'), nullable=False)
    relevance_score = Column(Float)  # 相关性分数

    # 关系
    paper = relationship("Paper", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="papers")

    __table_args__ = (
        UniqueConstraint('paper_id', 'keyword_id', name='unique_paper_keyword'),
    )

    def __repr__(self):
        return f"<PaperKeyword(paper_id={self.paper_id}, keyword_id={self.keyword_id})>"


# ============================================================================
# 分析相关模型
# ============================================================================

class Analysis(Base):
    """分析结果表"""
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False, index=True)

    # 分析结果（JSON格式存储）
    summary_text = Column(Text)
    keypoints = Column(JSONB, default={})  # 12类要点
    topic_analysis = Column(JSONB, default={})
    gap_analysis = Column(JSONB, default={})

    # 元数据
    analysis_version = Column(String(20), default='v4.0')
    model_used = Column(String(50))  # 使用的LLM模型
    status = Column(String(50), default='pending', index=True)  # pending, analyzing, completed, failed
    error_message = Column(Text)

    # 时间统计
    total_time = Column(Float)  # 总耗时（秒）
    llm_calls = Column(Integer, default=0)  # LLM调用次数
    tokens_used = Column(Integer, default=0)  # 使用的token数

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    paper = relationship("Paper", back_populates="analyses")
    research_gaps = relationship("ResearchGap", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Analysis(id={self.id}, paper_id={self.paper_id}, status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'summary_text': self.summary_text,
            'keypoints': self.keypoints,
            'topic_analysis': self.topic_analysis,
            'gap_analysis': self.gap_analysis,
            'status': self.status,
            'total_time': self.total_time,
            'llm_calls': self.llm_calls,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ResearchGap(Base):
    """研究空白表"""
    __tablename__ = 'research_gaps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)

    # 空白描述
    gap_type = Column(String(50), index=True)  # methodological, theoretical, data, application, evaluation
    description = Column(Text, nullable=False)
    importance = Column(String(20))  # high, medium, low
    difficulty = Column(String(20))  # low, medium, high
    potential_approach = Column(Text)
    expected_impact = Column(Text)

    # 代码生成关联
    generated_code_id = Column(Integer, ForeignKey('generated_code.id'))
    status = Column(String(50), default='identified')  # identified, code_generating, implemented, verified

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    analysis = relationship("Analysis", back_populates="research_gaps")
    generated_code = relationship("GeneratedCode", back_populates="research_gaps")

    def __repr__(self):
        return f"<ResearchGap(id={self.id}, type='{self.gap_type}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'gap_type': self.gap_type,
            'description': self.description,
            'importance': self.importance,
            'difficulty': self.difficulty,
            'potential_approach': self.potential_approach,
            'expected_impact': self.expected_impact,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# 代码相关模型
# ============================================================================

class GeneratedCode(Base):
    """生成的代码表"""
    __tablename__ = 'generated_code'

    id = Column(Integer, primary_key=True, autoincrement=True)
    gap_id = Column(Integer, ForeignKey('research_gaps.id'), nullable=False)

    # 代码内容
    code = Column(Text, nullable=False)
    language = Column(String(20))  # python, pytorch, tensorflow, etc.
    framework = Column(String(50))  # pytorch, tensorflow, sklearn, etc.
    dependencies = Column(Text)  # 依赖列表（JSON格式）
    docstring = Column(Text)  # 文档说明

    # 用户交互
    user_prompts = Column(ARRAY(Text), default=[])  # 用户的所有修改提示
    current_version = Column(Integer, default=1)

    # 执行结果
    execution_result = Column(JSONB, default={})  # 执行结果和指标
    test_passed = Column(Boolean, default=False)
    benchmark_scores = Column(JSONB, default={})  # 基准测试分数

    status = Column(String(50), default='generated')  # generated, tested, optimized, deployed
    quality_score = Column(Float)  # 代码质量评分（0-1）

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    research_gaps = relationship("ResearchGap", back_populates="generated_code")
    versions = relationship("CodeVersion", back_populates="parent_code", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="code", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GeneratedCode(id={self.id}, language='{self.language}', version={self.current_version})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'gap_id': self.gap_id,
            'code': self.code,
            'language': self.language,
            'framework': self.framework,
            'dependencies': self.dependencies,
            'docstring': self.docstring,
            'user_prompts': self.user_prompts,
            'current_version': self.current_version,
            'execution_result': self.execution_result,
            'test_passed': self.test_passed,
            'status': self.status,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CodeVersion(Base):
    """代码版本历史表"""
    __tablename__ = 'code_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_code_id = Column(Integer, ForeignKey('generated_code.id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    code_diff = Column(Text)  # 与上一版本的差异
    change_description = Column(Text)
    prompt = Column(Text)  # 生成此版本的提示词
    author = Column(String(50), default='AI')  # AI 或 User

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    parent_code = relationship("GeneratedCode", back_populates="versions")

    def __repr__(self):
        return f"<CodeVersion(id={self.id}, version={self.version_number}, author='{self.author}')>"


class Experiment(Base):
    """实验记录表"""
    __tablename__ = 'experiments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey('generated_code.id', ondelete='CASCADE'), nullable=False)

    # 实验配置
    config = Column(JSONB, default={})
    hyperparameters = Column(JSONB, default={})
    dataset_info = Column(JSONB, default={})

    # 实验结果
    results = Column(JSONB, default={})
    metrics = Column(JSONB, default={})  # 性能指标
    logs = Column(Text)

    # 状态
    status = Column(String(50), default='running')  # running, completed, failed
    duration = Column(Float)  # 运行时长（秒）

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)

    # 关系
    code = relationship("GeneratedCode", back_populates="experiments")

    def __repr__(self):
        return f"<Experiment(id={self.id}, code_id={self.code_id}, status='{self.status}')>"


# ============================================================================
# 知识图谱相关模型
# ============================================================================

class Relation(Base):
    """论文关系表（知识图谱）"""
    __tablename__ = 'relations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False, index=True)

    relation_type = Column(String(50), index=True)  # cites, extends, contradicts, applies, improves
    strength = Column(Float, default=0.5)  # 关系强度（0-1）
    evidence = Column(Text)  # 证据描述
    metadata = Column(JSONB, default={})  # 额外信息

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    source = relationship("Paper", foreign_keys=[source_id], back_populates="outgoing_relations")
    target = relationship("Paper", foreign_keys=[target_id], back_populates="incoming_relations")

    __table_args__ = (
        UniqueConstraint('source_id', 'target_id', 'relation_type', name='unique_relation'),
        Index('idx_relations_source_target', 'source_id', 'target_id'),
    )

    def __repr__(self):
        return f"<Relation(id={self.id}, {self.relation_type}, {self.source_id}→{self.target_id})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type,
            'strength': self.strength,
            'evidence': self.evidence,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# 任务相关模型
# ============================================================================

class Task(Base):
    """异步任务表"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), index=True)  # analyze, generate_code, build_graph, etc.
    status = Column(String(50), default='pending', index=True)  # pending, running, completed, failed

    # 任务参数（JSON格式）
    params = Column(JSONB, default={})

    # 任务结果
    result = Column(JSONB, default={})
    error = Column(Text)

    # 进度
    progress = Column(Float, default=0.0)  # 0-100
    current_step = Column(String(200))
    total_steps = Column(Integer)

    # 时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Float)  # 总耗时

    def __repr__(self):
        return f"<Task(id={self.id}, type='{self.task_type}', status='{self.status}', progress={self.progress}%)>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
