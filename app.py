"""Flask后端API v4.0 - 院士级科研智能助手
支持异步工作流、数据库持久化、代码生成
"""
import os
import sys
import json
import asyncio
import hashlib
import re
import platform
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# 在macOS上修复asyncio event loop问题
# macOS上的Kqueue selector在Python 3.9中可能有问题
if platform.system() == 'Darwin':  # macOS
    import selectors
    # 创建自定义的event loop policy，使用更稳定的selector
    class MacOSEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
        def new_event_loop(self):
            """创建一个不使用Kqueue的事件循环"""
            try:
                # 尝试使用PollSelector（如果可用）
                selector = selectors.PollSelector()
            except (AttributeError, OSError):
                # 回退到SelectSelector
                selector = selectors.SelectSelector()

            # 创建使用该selector的事件循环
            loop = asyncio.SelectorEventLoop(selector)
            return loop

    # 设置自定义policy
    asyncio.set_event_loop_policy(MacOSEventLoopPolicy())

# 加载环境变量（必须在导入其他模块前）
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 添加src到路径
sys.path.append(str(Path(__file__).parent))

from src.config import settings
from src.db_manager import DatabaseManager
from src.async_workflow import AsyncWorkflowEngine
from src.code_generator import CodeGenerator
from src.auth import hash_password, verify_password, generate_token, decode_token, auth_required

# v4.1 性能优化模块
try:
    from src.cache_manager import cache_manager, paper_cache, analysis_cache, graph_cache
    from src.api_middleware import compress_response, add_performance_headers, measure_time
    CACHE_AVAILABLE = True
    print("✓ 缓存和中间件模块加载成功")
except ImportError as e:
    print(f"⚠ 优化模块加载失败: {e}")
    CACHE_AVAILABLE = False
    cache_manager = None

# ============================================================================
# 应用初始化
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = str(settings.upload_dir)
app.config['JSON_AS_ASCII'] = False

# CORS配置 - 支持文件上传和所有HTTP方法
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# SocketIO配置 - 使用threading模式以兼容asyncio
# 注意：eventlet会monkey-patch标准库，在macOS上会破坏asyncio的Kqueue selector
# 因此我们使用threading模式，这样可以与asyncio共存
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    allow_upgrades=True  # 允许升级到WebSocket
)
SOCKETIO_MODE = 'threading'

# 初始化数据库
db = DatabaseManager()
try:
    db.create_tables()
    print("✓ 数据库初始化成功")
except Exception as e:
    print(f"⚠ 数据库初始化警告: {e}")

# 初始化工作流引擎
# 设置OpenAI API密钥环境变量（ChatOpenAI需要）
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = os.getenv('GLM_API_KEY', '')

workflow = AsyncWorkflowEngine(
    db_manager=db,
    llm_config={
        'model': os.getenv('LLM_MODEL', 'glm-4-flash'),
        'api_key': os.getenv('GLM_API_KEY'),
        'base_url': os.getenv('GLM_BASE_URL'),
        'max_concurrent': int(os.getenv('MAX_CONCURRENT', 5))
    }
)

# 初始化代码生成器
code_generator = CodeGenerator(db_manager=db, llm=None)

# ============================================================================
# 辅助函数
# ============================================================================

def create_response(success: bool, data: Any = None, message: str = "", error: str = "") -> Dict:
    """创建统一响应格式"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "version": "4.1.0"
    }

    if success:
        response["data"] = data
        if message:
            response["message"] = message
    else:
        response["error"] = error
        if message:
            response["message"] = message

    return response


def allowed_file(filename: str) -> bool:
    """检查文件类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def calculate_file_hash(filepath: str) -> str:
    """计算文件MD5"""
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def emit_progress(progress: int, message: str, step: str = ""):
    """发送进度更新"""
    socketio.emit('progress', {
        'progress': progress,
        'message': message,
        'step': step,
        'timestamp': datetime.now().isoformat()
    })


