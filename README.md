# 院士级科研智能助手 v4.1

<div align="center">

**基于大语言模型的螺旋式知识积累与代码生成平台**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.3%2B-brightgreen)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-red)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

**版本**: v4.1.0 | **状态**: 生产可用

</div>

---

## 🎯 项目简介

这是一个**院士级科研智能助手平台**，实现了从文献分析到代码智能生成的完整闭环，采用螺旋式知识积累架构，每次分析都沉淀为永久知识，支持100篇论文并发处理，性能提升30-1800倍。

### 核心特性

- 🔄 **螺旋式知识积累** - 从文献分析到代码验证的完整闭环
- 🚀 **高性能异步引擎** - 100篇论文并发，分析速度提升6倍
- 🤖 **Kimi 风格 AI 聊天** - 流式输出、Markdown渲染、LaTeX公式、论文引用
- 🔗 **LangChain 链式工作流** - SequentialChain 多步骤分析流程
- 📊 **Milvus 向量聚类** - 基于深度学习的语义论文聚类
- 🧠 **智能代码生成** - 6种策略自动生成可执行研究代码
- 🌐 **知识图谱可视化** - D3.js交互式图谱，自动发现论文关联
- 💾 **PostgreSQL持久化** - 完整的数据库ORM，支持复杂查询
- ⚡ **性能优化** - Redis缓存 + 30+索引 + Gzip压缩，查询加速50倍
- 🔒 **安全加固** - 文件上传验证、路径遍历防护、输入验证

---

## ✨ 主要功能

### 1. 文献分析
- 📄 智能PDF解析（支持中英文）
- ✍️ AI摘要生成（博士级提示词）
- 🎯 12类要点提取（创新点、方法、实验、结论等）
- 🔍 研究空白挖掘（5种类型）

### 2. 知识图谱
- 自动构建论文关系网络（5种关系类型）
- D3.js力导向布局可视化
- 节点交互、关系筛选、缩放拖拽

### 3. 代码生成
- 6种生成策略（方法改进、新方法、数据集创建等）
- Monaco Editor代码编辑器
- 版本历史管理
- AI辅助修改

### 4. AI 科研助手 (Kimi 风格)
- 流式输出，实时响应
- Markdown + 代码高亮 + LaTeX公式渲染
- 论文库智能问答 (RAG)
- 文献综述一键生成
- 多轮对话上下文记忆

### 5. 链式工作流 (LangChain)
- SequentialChain 多步骤分析
- 预设模板（论文分析、文献综述、代码生成）
- 自定义节点配置
- 可视化工作流编辑器

### 6. 向量聚类 (Milvus)
- Docker 部署 Milvus 向量数据库
- BGE-large 模型生成语义嵌入
- 基于语义相似度的论文聚类
- 相似论文智能推荐

### 7. 研究空白管理
- 智能识别研究空白
- 优先级排序（重要性+难度）
- 一键生成代码
- 导出分析报告

---

## 🏗️ 技术架构

### 后端
- **Python 3.8+** - 核心语言
- **Flask 3.0** - Web框架
- **PostgreSQL** - 主数据库
- **Milvus** - 向量数据库 (Docker 部署)
- **SQLAlchemy 2.0** - ORM框架
- **LangChain** - LLM 链式调用框架
- **Redis** - 缓存层（可选）
- **Socket.IO** - WebSocket实时通信
- **GLM-4 API** - 智谱AI大语言模型
- **Sentence-Transformers** - 文本嵌入模型 (BGE-large)

### 前端
- **Vue 3** - 前端框架
- **Element Plus** - UI组件库
- **D3.js** - 知识图谱可视化
- **Monaco Editor** - 代码编辑器
- **Axios** - HTTP客户端
- **Socket.IO** - WebSocket客户端

---

## 📦 快速开始

### 环境要求

```bash
Python 3.8+
Node.js 16+
PostgreSQL 14+
Docker & Docker Compose (用于 Milvus)
Redis (可选)
```

### 1. 克隆项目

```bash
git clone <repository-url>
cd nuc_Graduation_project
```

### 2. 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，填入必需的配置项
# 必需配置：
# DATABASE_URL - PostgreSQL数据库连接字符串
# GLM_API_KEY - 智谱AI API密钥（从 https://open.bigmodel.cn 获取）

