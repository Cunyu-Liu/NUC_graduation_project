"""Milvus 向量数据库集成模块 - v4.2院士版
支持论文 embedding 存储、语义搜索、向量聚类
"""
import os
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# 尝试导入 Milvus 客户端
try:
    from pymilvus import (
        connections, Collection, CollectionSchema, FieldSchema, DataType,
        utility, IndexType, MetricType
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    print("⚠️  pymilvus 未安装，向量数据库功能将受限")

# 尝试导入 sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers 未安装，将使用 API 生成 embedding")


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    paper_id: int
    distance: float
    title: str
    abstract: str
    year: Optional[int] = None
    venue: Optional[str] = None


@dataclass
class PaperEmbedding:
    """论文向量表示"""
    paper_id: int
    title: str
    abstract: str
    embedding: np.ndarray
    keywords: List[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    authors: List[str] = None


class MilvusVectorStore:
    """Milvus 向量存储管理器"""
    
    # 集合配置
    COLLECTION_NAME = "paper_embeddings"
    DIM = 1024  # 向量维度 (BGE-large-zh-v1.5 为 1024)
    INDEX_TYPE = "IVF_FLAT"  # 索引类型
    METRIC_TYPE = "L2"  # 距离度量
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: str = "19530",
                 db_manager=None):
        """
        初始化 Milvus 向量存储
        
        Args:
            host: Milvus 服务器地址
            port: Milvus 端口
            db_manager: 数据库管理器实例
        """
        if not MILVUS_AVAILABLE:
            raise ImportError("pymilvus 未安装，无法使用向量数据库功能")
        
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or os.getenv('MILVUS_PORT', '19530')
        self.db_manager = db_manager
        self.collection = None
        self.embedding_model = None
        
        # 初始化 embedding 模型
        self._init_embedding_model()
        
        # 连接到 Milvus
        self._connect()
        
        # 初始化集合
        self._init_collection()
    
    def _init_embedding_model(self):
        """初始化 embedding 模型"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # 使用 BGE-large-zh-v1.5，中文效果优秀
                model_name = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-large-zh-v1.5')
                print(f"📦 正在加载 embedding 模型: {model_name}")
                self.embedding_model = SentenceTransformer(model_name)
                self.DIM = self.embedding_model.get_sentence_embedding_dimension()
                print(f"✅ Embedding 模型加载成功，维度: {self.DIM}")
            except Exception as e:
                print(f"⚠️  Embedding 模型加载失败: {e}")
                self.embedding_model = None
        else:
            # 使用 LLM API 生成 embedding
            self.embedding_model = None
            print("⚠️  将使用 API 生成 embedding")
    
    def _connect(self):
        """连接到 Milvus 服务器"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            print(f"✅ 已连接到 Milvus: {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ 连接 Milvus 失败: {e}")
            raise
    
    def _init_collection(self):
        """初始化集合（如果不存在则创建）"""
        if not utility.has_collection(self.COLLECTION_NAME):
            print(f"📦 创建新集合: {self.COLLECTION_NAME}")
            self._create_collection()
        else:
            print(f"📦 使用已有集合: {self.COLLECTION_NAME}")
            self.collection = Collection(self.COLLECTION_NAME)
    
    def _create_collection(self):
        """创建向量集合"""
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="paper_id", dtype=DataType.INT64),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=10000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.DIM),
            FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="authors", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="year", dtype=DataType.INT32),
            FieldSchema(name="venue", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="created_at", dtype=DataType.INT64),
        ]
        
        # 创建 schema
        schema = CollectionSchema(fields, description="论文向量嵌入集合")
        
        # 创建集合
        self.collection = Collection(self.COLLECTION_NAME, schema)
        
        # 创建索引
        index_params = {
            "metric_type": self.METRIC_TYPE,
            "index_type": self.INDEX_TYPE,
            "params": {"nlist": 128}
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        print(f"✅ 集合创建成功，索引类型: {self.INDEX_TYPE}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        生成文本的 embedding
        
        Args:
            text: 输入文本
            
        Returns:
            embedding 向量
        """
        if self.embedding_model:
            # 使用本地模型
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding
        else:
            # 使用 API 生成 embedding (需要实现)
            raise NotImplementedError("API embedding 生成功能待实现")
    
    def add_paper(self, paper: PaperEmbedding) -> bool:
        """
        添加单篇论文到向量存储
        
        Args:
            paper: 论文向量表示
            
        Returns:
            是否成功
        """
        try:
            entities = [
                [paper.paper_id],
                [paper.title],
                [paper.abstract],
                [paper.embedding.tolist()],
                [json.dumps(paper.keywords)],
                [json.dumps(paper.authors or [])],
                [paper.year or 0],
                [paper.venue or ""],
                [int(datetime.now().timestamp())]
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            return True
        except Exception as e:
            print(f"❌ 添加论文失败: {e}")
            return False
    
    def add_papers_batch(self, papers: List[PaperEmbedding], batch_size: int = 100) -> Dict[str, Any]:
        """
        批量添加论文到向量存储
        
        Args:
            papers: 论文向量表示列表
            batch_size: 批处理大小
            
        Returns:
            操作结果统计
        """
        results = {"success": 0, "failed": 0, "errors": []}
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i+batch_size]
            try:
                entities = [
                    [p.paper_id for p in batch],
                    [p.title for p in batch],
                    [p.abstract for p in batch],
                    [p.embedding.tolist() for p in batch],
                    [json.dumps(p.keywords) for p in batch],
                    [json.dumps(p.authors or []) for p in batch],
                    [p.year or 0 for p in batch],
                    [p.venue or "" for p in batch],
                    [int(datetime.now().timestamp())] * len(batch)
                ]
                
                self.collection.insert(entities)
                results["success"] += len(batch)
            except Exception as e:
                results["failed"] += len(batch)
                results["errors"].append(str(e))
                print(f"❌ 批量添加失败: {e}")
        
        self.collection.flush()
        return results
    
    def search(self, 
               query: str, 
               top_k: int = 10,
               paper_ids: Optional[List[int]] = None) -> List[VectorSearchResult]:
        """
        语义搜索论文
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            paper_ids: 可选的论文ID过滤列表
            
        Returns:
            搜索结果列表
        """
        # 加载集合到内存
        self.collection.load()
        
        # 生成查询向量
        query_embedding = self.generate_embedding(query)
        
        # 搜索参数
        search_params = {"metric_type": self.METRIC_TYPE, "params": {"nprobe": 10}}
        
        # 执行搜索
        results = self.collection.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=f"paper_id in {paper_ids}" if paper_ids else None,
            output_fields=["paper_id", "title", "abstract", "year", "venue"]
        )
        
        # 解析结果
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append(VectorSearchResult(
                    paper_id=hit.entity.get("paper_id"),
                    distance=hit.distance,
                    title=hit.entity.get("title"),
                    abstract=hit.entity.get("abstract"),
                    year=hit.entity.get("year"),
                    venue=hit.entity.get("venue")
                ))
        
        return search_results
    
    def find_similar_papers(self, 
                           paper_id: int, 
                           top_k: int = 5) -> List[VectorSearchResult]:
        """
        查找与指定论文相似的论文
        
        Args:
            paper_id: 论文ID
            top_k: 返回结果数量
            
        Returns:
            相似论文列表
        """
        # 加载集合
        self.collection.load()
        
        # 查询该论文的 embedding
        results = self.collection.query(
            expr=f"paper_id == {paper_id}",
            output_fields=["embedding", "title", "abstract"]
        )
        
        if not results:
            return []
        
        paper_embedding = results[0]["embedding"]
        
        # 搜索相似论文
        search_params = {"metric_type": self.METRIC_TYPE, "params": {"nprobe": 10}}
        
        similar_results = self.collection.search(
            data=[paper_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k + 1,  # +1 因为要排除自己
            expr=f"paper_id != {paper_id}",
            output_fields=["paper_id", "title", "abstract", "year", "venue"]
        )
        
        # 解析结果
        similar_papers = []
        for hits in similar_results:
            for hit in hits[:top_k]:  # 只取前 top_k 个
                similar_papers.append(VectorSearchResult(
                    paper_id=hit.entity.get("paper_id"),
                    distance=hit.distance,
                    title=hit.entity.get("title"),
                    abstract=hit.entity.get("abstract"),
                    year=hit.entity.get("year"),
                    venue=hit.entity.get("venue")
                ))
        
        return similar_papers
    
    def cluster_papers(self, 
                      paper_ids: Optional[List[int]] = None,
                      n_clusters: int = 5) -> Dict[str, Any]:
        """
        基于向量的论文聚类
        
        Args:
            paper_ids: 要聚类的论文ID列表（None表示全部）
            n_clusters: 聚类数量
            
        Returns:
            聚类结果
        """
        from sklearn.cluster import KMeans
        
        # 加载集合
        self.collection.load()
        
        # 获取所有论文的向量
        if paper_ids:
            expr = f"paper_id in {paper_ids}"
        else:
            expr = None
        
        results = self.collection.query(
            expr=expr,
            output_fields=["paper_id", "title", "abstract", "embedding", "year", "venue"],
            limit=10000
        )
        
        if len(results) < n_clusters:
            return {"error": f"论文数量({len(results)})少于聚类数量({n_clusters})"}
        
        # 提取向量
        embeddings = np.array([r["embedding"] for r in results])
        paper_data = [
            {
                "paper_id": r["paper_id"],
                "title": r["title"],
                "abstract": r["abstract"],
                "year": r.get("year"),
                "venue": r.get("venue")
            }
            for r in results
        ]
        
        # 执行 K-Means 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # 整理聚类结果
        clusters = {i: [] for i in range(n_clusters)}
        for idx, label in enumerate(labels):
            clusters[label].append(paper_data[idx])
        
        # 计算每个聚类的中心论文（离质心最近的）
        cluster_analysis = {}
        for cluster_id, papers in clusters.items():
            if papers:
                cluster_analysis[str(cluster_id)] = {
                    "paper_count": len(papers),
                    "papers": [p["title"] for p in papers],
                    "representative_papers": papers[:3],  # 前3篇作为代表性论文
                    "years": [p["year"] for p in papers if p.get("year")]
                }
        
        return {
            "n_clusters": n_clusters,
            "total_papers": len(results),
            "method": "kmeans_vector",
            "cluster_analysis": cluster_analysis,
            "inertia": float(kmeans.inertia_)
        }
    
    def delete_paper(self, paper_id: int) -> bool:
        """
        从向量存储中删除论文
        
        Args:
            paper_id: 论文ID
            
        Returns:
            是否成功
        """
        try:
            self.collection.delete(expr=f"paper_id == {paper_id}")
            self.collection.flush()
            return True
        except Exception as e:
            print(f"❌ 删除论文失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取向量存储统计信息"""
        try:
            self.collection.load()
            count = self.collection.num_entities
            return {
                "total_papers": count,
                "collection_name": self.COLLECTION_NAME,
                "dimension": self.DIM,
                "connected": True
            }
        except Exception as e:
            return {
                "total_papers": 0,
                "collection_name": self.COLLECTION_NAME,
                "dimension": self.DIM,
                "connected": False,
                "error": str(e)
            }
    
    def close(self):
        """关闭连接"""
        try:
            connections.disconnect("default")
            print("✅ Milvus 连接已关闭")
        except:
            pass


class VectorStoreManager:
    """向量存储管理器（单例模式）"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_manager=None):
        if self._initialized:
            return
        
        self._initialized = True
        self.db_manager = db_manager
        self.vector_store = None
        
        # 尝试初始化
        self._try_init()
    
    def _try_init(self):
        """尝试初始化向量存储"""
        if not MILVUS_AVAILABLE:
            print("⚠️  Milvus 不可用")
            return
        
        try:
            self.vector_store = MilvusVectorStore(db_manager=self.db_manager)
            print("✅ 向量存储管理器初始化成功")
        except Exception as e:
            print(f"⚠️  向量存储初始化失败: {e}")
            self.vector_store = None
    
    def is_available(self) -> bool:
        """检查向量存储是否可用"""
        return self.vector_store is not None
    
    def sync_papers_from_db(self, paper_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        从数据库同步论文到向量存储
        
        Args:
            paper_ids: 要同步的论文ID列表（None表示全部）
            
        Returns:
            同步结果
        """
        if not self.is_available():
            return {"error": "向量存储不可用"}
        
        if not self.db_manager:
            return {"error": "数据库管理器未配置"}
        
        # 获取论文数据
        if paper_ids:
            papers = []
            for pid in paper_ids:
                paper = self.db_manager.get_paper(pid)
                if paper:
                    papers.append(paper)
        else:
            papers = self.db_manager.get_all_papers(limit=10000)
        
        if not papers:
            return {"error": "没有找到论文"}
        
        # 转换为 PaperEmbedding
        paper_embeddings = []
        for paper in papers:
            try:
                # 组合文本用于生成 embedding
                text = f"{paper.get('title', '')}\n{paper.get('abstract', '')}"
                
                # 获取关键词
                keywords = paper.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = json.loads(keywords)
                
                # 获取作者
                authors = paper.get('authors', [])
                
                embedding = self.vector_store.generate_embedding(text)
                
                paper_embeddings.append(PaperEmbedding(
                    paper_id=paper['id'],
                    title=paper.get('title', ''),
                    abstract=paper.get('abstract', ''),
                    embedding=embedding,
                    keywords=keywords,
                    year=paper.get('year'),
                    venue=paper.get('venue'),
                    authors=authors
                ))
            except Exception as e:
                print(f"⚠️  处理论文 {paper.get('id')} 失败: {e}")
                continue
        
        # 批量添加到向量存储
        results = self.vector_store.add_papers_batch(paper_embeddings)
        
        return {
            "synced": results["success"],
            "failed": results["failed"],
            "total": len(papers)
        }
    
    def search(self, query: str, top_k: int = 10) -> List[VectorSearchResult]:
        """语义搜索"""
        if not self.is_available():
            return []
        return self.vector_store.search(query, top_k)
    
    def find_similar(self, paper_id: int, top_k: int = 5) -> List[VectorSearchResult]:
        """查找相似论文"""
        if not self.is_available():
            return []
        return self.vector_store.find_similar_papers(paper_id, top_k)
    
    def cluster(self, paper_ids: Optional[List[int]] = None, n_clusters: int = 5) -> Dict[str, Any]:
        """向量聚类"""
        if not self.is_available():
            return {"error": "向量存储不可用"}
        return self.vector_store.cluster_papers(paper_ids, n_clusters)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.is_available():
            return {"available": False}
        return self.vector_store.get_stats()


# 全局实例
vector_store_manager = None

def get_vector_store_manager(db_manager=None) -> VectorStoreManager:
    """获取向量存储管理器实例"""
    global vector_store_manager
    if vector_store_manager is None:
        vector_store_manager = VectorStoreManager(db_manager=db_manager)
    return vector_store_manager
