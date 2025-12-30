#!/usr/bin/env python3
"""
依赖检查脚本 - 验证所有必需的包是否已安装
"""
import sys
import importlib
from typing import List, Tuple


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    检查包是否已安装

    Args:
        package_name: 包的显示名称
        import_name: 导入名称（如果与显示名称不同）

    Returns:
        (是否安装, 版本信息或错误消息)
    """
    if import_name is None:
        import_name = package_name

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', '未知版本')
        return True, f"✓ {package_name} ({version})"
    except ImportError as e:
        return False, f"✗ {package_name} 未安装"


def main():
    """检查所有依赖"""
    print("=" * 60)
    print("依赖检查 - 科研文献摘要提取系统 v2.0")
    print("=" * 60)
    print()

    # 核心依赖
    core_packages = [
        ("Python", None, "3.8"),
        ("langchain", "langchain", "0.2.0"),
        ("langchain-openai", "langchain_openai", "0.1.0"),
        ("langchain-core", "langchain_core", None),
    ]

    # 可选依赖
    optional_packages = [
        ("langgraph", "langgraph", None),
        ("PyPDF2", "PyPDF2", None),
        ("pdfplumber", "pdfplumber", None),
        ("PyMuPDF", "fitz", None),
        ("jieba", "jieba", None),
        ("scikit-learn", "sklearn", None),
        ("matplotlib", "matplotlib", None),
        ("plotly", "plotly", None),
        ("flask", "flask", None),
        ("flask-cors", "flask_cors", None),
        ("flask-socketio", "flask_socketio", None),
        ("python-dotenv", "dotenv", None),
        ("click", "click", None),
        ("rich", "rich", None),
    ]

    # 检查Python版本
    print("1. 核心依赖检查")
    print("-" * 60)
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"✗ Python {python_version.major}.{python_version.minor} (需要3.8+)")
        print("\n请升级Python版本到3.8或更高")
        return False

    # 检查核心包
    for pkg_name, imp_name, min_ver in core_packages[1:]:  # 跳过Python
        installed, msg = check_package(pkg_name, imp_name)
        print(msg)
        if not installed:
            print(f"\n请安装缺失的包: pip install {pkg_name}")
            return False

    print()
    print("2. 可选依赖检查")
    print("-" * 60)

    missing_optional = []
    for pkg_name, imp_name, min_ver in optional_packages:
        installed, msg = check_package(pkg_name, imp_name)
        print(msg)
        if not installed:
            missing_optional.append(pkg_name)

    print()
    print("3. 总结")
    print("-" * 60)

    if missing_optional:
        print(f"\n⚠️  有 {len(missing_optional)} 个可选包未安装：")
        for pkg in missing_optional:
            print(f"   - {pkg}")
        print("\n这些包用于特定功能，建议安装：")
        print(f"   pip install {' '.join(missing_optional)}")
    else:
        print("\n✓ 所有依赖都已安装！")

    print("\n下一步：")
    print("1. 配置环境变量：复制 .env.example 到 .env 并填入API密钥")
    print("2. 运行测试：python check_dependencies.py")
    print("3. 启动服务：python app.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