# 可选配置：
# REDIS_HOST, REDIS_PORT - Redis缓存配置
# MAX_CONCURRENT - 最大并发数（默认5）
```

### 4. 部署 Milvus 向量数据库 (Docker)

```bash
# 创建 Milvus 目录
mkdir -p milvus && cd milvus

# 下载 Milvus 独立版配置文件
wget https://github.com/milvus-io/milvus/releases/download/v2.3.3/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动 Milvus
sudo docker-compose up -d

# 检查 Milvus 状态
sudo docker-compose ps

# 返回项目目录
cd ..
```

Milvus 默认会监听 `localhost:19530`。

### 5. 初始化数据库

```bash
python main.py init-db
```

### 5. 优化数据库

```bash
python main.py optimize-db
```

### 6. 启动服务
pkill -f "python app.py"

```bash
# 启动后端（终端1）
python app.py

conda activate nuc

# 启动前端（终端2）
cd frontend
npm run serve
```

### 7. 访问应用

- 前端界面: http://localhost:8080
- 后端API: http://localhost:5001/api
- 健康检查: http://localhost:5001/api/health

---

## 📡 API接口文档

### 基础接口
- `GET /api/health` - 健康检查
- `GET /api/config` - 获取系统配置

### 论文管理
- `GET /api/papers` - 获取论文列表（支持搜索、过滤、分页）
- `GET /api/papers/<id>` - 获取论文详情
- `PUT /api/papers/<id>` - 更新论文信息
- `DELETE /api/papers/<id>` - 删除论文
- `POST /api/papers/batch-delete` - 批量删除论文

### 文件上传
- `POST /api/upload` - 上传PDF文件并自动解析入库

### 分析功能
- `POST /api/analyze` - 分析论文（支持摘要、要点、研究空白挖掘）
- `POST /api/batch-analyze` - 批量分析论文
- `POST /api/cluster` - 主题聚类分析

### 代码生成
- `POST /api/gaps/<id>/generate-code` - 为研究空白生成代码
- `GET /api/code/<id>` - 获取生成的代码
- `POST /api/code/<id>/modify` - AI辅助修改代码
- `GET /api/code/<id>/versions` - 查看代码版本历史

### 知识图谱
- `GET /api/knowledge-graph` - 获取知识图谱数据
- `POST /api/knowledge-graph/build` - 构建知识图谱
- `POST /api/relations` - 手动添加论文关系

### 统计查询
- `GET /api/statistics` - 获取统计信息
- `GET /api/gaps/priority` - 获取高优先级研究空白
- `GET /api/gaps/<id>` - 获取研究空白详情

### WebSocket
- WebSocket连接用于实时进度更新
- 事件类型：`progress` - 进度更新事件

---

## 📚 使用指南

### Web界面使用

1. **上传论文** - 支持单个或批量上传PDF
2. **分析论文** - 选择分析任务（摘要、要点、空白等）
3. **查看知识图谱** - 可视化论文关系网络
4. **生成代码** - 基于研究空白一键生成代码
5. **管理研究空白** - 查看、筛选、导出分析结果

### CLI命令行使用

```bash
# 分析单篇论文
python main.py analyze path/to/paper.pdf

# 批量处理
python main.py batch path/to/papers/

# 查看论文列表
python main.py list

