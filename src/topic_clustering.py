"""主题聚类模块 - 对多篇论文进行主题聚类分析"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import jieba
import jieba.analyse

from src.config import settings
from src.pdf_parser import ParsedPaper


class TopicClustering:
    """论文主题聚类分析器"""

    def __init__(
        self,
        n_clusters: int = 5,
        clustering_method: str = "kmeans",
        language: str = "chinese"
    ):
        """
        初始化主题聚类器

        Args:
            n_clusters: 聚类数量
            clustering_method: 聚类方法 ('kmeans', 'dbscan', 'hierarchical')
            language: 语言 ('chinese' 或 'english')
        """
        self.n_clusters = n_clusters
        self.clustering_method = clustering_method
        self.language = language

        # 初始化分词器和向量化器
        self.vectorizer = None
        self.cluster_model = None
        self.feature_names = None

    def preprocess_text(self, text: str) -> str:
        """
        预处理文本

        Args:
            text: 原始文本

        Returns:
            str: 预处理后的文本
        """
        # 提取摘要和主要章节
        lines = text.split("\n")
        important_lines = []

        for line in lines:
            line = line.strip()
            # 过滤掉太短的行和页眉页脚
            if 10 < len(line) < 200:
                important_lines.append(line)

        return " ".join(important_lines)

    def tokenize_chinese(self, text: str) -> str:
        """
        中文分词

        Args:
            text: 中文文本

        Returns:
            str: 分词后的文本
        """
        # 使用jieba分词
        words = jieba.cut(text)
        # 过滤停用词和短词
        stopwords = self._get_stopwords()
        filtered_words = [w for w in words if len(w) > 1 and w not in stopwords]
        return " ".join(filtered_words)

    def _get_stopwords(self) -> set:
        """获取停用词集合"""
        # 基础停用词
        stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "the", "a", "an", "and", "or", "but", "in", "on",
            "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were"
        }
        return stopwords

    def extract_keywords_from_papers(
        self,
        papers: List[ParsedPaper],
        top_keywords: int = 10
    ) -> Dict[str, List[str]]:
        """
        从论文中提取关键词

        Args:
            papers: 论文列表
            top_keywords: 每篇论文提取的关键词数量

        Returns:
            Dict[str, List[str]]: 论文文件名到关键词的映射
        """
        paper_keywords = {}

        for paper in papers:
            # 合并标题、摘要和章节
            content = paper.metadata.title or ""
            content += " " + (paper.metadata.abstract or "")
            for section_content in paper.metadata.sections.values():
                content += " " + section_content

            # 提取关键词
            if self.language == "chinese":
                keywords = jieba.analyse.extract_tags(content, topK=top_keywords)
            else:
                # 英文使用简单的TF-IDF
                vectorizer = TfidfVectorizer(max_features=top_keywords, stop_words='english')
                try:
                    tfidf_matrix = vectorizer.fit_transform([content])
                    feature_names = vectorizer.get_feature_names_out()
                    tfidf_scores = tfidf_matrix.toarray()[0]
                    top_indices = tfidf_scores.argsort()[-top_keywords:][::-1]
                    keywords = [feature_names[i] for i in top_indices]
                except:
                    keywords = []

            paper_keywords[paper.filename] = keywords

        return paper_keywords

    def prepare_paper_texts(self, papers: List[ParsedPaper]) -> List[str]:
        """
        准备用于聚类的论文文本

        Args:
            papers: 论文列表

        Returns:
            List[str]: 处理后的文本列表
        """
        paper_texts = []

        for paper in papers:
            # 合并标题、摘要和关键词
            text = paper.metadata.title or ""
            text += " " + (paper.metadata.abstract or "")

            # 添加主要章节
            for section_name, section_content in paper.metadata.sections.items():
                text += f" {section_name} {section_content}"

            # 添加关键词
            if paper.metadata.keywords:
                text += " " + " ".join(paper.metadata.keywords)

            # 预处理
            text = self.preprocess_text(text)

            # 中文分词
            if self.language == "chinese":
                text = self.tokenize_chinese(text)

            paper_texts.append(text)

        return paper_texts

    def fit_transform(self, papers: List[ParsedPaper]) -> np.ndarray:
        """
        训练聚类模型并转换数据

        Args:
            papers: 论文列表

        Returns:
            np.ndarray: 聚类标签
        """
        # 准备文本数据
        paper_texts = self.prepare_paper_texts(papers)

        # 文本向量化
        if self.language == "chinese":
            self.vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=1,
                max_df=0.8
            )
        else:
            self.vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=1,
                max_df=0.8,
                stop_words='english'
            )

        tfidf_matrix = self.vectorizer.fit_transform(paper_texts)
        self.feature_names = self.vectorizer.get_feature_names_out()

        # 选择聚类算法
        if self.clustering_method == "kmeans":
            self.cluster_model = KMeans(
                n_clusters=self.n_clusters,
                random_state=42,
                n_init=10
            )
        elif self.clustering_method == "dbscan":
            # 为DBSCAN动态调整eps参数
            # eps应该根据数据分布动态调整
            n_samples = tfidf_matrix.shape[0]
            if n_samples <= 3:
                # 样本太少，使用层次聚类替代
                print(f"  样本数量较少({n_samples})，使用层次聚类替代")
                self.cluster_model = AgglomerativeClustering(
                    n_clusters=max(2, n_samples - 1) if n_samples > 2 else 2
                )
                self.clustering_method = "hierarchical"  # 临时切换方法
            else:
                # 根据样本数量动态调整eps
                # 样本越多，eps应该越小（数据点越密集）
                eps = max(0.3, 0.8 - n_samples * 0.02)
                min_samples = min(2, n_samples - 1)
                self.cluster_model = DBSCAN(eps=eps, min_samples=min_samples)
                print(f"  DBSCAN参数: eps={eps:.2f}, min_samples={min_samples}")
        elif self.clustering_method == "hierarchical":
            self.cluster_model = AgglomerativeClustering(
                n_clusters=self.n_clusters
            )
        else:
            raise ValueError(f"未知的聚类方法: {self.clustering_method}")

        # 执行聚类
        labels = self.cluster_model.fit_predict(tfidf_matrix.toarray())

        return labels

    def analyze_clusters(
        self,
        papers: List[ParsedPaper],
        labels: np.ndarray
    ) -> Dict[int, Dict[str, any]]:
        """
        分析聚类结果

        Args:
            papers: 论文列表
            labels: 聚类标签

        Returns:
            Dict: 聚类分析结果
        """
        cluster_analysis = {}

        # 准备文本数据
        paper_texts = self.prepare_paper_texts(papers)
        tfidf_matrix = self.vectorizer.transform(paper_texts)

        unique_labels = np.unique(labels)

        # 处理DBSCAN的噪声点：将噪声点单独分组或分配到最近的簇
        noise_indices = []
        if -1 in unique_labels:
            noise_indices = np.where(labels == -1)[0].tolist()
            # 从unique_labels中移除-1以便正常处理其他簇
            unique_labels = unique_labels[unique_labels != -1]
            print(f"  DBSCAN发现 {len(noise_indices)} 个噪声点，将单独处理")

        # 正常处理聚类簇
        for cluster_id in unique_labels:
            # 获取该聚类的论文
            cluster_mask = labels == cluster_id
            cluster_papers = [papers[i] for i in range(len(papers)) if cluster_mask[i]]
            cluster_indices = np.where(cluster_mask)[0]

            # 计算聚类特征词的平均TF-IDF分数
            cluster_tfidf = tfidf_matrix[cluster_indices].mean(axis=0)
            top_feature_indices = cluster_tfidf.A1.argsort()[-10:][::-1]
            top_features = [self.feature_names[i] for i in top_feature_indices]

            # 分析结果
            cluster_analysis[int(cluster_id)] = {
                "paper_count": len(cluster_papers),
                "papers": [p.filename for p in cluster_papers],
                "top_keywords": top_features,
                "representative_papers": self._get_representative_papers(
                    cluster_papers, top_n=3
                )
            }

        # 处理噪声点：如果噪声点数量较多，将它们分组为"其他"类别
        # 或者分配到最近的簇
        if noise_indices:
            noise_papers = [papers[i] for i in noise_indices]

            if len(noise_papers) >= 2:
                # 如果有2个或更多噪声点，创建一个"其他"簇
                cluster_analysis[-1] = {
                    "paper_count": len(noise_papers),
                    "papers": [p.filename for p in noise_papers],
                    "top_keywords": ["未分类", "其他"],
                    "representative_papers": self._get_representative_papers(
                        noise_papers, top_n=3
                    )
                }
            elif len(noise_papers) == 1 and cluster_analysis:
                # 如果只有一个噪声点，分配到最近的簇（样本最多的簇）
                largest_cluster_id = max(
                    cluster_analysis.keys(),
                    key=lambda k: cluster_analysis[k]["paper_count"]
                )
                cluster_analysis[largest_cluster_id]["papers"].append(
                    noise_papers[0].filename
                )
                cluster_analysis[largest_cluster_id]["paper_count"] += 1

        return cluster_analysis

    def _get_representative_papers(
        self,
        papers: List[ParsedPaper],
        top_n: int = 3
    ) -> List[Dict[str, str]]:
        """
        获取代表性论文

        Args:
            papers: 论文列表
            top_n: 返回的论文数量

        Returns:
            List[Dict]: 代表性论文信息
        """
        # 按摘要长度和完整性排序
        scored_papers = []
        for paper in papers:
            score = len(paper.metadata.abstract) + len(paper.metadata.sections) * 100
            scored_papers.append((score, paper))

        # 选择得分最高的论文
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        representative = []

        for score, paper in scored_papers[:top_n]:
            representative.append({
                "filename": paper.filename,
                "title": paper.metadata.title,
                "abstract": paper.metadata.abstract[:200] + "..." if len(paper.metadata.abstract) > 200 else paper.metadata.abstract
            })

        return representative

    def visualize_clusters(
        self,
        papers: List[ParsedPaper],
        labels: np.ndarray,
        save_path: Optional[Path] = None
    ):
        """
        可视化聚类结果

        Args:
            papers: 论文列表
            labels: 聚类标签
            save_path: 保存路径
        """
        # 准备文本数据
        paper_texts = self.prepare_paper_texts(papers)
        tfidf_matrix = self.vectorizer.transform(paper_texts).toarray()

        # 使用t-SNE降维
        if len(papers) > 2:
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(papers)-1))
            tsne_results = tsne.fit_transform(tfidf_matrix)
        else:
            tsne_results = tfidf_matrix[:, :2]

        # 绘制散点图
        plt.figure(figsize=(12, 8))

        unique_labels = np.unique(labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for i, label in enumerate(unique_labels):
            if label == -1:  # 噪声点
                continue

            mask = labels == label
            plt.scatter(
                tsne_results[mask, 0],
                tsne_results[mask, 1],
                c=[colors[i]],
                label=f'Cluster {label}',
                alpha=0.7,
                s=100
            )

            # 添加论文标签
            for idx in np.where(mask)[0]:
                plt.annotate(
                    papers[idx].filename[:20],
                    (tsne_results[idx, 0], tsne_results[idx, 1]),
                    fontsize=8,
                    alpha=0.5
                )

        plt.title('Paper Topic Clustering', fontsize=16)
        plt.xlabel('t-SNE Component 1', fontsize=12)
        plt.ylabel('t-SNE Component 2', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 保存图像
        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"聚类可视化已保存到: {save_path}")

        plt.close()

    def save_cluster_report(
        self,
        cluster_analysis: Dict[int, Dict[str, any]],
        labels: np.ndarray,
        save_path: Optional[Path] = None
    ):
        """
        保存聚类分析报告

        Args:
            cluster_analysis: 聚类分析结果
            labels: 聚类标签
            save_path: 保存路径
        """
        save_path = save_path or settings.cluster_output_dir / "cluster_report.txt"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("论文主题聚类分析报告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"聚类方法: {self.clustering_method}\n")
            f.write(f"聚类数量: {len(cluster_analysis)}\n")
            f.write(f"论文总数: {len(labels)}\n\n")

            # 计算聚类质量
            if len(np.unique(labels)) > 1:
                # 这里可以添加轮廓系数等评估指标
                pass

            f.write("\n" + "=" * 80 + "\n")
            f.write("各聚类详细信息\n")
            f.write("=" * 80 + "\n\n")

            for cluster_id, info in cluster_analysis.items():
                f.write(f"\n{'─' * 80}\n")
                f.write(f"聚类 {cluster_id}\n")
                f.write(f"{'─' * 80}\n\n")

                f.write(f"论文数量: {info['paper_count']}\n\n")
                f.write(f"核心关键词: {', '.join(info['top_keywords'][:10])}\n\n")

                f.write("包含论文:\n")
                for i, paper_name in enumerate(info['papers'], 1):
                    f.write(f"  {i}. {paper_name}\n")

                f.write("\n代表性论文:\n")
                for i, rep_paper in enumerate(info['representative_papers'], 1):
                    f.write(f"\n  {i}. {rep_paper['title'] or rep_paper['filename']}\n")
                    f.write(f"     摘要: {rep_paper['abstract']}\n")

                f.write("\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("研究趋势与建议\n")
            f.write("=" * 80 + "\n\n")

            # 生成研究趋势分析
            trends = self._analyze_research_trends(cluster_analysis)
            f.write(trends)

        print(f"聚类报告已保存到: {save_path}")

    def _analyze_research_trends(
        self,
        cluster_analysis: Dict[int, Dict[str, any]]
    ) -> str:
        """
        分析研究趋势

        Args:
            cluster_analysis: 聚类分析结果

        Returns:
            str: 趋势分析文本
        """
        trends = []
        trends.append("基于聚类分析的研究方向归纳:\n\n")

        for cluster_id, info in cluster_analysis.items():
            trends.append(f"{cluster_id + 1}. 研究方向 {cluster_id + 1}\n")
            trends.append(f"   关键词: {', '.join(info['top_keywords'][:5])}\n")
            trends.append(f"   论文数: {info['paper_count']}\n")
            trends.append(f"   描述: 该方向主要关注{info['top_keywords'][0]}和{info['top_keywords'][1]}相关研究\n\n")

        trends.append("\n潜在研究空白:\n")
        trends.append("- 建议关注不同研究方向的交叉领域\n")
        trends.append("- 可探索关键词中出现较少但具有重要意义的主题\n")
        trends.append("- 关注论文数量较少但具有潜力的新兴研究方向\n")

        return "".join(trends)

    def cluster_papers(
        self,
        papers: List[ParsedPaper],
        save_visualization: bool = True,
        save_report: bool = True
    ) -> Dict[str, any]:
        """
        完整的聚类流程

        Args:
            papers: 论文列表
            save_visualization: 是否保存可视化
            save_report: 是否保存报告

        Returns:
            Dict: 聚类结果
        """
        print(f"开始对 {len(papers)} 篇论文进行主题聚类...")

        # 训练聚类模型
        labels = self.fit_transform(papers)

        # 分析聚类
        cluster_analysis = self.analyze_clusters(papers, labels)

        # 计算有效的聚类数量（不包括噪声点，除非噪声点形成了独立的簇）
        unique_labels = np.unique(labels)
        effective_cluster_count = len(cluster_analysis)

        print(f"聚类完成，共发现 {effective_cluster_count} 个主题类别")
        print("\n聚类分析结果:")
        for cluster_id, info in cluster_analysis.items():
            cluster_name = "未分类" if cluster_id == -1 else f"聚类 {cluster_id}"
            print(f"\n{cluster_name} ({info['paper_count']} 篇论文):")
            print(f"  关键词: {', '.join(info['top_keywords'][:5])}")

        # 保存可视化
        if save_visualization:
            viz_path = settings.cluster_output_dir / "cluster_visualization.png"
            self.visualize_clusters(papers, labels, viz_path)

        # 保存报告
        if save_report:
            self.save_cluster_report(cluster_analysis, labels)

        return {
            "labels": labels,
            "cluster_analysis": cluster_analysis,
            "unique_clusters": effective_cluster_count
        }


def cluster_papers_from_files(
    pdf_paths: List[str],
    n_clusters: int = 5,
    method: str = "kmeans"
) -> Dict[str, any]:
    """
    便捷函数：从PDF文件列表进行聚类

    Args:
        pdf_paths: PDF文件路径列表
        n_clusters: 聚类数量
        method: 聚类方法

    Returns:
        Dict: 聚类结果
    """
    from src.pdf_parser import PDFParser

    # 解析PDF
    print("正在解析PDF文件...")
    parser = PDFParser()
    papers = []
    for pdf_path in pdf_paths:
        try:
            paper = parser.parse_pdf(pdf_path)
            papers.append(paper)
        except Exception as e:
            print(f"解析失败 {pdf_path}: {e}")

    # 执行聚类
    clustering = TopicClustering(n_clusters=n_clusters, clustering_method=method)
    results = clustering.cluster_papers(papers)

    return results
