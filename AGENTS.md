# AGENTS.md - 院士级科研智能助手 v4.2

> 本文档面向AI编程助手，包含项目架构、开发规范和重要实现细节。
> 项目语言：中文（注释和文档主要使用中文）

---

## 项目概述

**院士级科研智能助手**是一个基于大语言模型的螺旋式知识积累与代码生成平台，实现从文献分析到代码智能生成的完整闭环。

### 核心功能
- 📄 智能PDF解析（支持中英文）
- 🧠 AI摘要生成与12类要点提取（创新点、方法、实验、结论等）
- 🤖 **Kimi 风格 AI 聊天** - 流式输出、RAG、文献综述生成
- 🔗 **LangChain 链式工作流** - SequentialChain 多步骤分析
- 📊 **Milvus 向量聚类** - 基于深度学习的语义聚类
- 🔍 研究空白挖掘（5种类型）
- 🌐 知识图谱可视化（D3.js力导向布局）
- 💻 智能代码生成（6种策略）
- 📈 批量论文并发处理（支持100篇）

### 版本信息
- **当前版本**: v4.2.0
- **状态**: 生产可用
- **最后更新**: 2026-02-20

---

## 技术栈

### 后端技术栈
| 技术 | 版本 | 用途 |
|-----|------|-----|
| Python | 3.8+ | 核心语言 |
| Flask | 3.0+ | Web框架 |
| SQLAlchemy | 2.0+ | ORM框架 |
| PostgreSQL | 14+ | 主数据库 |
| Milvus | 2.3+ | 向量数据库 |
| Redis | 5.0+ | 缓存层（可选） |
| Socket.IO | 5.3+ | WebSocket实时通信 |
| LangChain | 0.2+ | LLM编排与链式调用 |
| Sentence-Transformers | 2.2+ | 文本嵌入模型 |
| GLM-4 API | - | 智谱AI大语言模型 |

### 前端技术栈
| 技术 | 版本 | 用途 |
|-----|------|-----|
| Vue | 3.3+ | 前端框架 |
| Element Plus | 2.4+ | UI组件库 |
| D3.js | 7.9+ | 知识图谱可视化 |
| Monaco Editor | 0.45+ | 代码编辑器 |
| Axios | 1.6+ | HTTP客户端 |
| Socket.IO Client | 4.6+ | WebSocket客户端 |

---

## 项目结构

```
nuc_Graduation_project/
├── app.py                       # Flask后端API入口
├── main.py                      # CLI命令行工具入口
├── requirements.txt             # Python依赖清单
├── start.sh                     # 启动脚本
├── .env.example                 # 环境变量示例
├── .env                         # 实际环境变量（需创建）
│
├── src/                         # 后端源代码
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库模型定义（SQLAlchemy ORM）
│   ├── db_manager.py            # 数据库管理器（CRUD操作）
│   ├── async_workflow.py        # 异步工作流引擎
│   ├── chain_workflow.py        # LangChain 链式工作流引擎 (v4.2)
│   ├── chat_engine.py           # AI 聊天引擎 (v4.2)
│   ├── vector_store.py          # Milvus 向量存储管理器 (v4.2)
│   ├── code_generator.py        # 智能代码生成引擎
│   ├── pdf_parser_enhanced.py   # PDF解析器
│   ├── prompts_doctoral.py      # 博士级提示词模板
│   ├── cache_manager.py         # Redis缓存管理
│   ├── api_middleware.py        # API中间件（压缩、性能头）
│   ├── database_optimization.py # 数据库优化工具
│   ├── auth.py                  # JWT认证工具
│   └── ...                      # 其他模块
│
├── frontend/                    # Vue 3前端项目
│   ├── package.json             # npm依赖
│   ├── src/
│   │   ├── main.js              # 入口文件
│   │   ├── App.vue              # 根组件
│   │   ├── router/              # 路由配置
│   │   ├── store/               # Vuex状态管理
│   │   ├── api/                 # API封装
│   │   ├── components/          # 可复用组件
│   │   │   ├── KnowledgeGraph.vue    # 知识图谱组件
│   │   │   ├── CodeEditor.vue        # 代码编辑器组件
│   │   │   ├── UploadDialog.vue      # 上传对话框
│   │   │   └── ProgressDialog.vue    # 进度对话框
│   │   └── views/               # 页面视图
│   │       ├── Home.vue              # 首页
│   │       ├── Analyze.vue           # 单篇分析
│   │       ├── KimiChat.vue          # Kimi 风格 AI 聊天 (v4.2)
│   │       ├── ChainWorkflow.vue     # 链式工作流 (v4.2)
│   │       ├── Cluster.vue           # 聚类分析（含向量聚类）
│   │       ├── Files.vue             # 文件管理
│   │       ├── ResearchGaps.vue      # 研究空白
│   │       ├── KnowledgeGraph.vue    # 知识图谱
│   │       └── ...
│   └── node_modules/            # npm依赖目录
│
├── output/                      # 输出目录
│   ├── uploads/                 # 上传的PDF文件
│   ├── summaries/               # 生成的摘要
│   └── keypoints/               # 提取的要点
│
├── docs/                        # 文档
│   └── ARCHITECTURE_V4.md       # 架构设计文档
│
└── tests/                       # 测试文件
    ├── test_api.py              # API测试脚本
    └── test_upload.py           # 上传测试
```

