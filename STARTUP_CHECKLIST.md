#!/bin/bash
# 完整启动检查脚本

echo "========================================"
echo "  科研文献摘要提取系统 v2.0"
echo "  启动前完整检查"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_passed=0
check_failed=0

# 检查函数
check_item() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((check_passed++))
    else
        echo -e "${RED}✗${NC} $2"
        ((check_failed++))
    fi
}

# 1. Python版本检查
echo "1. Python版本检查"
python3 --version >/dev/null 2>&1
check_item $? "Python 3 已安装"

python3 --version | grep -E "Python 3\.[8-9]|Python 3\.1[0-9]" >/dev/null 2>&1
check_item $? "Python 版本 >= 3.8"

# 2. 依赖安装检查
echo ""
echo "2. Python依赖检查"

packages=("langchain" "flask" "click" "rich" "dotenv")
for pkg in "${packages[@]}"; do
    python3 -c "import $pkg" >/dev/null 2>&1
    check_item $? "$pkg 已安装"
done

# 3. 配置文件检查
echo ""
echo "3. 配置文件检查"

if [ -f .env ]; then
    check_item 0 ".env 文件存在"

    if grep -q "GLM_API_KEY=" .env && ! grep -q "GLM_API_KEY=your_" .env; then
        check_item 0 "GLM_API_KEY 已配置"
    else
        check_item 1 "GLM_API_KEY 未配置"
    fi
else
    check_item 1 ".env 文件不存在（请从.env.example复制）"
fi

# 4. 输出目录检查
echo ""
echo "4. 输出目录检查"

dirs=("output" "output/summaries" "output/keypoints" "output/clusters" "output/uploads")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_item 0 "$dir 目录存在"
    else
        check_item 1 "$dir 目录不存在"
    fi
done

# 5. 模块导入检查
echo ""
echo "5. 核心模块导入检查"

modules=("src.config" "src.pdf_parser" "src.prompts" "src.workflow")
for mod in "${modules[@]}"; do
    python3 -c "import $mod" >/dev/null 2>&1
    check_item $? "$mod 导入成功"
done

# 6. 可选组件检查
echo ""
echo "6. 可选组件检查"

python3 -c "import langgraph" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    check_item 0 "LangGraph 已安装（完整功能）"
else
    echo -e "${YELLOW}⚠${NC} LangGraph 未安装（将使用简化工作流）"
fi

# 7. 网络连接检查
echo ""
echo "7. 网络连接检查"

curl -s --connect-timeout 3 https://open.bigmodel.cn >/dev/null 2>&1
if [ $? -eq 0 ]; then
    check_item 0 "可以访问 GLM-4 API"
else
    echo -e "${YELLOW}⚠${NC} 无法访问 GLM-4 API（检查网络）"
fi

# 总结
echo ""
echo "========================================"
echo "检查总结"
echo "========================================"
echo -e "${GREEN}通过: $check_passed${NC}"
echo -e "${RED}失败: $check_failed${NC}"
echo ""

if [ $check_failed -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！可以启动系统${NC}"
    echo ""
    echo "启动命令："
    echo "  Web模式: python3 app.py"
    echo "  CLI模式: python3 main.py analyze paper.pdf"
    echo ""
    exit 0
else
    echo -e "${RED}✗ 有 $check_failed 项检查失败${NC}"
    echo ""
    echo "修复建议："
    echo "1. 安装依赖: pip3 install -r requirements.txt"
    echo "2. 配置API: cp .env.example .env && nano .env"
    echo "3. 运行检查: python3 check_system.py"
    echo ""
    exit 1
fi
