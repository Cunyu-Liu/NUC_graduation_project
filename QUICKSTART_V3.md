# 博士级文献分析系统 v3.0 - 快速开始指南

## 🚀 5分钟快速上手

### 步骤1: 环境准备

#### 1.1 安装依赖
```bash
# 克隆或进入项目目录
cd nuc_Graduation_project

# 安装Python依赖
pip install -r requirements.txt
```

#### 1.2 配置API密钥
```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件,添加你的GLM-4 API密钥
# GLM_API_KEY=your_api_key_here
```

**获取API密钥**：访问 [智谱AI开放平台](https://open.bigmodel.cn/) 注册并获取API密钥

---

## 📖 三种使用方式

### 方式1: Python代码调用（推荐）

#### 单篇论文深度分析
```python
from src.doctoral_analyzer import DoctoralAnalyzer

# 初始化分析器
analyzer = DoctoralAnalyzer(
    model="glm-4-plus"  # 最佳质量,也可用glm-4-air(性价比)
)

# 分析单篇论文
result = analyzer.analyze_single_paper(
    pdf_path="papers/your_paper.pdf",
    tasks=["summary", "keypoints", "topic"],  # 启用所有任务
    save=True
)

# 查看结果
print(f"标题: {result['parsing']['title']}")
print(f"摘要:\n{result['summary']['summary_text']}")
print(f"创新点数量: {len(result['keypoints']['innovations'])}")
print(f"研究空白数量: {len(result['keypoints']['research_gaps'])}")
```

#### 多篇论文综合分析
```python
from src.doctoral_analyzer import DoctoralAnalyzer

analyzer = DoctoralAnalyzer(model="glm-4-plus")

# 分析多篇论文(自动主题聚类 + 研究空白挖掘)
result = analyzer.analyze_multiple_papers(
    pdf_paths=[
        "papers/paper1.pdf",
        "papers/paper2.pdf",
        "papers/paper3.pdf"
    ],
    enable_clustering=True,   # 启用主题聚类
    enable_gap_mining=True,   # 启用研究空白挖掘
    save=True
)

# 查看聚类结果
print(f"识别主题数: {result['clustering']['unique_clusters']}")

# 查看研究空白
print(f"发现研究空白: {result['research_gaps']['summary']['total_gaps_identified']}个")
print(f"优先级空白:")
for gap in result['research_gaps']['priority_gaps'][:3]:
    print(f"  - {gap['description']}")
    print(f"    重要性: {gap['importance']} | 难度: {gap['difficulty']}")
```

#### 论文对比分析
```python
from src.doctoral_analyzer import DoctoralAnalyzer

analyzer = DoctoralAnalyzer()

# 对比2-5篇论文
comparison = analyzer.compare_papers(
    pdf_paths=[
        "papers/method_a.pdf",
        "papers/method_b.pdf",
        "papers/method_c.pdf"
    ],
    save=True
)

# 查看对比结果
print(comparison['comparison_table'])
```

---

### 方式2: 命令行使用

#### 分析单篇论文
```bash
# 基础分析
python -c "
from src.doctoral_analyzer import analyze_paper
result = analyze_paper('papers/your_paper.pdf')
print(result['summary']['summary_text'])
"

# 或者创建简单的脚本
cat > analyze.py << 'EOF'
from src.doctoral_analyzer import analyze_paper
import sys

result = analyze_paper(sys.argv[1])
print("=== 分析结果 ===")
print(f"标题: {result['parsing']['title']}")
print(f"\n摘要:\n{result['summary']['summary_text']}")
print(f"\n创新点: {len(result['keypoints']['innovations'])}个")
print(f"研究空白: {len(result['keypoints']['research_gaps'])}个")
EOF

python analyze.py papers/your_paper.pdf
```

#### 批量分析
```python
# batch_analyze.py
from src.doctoral_analyzer import DoctoralAnalyzer
import glob

analyzer = DoctoralAnalyzer(model="glm-4-air")  # 使用性价比模型

pdf_files = glob.glob("papers/*.pdf")
print(f"发现 {len(pdf_files)} 篇论文")

result = analyzer.analyze_multiple_papers(
    pdf_paths=pdf_files,
    enable_clustering=True,
    enable_gap_mining=True
)

print(f"\n分析完成!")
print(f"识别主题: {result['clustering']['unique_clusters']}个")
print(f"研究空白: {result['research_gaps']['summary']['total_gaps_identified']}个")
```

运行:
```bash
python batch_analyze.py
```

---

### 方式3: Web界面使用

#### 启动后端
```bash
# 确保已配置.env文件
python app.py
```

后端将运行在 `http://localhost:5000`

#### 启动前端（新终端）
```bash
cd frontend
npm install  # 首次运行需要安装依赖
npm run serve
```

前端将运行在 `http://localhost:8080`

#### 使用界面
1. 访问 `http://localhost:8080`
2. 点击"单篇分析"上传PDF
3. 选择要执行的任务：
   - ✅ 生成博士级摘要
   - ✅ 深度要点提取（12类）
   - ✅ 主题分析
4. 点击"开始分析"
5. 实时查看进度
6. 查看结果并下载

---

## 📊 输出结果说明

### 单篇分析输出
保存位置: `output/summaries/[filename]_doctoral_analysis.json`

```json
{
  "filename": "example.pdf",
  "analysis_time": "2025-01-15T10:30:00",
  "parsing": {
    "title": "论文标题",
    "authors": ["作者1", "作者2"],
    "page_count": 10,
    "language": "en",
    "sections_count": 7,
    "references_count": 35
  },
  "summary": {
    "summary_text": "博士级摘要内容...",
    "word_count": 600
  },
  "keypoints": {
    "innovations": ["创新点1", "创新点2", ...],
    "research_gaps": ["空白1", "空白2", ...],
    "theoretical_framework": ["理论1", "理论2", ...],
    "methods": ["方法1", "方法2", ...],
    "experimental_design": ["实验1", "实验2", ...],
    "datasets": ["数据集1", "数据集2", ...],
    "conclusions": ["结论1", "结论2", ...],
    "statistical_analysis": ["统计1", "统计2", ...],
    "related_work_comparison": ["对比1", "对比2", ...],
    "reproducibility": ["可复现性1", ...],
    "contributions": ["贡献1", "贡献2", ...],
    "limitations": ["局限性1", "局限性2", ...]
  },
  "topic_analysis": {
    "analysis_text": "主题分析..."
  }
}
```

### 多篇分析输出
保存位置: `output/clusters/multi_paper_analysis_[timestamp].json`

包含:
- 各篇论文的单独分析
- 主题聚类结果
- 研究空白报告
- 趋势分析

---

## 💡 使用技巧

### 1. 模型选择
| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 重要论文精读 | `glm-4-plus` | 最佳质量 |
| 批量筛选 | `glm-4-air` | 性价比高 |
| 快速预览 | `glm-4-flash` | 速度快 |

### 2. 任务选择
```python
# 快速了解论文
tasks=["summary"]

# 深度理解
tasks=["summary", "keypoints"]

# 完整分析
tasks=["summary", "keypoints", "topic"]
```

### 3. 批量处理建议
```python
# 方案A: 串行处理(稳定)
for pdf in pdf_files:
    result = analyzer.analyze_single_paper(pdf)
    time.sleep(1)  # 避免API限流

# 方案B: 并行处理(快速)
result = analyzer.analyze_multiple_papers(
    pdf_files,
    enable_clustering=True
)  # 内部自动并行
```

### 4. 成本优化
- 使用 `glm-4-air` 进行初筛
- 仅对重要论文使用 `glm-4-plus`
- 启用缓存避免重复分析

---

## 🎯 典型使用场景

### 场景1: 文献综述
```python
# 分析一个领域的10篇论文
papers = glob.glob("survey_papers/*.pdf")

result = analyzer.analyze_multiple_papers(
    papers,
    enable_clustering=True,
    enable_gap_mining=True
)

# 查看主要研究方向
print("识别的研究主题:")
for cluster in result['clustering']['cluster_analysis'].values():
    print(f"  - {cluster['top_keywords'][:3]}")

# 查看研究空白
print("\n潜在研究方向:")
for gap in result['research_gaps']['priority_gaps']:
    print(f"  - {gap['description']}")
```

### 场景2: 论文写作辅助
```python
# 分析相关工作
result = analyzer.analyze_single_paper(
    "related_work.pdf",
    tasks=["keypoints"]
)

# 提取需要的信息
print(f"创新点: {result['keypoints']['innovations']}")
print(f"方法对比: {result['keypoints']['related_work_comparison']}")
print(f"局限性: {result['keypoints']['limitations']}")
```

### 场景3: 方法对比
```python
# 对比3种方法
comparison = analyzer.compare_papers([
    "method_a.pdf",
    "method_b.pdf",
    "method_c.pdf"
])

print(comparison['comparison_table'])
```

---

## ⚠️ 常见问题

### Q1: API调用失败
**A**: 检查:
1. `.env`文件中的API密钥是否正确
2. 网络连接是否正常
3. API余额是否充足

### Q2: PDF解析失败
**A**:
1. 确认PDF文件没有损坏
2. 尝试用其他PDF阅读器打开
3. 某些扫描版PDF可能无法解析

### Q3: 分析速度慢
**A**:
1. 使用 `glm-4-air` 替代 `glm-4-plus`
2. 减少 `tasks` 数量
3. 使用批量分析的并行功能

### Q4: 内存不足
**A**:
1. 减少批量分析的文件数量
2. 处理完一批后保存结果再处理下一批
3. 增加系统内存

---

## 📚 下一步

- 📖 阅读完整文档: `README.md`
- 🔍 查看升级详情: `UPGRADE_DOCTORAL.md`
- 💻 查看示例代码: `examples/` 目录
- 🎓 学习最佳实践: `docs/BEST_PRACTICES.md`

---

**祝您科研顺利！** 🎓📄✨

---

**版本**: v3.0 Doctoral Edition
**更新日期**: 2025年
