@echo off
chcp 65001 >nul
echo ======================================
echo   科研文献摘要提取系统 v2.0
echo ======================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查.env文件
if not exist .env (
    echo ⚠️  未找到.env文件，正在从.env.example创建...
    copy .env.example .env >nul
    echo ✓ 已创建.env文件
    echo.
    echo ⚠️  请编辑.env文件，填入你的GLM-4 API密钥！
    echo    获取地址: https://open.bigmodel.cn/
    echo.
    pause
)

REM 检查依赖
echo 📦 检查Python依赖...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python依赖未安装，正在安装...
    pip install -r requirements.txt
)

echo.
echo 请选择启动模式：
echo 1) Web服务器模式 (推荐)
echo 2) 命令行模式
echo 3) 测试模式
set /p choice="请输入选项 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动Web服务器...
    echo    访问地址: http://localhost:5000
    echo    按Ctrl+C停止服务
    echo.
    python app.py
) else if "%choice%"=="2" (
    echo.
    echo 📝 命令行模式
    echo 用法示例:
    echo   python main.py analyze paper.pdf
    echo   python main.py summarize paper.pdf
    echo   python main.py extract paper.pdf
    echo   python main.py cluster paper1.pdf paper2.pdf
    echo   python main.py config
    echo.
    cmd /k
) else if "%choice%"=="3" (
    echo.
    echo 🧪 运行测试...
    python tests.py
    pause
) else (
    echo ❌ 无效选项
    pause
    exit /b 1
)