# 查看统计信息
python main.py stats
```

---

## 📊 性能指标

| 功能 | v3.0 | v4.1 | 提升 |
|------|------|------|------|
| 并发能力 | 1篇 | 100篇 | **100x** |
| 分析速度 | 60秒/篇 | 10秒/篇 | **6x** |
| 查询速度 | 500ms | 50ms | **10x** |
| 响应大小 | 100KB | 25KB | **4x减少** |
| 统计查询 | 200ms | 4ms | **50x** |

---

## 🔧 配置说明

### 数据库配置

```python
# src/config.py
DATABASE_URL = "postgresql://user:password@localhost/literature_analysis"
```

### LLM配置

```python
# 环境变量
GLM_API_KEY = "your_api_key"
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
LLM_MODEL = "glm-4-plus"
```

### 缓存配置

```python
# 环境变量（可选）
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
```

---

## 📂 项目结构

```
nuc_Graduation_project/
├── app.py                       # 后端API入口
├── main.py                      # CLI工具入口
├── requirements.txt             # Python依赖
├── src/
│   ├── database.py              # 数据库模型
│   ├── db_manager.py            # 数据库管理器
│   ├── async_workflow.py        # 异步工作流引擎
│   ├── code_generator.py        # 代码生成引擎
│   ├── cache_manager.py         # Redis缓存管理
│   ├── database_optimization.py # 数据库优化
│   ├── api_middleware.py        # API中间件
│   ├── pdf_parser_enhanced.py   # PDF解析器
│   ├── prompts_doctoral.py      # 博士级提示词
│   └── config.py                # 配置管理
├── frontend/
│   ├── src/
│   │   ├── components/          # Vue组件
│   │   │   ├── KnowledgeGraph.vue    # 知识图谱
│   │   │   └── CodeEditor.vue        # 代码编辑器
│   │   ├── views/               # 页面视图
│   │   │   └── ResearchGaps.vue      # 研究空白管理
│   │   ├── router/              # 路由配置
│   │   ├── api/                 # API封装
│   │   └── App.vue              # 根组件
│   └── package.json             # 前端依赖
├── README.md                    # 本文档
├── QUICKSTART.md                # 快速开始指南
└── PERFORMANCE_OPTIMIZATION.md  # 性能优化详情
```

---

## 🎯 核心优势

### 1. 螺旋式知识积累
```
论文上传 → 深度解析 → 知识提取 → 关联分析 →
空白挖掘 → 代码生成 → 实验验证 → 新论文 → ...
  ↑_______________________________________________|
            形成知识积累闭环
```

### 2. 完整的科研闭环
从文献分析到代码实现的完整流程，真正实现"AI科研助手"

### 3. 高性能设计
- 异步并发：100篇论文同时处理
- 数据库优化：30+索引，查询加速10-100倍
- 智能缓存：Redis缓存，命中率>80%
- 响应压缩：Gzip压缩，减少60-80%传输量

### 4. 现代化架构
- 前后端分离
- RESTful API
- WebSocket实时通信
- PostgreSQL持久化
- 容器化部署就绪

---

## 🔒 安全特性

- ✅ 文件上传大小验证
- ✅ 文件类型检查
- ✅ 路径遍历防护
- ✅ SQL注入防护（ORM）
- ✅ XSS防护（前端转义）
- ✅ CORS配置
- ✅ 输入验证

---

## 🚀 部署

### Docker部署（推荐）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 手动部署

详见 [QUICKSTART.md](QUICKSTART.md)

---

## 📖 文档

- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - 性能优化详情

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- 智谱AI GLM-4 API
- LangChain社区
- Vue.js社区
- D3.js社区

---

## 🔧 版本更新日志

### v4.1.3 (2026-01-15) - 紧急修复

**🚨 关键修复**:
- ✅ 修复ORM关系映射错误（ResearchGap-GeneratedCode外键冲突）
- ✅ 明确指定foreign_keys参数解决循环引用
- ✅ 创建数据库修复工具 `fix_database.py`

**新增文档**:
- `ORM_FIX.md` - ORM错误完整修复指南

**重要**: 需要重新创建数据库才能生效！详见 `ORM_FIX.md`

### v4.1.2 (2026-01-15)

**紧急修复**:
- ✅ 修复研究空白加载失败问题
- ✅ API现在返回所有研究空白，而不仅仅是高优先级的
- ✅ 添加数据库诊断工具 `check_gaps.py`
- ✅ 改进空数据处理和错误提示

**新增工具**:
- `check_gaps.py` - 数据库检查和测试数据生成工具
- `test_api.py` - API自动化测试脚本
- `GAP_LOADING_FIX.md` - 研究空白问题修复指南

### v4.1.1 (2026-01-15)

**修复内容**:
- ✅ 创建requirements.txt，完整列出所有Python依赖
- ✅ 创建.env.example环境变量配置示例
- ✅ 修复前后端API接口不匹配问题
- ✅ 更新论文管理页面，适配数据库驱动架构
- ✅ 更新分析页面，支持基于论文ID的分析
- ✅ 添加主题聚类API接口
- ✅ 修复WebSocket连接配置

**改进**:
- 前端完全迁移到数据库驱动架构
- 所有API接口统一使用RESTful风格
- 优化错误处理和用户提示

---

**当前版本**: v4.1.3
**最后更新**: 2026-01-15
**状态**: 🚨 需要重新创建数据库
