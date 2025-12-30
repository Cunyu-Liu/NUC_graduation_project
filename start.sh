#!/bin/bash

echo "======================================"
echo "  科研文献摘要提取系统 v2.0"
echo "======================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，正在从.env.example创建..."
    cp .env.example .env
    echo "✓ 已创建.env文件"
    echo ""
    echo "⚠️  请编辑.env文件，填入你的GLM-4 API密钥！"
    echo "   获取地址: https://open.bigmodel.cn/"
    echo ""
    read -p "按Enter继续（确保已配置API密钥）..."
fi

# 检查依赖
echo "📦 检查Python依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Python依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

echo ""
echo "请选择启动模式："
echo "1) Web服务器模式 (推荐)"
echo "2) 命令行模式"
echo "3) 测试模式"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动Web服务器..."
        echo "   访问地址: http://localhost:5000"
        echo "   按Ctrl+C停止服务"
        echo ""
        python3 app.py
        ;;
    2)
        echo ""
        echo "📝 命令行模式"
        echo "用法示例:"
        echo "  python main.py analyze paper.pdf"
        echo "  python main.py summarize paper.pdf"
        echo "  python main.py extract paper.pdf"
        echo "  python main.py cluster paper1.pdf paper2.pdf"
        echo "  python main.py config"
        echo ""
        exec bash
        ;;
    3)
        echo ""
        echo "🧪 运行测试..."
        python3 tests.py
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
