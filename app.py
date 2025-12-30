"""Flask后端API - 提供Web服务接口"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# 添加src到路径
sys.path.append(str(Path(__file__).parent))

from src.config import settings
from src.pdf_parser import PDFParser
from src.summary_generator import SummaryGenerator
from src.keypoint_extractor import KeypointExtractor
from src.topic_clustering import TopicClustering
from src.workflow import PaperAnalysisWorkflow

# 创建Flask应用
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB最大上传
app.config['UPLOAD_FOLDER'] = str(settings.upload_dir)

# 启用CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 配置SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# 辅助函数
# ============================================================================

def allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def create_response(success: bool, data: Any = None, message: str = "", error: str = "") -> Dict:
    """创建统一响应格式"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
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


def emit_progress(progress: int, message: str, step: str = ""):
    """发送进度更新（WebSocket）"""
    socketio.emit('progress', {
        'progress': progress,
        'message': message,
        'step': step,
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# 路由：健康检查和配置
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify(create_response(
        success=True,
        message="系统运行正常",
        data={"version": "1.0.0"}
    ))


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    config_data = {
        "model": settings.default_model,
        "temperature": settings.default_temperature,
        "maxTokens": settings.max_tokens,
        "uploadDir": str(settings.upload_dir),
        "outputDir": str(settings.output_dir)
    }
    return jsonify(create_response(success=True, data=config_data))


# ============================================================================
# 路由：文件上传和管理
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传PDF文件"""
    if 'file' not in request.files:
        return jsonify(create_response(success=False, error="没有上传文件")), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify(create_response(success=False, error="未选择文件")), 400

    if not allowed_file(file.filename):
        return jsonify(create_response(success=False, error="只支持PDF文件")), 400

    try:
        # 安全保存文件
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(filepath)

        return jsonify(create_response(
            success=True,
            message="文件上传成功",
            data={
                "filename": filename,
                "filepath": str(filepath),
                "size": filepath.stat().st_size
            }
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=f"上传失败: {str(e)}")), 500


@app.route('/api/files', methods=['GET'])
def list_files():
    """列出已上传的文件"""
    try:
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        files = []

        for filepath in upload_dir.glob("*.pdf"):
            files.append({
                "filename": filepath.name,
                "size": filepath.stat().st_size,
                "uploadedAt": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            })

        files.sort(key=lambda x: x['uploadedAt'], reverse=True)

        return jsonify(create_response(
            success=True,
            data={"files": files}
        ))

    except Exception as e:
        return jsonify(create_response(success=False, error=f"获取文件列表失败: {str(e)}")), 500


@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename: str):
    """删除文件"""
    try:
        filepath = Path(app.config['UPLOAD_FOLDER']) / secure_filename(filename)

        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return jsonify(create_response(success=True, message="文件删除成功"))
        else:
            return jsonify(create_response(success=False, error="文件不存在")), 404

    except Exception as e:
        return jsonify(create_response(success=False, error=f"删除失败: {str(e)}")), 500


# ============================================================================
# 路由：PDF解析
# ============================================================================

@app.route('/api/parse', methods=['POST'])
def parse_pdf():
    """解析PDF文件"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath or not Path(filepath).exists():
            return jsonify(create_response(success=False, error="文件路径无效")), 400

        emit_progress(10, "开始解析PDF...")

        parser = PDFParser()
        paper = parser.parse_pdf(filepath)

        emit_progress(100, "PDF解析完成")

        result = {
            "filename": paper.filename,
            "pageCount": paper.page_count,
            "fullTextLength": len(paper.full_text),
            "metadata": {
                "title": paper.metadata.title,
                "abstract": paper.metadata.abstract,
                "keywords": paper.metadata.keywords,
                "sections": list(paper.metadata.sections.keys())
            }
        }

        return jsonify(create_response(
            success=True,
            message="PDF解析成功",
            data=result
        ))

    except Exception as e:
        emit_progress(0, f"解析失败: {str(e)}")
        return jsonify(create_response(success=False, error=f"解析失败: {str(e)}")), 500


# ============================================================================
# 路由：摘要生成
# ============================================================================

@app.route('/api/summarize', methods=['POST'])
def generate_summary():
    """生成论文摘要"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        model = data.get('model', settings.default_model)
        temperature = data.get('temperature', settings.default_temperature)

        if not filepath or not Path(filepath).exists():
            return jsonify(create_response(success=False, error="文件路径无效")), 400

        emit_progress(10, "正在解析PDF...")

        # 解析PDF
        parser = PDFParser()
        paper = parser.parse_pdf(filepath)

        emit_progress(30, "正在生成摘要...")

        # 生成摘要
        generator = SummaryGenerator(model=model, temperature=temperature)
        summary = generator.generate_summary(paper, save=True)

        emit_progress(100, "摘要生成完成")

        return jsonify(create_response(
            success=True,
            message="摘要生成成功",
            data={"summary": summary}
        ))

    except Exception as e:
        emit_progress(0, f"生成失败: {str(e)}")
        return jsonify(create_response(success=False, error=f"生成失败: {str(e)}")), 500


# ============================================================================
# 路由：要点提取
# ============================================================================

@app.route('/api/extract', methods=['POST'])
def extract_keypoints():
    """提取论文要点"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        model = data.get('model', settings.default_model)

        if not filepath or not Path(filepath).exists():
            return jsonify(create_response(success=False, error="文件路径无效")), 400

        emit_progress(10, "正在解析PDF...")

        # 解析PDF
        parser = PDFParser()
        paper = parser.parse_pdf(filepath)

        emit_progress(30, "正在提取要点...")

        # 提取要点
        extractor = KeypointExtractor(model=model)
        keypoints = extractor.extract_keypoints(paper, save=True)

        emit_progress(100, "要点提取完成")

        return jsonify(create_response(
            success=True,
            message="要点提取成功",
            data=keypoints
        ))

    except Exception as e:
        emit_progress(0, f"提取失败: {str(e)}")
        return jsonify(create_response(success=False, error=f"提取失败: {str(e)}")), 500


# ============================================================================
# 路由：完整分析（使用LangGraph工作流）
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_paper():
    """完整分析论文（使用工作流）"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        tasks = data.get('tasks', ['summary', 'keypoints', 'topic'])

        if not filepath or not Path(filepath).exists():
            return jsonify(create_response(success=False, error="文件路径无效")), 400

        emit_progress(5, "初始化工作流...")

        # 执行工作流
        workflow = PaperAnalysisWorkflow()

        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(workflow.analyze(filepath, tasks))
        finally:
            loop.close()

        if result['status'] == 'failed':
            return jsonify(create_response(
                success=False,
                error="工作流执行失败",
                data={"errors": result['errors']}
            )), 500

        emit_progress(100, "分析完成")

        # 准备返回数据
        response_data = {
            "status": result['status'],
            "summary": result.get('summary'),
            "keypoints": result.get('keypoints'),
            "topicAnalysis": result.get('topic_analysis'),
            "errors": result.get('errors', [])
        }

        return jsonify(create_response(
            success=True,
            message="分析完成",
            data=response_data
        ))

    except Exception as e:
        emit_progress(0, f"分析失败: {str(e)}")
        return jsonify(create_response(success=False, error=f"分析失败: {str(e)}")), 500


# ============================================================================
# 路由：主题聚类
# ============================================================================

@app.route('/api/cluster', methods=['POST'])
def cluster_papers():
    """多篇论文主题聚类"""
    try:
        data = request.get_json()
        filepaths = data.get('filepaths', [])
        n_clusters = data.get('nClusters', 5)
        method = data.get('method', 'kmeans')
        language = data.get('language', 'chinese')

        if len(filepaths) < 2:
            return jsonify(create_response(success=False, error="至少需要2篇论文")), 400

        emit_progress(10, f"正在解析 {len(filepaths)} 篇论文...")

        # 解析所有PDF
        parser = PDFParser()
        papers = []

        for i, filepath in enumerate(filepaths):
            if not Path(filepath).exists():
                continue

            try:
                paper = parser.parse_pdf(filepath)
                papers.append(paper)
                emit_progress(
                    10 + int(30 * (i + 1) / len(filepaths)),
                    f"解析中 ({i + 1}/{len(filepaths)})..."
                )
            except Exception as e:
                print(f"解析失败 {filepath}: {e}")

        if len(papers) < 2:
            return jsonify(create_response(success=False, error="成功解析的论文不足2篇")), 400

        emit_progress(50, "正在进行主题聚类...")

        # 执行聚类
        clustering = TopicClustering(
            n_clusters=min(n_clusters, len(papers)),
            clustering_method=method,
            language=language
        )

        results = clustering.cluster_papers(papers, save_visualization=True, save_report=True)

        emit_progress(100, "聚类分析完成")

        return jsonify(create_response(
            success=True,
            message="聚类分析完成",
            data={
                "clusterCount": results['unique_clusters'],
                "clusterAnalysis": results['cluster_analysis']
            }
        ))

    except Exception as e:
        emit_progress(0, f"聚类失败: {str(e)}")
        return jsonify(create_response(success=False, error=f"聚类失败: {str(e)}")), 500


# ============================================================================
# 路由：下载结果
# ============================================================================

@app.route('/api/download/<result_type>/<filename>', methods=['GET'])
def download_result(result_type: str, filename: str):
    """下载分析结果"""
    try:
        if result_type == 'summary':
            directory = settings.summary_output_dir
        elif result_type == 'keypoints':
            directory = settings.keypoints_output_dir
        elif result_type == 'cluster':
            directory = settings.cluster_output_dir
        else:
            return jsonify(create_response(success=False, error="无效的结果类型")), 400

        filepath = directory / secure_filename(filename)

        if not filepath.exists():
            return jsonify(create_response(success=False, error="文件不存在")), 404

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        return jsonify(create_response(success=False, error=f"下载失败: {str(e)}")), 500


# ============================================================================
# WebSocket事件处理
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端已断开')


@socketio.on('ping')
def handle_ping():
    """心跳检测"""
    emit('pong', {'timestamp': datetime.now().isoformat()})


# ============================================================================
# 错误处理
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404错误"""
    return jsonify(create_response(success=False, error="接口不存在")), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误"""
    return jsonify(create_response(success=False, error=f"服务器内部错误: {str(error)}")), 500


# ============================================================================
# 主函数
# ============================================================================

def run_server():
    """运行Flask服务器"""
    print("=" * 60)
    print("科研文献摘要提取系统 - Web服务器")
    print("=" * 60)
    print(f"服务器地址: http://{settings.flask_host}:{settings.flask_port}")
    print(f"API文档: http://{settings.flask_host}:{settings.flask_port}/api/health")
    print(f"上传目录: {settings.upload_dir}")
    print(f"输出目录: {settings.output_dir}")
    print("=" * 60)

    # 启动服务器
    socketio.run(
        app,
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    run_server()
