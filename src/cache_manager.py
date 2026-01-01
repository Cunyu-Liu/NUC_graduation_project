"""Redis缓存管理器 - v4.1性能优化版"""
import os
import json
import hashlib
from typing import Any, Optional, List
from datetime import timedelta
import redis
from src.config import settings


class RedisCacheManager:
    """Redis缓存管理器"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 password: str = None, decode_responses: bool = True):
        """
        初始化Redis客户端

        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            password: 密码
            decode_responses: 是否自动解码响应
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            print("✓ Redis连接成功")
        except Exception as e:
            print(f"⚠ Redis连接失败: {e}")
            print("  将使用内存缓存替代")
            self.redis_client = None
            self.memory_cache = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Redis获取失败: {e}")
        else:
            return self.memory_cache.get(key)

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存

        Args:
            key: 键
            value: 值
            ttl: 过期时间（秒），默认1小时
        """
        if self.redis_client:
            try:
                return self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, ensure_ascii=False)
                )
            except Exception as e:
                print(f"Redis设置失败: {e}")
        else:
            self.memory_cache[key] = value
            return True

        return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.redis_client:
            try:
                return self.redis_client.delete(key) > 0
            except Exception as e:
                print(f"Redis删除失败: {e}")
        else:
            if key in self.memory_cache:
                del self.memory_cache[key]
                return True
        return False

    def delete_pattern(self, pattern: str) -> int:
        """批量删除缓存"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis批量删除失败: {e}")
        return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self.redis_client:
            try:
                return self.redis_client.exists(key) > 0
            except Exception as e:
                print(f"Redis检查失败: {e}")
        else:
            return key in self.memory_cache
        return False

    def clear_all(self) -> bool:
        """清空所有缓存"""
        if self.redis_client:
            try:
                return self.redis_client.flushdb()
            except Exception as e:
                print(f"Redis清空失败: {e}")
        else:
            self.memory_cache.clear()
            return True
        return False


# ============================================================================
# 缓存装饰器
# ============================================================================

def cache_result(key_prefix: str, ttl: int = 3600):
    """
    缓存结果装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [key_prefix]

            # 添加参数到键
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

            cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    使缓存失效装饰器

    Args:
        pattern: 缓存键模式
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 执行函数
            result = func(*args, **kwargs)

            # 使相关缓存失效
            cache_manager.delete_pattern(pattern)

            return result
        return wrapper
    return decorator


# ============================================================================
# 针对特定业务的缓存工具
# ============================================================================

class PaperCache:
    """论文相关缓存"""

    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager

    def get_paper_list(
        self,
        search: str = '',
        year_from: int = None,
        year_to: int = None,
        venue: str = '',
        skip: int = 0,
        limit: int = 20
    ) -> Optional[List]:
        """获取论文列表缓存"""
        cache_key = f"papers:list:{search}:{year_from}:{year_to}:{venue}:{skip}:{limit}"
        return self.cache.get(cache_key)

    def set_paper_list(self, params: dict, papers: List, ttl: int = 300):
        """设置论文列表缓存（5分钟）"""
        cache_key = f"papers:list:{params.get('search', '')}:{params.get('year_from', '')}:{params.get('year_to', '')}:{params.get('venue', '')}:{params.get('skip', 0)}:{params.get('limit', 20)}"
        self.cache.set(cache_key, papers, ttl)

    def invalidate_paper_lists(self):
        """使所有论文列表缓存失效"""
        self.cache.delete_pattern("papers:list:*")

    def get_paper_detail(self, paper_id: int) -> Optional[dict]:
        """获取论文详情缓存"""
        return self.cache.get(f"paper:detail:{paper_id}")

    def set_paper_detail(self, paper_id: int, paper_data: dict, ttl: int = 600):
        """设置论文详情缓存（10分钟）"""
        self.cache.set(f"paper:detail:{paper_id}", paper_data, ttl)

    def invalidate_paper(self, paper_id: int):
        """使论文缓存失效"""
        self.cache.delete(f"paper:detail:{paper_id}")
        self.invalidate_paper_lists()


class AnalysisCache:
    """分析结果缓存"""

    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager

    def get_analysis_result(self, paper_id: int) -> Optional[dict]:
        """获取分析结果缓存"""
        return self.cache.get(f"analysis:result:{paper_id}")

    def set_analysis_result(self, paper_id: int, analysis: dict, ttl: int = 1800):
        """设置分析结果缓存（30分钟）"""
        self.cache.set(f"analysis:result:{paper_id}", analysis, ttl)

    def invalidate_analysis(self, paper_id: int):
        """使分析缓存失效"""
        self.cache.delete(f"analysis:result:{paper_id}")


class GraphCache:
    """知识图谱缓存"""

    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager

    def get_graph_data(self, paper_ids: tuple = None) -> Optional[dict]:
        """获取图谱数据缓存"""
        if paper_ids:
            cache_key = f"graph:data:{','.join(map(str, paper_ids))}"
        else:
            cache_key = "graph:data:all"
        return self.cache.get(cache_key)

    def set_graph_data(self, paper_ids: tuple or None, graph: dict, ttl: int = 600):
        """设置图谱数据缓存（10分钟）"""
        if paper_ids:
            cache_key = f"graph:data:{','.join(map(str, paper_ids))}"
        else:
            cache_key = "graph:data:all"
        self.cache.set(cache_key, graph, ttl)

    def invalidate_graph(self):
        """使图谱缓存失效"""
        self.cache.delete_pattern("graph:data:*")


class StatisticsCache:
    """统计数据缓存"""

    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager

    def get_statistics(self) -> Optional[dict]:
        """获取统计缓存"""
        return self.cache.get("statistics:all")

    def set_statistics(self, stats: dict, ttl: int = 60):
        """设置统计缓存（1分钟）"""
        self.cache.set("statistics:all", stats, ttl)

    def invalidate_statistics(self):
        """使统计缓存失效"""
        self.cache.delete("statistics:all")


# ============================================================================
# 全局缓存管理器实例
# ============================================================================

try:
    cache_manager = RedisCacheManager(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD', None)
    )

    # 业务缓存实例
    paper_cache = PaperCache(cache_manager)
    analysis_cache = AnalysisCache(cache_manager)
    graph_cache = GraphCache(cache_manager)
    stats_cache = StatisticsCache(cache_manager)

except Exception as e:
    print(f"⚠ 缓存初始化失败: {e}")
    cache_manager = None
    paper_cache = None
    analysis_cache = None
    graph_cache = None
    stats_cache = None
