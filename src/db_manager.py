"""数据库管理器 - v4.0院士版
提供数据库连接、会话管理、CRUD操作
"""
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from src.database import (
    Base, Paper, Author, Keyword, Analysis, ResearchGap,
    GeneratedCode, Relation, Task, User, PaperAuthor, PaperKeyword
)
from datetime import datetime
import os


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_url: str = None):
        """
        初始化数据库连接

        Args:
            db_url: 数据库URL，默认从环境变量读取
        """
        if db_url is None:
            from src.config import settings
            db_url = getattr(settings, 'database_url', None)

        if db_url is None:
            db_url = os.getenv(
                'DATABASE_URL',
                'postgresql://nuc:020509@localhost:5432/literature_analysis'
            )

        # 创建引擎
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=10,  # 连接池大小
            max_overflow=20,  # 最大溢出连接数
            pool_pre_ping=True,  # 连接健康检查
            echo=False  # 不打印SQL（生产环境）
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        print("✓ 数据库表创建成功")

    def drop_tables(self):
        """删除所有表（慎用）"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠ 数据库表已删除")

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ============================================================================
    # Paper CRUD操作
    # ============================================================================

    def create_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建论文记录"""
        with self.get_session() as session:
            # 检查是否已存在（通过pdf_hash）
            existing = session.query(Paper).filter(
                Paper.pdf_hash == paper_data.get('pdf_hash')
            ).first()

            if existing:
                print(f"  论文已存在: {existing.title}")
                return existing.to_dict()

            # 过滤掉不是Paper模型的字段(authors和keywords通过关系管理)
            paper_fields = {k: v for k, v in paper_data.items()
                          if k not in ['authors', 'keywords']}

            # 创建论文
            paper = Paper(**paper_fields)
            session.add(paper)
            session.flush()  # 获取ID

            # 添加作者
            if 'authors' in paper_data:
                for author_data in paper_data['authors']:
                    self._add_author_to_paper(session, paper.id, author_data)

            # 添加关键词
            if 'keywords' in paper_data:
                for keyword_data in paper_data['keywords']:
                    self._add_keyword_to_paper(session, paper.id, keyword_data)

            session.commit()
            session.refresh(paper)
            print(f"  ✓ 创建论文: {paper.title[:60]}")
            return paper.to_dict()

    def get_paper(self, paper_id: int) -> Optional[Dict[str, Any]]:
        """获取论文详情"""
        with self.get_session() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            return paper.to_dict() if paper else None

    def get_papers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        year_from: int = None,
        year_to: int = None,
        venue: str = None
    ) -> List[Dict[str, Any]]:
        """获取论文列表（支持搜索和过滤）"""
        with self.get_session() as session:
            query = session.query(Paper)

            # 搜索
            if search:
                query = query.filter(
                    or_(
                        Paper.title.ilike(f'%{search}%'),
                        Paper.abstract.ilike(f'%{search}%')
                    )
                )

            # 年份过滤
            if year_from:
                query = query.filter(Paper.year >= year_from)
            if year_to:
                query = query.filter(Paper.year <= year_to)

            # 发表场所过滤
            if venue:
                query = query.filter(Paper.venue.ilike(f'%{venue}%'))

            # 排序和分页
            query = query.order_by(Paper.created_at.desc())
            query = query.offset(skip).limit(limit)

            papers = query.all()
            return [paper.to_dict() for paper in papers]

    def update_paper(self, paper_id: int, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新论文信息"""
        with self.get_session() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                return None

            for key, value in paper_data.items():
                if hasattr(paper, key):
                    setattr(paper, key, value)

            paper.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(paper)
            return paper.to_dict()

    def delete_paper(self, paper_id: int) -> bool:
        """删除论文（级联删除相关数据）"""
        with self.get_session() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                return False

            session.delete(paper)
            session.commit()
            print(f"  ✓ 删除论文: {paper.title}")
            return True

    def batch_delete_papers(self, paper_ids: List[int]) -> int:
        """批量删除论文"""
        with self.get_session() as session:
            count = session.query(Paper).filter(Paper.id.in_(paper_ids)).delete()
            session.commit()
            print(f"  ✓ 批量删除 {count} 篇论文")
            return count

    # ============================================================================
    # Analysis CRUD操作
    # ============================================================================

    def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建分析记录"""
        with self.get_session() as session:
            analysis = Analysis(**analysis_data)
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis.to_dict()

    def get_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """获取分析详情"""
        with self.get_session() as session:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            return analysis.to_dict() if analysis else None

    def get_analyses_by_paper(self, paper_id: int) -> List[Dict[str, Any]]:
        """获取论文的所有分析"""
        with self.get_session() as session:
            analyses = session.query(Analysis).filter(
                Analysis.paper_id == paper_id
            ).order_by(Analysis.created_at.desc()).all()
            return [a.to_dict() for a in analyses]

    def update_analysis(self, analysis_id: int, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新分析记录"""
        with self.get_session() as session:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                return None

            for key, value in analysis_data.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)

            analysis.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(analysis)
            return analysis.to_dict()

    def delete_analysis(self, analysis_id: int) -> bool:
        """删除分析记录"""
        with self.get_session() as session:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                return False

            session.delete(analysis)
            session.commit()
            return True

    # ============================================================================
    # ResearchGap CRUD操作
    # ============================================================================

    def create_research_gap(self, gap_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建研究空白"""
        with self.get_session() as session:
            gap = ResearchGap(**gap_data)
            session.add(gap)
            session.commit()
            session.refresh(gap)
            return gap.to_dict()

    def get_gaps_by_analysis(self, analysis_id: int) -> List[Dict[str, Any]]:
        """获取分析的所有研究空白"""
        with self.get_session() as session:
            gaps = session.query(ResearchGap).filter(
                ResearchGap.analysis_id == analysis_id
            ).order_by(ResearchGap.created_at.desc()).all()
            return [gap.to_dict() for gap in gaps]

    def get_priority_gaps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取高优先级研究空白"""
        with self.get_session() as session:
            gaps = session.query(ResearchGap).filter(
                and_(
                    ResearchGap.importance == 'high',
                    ResearchGap.status == 'identified'
                )
            ).order_by(ResearchGap.created_at.desc()).limit(limit).all()
            return [gap.to_dict() for gap in gaps]

    def get_all_gaps(self, limit: int = 100, skip: int = 0, importance: str = None) -> List[Dict[str, Any]]:
        """获取所有研究空白，支持筛选"""
        with self.get_session() as session:
            query = session.query(ResearchGap)

            # 可选筛选条件
            if importance:
                query = query.filter(ResearchGap.importance == importance)

            gaps = query.order_by(ResearchGap.created_at.desc()).offset(skip).limit(limit).all()
            return [gap.to_dict() for gap in gaps]

    def get_research_gap(self, gap_id: int) -> Optional[Dict[str, Any]]:
        """获取研究空白详情"""
        with self.get_session() as session:
            gap = session.query(ResearchGap).filter(ResearchGap.id == gap_id).first()
            return gap.to_dict() if gap else None

    def update_research_gap(self, gap_id: int, gap_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新研究空白"""
        with self.get_session() as session:
            gap = session.query(ResearchGap).filter(ResearchGap.id == gap_id).first()
            if not gap:
                return None

            for key, value in gap_data.items():
                if hasattr(gap, key) and key != 'id':
                    setattr(gap, key, value)

            session.commit()
            session.refresh(gap)
            return gap.to_dict()

    # ============================================================================
    # GeneratedCode CRUD操作
    # ============================================================================

    def create_generated_code(self, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建生成的代码记录"""
        with self.get_session() as session:
            code = GeneratedCode(**code_data)
            session.add(code)
            session.commit()
            session.refresh(code)
            return code.to_dict()

    def get_code(self, code_id: int) -> Optional[Dict[str, Any]]:
        """获取代码详情"""
        with self.get_session() as session:
            code = session.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
            return code.to_dict() if code else None

    def update_code(self, code_id: int, code_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新代码"""
        with self.get_session() as session:
            code = session.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
            if not code:
                return None

            for key, value in code_data.items():
                if hasattr(code, key):
                    setattr(code, key, value)

            code.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(code)
            return code.to_dict()

    def add_user_prompt(self, code_id: int, prompt: str) -> Optional[Dict[str, Any]]:
        """添加用户修改提示"""
        with self.get_session() as session:
            code = session.query(GeneratedCode).filter(GeneratedCode.id == code_id).first()
            if not code:
                return None

            if code.user_prompts is None:
                code.user_prompts = []

            code.user_prompts.append(prompt)
            code.current_version += 1
            code.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(code)
            return code.to_dict()

    # ============================================================================
    # Relation CRUD操作（知识图谱）
    # ============================================================================

    def create_relation(self, relation_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建论文关系"""
        with self.get_session() as session:
            relation = Relation(**relation_data)
            session.add(relation)
            session.commit()
            session.refresh(relation)
            return relation.to_dict()

    def get_relations(self, paper_id: int) -> List[Dict[str, Any]]:
        """获取论文的所有关系"""
        with self.get_session() as session:
            relations = session.query(Relation).filter(
                or_(
                    Relation.source_id == paper_id,
                    Relation.target_id == paper_id
                )
            ).all()
            return [r.to_dict() for r in relations]

    def get_paper_graph(self, paper_ids: List[int] = None) -> Dict[str, Any]:
        """获取论文关系图数据"""
        with self.get_session() as session:
            query = session.query(Relation)

            if paper_ids:
                query = query.filter(
                    or_(
                        Relation.source_id.in_(paper_ids),
                        Relation.target_id.in_(paper_ids)
                    )
                )

            relations = query.all()

            # 构建图数据
            nodes = set()
            edges = []

            for rel in relations:
                nodes.add(rel.source_id)
                nodes.add(rel.target_id)
                edges.append({
                    'source': rel.source_id,
                    'target': rel.target_id,
                    'type': rel.relation_type,
                    'strength': rel.strength
                })

            # 获取节点信息
            papers = session.query(Paper).filter(Paper.id.in_(list(nodes))).all()
            node_data = {p.id: p.to_dict() for p in papers}

            return {
                'nodes': node_data,
                'edges': edges
            }

    # ============================================================================
    # Task CRUD操作
    # ============================================================================

    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建任务"""
        with self.get_session() as session:
            task = Task(**task_data)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        with self.get_session() as session:
            return session.query(Task).filter(Task.id == task_id).first()

    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> Optional[Task]:
        """更新任务状态"""
        with self.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                return None

            for key, value in task_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            session.commit()
            session.refresh(task)
            return task

    def get_running_tasks(self) -> List[Task]:
        """获取正在运行的任务"""
        with self.get_session() as session:
            return session.query(Task).filter(
                Task.status == 'running'
            ).all()

    # ============================================================================
    # 辅助方法
    # ============================================================================

    def _add_author_to_paper(self, session: Session, paper_id: int, author_data: Dict[str, Any]):
        """添加作者到论文"""
        author_name = author_data.get('name')
        if not author_name:
            return

        # 查找或创建作者
        author = session.query(Author).filter(Author.name == author_name).first()
        if not author:
            author = Author(name=author_name)
            session.add(author)
            session.flush()

        # 创建关联
        paper_author = PaperAuthor(
            paper_id=paper_id,
            author_id=author.id,
            author_order=author_data.get('order'),
            is_corresponding=author_data.get('is_corresponding', False)
        )
        session.add(paper_author)

    def _add_keyword_to_paper(self, session: Session, paper_id: int, keyword_data: str):
        """添加关键词到论文"""
        keyword_str = keyword_data.strip()
        if not keyword_str:
            return

        # 查找或创建关键词
        keyword = session.query(Keyword).filter(Keyword.keyword == keyword_str).first()
        if not keyword:
            keyword = Keyword(keyword=keyword_str)
            session.add(keyword)
            session.flush()

        # 创建关联
        paper_keyword = PaperKeyword(
            paper_id=paper_id,
            keyword_id=keyword.id
        )
        session.add(paper_keyword)

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.get_session() as session:
            return {
                'total_papers': session.query(Paper).count(),
                'total_authors': session.query(Author).count(),
                'total_keywords': session.query(Keyword).count(),
                'total_analyses': session.query(Analysis).count(),
                'total_gaps': session.query(ResearchGap).count(),
                'total_generated_code': session.query(GeneratedCode).count(),
                'total_relations': session.query(Relation).count(),
                'total_users': session.query(User).count(),
                'completed_analyses': session.query(Analysis).filter(
                    Analysis.status == 'completed'
                ).count(),
                'pending_tasks': session.query(Task).filter(
                    Task.status == 'pending'
                ).count()
            }

    # ============================================================================
    # User CRUD操作
    # ============================================================================

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        with self.get_session() as session:
            # 检查用户名是否已存在
            existing_username = session.query(User).filter(
                User.username == user_data.get('username')
            ).first()

            if existing_username:
                raise ValueError(f"用户名 '{user_data.get('username')}' 已被使用")

            # 检查邮箱是否已存在
            existing_email = session.query(User).filter(
                User.email == user_data.get('email')
            ).first()

            if existing_email:
                raise ValueError(f"邮箱 '{user_data.get('email')}' 已被注册")

            # 创建用户
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # 在session关闭前，将对象转为dict再返回
            # 使用expunge将对象从session中分离
            session.expunge(user)

            return user

    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户详情"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.expunge(user)
            return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        with self.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                session.expunge(user)
            return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        with self.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                session.expunge(user)
            return user

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """更新用户信息"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            for key, value in user_data.items():
                if hasattr(user, key) and key != 'id':  # 不允许修改ID
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user

    def update_user_login_info(self, user_id: int) -> Optional[User]:
        """更新用户登录信息（登录次数和最后登录时间）"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            user.login_count = (user.login_count or 0) + 1
            user.last_login_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user

    def change_password(self, user_id: int, new_password_hash: str) -> bool:
        """修改密码"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.password_hash = new_password_hash
            user.updated_at = datetime.utcnow()
            session.commit()
            return True
