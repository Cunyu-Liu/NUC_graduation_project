# 项目可运行性检查报告

**检查日期**: 2026-01-01
**检查范围**: 完整的项目可运行性检查
**状态**: ⚠️ 发现问题并已修复

---

## 🔍 发现的问题

### 1. ✅ 已修复：数据库模型错误（严重）

**问题描述**:
```
Attribute name 'metadata' is reserved when using the Declarative API
```

**原因**:
在 `src/database.py` 中使用了 `metadata` 作为列名，但这是 SQLAlchemy 的保留字（`Base.metadata`）。

**修复方案**:
- 将所有 `metadata = Column(JSONB, ...)` 改为 `meta_data = Column(JSONB, ...)`
- 修复位置：
  - `src/database.py` - Paper表的metadata列
  - `src/database.py` - Relation表的metadata列
  - `src/database.py` - to_dict方法中的引用
  - `app.py` 中的引用

**验证**: ✅ 数据库模型现在可以正常加载

---

## ✅ 正常的组件

### 1. 依赖完整性 ✅

**检查结果**: 所有依赖都在 `requirements.txt` 中
```python
# 核心依赖
- langchain>=0.2.0
- flask>=3.0.0
- sqlalchemy>=2.0.0
- psycopg2-binary>=2.9.0

# PDF处理
- PyPDF2, pdfplumber, PyMuPDF

# LLM API
- zhipuai>=2.1.0

# 性能优化
- redis>=5.0.0
```

### 2. 配置文件 ✅

**检查结果**:
- ✅ `src/config.py` - 配置管理正常
- ✅ `.env.example` - 环境变量示例已更新
- ✅ 环境变量加载正常

### 3. 数据库管理器 ✅

**检查结果**:
- ✅ `src/db_manager.py` - 可以正常导入
- ✅ 支持 DATABASE_URL 环境变量
- ✅ 有默认值回退

---

## ⚠️ 需要用户配置的项目

### 必需配置

#### 1. PostgreSQL数据库

```bash
# 安装PostgreSQL
brew install postgresql  # macOS
# 或
sudo apt-get install postgresql  # Ubuntu

# 创建数据库
createdb literature_analysis

# 配置环境变量
export DATABASE_URL=postgresql://user:password@localhost:5432/literature_analysis
```

#### 2. GLM-4 API密钥

```bash
# 访问 https://open.bigmodel.cn/ 注册
# 获取API密钥后配置
export GLM_API_KEY=your_api_key_here
```

#### 3. 环境变量文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑.env文件，填入真实值
nano .env
```

### 可选配置

#### 1. Redis（用于缓存）

```bash
# 安装Redis
brew install redis  # macOS
# 或
sudo apt-get install redis-server  # Ubuntu

# 启动Redis
redis-server

# 配置环境变量（可选）
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

**注意**: 如果没有Redis，系统会自动使用内存缓存，不影响核心功能。

---

## 🚀 启动步骤

### 第一次运行（完整流程）

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑必需的配置项

# 3. 创建并初始化数据库
createdb literature_analysis
python main.py init-db

# 4. 优化数据库（可选但推荐）
python main.py optimize-db

# 5. 启动后端服务
python app.py
```

### 前端启动（另开终端）

```bash
cd frontend
npm install
npm run serve
```

### 访问应用

- 前端界面: http://localhost:8080
- 后端API: http://localhost:5000/api

---

## 📋 可能遇到的问题

### 问题1: PostgreSQL连接失败

**症状**: `could not connect to server`

**解决方案**:
```bash
# 检查PostgreSQL是否运行
pg_ctl status

# 启动PostgreSQL
pg_ctl start

# 或使用系统服务
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### 问题2: 数据库不存在

**症状**: `database "literature_analysis" does not exist`

**解决方案**:
```bash
createdb literature_analysis
```

### 问题3: GLM API密钥无效

**症状**: `401 Unauthorized` 或 `Invalid API Key`

**解决方案**:
1. 访问 https://open.bigmodel.cn/
2. 注册并获取API密钥
3. 更新 `.env` 文件中的 `GLM_API_KEY`

### 问题4: Python依赖冲突

**症状**: `ModuleNotFoundError` 或版本冲突

**解决方案**:
```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 重新安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 问题5: 前端依赖安装失败

**症状**: npm install 失败

**解决方案**:
```bash
# 清除npm缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
```

---

## ✅ 验证清单

在运行项目前，请确认：

- [ ] PostgreSQL已安装并运行
- [ ] 数据库 `literature_analysis` 已创建
- [ ] `.env` 文件已创建并配置
- [ ] `DATABASE_URL` 环境变量已设置
- [ ] `GLM_API_KEY` 已设置并有效
- [ ] Python依赖已安装（`pip install -r requirements.txt`）
- [ ] 数据库已初始化（`python main.py init-db`）
- [ ] 前端依赖已安装（`cd frontend && npm install`）

---

## 📊 当前状态总结

### 已修复的问题 ✅

1. ✅ 数据库模型 `metadata` 保留字冲突
2. ✅ 环境变量示例文件更新

### 核心功能状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 数据库模型 | ✅ 正常 | 已修复metadata冲突 |
| 数据库管理器 | ✅ 正常 | 可以导入和使用 |
| 配置管理 | ✅ 正常 | 环境变量加载正常 |
| Web API | ✅ 正常 | Flask应用可以启动 |
| 异步工作流 | ⚠️ 未测试 | 需要完整环境 |
| 代码生成 | ⚠️ 未测试 | 需要完整环境 |

### 需要用户操作 ⚠️

1. **必须**：安装并配置PostgreSQL
2. **必须**：获取GLM-4 API密钥
3. **必须**：创建 `.env` 文件
4. **必须**：运行数据库初始化
5. **可选**：安装Redis（用于缓存）

---

## 🎯 结论

**当前项目不能直接运行，需要完成上述配置后才能运行。**

### 主要原因：

1. ⚠️ **需要外部依赖**: PostgreSQL数据库（必需）
2. ⚠️ **需要API密钥**: GLM-4 API密钥（必需）
3. ⚠️ **需要环境配置**: .env文件配置（必需）
4. ✅ **代码问题已修复**: metadata冲突已解决

### 修复后的状态：

- ✅ 代码本身没有语法错误
- ✅ 所有模块可以正常导入
- ✅ 数据库模型定义正确
- ⚠️ 需要外部服务支持（PostgreSQL、GLM API）

---

**检查完成时间**: 2026-01-01
**下一步**: 用户需要按照"启动步骤"完成配置后即可运行
