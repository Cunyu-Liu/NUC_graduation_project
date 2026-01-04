"""Flask后端API v4.0 - 院士级科研智能助手
支持异步工作流、数据库持久化、代码生成
"""
import os
import sys
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# 添加src到路径
sys.path.append(str(Path(__file__).parent))

from src.config import settings
from src.db_manager import DatabaseManager
from src.async_workflow import AsyncWorkflowEngine
from src.code_generator import CodeGenerator

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

# CORS配置
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SocketIO配置
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 初始化数据库
db = DatabaseManager()
try:
    db.create_tables()
    print("✓ 数据库初始化成功")
except Exception as e:
    print(f"⚠ 数据库初始化警告: {e}")

# 初始化工作流引擎
workflow = AsyncWorkflowEngine(
    db_manager=db,
    llm_config={
        'model': os.getenv('LLM_MODEL', 'glm-4-plus'),
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
    """异步路由装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
        return result
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
            data=[paper.to_dict() for paper in papers],
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
                'paper': paper.to_dict(),
                'analyses': [a.to_dict() for a in analyses],
                'relations': [r.to_dict() for r in relations]
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
            data=paper.to_dict(),
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

        # 保存文件
        filename = secure_filename(file.filename)
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
            'metadata': {
                'authors': paper.metadata.authors,
                'keywords': paper.metadata.keywords,
                'sections_count': len(paper.metadata.sections),
                'references_count': len(paper.metadata.references)
            },
            'authors': [{'name': name} for name in paper.metadata.authors],
            'keywords': paper.metadata.keywords
        }

        paper_record = db.create_paper(paper_data)

        return jsonify(create_response(
            success=True,
            data=paper_record.to_dict(),
            message="文件上传并解析成功"
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/analyze', methods=['POST'])
@async_route
async def analyze_paper():
    """分析论文（完整工作流）"""
    try:
        data = request.get_json()
        paper_id = data.get('paper_id')
        tasks = data.get('tasks', ['summary', 'keypoints', 'gaps'])
        auto_generate_code = data.get('auto_generate_code', True)

        if not paper_id:
            return jsonify(create_response(success=False, error="缺少paper_id")), 400

        # 获取论文
        paper = db.get_paper(paper_id)
        if not paper:
            return jsonify(create_response(success=False, error="论文不存在")), 404

        # 安全地构建PDF路径（防止路径遍历攻击）
        pdf_filename = secure_filename(paper.pdf_path)
        pdf_path = (Path(settings.upload_dir) / pdf_filename).resolve()
        if not str(pdf_path).startswith(str(Path(settings.upload_dir).resolve())):
            return jsonify(create_response(success=False, error="非法文件路径")), 400
        if not pdf_path.exists():
            return jsonify(create_response(success=False, error="PDF文件不存在")), 404

        # 执行工作流
        emit_progress(10, "开始分析论文", "初始化")

        result = await workflow.execute_paper_workflow(
            pdf_path=str(pdf_path),
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
        emit_progress(0, f"分析失败: {str(e)}", "错误")
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/batch-analyze', methods=['POST'])
@async_route
async def batch_analyze_papers():
    """批量分析论文"""
    try:
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
                pdf_path = Path(settings.upload_dir) / paper.pdf_path
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
            data=code_record.to_dict(),
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
            data=code.to_dict()
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
            data=updated_code.to_dict(),
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
    """获取高优先级研究空白"""
    try:
        limit = int(request.args.get('limit', 20))

        gaps = db.get_priority_gaps(limit=limit)

        return jsonify(create_response(
            success=True,
            data=[gap.to_dict() for gap in gaps],
            message=f"获取到 {len(gaps)} 个高优先级研究空白"
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
            data=gap.to_dict()
        ))
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@app.route('/api/code/<int:code_id>/versions', methods=['GET'])
def get_code_versions(code_id: int):
    """获取代码版本历史"""
    try:
        versions = db.get_code_versions(code_id)

        return jsonify(create_response(
            success=True,
            data=[v.to_dict() for v in versions],
            message=f"获取到 {len(versions)} 个版本"
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
            data=relation.to_dict(),
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

    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
