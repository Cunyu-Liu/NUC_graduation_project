"""知识图谱构建器 - 自动构建论文关系网络
基于论文内容相似度、关键词重叠、引用关系等建立连接
"""
import asyncio
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.db_manager import DatabaseManager
from src.database import Paper, Relation


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    # 关系类型定义
    RELATION_TYPES = {
        'similar_topic': {'threshold': 0.7, 'weight': 0.8},  # 主题相似
        'shares_keywords': {'threshold': 0.5, 'weight': 0.6},  # 关键词共享
        'same_venue': {'threshold': 1.0, 'weight': 0.3},  # 同一会刊
        'same_year': {'threshold': 1.0, 'weight': 0.2},  # 同年发表
        'cites': {'threshold': 1.0, 'weight': 1.0},  # 引用关系（需要进一步实现）
    }

    def __init__(self, db_manager: DatabaseManager = None):
        """
        初始化知识图谱构建器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager or DatabaseManager()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )

    async def build_graph_for_papers(
        self,
        paper_ids: List[int] = None,
        min_similarity: float = 0.3,
        max_relations_per_paper: int = 10
    ) -> Dict[str, Any]:
        """
        为指定论文构建知识图谱

        Args:
            paper_ids: 论文ID列表，如果为None则使用所有论文
            min_similarity: 最小相似度阈值
            max_relations_per_paper: 每篇论文最大关系数

        Returns:
            构建结果统计
        """
        print(f"\n{'='*80}")
        print("开始构建知识图谱...")
        print(f"{'='*80}\n")

        # 获取论文数据
        papers = self._get_papers(paper_ids)
        if len(papers) < 2:
            print("论文数量不足，无法构建知识图谱")
            return {'nodes': 0, 'edges': 0, 'message': '论文数量不足'}

        print(f"获取到 {len(papers)} 篇论文")

        # 清空现有关系（如果指定了特定论文）
        if paper_ids:
            self._clear_existing_relations(paper_ids)

        # 计算内容相似度并创建关系
        relations_created = 0

        # 1. 基于内容的相似度
        content_relations = self._build_content_relations(
            papers, min_similarity, max_relations_per_paper
        )
        relations_created += len(content_relations)

        # 2. 基于关键词的相似度
        keyword_relations = self._build_keyword_relations(
            papers, max_relations_per_paper
        )
        relations_created += len(keyword_relations)

        # 3. 基于元数据的关系（会刊、年份）
        meta_relations = self._build_meta_relations(papers)
        relations_created += len(meta_relations)

        # 合并所有关系并去重
        all_relations = self._merge_relations(
            content_relations + keyword_relations + meta_relations
        )

        # 保存到数据库
        saved_count = self._save_relations(all_relations)

        result = {
            'nodes': len(papers),
            'edges': saved_count,
            'relation_types': self._count_relation_types(all_relations),
            'message': f'成功构建知识图谱: {len(papers)} 个节点, {saved_count} 条边'
        }

        print(f"\n✓ 知识图谱构建完成: {result['message']}")
        return result

    def _get_papers(self, paper_ids: List[int] = None) -> List[Dict]:
        """获取论文数据"""
        if paper_ids:
            return self.db.batch_get_papers(paper_ids)
        else:
            # 获取所有论文（限制1000篇以避免内存问题）
            return self.db.get_papers(limit=1000)

    def _clear_existing_relations(self, paper_ids: List[int]):
        """清除指定论文的现有关系"""
        with self.db.get_session() as session:
            # 删除与这些论文相关的所有关系
            session.query(Relation).filter(
                (Relation.source_id.in_(paper_ids)) |
                (Relation.target_id.in_(paper_ids))
            ).delete(synchronize_session=False)

    def _build_content_relations(
        self,
        papers: List[Dict],
        min_similarity: float,
        max_relations: int
    ) -> List[Dict]:
        """基于论文内容构建相似度关系"""
        if len(papers) < 2:
            return []

        print("  - 计算内容相似度...")

        # 准备文本数据
        texts = []
        for paper in papers:
            text_parts = [
                paper.get('title', ''),
                paper.get('abstract', ''),
                ' '.join(paper.get('metadata', {}).get('keywords', []))
            ]
            texts.append(' '.join(filter(None, text_parts)))

        # 计算TF-IDF和相似度
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
        except Exception as e:
            print(f"    TF-IDF计算失败: {e}")
            return []

        relations = []
        n = len(papers)

        for i in range(n):
            # 找出与当前论文最相似的其他论文
            similarities = []
            for j in range(n):
                if i != j:
                    sim = similarity_matrix[i][j]
                    if sim >= min_similarity:
                        similarities.append((j, sim))

            # 按相似度排序并取前N个
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:max_relations]

            for j, sim in similarities:
                # 确保source_id < target_id避免重复
                source_id = papers[i]['id']
                target_id = papers[j]['id']

                if source_id > target_id:
                    source_id, target_id = target_id, source_id

                relations.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relation_type': 'similar_topic',
                    'strength': float(sim),
                    'evidence': f'内容相似度: {sim:.3f}'
                })

        print(f"    找到 {len(relations)} 个内容相似关系")
        return relations

    def _build_keyword_relations(
        self,
        papers: List[Dict],
        max_relations: int
    ) -> List[Dict]:
        """基于关键词构建关系"""
        print("  - 分析关键词关系...")

        # 构建关键词到论文的倒排索引
        keyword_to_papers = defaultdict(set)
        paper_keywords = {}

        for paper in papers:
            paper_id = paper['id']
            keywords = paper.get('metadata', {}).get('keywords', [])
            paper_keywords[paper_id] = set(keywords)

            for kw in keywords:
                keyword_to_papers[kw].add(paper_id)

        # 基于关键词共现计算关系
        relations = []
        n = len(papers)

        for i in range(n):
            paper_i = papers[i]
            id_i = paper_i['id']
            keywords_i = paper_keywords.get(id_i, set())

            if not keywords_i:
                continue

            keyword_scores = defaultdict(float)

            # 找出与当前论文有关键词重叠的其他论文
            for kw in keywords_i:
                for other_id in keyword_to_papers[kw]:
                    if other_id != id_i:
                        keyword_scores[other_id] += 1

            # 计算Jaccard相似度
            similarities = []
            for other_id, common_count in keyword_scores.items():
                keywords_j = paper_keywords.get(other_id, set())
                if keywords_j:
                    union_count = len(keywords_i | keywords_j)
                    jaccard = common_count / union_count if union_count > 0 else 0
                    if jaccard >= 0.2:  # 至少20%的关键词重叠
                        similarities.append((other_id, jaccard))

            # 排序并取前N
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:max_relations]

            for other_id, sim in similarities:
                # 确保source_id < target_id
                source_id = min(id_i, other_id)
                target_id = max(id_i, other_id)

                relations.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relation_type': 'shares_keywords',
                    'strength': float(sim),
                    'evidence': f'关键词Jaccard相似度: {sim:.3f}'
                })

        print(f"    找到 {len(relations)} 个关键词关系")
        return relations

    def _build_meta_relations(self, papers: List[Dict]) -> List[Dict]:
        """基于元数据构建关系（会刊、年份）"""
        print("  - 分析元数据关系...")

        relations = []

        # 按会刊分组
        venue_groups = defaultdict(list)
        year_groups = defaultdict(list)

        for paper in papers:
            paper_id = paper['id']
            venue = paper.get('venue')
            year = paper.get('year')

            if venue:
                venue_groups[venue].append(paper_id)
            if year:
                year_groups[year].append(paper_id)

        # 创建同会刊关系（限制每对论文只创建一次）
        for venue, paper_ids in venue_groups.items():
            if len(paper_ids) >= 2:
                for i in range(len(paper_ids)):
                    for j in range(i + 1, len(paper_ids)):
                        relations.append({
                            'source_id': paper_ids[i],
                            'target_id': paper_ids[j],
                            'relation_type': 'same_venue',
                            'strength': 0.3,
                            'evidence': f'发表于: {venue}'
                        })

        # 创建同年关系
        for year, paper_ids in year_groups.items():
            if len(paper_ids) >= 2:
                for i in range(len(paper_ids)):
                    for j in range(i + 1, len(paper_ids)):
                        # 检查是否已存在同会刊关系
                        existing = any(
                            r['source_id'] == min(paper_ids[i], paper_ids[j]) and
                            r['target_id'] == max(paper_ids[i], paper_ids[j]) and
                            r['relation_type'] == 'same_venue'
                            for r in relations
                        )
                        if not existing:
                            relations.append({
                                'source_id': paper_ids[i],
                                'target_id': paper_ids[j],
                                'relation_type': 'same_year',
                                'strength': 0.2,
                                'evidence': f'发表年份: {year}'
                            })

        print(f"    找到 {len(relations)} 个元数据关系")
        return relations

    def _merge_relations(self, relations: List[Dict]) -> List[Dict]:
        """合并关系，去重并选择最强关系"""
        relation_map = {}

        for rel in relations:
            key = (rel['source_id'], rel['target_id'])

            if key in relation_map:
                # 如果已存在关系，保留强度更高的
                existing = relation_map[key]
                if rel['strength'] > existing['strength']:
                    relation_map[key] = rel
            else:
                relation_map[key] = rel

        return list(relation_map.values())

    def _save_relations(self, relations: List[Dict]) -> int:
        """保存关系到数据库"""
        count = 0
        for rel_data in relations:
            try:
                self.db.create_relation(rel_data)
                count += 1
            except Exception as e:
                # 忽略重复关系错误
                if 'unique_relation' not in str(e):
                    print(f"    保存关系失败: {e}")

        return count

    def _count_relation_types(self, relations: List[Dict]) -> Dict[str, int]:
        """统计关系类型分布"""
        counts = defaultdict(int)
        for rel in relations:
            counts[rel['relation_type']] += 1
        return dict(counts)

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        stats = self.db.get_statistics()
        return {
            'total_nodes': stats.get('total_papers', 0),
            'total_edges': stats.get('total_relations', 0),
            'avg_degree': stats.get('total_relations', 0) * 2 / max(stats.get('total_papers', 1), 1)
        }


async def build_knowledge_graph_for_papers(
    paper_ids: List[int] = None,
    db_manager: DatabaseManager = None
) -> Dict[str, Any]:
    """
    便捷函数：为论文构建知识图谱

    Args:
        paper_ids: 论文ID列表
        db_manager: 数据库管理器

    Returns:
        构建结果
    """
    builder = KnowledgeGraphBuilder(db_manager)
    return await builder.build_graph_for_papers(paper_ids)