---

## 环境配置

### 必需环境变量
创建 `.env` 文件（从 `.env.example` 复制）：

```bash
# 数据库配置（必需）
DATABASE_URL=postgresql://username:password@localhost:5432/literature_analysis

# GLM-4 API配置（必需）- 从 https://open.bigmodel.cn 获取
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# LLM模型配置
DEFAULT_MODEL=glm-4-flash       # 或 glm-4-plus
DEFAULT_TEMPERATURE=0.3
MAX_TOKENS=4000

# Flask配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True

# 输出目录
OUTPUT_DIR=./output

# 并发控制
MAX_CONCURRENT=5

# Redis缓存（可选）
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

---

## 构建与运行

### 后端启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python main.py init-db

# 3. 优化数据库（创建索引）
python main.py optimize-db

# 4. 启动后端服务
python app.py
# 或使用启动脚本
./start.sh
```

后端服务地址：http://localhost:5001

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run serve
```

前端地址：http://localhost:8080

### 命令行工具

```bash
# 分析单篇论文
python main.py analyze path/to/paper.pdf

# 批量分析
python main.py batch path/to/papers/ --limit 10

# 查看统计
python main.py stats

# 查看论文列表
python main.py list

# 生成代码
python main.py generate-code <gap_id>
```

---

## 数据库架构

### 核心表结构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   papers    │    │   authors   │    │  keywords   │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄──►│ id (PK)     │    │ id (PK)     │
│ title       │    │ name        │    │ keyword     │
│ abstract    │    │ affiliation │    │ category    │
│ pdf_hash    │    │ email       │    │ paper_count │
│ year        │    └─────────────┘    └─────────────┘
│ venue       │
│ meta_data   │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  analyses   │    │research_gaps│    │generated_code│
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄──►│ id (PK)     │◄──►│ id (PK)     │
│ paper_id    │    │ paper_id    │    │ gap_id      │
│ summary     │    │ description │    │ code        │
│ keypoints   │    │ gap_type    │    │ language    │
│ status      │    │ priority    │    │ framework   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 数据库关系说明

- **Paper** 与 **Author**：多对多（通过 paper_authors 关联表）
- **Paper** 与 **Keyword**：多对多（通过 paper_keywords 关联表）
- **Paper** 与 **Analysis**：一对多
- **Paper** 与 **ResearchGap**：一对多
- **ResearchGap** 与 **GeneratedCode**：一对多

### 重要约束

- `papers.pdf_hash`：唯一索引，用于PDF去重
- `authors.name`：唯一索引
- `keywords.keyword`：唯一索引

---

## API架构

### RESTful API 端点

```
基础路径: /api

# 健康检查
GET  /health                    # 服务健康状态
GET  /config                    # 获取系统配置

# 论文管理
GET  /papers                    # 获取论文列表（支持搜索、分页）
GET  /papers/<id>               # 获取论文详情
PUT  /papers/<id>               # 更新论文信息
DELETE /papers/<id>             # 删除论文
POST /papers/batch-delete       # 批量删除

# 文件上传
POST /upload                    # 上传PDF文件

# 分析功能
POST /analyze                   # 分析论文（单篇）
POST /batch-analyze             # 批量分析
POST /cluster                   # 主题聚类

# 代码生成
POST /gaps/<id>/generate-code   # 为研究空白生成代码
GET  /code/<id>                 # 获取生成的代码
POST /code/<id>/modify          # AI辅助修改代码
GET  /code/<id>/versions        # 查看代码版本历史

# 知识图谱
GET  /knowledge-graph           # 获取知识图谱数据
POST /knowledge-graph/build     # 构建知识图谱
POST /relations                 # 手动添加论文关系

# 统计查询
GET  /statistics                # 获取统计信息
GET  /gaps/priority             # 获取高优先级研究空白
GET  /gaps/<id>                 # 获取研究空白详情
```

### WebSocket 事件

```javascript
// 连接地址: ws://localhost:5001

// 进度更新事件
socket.on('progress', (data) => {
  data.progress   // 进度百分比 (0-100)
  data.message    // 进度消息
  data.step       // 当前步骤
  data.timestamp  // 时间戳
})
```

### 统一响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2026-01-15T10:30:00",
  "version": "4.1.0"
}
```

---

## 开发规范

### 代码风格

1. **注释语言**：主要使用中文注释
2. **命名规范**：
   - 类名：PascalCase（如 `AsyncWorkflowEngine`）
   - 函数/变量：snake_case（如 `get_papers`）
   - 常量：UPPER_CASE
3. **文件编码**：UTF-8

### 模块导入顺序

```python
# 1. 标准库
import os
import sys
from pathlib import Path

# 2. 第三方库
from flask import Flask
from sqlalchemy import create_engine

# 3. 项目内部模块
from src.config import settings
from src.db_manager import DatabaseManager
```

### 异步编程规范

