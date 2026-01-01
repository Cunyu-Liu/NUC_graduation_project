"""API性能优化中间件 - v4.1"""
import gzip
import json
from functools import wraps
from flask import request, response, after_this_request
import time


def compress_response():
    """
    响应压缩中间件

    自动对JSON响应进行gzip压缩，减少传输数据量
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行视图函数
            resp = f(*args, **kwargs)

            # 只对JSON响应压缩
            if isinstance(resp, tuple):
                response_obj, status = resp[0], resp[1]
            else:
                response_obj, status = resp, 200

            # 检查是否是JSON响应
            if hasattr(response_obj, 'get_json') or \
               (isinstance(response_obj, dict) and 'data' in response_obj):
                @after_this_request
                def compress(response_obj):
                    # 检查客户端是否支持gzip
                    accept_encoding = request.headers.get('Accept-Encoding', '')
                    if 'gzip' in accept_encoding:
                        # 获取响应数据
                        data = response_obj.get_data()

                        # 压缩数据
                        compressed_data = gzip.compress(data, compresslevel=6)

                        # 更新响应头
                        response_obj.set_data(compressed_data)
                        response_obj.headers['Content-Encoding'] = 'gzip'
                        response_obj.headers['Content-Length'] = len(compressed_data)

                    return response_obj

            return resp
        return decorated_function
    return decorator


def add_performance_headers():
    """
    添加性能头中间件

    添加缓存控制、CORS等HTTP头
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = f(*args, **kwargs)

            if hasattr(resp, 'headers'):
                # 缓存控制
                if request.endpoint in ['api.get_papers', 'api.get_paper_detail']:
                    # 可缓存的数据
                    resp.headers['Cache-Control'] = 'public, max-age=300'  # 5分钟
                else:
                    # 动态数据
                    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

                # 安全头
                resp.headers['X-Content-Type-Options'] = 'nosniff'
                resp.headers['X-Frame-Options'] = 'DENY'

                # 性能头
                resp.headers['X-Powered-By'] = 'Academician Assistant v4.1'

            return resp
        return decorated_function
    return decorator


def measure_time():
    """
    测量响应时间中间件

    记录每个API的响应时间，用于性能监控
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # 执行视图函数
            result = f(*args, **kwargs)

            # 计算耗时
            duration = (time.time() - start_time) * 1000  # 毫秒

            # 记录日志（可选）
            if duration > 1000:  # 超过1秒
                print(f"⚠ API {f.__name__} 耗时: {duration:.2f}ms")

            # 添加响应头
            if hasattr(result, 'headers'):
                result.headers['X-Response-Time'] = f'{duration:.2f}ms'

            return result
        return decorated_function
    return decorator


def validate_json_content_type():
    """
    验证JSON内容类型中间件

    确保POST/PUT请求有正确的Content-Type
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = request.headers.get('Content-Type', '')

                # 如果没有JSON content-type但期望JSON
                if 'application/json' not in content_type and request.data:
                    # 尝试解析为JSON
                    try:
                        request._cached_json = json.loads(request.data.decode('utf-8'))
                    except:
                        pass

            return f(*args, **kwargs)
        return decorated_function
    return decorator


class ResponseOptimizer:
    """响应优化器"""

    @staticmethod
    def optimize_response(data: dict, request_path: str) -> dict:
        """
        优化响应数据

        根据不同的API返回优化后的数据，减少传输量
        """
        # 对于大列表数据，只返回关键字段
        if 'papers' in data and isinstance(data['papers'], list):
            papers = data['papers']
            # 列表视图：只返回ID、标题、年份
            optimized = []
            for paper in papers[:100]:  # 最多返回100个
                optimized.append({
                    'id': paper.get('id'),
                    'title': paper.get('title', '')[:100] + '...' if len(paper.get('title', '')) > 100 else paper.get('title', ''),
                    'year': paper.get('year'),
                    'venue': paper.get('venue', '')[:50]
                })
            data['papers'] = optimized
            data['total_count'] = len(papers)  # 总数

        # 对于分析结果，移除冗余的中间数据
        elif 'keypoints' in data and isinstance(data['keypoints'], dict):
            keypoints = data['keypoints']
            # 移除空列表
            data['keypoints'] = {
                k: v for k, v in keypoints.items()
                if v and len(v) > 0
            }

        return data

    @staticmethod
    def paginate_data(data: list, page: int = 1, per_page: int = 20) -> dict:
        """
        分页数据

        Args:
            data: 原始数据列表
            page: 页码
            per_page: 每页数量

        Returns:
            分页后的数据
        """
        total = len(data)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'data': data[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }


def apply_cache_from_request(cache_manager):
    """
    从请求应用缓存

    根据查询参数自动生成缓存键
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 只对GET请求缓存
            if request.method != 'GET':
                return f(*args, **kwargs)

            # 生成缓存键
            cache_key = f"{request.endpoint}:{request.query_string.decode()}"

            # 尝试从缓存获取
            if cache_manager:
                cached = cache_manager.get(cache_key)
                if cached:
                    return jsonify(create_response(
                        success=True,
                        data=cached,
                        message="来自缓存"
                    ))

            # 执行视图函数
            result = f(*args, **kwargs)

            # 存入缓存（如果是成功响应）
            if cache_manager and isinstance(result, tuple) is False:
                try:
                    response_data = result.get_json() if hasattr(result, 'get_json') else result
                    if isinstance(response_data, dict) and response_data.get('success'):
                        cache_manager.set(cache_key, response_data, ttl=300)
                except:
                    pass

            return result
        return decorated_function
    return decorator


# ============================================================================
# 使用示例
# ============================================================================

"""
在Flask路由中使用示例：

@app.route('/api/papers')
@compress_response()
@add_performance_headers()
@measure_time()
def get_papers():
    papers = db.get_papers(...)
    return jsonify(create_response(success=True, data=papers))

@app.route('/api/papers/<int:paper_id>')
@compress_response()
@add_performance_headers()
def get_paper_detail(paper_id):
    paper = db.get_paper(paper_id)
    return jsonify(create_response(success=True, data=paper))
"""
