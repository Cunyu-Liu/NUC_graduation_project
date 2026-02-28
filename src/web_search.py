"""联网搜索模块 - 支持多种搜索引擎
提供免费的 DuckDuckGo 搜索，无需 API key
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
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
        # 创建 SSL 上下文，忽略证书验证（解决某些环境的 SSL 问题）
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
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
            
            # 尝试多个 DuckDuckGo 域名
            urls = [
                f"https://html.duckduckgo.com/html/?q={encoded_query}",
                f"https://duckduckgo.com/html/?q={encoded_query}",
            ]
            
            html = None
            for url in urls:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    req = urllib.request.Request(url, headers=headers)
                    
                    print(f"[DEBUG] 发送DuckDuckGo搜索请求: {url[:80]}...")
                    
                    with urllib.request.urlopen(req, timeout=15, context=self.ssl_context) as response:
                        # 处理 gzip 压缩
                        import gzip
                        if response.headers.get('Content-Encoding') == 'gzip':
                            html = gzip.decompress(response.read()).decode('utf-8', errors='ignore')
                        else:
                            html = response.read().decode('utf-8', errors='ignore')
                        
                        if html and len(html) > 100:
                            print(f"[DEBUG] 成功获取响应，长度: {len(html)}")
                            break
                            
                except Exception as e:
                    print(f"[DEBUG] URL {url} 失败: {e}")
                    continue
            
            if not html:
                print("[DEBUG] 所有 DuckDuckGo URL 都失败")
                return []
            
            results = []
            
            # 尝试多种解析模式
            # 模式1: 新版 DuckDuckGo 格式
            result_blocks = re.findall(
                r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>.*?</div>',
                html, re.DOTALL | re.IGNORECASE
            )
            
            if not result_blocks:
                # 模式2: 更通用的结果匹配
                result_blocks = re.findall(
                    r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    html, re.DOTALL | re.IGNORECASE
                )
            
            if not result_blocks:
                # 模式3: 更宽松的匹配
                result_blocks = re.findall(
                    r'<h[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?</h[^>]*>.*?<p[^>]*>(.*?)</p>',
                    html, re.DOTALL | re.IGNORECASE
                )
            
            if not result_blocks:
                # 模式4: 极简匹配 - 直接匹配所有链接
                all_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
                print(f"[DEBUG] 找到 {len(all_links)} 个链接")
                # 过滤出看起来像是搜索结果的链接
                for href, title in all_links:
                    if href.startswith('http') and not 'duckduckgo.com' in href:
                        clean_title = re.sub(r'<[^>]+>', '', title).strip()
                        if len(clean_title) > 5:
                            results.append(SearchResult(
                                title=clean_title,
                                url=href,
                                snippet="",
                                source="DuckDuckGo"
                            ))
                            if len(results) >= max_results:
                                break
            
            print(f"[DEBUG] 解析到 {len(result_blocks)} 个结果块")
            
            for href, title, snippet in result_blocks[:max_results]:
                # 清理 HTML 标签
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                
                # 处理重定向 URL
                if href.startswith('/l/'):
                    # 提取实际 URL
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        href = urllib.parse.unquote(match.group(1))
                elif href.startswith('//'):
                    href = 'https:' + href
                
                # 过滤无效链接
                if not href.startswith('http'):
                    continue
                
                # 过滤 DuckDuckGo 自己的链接
                if 'duckduckgo.com' in href:
                    continue
                    
                if clean_title and href and len(clean_title) > 3:
                    results.append(SearchResult(
                        title=clean_title,
                        url=href,
                        snippet=clean_snippet,
                        source="DuckDuckGo"
                    ))
            
            print(f"[DEBUG] DuckDuckGo搜索完成: 返回{len(results)}条结果")
            return results
            
        except Exception as e:
            print(f"⚠️ DuckDuckGo 搜索失败: {e}")
            import traceback
            traceback.print_exc()
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
            
            with urllib.request.urlopen(req, timeout=10, context=self.ssl_context) as response:
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
    
    def search_serpapi(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        使用 SerpAPI 进行 Google 搜索（备用方案）
        需要配置 SERPAPI_KEY 环境变量
        """
        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            return []
        
        try:
            self._rate_limit()
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": max_results
            }
            
            url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=15, context=self.ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            for item in data.get('organic_results', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    source="Google (via SerpAPI)"
                ))
            
            return results
            
        except Exception as e:
            print(f"⚠️ SerpAPI 搜索失败: {e}")
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
        
        all_results = []
        
        # 优先使用 DuckDuckGo（免费）
        ddgs_results = self.search_duckduckgo(query, max_results)
        if ddgs_results:
            all_results.extend(ddgs_results)
            print(f"✅ DuckDuckGo 找到 {len(ddgs_results)} 条结果")
        
        # 如果 DuckDuckGo 结果不足，尝试 SerpAPI
        if len(all_results) < max_results:
            remaining = max_results - len(all_results)
            serp_results = self.search_serpapi(query, remaining)
            if serp_results:
                # 去重
                existing_urls = {r.url for r in all_results}
                for r in serp_results:
                    if r.url not in existing_urls:
                        all_results.append(r)
                        existing_urls.add(r.url)
                print(f"✅ SerpAPI 补充 {len(serp_results)} 条结果")
        
        # 如果还是没有，尝试 Bing
        if len(all_results) < max_results:
            remaining = max_results - len(all_results)
            bing_results = self.search_bing(query, remaining)
            if bing_results:
                existing_urls = {r.url for r in all_results}
                for r in bing_results:
                    if r.url not in existing_urls:
                        all_results.append(r)
                        existing_urls.add(r.url)
                print(f"✅ Bing 补充 {len(bing_results)} 条结果")
        
        # 如果所有搜索都失败，返回模拟结果（用于测试）
        if not all_results and os.getenv('WEB_SEARCH_FALLBACK', 'false').lower() == 'true':
            print("⚠️ 所有搜索源失败，使用备用提示")
            all_results = [
                SearchResult(
                    title="搜索服务暂时不可用",
                    url="https://www.google.com/search?q=" + urllib.parse.quote_plus(query),
                    snippet=f"无法获取实时搜索结果。请直接访问 Google 搜索: {query[:50]}...",
                    source="Fallback"
                )
            ]
        
        print(f"✅ 搜索完成，共找到 {len(all_results)} 条结果")
        return all_results[:max_results]
    
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
        lines.append(f"（共找到 {len(results)} 条相关结果）\n")
        
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.title}")
            lines.append(f"   来源: {r.source}")
            lines.append(f"   链接: {r.url}")
            if r.snippet:
                lines.append(f"   摘要: {r.snippet}")
            lines.append("")  # 空行分隔
        
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
    print("=" * 60)
    print("测试联网搜索功能")
    print("=" * 60)
    
    test_queries = [
        "Python programming language",
        "深度学习最新进展",
        "transformer architecture"
    ]
    
    engine = get_search_engine()
    
    for query in test_queries:
        print(f"\n🔍 搜索: {query}")
        print("-" * 40)
        results = engine.search(query, max_results=3)
        for r in results:
            print(f"\n标题: {r.title}")
            print(f"链接: {r.url}")
            print(f"摘要: {r.snippet[:100]}..." if len(r.snippet) > 100 else f"摘要: {r.snippet}")
            print(f"来源: {r.source}")
