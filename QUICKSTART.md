# 快速启动指南 - 科研文献摘要提取系统 v2.0

## 📋 前置要求检查

### 1. Python环境
```bash
python3 --version  # 需要 >= 3.8
```

### 2. Node.js环境（仅Web界面）
```bash
node --version  # 需要 >= 16
npm --version
```

### 3. GLM-4 API密钥
访问 https://open.bigmodel.cn/ 注册并获取API密钥

---

## 🚀 快速启动（5分钟）

### 步骤1: 安装后端依赖

```bash
# 进入项目目录
cd nuc_design

# 安装Python依赖
pip install -r requirements.txt
```

**如果遇到安装问题，使用：**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤2: 配置环境变量

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用其他编辑器
```

**必须配置的变量：**
```bash
GLM_API_KEY=你的GLM_API密钥
```

**可选配置：**
```bash
DEFAULT_MODEL=glm-4-flash  # 或 glm-4-air, glm-4-plus
DEFAULT_TEMPERATURE=0.3
FLASK_PORT=5000
```

### 步骤3: 验证安装

```bash
# 检查依赖
python check_dependencies.py

# 检查系统
python check_system.py
```

**两个脚本都应该显示全部通过 ✓**

### 步骤4: 启动服务

**选项A: Web模式（推荐）**
```bash
python app.py
```
然后访问：http://localhost:5000

**选项B: 命令行模式**
```bash
# 分析单篇论文
python main.py analyze /path/to/paper.pdf

# 只生成摘要
python main.py summarize /path/to/paper.pdf

# 只提取要点
python main.py extract /path/to/paper.pdf

# 主题聚类
python main.py cluster paper1.pdf paper2.pdf paper3.pdf
```

---

## 🌐 Web界面使用（可选）

### 安装前端依赖

```bash
cd frontend
npm install
```

### 启动前端开发服务器

```bash
npm run serve
```

访问：http://localhost:8080

### 构建前端（生产）

```bash
npm run build
```

构建后的文件会输出到 `../dist/`，Flask会自动服务这些文件。

---

## ❓ 常见问题

### 问题1: pip install 失败

**解决方案：**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者逐个安装核心依赖
pip install langchain langchain-openai
pip install flask flask-cors flask-socketio
pip install PyMuPDF pdfplumber
```

### 问题2: API调用失败

**检查：**
```bash
# 确认.env文件存在且包含API密钥
cat .env | grep GLM_API_KEY

# 确认API密钥格式（通常以数字开头）
```

**正确的格式：**
```bash
GLM_API_KEY=1234567890abcdef1234567890abcdef
```

### 问题3: 导入错误

```bash
# ModuleNotFoundError: No module named 'xxx'
pip install xxx

# 或
pip install -r requirements.txt --upgrade
```

### 问题4: 前端空白页

**检查：**
1. 后端是否启动：`python app.py`
2. 前端代理配置：`frontend/vue.config.js`
3. 浏览器控制台错误：F12

### 问题5: PDF解析失败

**原因：**
- PDF文件有密码保护
- PDF文件损坏
- PDF是扫描图像（无文本层）

**解决方案：**
使用有文本层的PDF，或先用OCR工具处理

---

## 🧪 测试系统

### 运行完整测试

```bash
# 1. 依赖检查
python check_dependencies.py

# 2. 系统检查
python check_system.py

# 3. 功能测试（需要准备测试PDF）
python tests.py
```

### 手动测试

**测试PDF解析：**
```bash
python main.py parse /path/to/test.pdf
```

**测试摘要生成：**
```bash
python main.py summarize /path/to/test.pdf
```

---

## 📊 性能优化建议

### 1. 使用更快的模型

```bash
# .env文件
DEFAULT_MODEL=glm-4-air  # 比glm-4-flash更快
```

### 2. 调整并发数

```python
# app.py中修改
# 增加并发处理能力
```

### 3. 使用GPU加速

如果使用本地模型，可以配置GPU加速

---

## 🔧 开发模式

### 启用调试模式

```bash
# .env文件
FLASK_DEBUG=True
```

### 查看日志

```bash
# 所有日志输出到控制台
python app.py 2>&1 | tee app.log
```

### 热重载

```bash
# 后端热重载
pip install flask-restart
flask run --reload

# 前端热重载（开发模式）
cd frontend
npm run serve  # 自动热重载
```

---

## 📚 下一步

1. **查看完整文档**：`README.md`
2. **查看示例代码**：`examples.py`
3. **自定义提示词**：编辑 `src/prompts.py`
4. **添加新功能**：参考 `README.md` 的开发指南

---

## 🆘 获取帮助

1. 运行诊断脚本：`python check_system.py`
2. 查看错误日志
3. 检查文档：`README.md`
4. 提交Issue：GitHub Issues

---

## ✅ 启动清单

- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装（pip install -r requirements.txt）
- [ ] .env文件已配置（包含GLM_API_KEY）
- [ ] 系统检查通过（python check_system.py）
- [ ] 后端服务启动（python app.py）
- [ ] 访问 http://localhost:5000

全部完成？🎉 开始使用吧！

---

**快速命令参考：**

```bash
# 安装
pip install -r requirements.txt

# 配置
cp .env.example .env
nano .env  # 填入API密钥

# 检查
python check_system.py

# 启动
python app.py

# 使用
python main.py analyze paper.pdf
```