def async_route(f):
    """异步路由装饰器 - 使用asyncio.run()确保正确的循环管理"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            # asyncio.run() 会创建新的事件循环并正确管理生命周期
            # 这比手动创建循环更安全，特别是在macOS上
            result = asyncio.run(f(*args, **kwargs))
            return result
        except Exception as e:
            # 记录异常以便调试
            import traceback
            print(f"[ERROR] async_route error: {e}")
            traceback.print_exc()
            raise
    return wrapper


# ============================================================================
# 基础路由：健康检查和配置
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    stats = db.get_statistics()
    return jsonify(create_response(
        success=True,
        message="系统运行正常",
        data={"version": "4.1.0", "stats": stats}
    ))


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    config_data = {
        "model": os.getenv('LLM_MODEL', 'glm-4-plus'),
        "temperature": settings.default_temperature,
        "maxTokens": settings.max_tokens,
        "uploadDir": str(settings.upload_dir),
        "outputDir": str(settings.output_dir),
        "maxConcurrent": int(os.getenv('MAX_CONCURRENT', 5))
    }
    return jsonify(create_response(success=True, data=config_data))


# ============================================================================
# 用户认证相关API
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        # 打印请求信息用于调试
        print(f"\n[DEBUG] ========== 注册请求调试信息 ==========")
        print(f"[DEBUG] Content-Type: {request.content_type}")
        print(f"[DEBUG] 原始数据: {request.data[:500]}")  # 打印前500字节
        print(f"[DEBUG] 数据长度: {len(request.data)}")

        # 获取请求数据
        data = request.get_json(force=True, silent=True)

        print(f"[DEBUG] 解析后的数据: {data}")

        # 如果JSON解析失败
        if data is None:
            print(f"[DEBUG] ❌ JSON解析失败 - data is None")
            print(f"[DEBUG] 尝试不使用silent参数重新解析...")
            try:
                data = request.get_json(force=True)
                print(f"[DEBUG] 强制解析成功: {data}")
            except Exception as e:
                print(f"[DEBUG] ❌ 强制解析也失败: {e}")
                import traceback
                traceback.print_exc()

            return jsonify(create_response(
                success=False,
                error="无效的JSON数据"
            )), 400

        # 验证必填字段
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')

        print(f"[DEBUG] 提取的字段 - username: {username}, email: {email}, password: {'*' * len(password) if password else 'None'}")

        if not username or not email or not password:
            print(f"[DEBUG] 必填字段缺失")
            return jsonify(create_response(
                success=False,
                error="用户名、邮箱和密码不能为空"
            )), 400

        # 验证用户名格式（3-20个字符，只能包含字母、数字、下划线）
        username = data.get('username', '').strip()
        if not username:
            return jsonify(create_response(
                success=False,
                error="用户名不能为空"
            )), 400

        if len(username) < 3 or len(username) > 20:
            return jsonify(create_response(
                success=False,
                error="用户名长度必须在3-20个字符之间"
            )), 400

        # 验证邮箱格式
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify(create_response(
                success=False,
                error="邮箱不能为空"
            )), 400

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify(create_response(
                success=False,
                error="邮箱格式不正确"
            )), 400

        # 验证密码长度（至少6个字符）
        password = data.get('password', '')
        if not password:
            return jsonify(create_response(
                success=False,
                error="密码不能为空"
            )), 400

        if len(password) < 6:
            return jsonify(create_response(
                success=False,
                error="密码长度至少为6个字符"
            )), 400

        # 加密密码
        password_hash = hash_password(password)

        # 准备用户数据
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'full_name': data.get('full_name', '').strip(),
            'bio': data.get('bio', '').strip(),
            'institution': data.get('institution', '').strip(),
            'research_interests': data.get('research_interests', []),
            'is_active': True,
            'is_verified': False
        }

        # 创建用户
        try:
            print(f"[DEBUG] 准备创建用户: {username}")
            user = db.create_user(user_data)
            print(f"[DEBUG] 用户创建成功: {user.id if user else 'None'}")
        except ValueError as e:
            print(f"[DEBUG] ValueError: {str(e)}")
            return jsonify(create_response(
                success=False,
                error=str(e)
            )), 400
        except Exception as e:
            print(f"[DEBUG] Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify(create_response(
                success=False,
                error=f"创建用户失败: {str(e)}"
            )), 500

        # 生成token
        token = generate_token(user.id, user.username, user.email)

        # 转换用户数据为字典
        user_dict = user.to_dict() if user else None

        return jsonify(create_response(
            success=True,
            data={
                'token': token,
                'user': user_dict
            },
            message="注册成功"
        )), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(create_response(
            success=False,
            error=f"服务器错误: {str(e)}"
        )), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('login_identifier') or not data.get('password'):
            return jsonify(create_response(
                success=False,
                error="用户名/邮箱和密码不能为空"
            )), 400

        login_identifier = data.get('login_identifier').strip()
        password = data.get('password')

        # 查找用户（通过用户名或邮箱）
        user = db.get_user_by_username(login_identifier)
        if not user:
            user = db.get_user_by_email(login_identifier)

        if not user:
            return jsonify(create_response(
                success=False,
                error="用户名或密码错误"
            )), 401

        # 验证密码
        if not verify_password(password, user.password_hash):
            return jsonify(create_response(
                success=False,
                error="用户名或密码错误"
            )), 401

        # 检查用户状态
        if not user.is_active:
            return jsonify(create_response(
                success=False,
                error="账号已被禁用"
            )), 403

        # 更新登录信息
        db.update_user_login_info(user.id)

        # 生成token
        token = generate_token(user.id, user.username, user.email)

        return jsonify(create_response(
            success=True,
            data={
                'token': token,
                'user': user.to_dict()
            },
            message="登录成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/auth/user', methods=['GET'])
@auth_required
def get_current_user():
    """获取当前登录用户信息"""
    try:
        user_id = getattr(request, 'current_user_id', None)
        if not user_id:
            return jsonify(create_response(
                success=False,
                error="未登录"
            )), 401

        user = db.get_user(user_id)
        if not user:
            return jsonify(create_response(
                success=False,
                error="用户不存在"
            )), 404

        return jsonify(create_response(
            success=True,
            data=user.to_dict()
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/auth/user', methods=['PUT'])
@auth_required
def update_current_user():
    """更新当前用户信息"""
    try:
        user_id = getattr(request, 'current_user_id', None)
        if not user_id:
            return jsonify(create_response(
                success=False,
                error="未登录"
            )), 401

        data = request.get_json()

        # 不允许直接修改的字段
        protected_fields = ['id', 'username', 'email', 'password_hash',
                          'login_count', 'last_login_at', 'created_at', 'is_verified']
        for field in protected_fields:
            if field in data:
                del data[field]

        # 更新用户信息
        user = db.update_user(user_id, data)
        if not user:
            return jsonify(create_response(
                success=False,
                error="用户不存在"
            )), 404

        return jsonify(create_response(
            success=True,
            data=user.to_dict(),
            message="用户信息更新成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/auth/change-password', methods=['POST'])
@auth_required
def change_password():
    """修改密码"""
    try:
        user_id = getattr(request, 'current_user_id', None)
        if not user_id:
            return jsonify(create_response(
                success=False,
                error="未登录"
            )), 401

        data = request.get_json()

        # 验证必填字段
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify(create_response(
                success=False,
                error="旧密码和新密码不能为空"
            )), 400

        # 获取用户
        user = db.get_user(user_id)
        if not user:
            return jsonify(create_response(
                success=False,
                error="用户不存在"
            )), 404

        # 验证旧密码
        if not verify_password(data.get('old_password'), user.password_hash):
            return jsonify(create_response(
                success=False,
                error="旧密码错误"
            )), 400

        # 验证新密码长度
        if len(data.get('new_password')) < 6:
            return jsonify(create_response(
                success=False,
                error="新密码长度至少为6个字符"
            )), 400

        # 更新密码
        new_password_hash = hash_password(data.get('new_password'))
        success = db.change_password(user_id, new_password_hash)

        if not success:
            return jsonify(create_response(
                success=False,
                error="密码修改失败"
            )), 500

        return jsonify(create_response(
            success=True,
            message="密码修改成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 论文管理CRUD
# ============================================================================

@app.route('/api/papers', methods=['GET'])
def get_papers():
    """获取论文列表（支持搜索和过滤）"""
    try:
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        year_from = request.args.get('year_from', type=int)
        year_to = request.args.get('year_to', type=int)
        venue = request.args.get('venue', '')

        papers = db.get_papers(
            skip=skip,
            limit=limit,
            search=search,
            year_from=year_from,
            year_to=year_to,
            venue=venue
        )

        return jsonify(create_response(
            success=True,
            data=papers,
            message=f"获取到 {len(papers)} 篇论文"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/papers/<int:paper_id>', methods=['GET'])
def get_paper_detail(paper_id: int):
    """获取论文详情"""
    try:
        paper = db.get_paper(paper_id)
        if not paper:
            return jsonify(create_response(success=False, error="论文不存在")), 404

        # 获取分析历史
        analyses = db.get_analyses_by_paper(paper_id)

        # 获取关系
        relations = db.get_relations(paper_id)

        return jsonify(create_response(
            success=True,
            data={
                'paper': paper,
                'analyses': analyses,
                'relations': relations
            }
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/papers/<int:paper_id>', methods=['PUT'])
def update_paper(paper_id: int):
    """更新论文信息"""
    try:
        data = request.get_json()
        paper = db.update_paper(paper_id, data)

        if not paper:
            return jsonify(create_response(success=False, error="论文不存在")), 404

        return jsonify(create_response(
            success=True,
            data=paper,
            message="论文更新成功"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(paper_id: int):
    """删除论文"""
    try:
        success = db.delete_paper(paper_id)
        if not success:
            return jsonify(create_response(success=False, error="论文不存在")), 404

        return jsonify(create_response(
            success=True,
            message="论文删除成功"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/papers/batch-delete', methods=['POST'])
def batch_delete_papers():
    """批量删除论文"""
    try:
        data = request.get_json()
        paper_ids = data.get('paper_ids', [])

        count = db.batch_delete_papers(paper_ids)

        return jsonify(create_response(
            success=True,
            data={'deleted_count': count},
            message=f"成功删除 {count} 篇论文"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 文件上传和分析
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传PDF文件"""
    try:
        if 'file' not in request.files:
            return jsonify(create_response(success=False, error="没有文件")), 400

        # 添加文件大小检查
        if request.content_length and request.content_length > 100 * 1024 * 1024:
            return jsonify(create_response(success=False, error="文件大小超过限制（最大100MB）")), 413

        file = request.files['file']
        if file.filename == '':
            return jsonify(create_response(success=False, error="文件名为空")), 400

        if not allowed_file(file.filename):
            return jsonify(create_response(success=False, error="仅支持PDF文件")), 400

        # 保存文件 - 生成唯一文件名以避免冲突
        original_filename = file.filename
        # 使用时间戳 + 原始文件名（去除特殊字符）生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # 清理文件名：保留扩展名，移除特殊字符
        file_ext = Path(original_filename).suffix or '.pdf'
        safe_basename = secure_filename(Path(original_filename).stem) or 'paper'
        filename = f"{timestamp}_{safe_basename}{file_ext}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(filepath))

        # 计算文件哈希
        file_hash = calculate_file_hash(str(filepath))

        # 解析PDF并保存到数据库
        from src.pdf_parser_enhanced import EnhancedPDFParser
        parser = EnhancedPDFParser()
        paper = parser.parse_pdf(str(filepath))

        paper_data = {
            'title': paper.metadata.title,
            'abstract': paper.metadata.abstract,
            'pdf_path': filename,
            'pdf_hash': file_hash,
            'year': paper.metadata.year,
            'venue': paper.metadata.publication_venue,
            'doi': paper.metadata.doi,
            'page_count': paper.page_count,
            'language': paper.language,
            'meta_data': {
                'authors': paper.metadata.authors,
                'keywords': paper.metadata.keywords,
                'sections_count': len(paper.metadata.sections),
                'references_count': len(paper.metadata.references)
            },
            'authors': [{'name': name} for name in paper.metadata.authors],
            'keywords': paper.metadata.keywords
        }

        print(f"[DEBUG] 准备创建论文记录: {paper_data.get('title', 'Unknown')}")
        print(f"[DEBUG] paper_data类型: {type(paper_data)}")

        paper_record = db.create_paper(paper_data)

        print(f"[DEBUG] 论文记录创建成功: {paper_record}")

        return jsonify(create_response(
            success=True,
            data=paper_record,
            message="文件上传并解析成功"
        ))

    except Exception as e:
        import traceback
        print(f"[ERROR] 上传失败: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/analyze', methods=['POST'])
@async_route
async def analyze_paper():
    """分析论文（完整工作流）"""
    try:
        import traceback
        data = request.get_json()
        paper_id = data.get('paper_id')
        tasks = data.get('tasks', ['summary', 'keypoints', 'gaps'])
        auto_generate_code = data.get('auto_generate_code', True)

        print(f"[DEBUG] 分析请求: paper_id={paper_id}, tasks={tasks}")

        if not paper_id:
            return jsonify(create_response(success=False, error="缺少paper_id")), 400

        # 获取论文
        paper = db.get_paper(paper_id)
        if not paper:
            print(f"[ERROR] 论文不存在: paper_id={paper_id}")
            return jsonify(create_response(success=False, error="论文不存在")), 404

        print(f"[DEBUG] 论文数据: {paper}")

        # paper 是字典,需要用字典方式访问
        # pdf_path 已经是安全的文件名，不需要再次调用 secure_filename
        pdf_filename = paper.get('pdf_path', '')
        if not pdf_filename:
            print(f"[ERROR] 论文没有pdf_path字段")
            return jsonify(create_response(success=False, error="论文数据异常:缺少pdf_path")), 400

        # 安全地构建PDF路径（防止路径遍历攻击）
        pdf_path = (Path(settings.upload_dir) / pdf_filename).resolve()
        if not str(pdf_path).startswith(str(Path(settings.upload_dir).resolve())):
            return jsonify(create_response(success=False, error="非法文件路径")), 400

        if not pdf_path.exists():
            print(f"[ERROR] PDF文件不存在: {pdf_path}")
            return jsonify(create_response(success=False, error="PDF文件不存在")), 404

        print(f"[DEBUG] PDF路径: {pdf_path}")

        # 执行工作流 - 传递paper_id避免重复保存
        emit_progress(10, "开始分析论文", "初始化")

        result = await workflow.execute_paper_workflow(
            pdf_path=str(pdf_path),
            paper_id=paper_id,  # 传递已存在的论文ID
            tasks=tasks,
            auto_generate_code=auto_generate_code
        )

        emit_progress(100, "分析完成", "完成")

        return jsonify(create_response(
            success=True,
            data=result,
            message="论文分析完成"
        ))

    except Exception as e:
        import traceback
        print(f"[ERROR] 分析失败: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        emit_progress(0, f"分析失败: {str(e)}", "错误")
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/batch-analyze', methods=['POST'])
@async_route
async def batch_analyze_papers():
    """批量分析论文"""
    try:
        import traceback
        data = request.get_json()
        paper_ids = data.get('paper_ids', [])
        tasks = data.get('tasks', ['summary', 'keypoints'])

        if not paper_ids:
            return jsonify(create_response(success=False, error="缺少paper_ids")), 400

        # 获取论文
        pdf_paths = []
        for paper_id in paper_ids:
            paper = db.get_paper(paper_id)
            if paper:
                # paper 是字典,需要用字典方式访问
                pdf_filename = paper.get('pdf_path')
                if pdf_filename:
                    pdf_path = Path(settings.upload_dir) / pdf_filename
                    if pdf_path.exists():
                        pdf_paths.append(str(pdf_path))

        if not pdf_paths:
            return jsonify(create_response(success=False, error="没有有效的PDF文件")), 400

        # 批量处理
        emit_progress(10, f"开始批量处理 {len(pdf_paths)} 篇论文", "初始化")

        summary = await workflow.batch_process_papers(
            pdf_paths=pdf_paths,
            tasks=tasks
        )

        emit_progress(100, "批量处理完成", "完成")

        return jsonify(create_response(
            success=True,
            data=summary,
            message=f"批量处理完成: {summary['success']}/{summary['total']} 成功"
        ))

    except Exception as e:
        import traceback
        print(f"[ERROR] 批量分析失败: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/cluster', methods=['POST'])
def cluster_papers():
    """主题聚类分析"""
    try:
        import traceback
        from src.topic_clustering import TopicClustering
        from src.pdf_parser_enhanced import EnhancedPDFParser

        data = request.get_json()
        paper_ids = data.get('paper_ids', [])
        n_clusters = data.get('n_clusters', 5)
        method = data.get('method', 'kmeans')
        language = data.get('language', 'chinese')

        if not paper_ids:
            return jsonify(create_response(success=False, error="缺少paper_ids")), 400

        # 获取论文PDF路径
        pdf_paths = []
        paper_titles = []
        for paper_id in paper_ids:
            paper = db.get_paper(paper_id)
            if paper:
                # paper 是字典,需要用字典方式访问
                pdf_filename = paper.get('pdf_path')
                if pdf_filename:
                    pdf_path = Path(settings.upload_dir) / pdf_filename
                    if pdf_path.exists():
                        pdf_paths.append(str(pdf_path))
                        paper_titles.append(paper.get('title') or pdf_filename)

        if len(pdf_paths) < 2:
            return jsonify(create_response(success=False, error="至少需要2篇论文才能进行聚类")), 400

        # 解析PDF
        parser = EnhancedPDFParser()
        papers = []
        for pdf_path in pdf_paths:
            try:
                paper = parser.parse_pdf(pdf_path)
                papers.append(paper)
            except Exception as e:
                print(f"解析PDF失败 {pdf_path}: {e}")

        if len(papers) < 2:
            return jsonify(create_response(success=False, error="成功解析的论文数量不足")), 400

        # 执行聚类
        emit_progress(20, f"开始聚类分析 {len(papers)} 篇论文", "聚类中")

        clustering = TopicClustering(
            n_clusters=n_clusters,
            clustering_method=method,
            language=language
        )

        result = clustering.cluster_papers(
            papers=papers,
            save_visualization=False,
            save_report=False
        )

        emit_progress(100, "聚类分析完成", "完成")

        # 格式化返回数据
        formatted_result = {
            'n_clusters': result['unique_clusters'],
            'cluster_analysis': result['cluster_analysis'],
            'papers': paper_titles,
            'labels': result['labels'].tolist()
        }

        return jsonify(create_response(
            success=True,
            data=formatted_result,
            message=f"聚类完成，共发现 {result['unique_clusters']} 个主题类别"
        ))

    except Exception as e:
        import traceback
        print(f"[ERROR] 聚类失败: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 代码生成
# ============================================================================

@app.route('/api/gaps/<int:gap_id>/generate-code', methods=['POST'])
@async_route
async def generate_gap_code(gap_id: int):
    """为研究空白生成代码"""
    try:
        data = request.get_json()
        strategy = data.get('strategy', 'method_improvement')
        user_prompt = data.get('user_prompt')

        # 获取研究空白
        from src.database import ResearchGap
        gap = db.db_manager.query(ResearchGap).filter(
            ResearchGap.id == gap_id
        ).first()

        if not gap:
            return jsonify(create_response(success=False, error="研究空白不存在")), 404

        emit_progress(20, "开始生成代码", "生成中")

        # 生成代码
        code_data = await code_generator.generate_code_async(
            research_gap=gap,
            strategy=strategy,
            user_prompt=user_prompt
        )

        # 保存到数据库
        code_data['gap_id'] = gap_id
        code_record = db.create_generated_code(code_data)

        emit_progress(100, "代码生成完成", "完成")

        return jsonify(create_response(
            success=True,
            data=code_record,
            message="代码生成成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/code/<int:code_id>', methods=['GET'])
def get_code(code_id: int):
    """获取生成的代码"""
    try:
        code = db.get_code(code_id)
        if not code:
            return jsonify(create_response(success=False, error="代码不存在")), 404

        return jsonify(create_response(
            success=True,
            data=code
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/code/<int:code_id>/modify', methods=['POST'])
@async_route
async def modify_code(code_id: int):
    """修改生成的代码"""
    try:
        data = request.get_json()
        user_prompt = data.get('user_prompt')

        if not user_prompt:
            return jsonify(create_response(success=False, error="缺少user_prompt")), 400

        emit_progress(10, "开始修改代码", "处理中")

        # 修改代码
        updated_code = await code_generator.modify_code_async(
            code_id=code_id,
            user_prompt=user_prompt,
            db_manager=db
        )

        emit_progress(100, "代码修改完成", "完成")

        return jsonify(create_response(
            success=True,
            data=updated_code,
            message="代码修改成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 知识图谱
# ============================================================================

@app.route('/api/knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    """获取知识图谱数据"""
    try:
        paper_ids = request.args.getlist('paper_ids', type=int)

        graph = db.get_paper_graph(paper_ids if paper_ids else None)

        return jsonify(create_response(
            success=True,
            data=graph,
            message=f"获取知识图谱: {len(graph['nodes'])} 个节点, {len(graph['edges'])} 条边"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 统计和分析
# ============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        stats = db.get_statistics()

        return jsonify(create_response(
            success=True,
            data=stats
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/gaps/priority', methods=['GET'])
def get_priority_gaps():
    """获取高优先级研究空白（改为返回所有研究空白）"""
    try:
        limit = int(request.args.get('limit', 100))
        importance = request.args.get('importance', None)  # 可选筛选

        # 使用新的get_all_gaps方法获取所有研究空白
        gaps = db.get_all_gaps(limit=limit, skip=0, importance=importance)

        return jsonify(create_response(
            success=True,
            data=gaps,
            message=f"获取到 {len(gaps)} 个研究空白"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/gaps/<int:gap_id>', methods=['GET'])
def get_gap_detail(gap_id: int):
    """获取研究空白详情"""
    try:
        gap = db.get_research_gap(gap_id)
        if not gap:
            return jsonify(create_response(success=False, error="研究空白不存在")), 404

        return jsonify(create_response(
            success=True,
            data=gap
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/code/<int:code_id>/versions', methods=['GET'])
def get_code_versions(code_id: int):
    """获取代码版本历史"""
    try:
        code = db.get_code(code_id)
        if not code:
            return jsonify(create_response(success=False, error="代码不存在")), 404

        # 简单返回当前代码信息，版本历史功能待实现
        return jsonify(create_response(
            success=True,
            data=[code],
            message=f"获取到代码信息"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/knowledge-graph/build', methods=['POST'])
def build_knowledge_graph():
    """手动构建知识图谱"""
    try:
        data = request.get_json()
        paper_ids = data.get('paper_ids', [])

        # 这里可以触发图谱重新构建
        # 实际实现取决于你的图谱构建逻辑

        return jsonify(create_response(
            success=True,
            message="知识图谱构建任务已提交"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/relations', methods=['POST'])
def add_relation():
    """手动添加论文关系"""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        relation_type = data.get('relation_type')
        strength = data.get('strength', 0.5)
        evidence = data.get('evidence', '')

        if not all([source_id, target_id, relation_type]):
            return jsonify(create_response(success=False, error="缺少必要参数")), 400

        relation = db.create_relation({
            'source_id': source_id,
            'target_id': target_id,
            'relation_type': relation_type,
            'strength': strength,
            'evidence': evidence
        })

        return jsonify(create_response(
            success=True,
            data=relation,
            message="关系添加成功"
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 院士级科研智能助手 v4.1")
    print("="*80)
    print(f"✓ 后端服务: http://localhost:5001")
    print(f"✓ API版本: 4.0.0")
    print(f"✓ 数据库: PostgreSQL")
    print(f"✓ 支持异步: 是")
    print(f"✓ WebSocket: 启用")
    print("="*80 + "\n")

    socketio.run(app, debug=True, port=5001, host='0.0.0.0', allow_unsafe_werkzeug=True)
