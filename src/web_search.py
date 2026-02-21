"""联网搜索模块 - 支持多种搜索引擎
提供免费的 DuckDuckGo 搜索，无需 API key
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str = "web"
    timestamp: Optional[str] = None


class WebSearchEngine:
    """网页搜索引擎"""
    
    def __init__(self):
        self.last_search_time = 0
        self.min_interval = 1.0  # 最小搜索间隔（秒）
    
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_search_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_search_time = time.time()
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        使用 DuckDuckGo 搜索（免费，无需 API key）
        
        Args:
            query: 搜索关键词
            max_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            self._rate_limit()
            
            # DuckDuckGo HTML 版本搜索
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            results = []
            
            # 解析搜索结果
            # DuckDuckGo HTML 结果格式
            result_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>'
            
            titles = re.findall(result_pattern, html, re.DOTALL)
            snippets = re.findall(snippet_pattern, html, re.DOTALL)
            
            for i, (href, title) in enumerate(titles[:max_results]):
                # 清理 HTML 标签
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                clean_snippet = re.sub(r'<[^>]+>', '', snippets[i] if i < len(snippets) else '').strip()
                
                # 处理重定向 URL
                if href.startswith('/l/'):
                    # 提取实际 URL
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        href = urllib.parse.unquote(match.group(1))
                
                if clean_title and href:
                    results.append(SearchResult(
                        title=clean_title,
                        url=href,
                        snippet=clean_snippet,
                        source="DuckDuckGo"
                    ))
            
            return results
            
        except Exception as e:
            print(f"⚠️ DuckDuckGo 搜索失败: {e}")
            return []
    
    def search_bing(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        使用 Bing 搜索（备用方案）
        需要配置 BING_API_KEY 环境变量
        """
        api_key = os.getenv('BING_API_KEY')
        if not api_key:
            return []
        
        try:
            self._rate_limit()
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {"q": query, "count": max_results, "textDecorations": False}
            
            req = urllib.request.Request(
                f"{url}?{urllib.parse.urlencode(params)}",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            for item in data.get('webPages', {}).get('value', []):
                results.append(SearchResult(
                    title=item.get('name', ''),
                    url=item.get('url', ''),
                    snippet=item.get('snippet', ''),
                    source="Bing"
                ))
            
            return results
            
        except Exception as e:
            print(f"⚠️ Bing 搜索失败: {e}")
            return []
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        综合搜索：尝试多种搜索引擎
        
        Args:
            query: 搜索关键词
            max_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        print(f"🔍 执行网络搜索: {query[:50]}...")
        
        # 优先使用 DuckDuckGo（免费）
        results = self.search_duckduckgo(query, max_results)
        
        # 如果失败，尝试 Bing
        if not results:
            results = self.search_bing(query, max_results)
        
        print(f"✅ 搜索完成，找到 {len(results)} 条结果")
        return results
    
    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """
        将搜索结果格式化为 LLM 可用的上下文
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化后的文本
        """
        if not results:
            return ""
        
        lines = ["【网络搜索结果】"]
        
        for i, r in enumerate(results, 1):
            lines.append(f"\n{i}. {r.title}")
            lines.append(f"   来源: {r.source}")
            lines.append(f"   链接: {r.url}")
            lines.append(f"   摘要: {r.snippet}")
        
        return "\n".join(lines)


# 全局搜索引擎实例
_search_engine = None

def get_search_engine() -> WebSearchEngine:
    """获取搜索引擎实例（单例）"""
    global _search_engine
    if _search_engine is None:
        _search_engine = WebSearchEngine()
    return _search_engine


def web_search(query: str, max_results: int = 5) -> List[SearchResult]:
    """
    便捷的搜索函数
    
    Args:
        query: 搜索关键词
        max_results: 返回结果数量
        
    Returns:
        搜索结果列表
        
    Example:
        >>> results = web_search("蛋白质语言模型最新进展", max_results=3)
        >>> for r in results:
        ...     print(f"{r.title}: {r.url}")
    """
    engine = get_search_engine()
    return engine.search(query, max_results)


if __name__ == "__main__":
    # 测试
    results = web_search("Python programming language", max_results=3)
    for r in results:
        print(f"- {r.title}\n  {r.url}\n  {r.snippet[:100]}...\n")