```python
# 使用 asyncio 进行异步操作
import asyncio

class AsyncWorkflowEngine:
    async def execute(self):
        # 使用 semaphore 控制并发
        async with self.semaphore:
            result = await self._analyze()
        return result

# 在同步代码中调用异步函数
def sync_call():
    return asyncio.run(async_function())
```

---

## 核心模块说明

### 1. 异步工作流引擎 (async_workflow.py)

```python
# 工作流状态枚举
class WorkflowState(Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GRAPH_BUILDING = "graph_building"
    CODE_GENERATING = "code_generating"
    COMPLETED = "completed"
    FAILED = "failed"
```

**关键方法**：
- `execute_paper_workflow()` - 执行完整论文分析流程
- `batch_process_papers()` - 批量处理多篇论文

### 2. 数据库管理器 (db_manager.py)

使用上下文管理器管理会话：

```python
with self.get_session() as session:
    paper = session.query(Paper).filter(...).first()
    # 自动提交/回滚
```

### 3. 代码生成器 (code_generator.py)

支持6种生成策略：
- `method_improvement` - 方法改进
- `new_method` - 新方法提出
- `dataset_creation` - 数据集构建
- `experiment_design` - 实验设计
- `model_implementation` - 模型实现
- `algorithm_optimization` - 算法优化

### 4. PDF解析器 (pdf_parser_enhanced.py)

支持：
- 文本提取
- 表格识别
- 图片提取
- 元数据解析

---

## 测试策略

### API测试

```bash
# 运行API测试（需先启动后端）
python test_api.py
```

### 数据库检查

```bash
# 检查数据库状态和研究空白数据
python check_gaps.py
```

### 手动测试端点

```bash
# 健康检查
curl http://localhost:5001/api/health

# 获取论文列表
curl http://localhost:5001/api/papers
```

---

## 安全注意事项

### 已实现的安全措施

1. **文件上传安全**：
   - 文件类型验证（仅PDF）
   - 文件大小限制（100MB）
   - 文件名安全处理（`secure_filename`）

2. **数据库安全**：
   - 使用ORM防止SQL注入
   - 连接池管理

3. **认证安全**：
   - JWT token认证
   - 密码SHA256加密（带盐值）
   - Token有效期7天

4. **API安全**：
   - CORS配置
   - 输入验证

### 敏感信息处理

- API密钥存储在 `.env` 文件（已加入 `.gitignore`）
- 生产环境应使用环境变量而非硬编码
- JWT密钥应从环境变量读取

---

## 故障排查

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务
   pg_isready -h localhost -p 5432
   
   # 检查数据库是否存在
   psql -U username -d literature_analysis -c "\dt"
   ```

2. **WebSocket连接问题（macOS）**
   - 项目已配置使用 `threading` 模式而非 `eventlet`
   - 避免与asyncio event loop冲突

3. **LLM API调用失败**
   - 检查 `GLM_API_KEY` 是否配置
   - 验证API密钥有效性

4. **前端构建失败**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run serve
   ```

### 日志查看

```python
# Flask应用日志
# 在 app.py 中设置调试模式
FLASK_DEBUG=True

# SQLAlchemy SQL日志
# 在 db_manager.py 中设置 echo=True
self.engine = create_engine(..., echo=True)
```

---

## 性能优化

### 已实施的优化

1. **数据库优化**：
   - 30+ 索引
   - 连接池（pool_size=10, max_overflow=20）

2. **缓存层**：
   - Redis缓存（可选）
   - API响应缓存

3. **并发处理**：
   - 异步工作流
   - Semaphore控制并发数
   - 支持100篇论文批量处理

4. **响应优化**：
   - Gzip压缩
   - 分页查询

---

## 扩展开发指南

### 添加新的分析任务

1. 在 `async_workflow.py` 中添加任务处理逻辑
2. 在 `prompts_doctoral.py` 中添加提示词模板
3. 更新前端任务选择界面

### 添加新的代码生成策略

1. 在 `code_generator.py` 的 `CodeGenerationStrategy.STRATEGIES` 中添加策略定义
2. 实现对应的代码生成模板
3. 添加前端策略选择选项

### 数据库迁移

```python
# 使用Alembic进行数据库迁移
# 1. 创建迁移脚本
alembic revision --autogenerate -m "add new table"

# 2. 执行迁移
alembic upgrade head
```

---

## 外部依赖

### 必需服务

1. **PostgreSQL 14+**
   - 安装：https://www.postgresql.org/download/

2. **Redis**（可选，用于缓存）
   - 安装：https://redis.io/download

3. **GLM-4 API密钥**
   - 注册：https://open.bigmodel.cn/
   - 创建应用获取API Key

---

## 相关文档

- `README.md` - 项目概述和快速开始
- `docs/ARCHITECTURE_V4.md` - 详细架构设计
- `BUG_FIX_SUMMARY.md` - 已知问题和修复记录
- `FINAL_SUMMARY.md` - 项目总结

---

## 联系与支持

- **项目类型**: 毕业设计项目
- **开发语言**: 中文
- **许可证**: MIT License

---

*最后更新: 2026-02-04*
