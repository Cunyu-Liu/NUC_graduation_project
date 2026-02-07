"""知识图谱构建器 - 自动构建论文关系网络
基于论文内容相似度、关键词重叠、引用关系等建立连接
"""
import asyncio
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.db_manager import DatabaseManager
from src.database import Paper, Relation


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    # 关系类型定义（使用中文）- 已移除同年发表，新增多种有价值关系
    RELATION_TYPES = {
        '主题相似': {'threshold': 0.7, 'weight': 0.8},      # 主题相似
        '关键词共享': {'threshold': 0.5, 'weight': 0.6},    # 关键词共享
        '同一会刊': {'threshold': 1.0, 'weight': 0.3},      # 同一会刊
        '共同作者': {'threshold': 1.0, 'weight': 0.7},      # 共同作者关系
        '引用关系': {'threshold': 1.0, 'weight': 1.0},      # 引用关系
        '方法相似': {'threshold': 0.6, 'weight': 0.75},     # 方法论相似
        '研究脉络': {'threshold': 0.5, 'weight': 0.65},     # 时间演进关系
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

        # 3. 基于元数据的关系（会刊）
        meta_relations = self._build_meta_relations(papers)
        relations_created += len(meta_relations)

        # 4. 共同作者关系
        author_relations = self._build_author_relations(papers)
        relations_created += len(author_relations)

        # 5. 方法论相似关系
        method_relations = self._build_method_relations(
            papers, max_relations_per_paper
        )
        relations_created += len(method_relations)

        # 6. 研究脉络关系（基于时间和主题）
        evolution_relations = self._build_evolution_relations(
            papers, max_relations_per_paper
        )
        relations_created += len(evolution_relations)

        # 合并所有关系并去重
        all_relations = self._merge_relations(
            content_relations + keyword_relations + meta_relations + 
            author_relations + method_relations + evolution_relations
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
                    'relation_type': '主题相似',
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
                    'relation_type': '关键词共享',
                    'strength': float(sim),
                    'evidence': f'关键词Jaccard相似度: {sim:.3f}'
                })

        print(f"    找到 {len(relations)} 个关键词关系")
        return relations

    def _build_meta_relations(self, papers: List[Dict]) -> List[Dict]:
        """基于元数据构建关系（仅会刊，年份关系已移除）"""
        print("  - 分析元数据关系...")

        relations = []

        # 按会刊分组
        venue_groups = defaultdict(list)

        for paper in papers:
            paper_id = paper['id']
            venue = paper.get('venue')

            if venue:
                venue_groups[venue].append(paper_id)

        # 创建同会刊关系（限制每对论文只创建一次）
        for venue, paper_ids in venue_groups.items():
            if len(paper_ids) >= 2:
                for i in range(len(paper_ids)):
                    for j in range(i + 1, len(paper_ids)):
                        relations.append({
                            'source_id': paper_ids[i],
                            'target_id': paper_ids[j],
                            'relation_type': '同一会刊',
                            'strength': 0.3,
                            'evidence': f'发表于: {venue}'
                        })

        print(f"    找到 {len(relations)} 个元数据关系")
        return relations

    def _build_author_relations(self, papers: List[Dict]) -> List[Dict]:
        """
        基于共同作者构建关系
        如果两篇论文有共同作者，则建立关系
        """
        print("  - 分析共同作者关系...")

        relations = []
        n = len(papers)

        # 构建作者到论文的映射
        author_to_papers: Dict[str, Set[int]] = defaultdict(set)
        paper_authors: Dict[int, Set[str]] = {}

        for paper in papers:
            paper_id = paper['id']
            # 从metadata中获取作者
            authors = paper.get('metadata', {}).get('authors', [])
            if not authors:
                authors = paper.get('authors', [])
            
            author_set = set()
            for author in authors:
                if isinstance(author, str):
                    author_name = author.strip()
                    if author_name:
                        author_set.add(author_name)
                        author_to_papers[author_name].add(paper_id)
                elif isinstance(author, dict):
                    author_name = author.get('name', '').strip()
                    if author_name:
                        author_set.add(author_name)
                        author_to_papers[author_name].add(paper_id)
            
            paper_authors[paper_id] = author_set

        # 查找有共同作者的论文对
        for i in range(n):
            paper_i = papers[i]
            id_i = paper_i['id']
            authors_i = paper_authors.get(id_i, set())

            if not authors_i:
                continue

            for j in range(i + 1, n):
                paper_j = papers[j]
                id_j = paper_j['id']
                authors_j = paper_authors.get(id_j, set())

                if not authors_j:
                    continue

                # 计算共同作者
                common_authors = authors_i & authors_j
                
                if common_authors:
                    # 根据共同作者数量计算强度
                    strength = min(1.0, len(common_authors) / max(len(authors_i), len(authors_j)) * 1.5)
                    
                    relations.append({
                        'source_id': id_i,
                        'target_id': id_j,
                        'relation_type': '共同作者',
                        'strength': float(strength),
                        'evidence': f'共同作者: {", ".join(list(common_authors)[:3])}'
                    })

        print(f"    找到 {len(relations)} 个共同作者关系")
        return relations

    def _build_method_relations(self, papers: List[Dict], max_relations: int) -> List[Dict]:
        """
        基于方法论相似度构建关系
        通过分析方法章节中的关键词来判断
        """
        print("  - 分析方法论相似关系...")

        relations = []
        n = len(papers)

        # 提取每篇论文的方法关键词
        method_keywords = {}
        method_indicators = {
            'deep learning', 'neural network', 'cnn', 'rnn', 'lstm', 'transformer',
            'bert', 'gpt', 'attention', 'gan', 'reinforcement learning',
            'supervised', 'unsupervised', 'semi-supervised', 'self-supervised',
            'classification', 'regression', 'clustering', 'generation',
            'optimization', 'gradient descent', 'adam', 'sgd',
            'cnn', 'resnet', 'vgg', 'inception', 'yolo',
            'rnn', 'lstm', 'gru', 'seq2seq', 'attention mechanism',
            '机器学习', '深度学习', '神经网络', '卷积', '循环神经网络',
            '监督学习', '无监督学习', '强化学习', '迁移学习',
            'classification', 'regression', 'clustering',
            'decision tree', 'random forest', 'svm', 'k-means',
            'naive bayes', 'logistic regression', 'linear regression'
        }

        for paper in papers:
            paper_id = paper['id']
            # 尝试从方法章节提取
            sections = paper.get('metadata', {}).get('sections', {})
            method_text = ""
            
            for section_name, section_content in sections.items():
                lower_name = section_name.lower()
                if any(keyword in lower_name for keyword in ['method', 'methodology', 'approach', 'model', 'algorithm', '方法']):
                    method_text += " " + section_content
            
            # 如果没有方法章节，使用标题和摘要
            if not method_text:
                method_text = paper.get('title', '') + " " + paper.get('abstract', '')

            # 提取方法关键词
            method_text_lower = method_text.lower()
            found_keywords = set()
            
            for indicator in method_indicators:
                if indicator in method_text_lower:
                    found_keywords.add(indicator)
            
            method_keywords[paper_id] = found_keywords

        # 计算方法相似度
        for i in range(n):
            paper_i = papers[i]
            id_i = paper_i['id']
            keywords_i = method_keywords.get(id_i, set())

            if not keywords_i:
                continue

            similarities = []
            for j in range(n):
                if i == j:
                    continue
                
                paper_j = papers[j]
                id_j = paper_j['id']
                keywords_j = method_keywords.get(id_j, set())
                
                if not keywords_j:
                    continue

                # 计算Jaccard相似度
                intersection = len(keywords_i & keywords_j)
                union = len(keywords_i | keywords_j)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= 0.2:  # 至少20%的方法重叠
                        similarities.append((j, similarity, intersection))

            # 排序并取前N
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:max_relations]

            for j, sim, common_count in similarities:
                source_id = papers[i]['id']
                target_id = papers[j]['id']

                if source_id > target_id:
                    source_id, target_id = target_id, source_id

                relations.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relation_type': '方法相似',
                    'strength': float(sim),
                    'evidence': f'共享{common_count}个方法关键词'
                })

        print(f"    找到 {len(relations)} 个方法相似关系")
        return relations

    def _build_evolution_relations(self, papers: List[Dict], max_relations: int) -> List[Dict]:
        """
        构建研究脉络关系（时间演进关系）
        基于发表时间和内容相似度，找出研究的发展脉络
        """
        print("  - 分析研究脉络关系...")

        relations = []
        
        # 按年份排序
        papers_with_year = []
        for paper in papers:
            year = paper.get('year') or paper.get('metadata', {}).get('year', 0)
            try:
                year = int(year) if year else 0
            except:
                year = 0
            papers_with_year.append((paper, year))
        
        # 只考虑有年份信息的论文
        papers_with_year = [(p, y) for p, y in papers_with_year if y > 1990]
        papers_with_year.sort(key=lambda x: x[1])  # 按年份排序

        if len(papers_with_year) < 2:
            print("    论文年份信息不足，跳过研究脉络分析")
            return relations

        # 对于每篇论文，找后续年份中内容最相似的论文
        for i, (paper_i, year_i) in enumerate(papers_with_year):
            id_i = paper_i['id']
            
            # 准备文本
            text_i = paper_i.get('title', '') + " " + paper_i.get('abstract', '')
            
            similarities = []
            
            # 只考虑后续年份的论文
            for j in range(i + 1, min(i + 10, len(papers_with_year))):
                paper_j, year_j = papers_with_year[j]
                id_j = paper_j['id']
                
                # 年份差不能超过5年
                if year_j - year_i > 5:
                    continue
                
                text_j = paper_j.get('title', '') + " " + paper_j.get('abstract', '')
                
                # 简单计算相似度（基于关键词重叠）
                words_i = set(text_i.lower().split())
                words_j = set(text_j.lower().split())
                
                if words_i and words_j:
                    intersection = len(words_i & words_j)
                    union = len(words_i | words_j)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity >= 0.3:
                        similarities.append((id_j, similarity, year_j - year_i))

            # 排序并取前N
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:3]  # 每篇论文最多3个演进关系

            for target_id, sim, year_diff in similarities:
                relations.append({
                    'source_id': id_i,
                    'target_id': target_id,
                    'relation_type': '研究脉络',
                    'strength': float(sim),
                    'evidence': f'{year_diff}年演进，相似度{sim:.2f}'
                })

        print(f"    找到 {len(relations)} 个研究脉络关系")
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
