#!/usr/bin/env python3
"""
系统完整性检查脚本 - 验证所有模块是否能正常导入
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("模块导入测试 - 科研文献摘要提取系统 v2.0")
    print("=" * 60)
    print()

    tests = []

    # 测试1: 配置模块
    print("1. 测试配置模块...")
    try:
        from src.config import settings
        print(f"   ✓ 配置模块导入成功")
        print(f"   - 模型: {settings.default_model}")
        print(f"   - API密钥: {'已设置' if settings.glm_api_key else '⚠️  未设置'}")
        tests.append(("配置模块", True))
    except Exception as e:
        print(f"   ✗ 配置模块导入失败: {e}")
        tests.append(("配置模块", False))

    # 测试2: PDF解析模块
    print("\n2. 测试PDF解析模块...")
    try:
        from src.pdf_parser import PDFParser, ParsedPaper
        print("   ✓ PDF解析模块导入成功")
        tests.append(("PDF解析", True))
    except Exception as e:
        print(f"   ✗ PDF解析模块导入失败: {e}")
        tests.append(("PDF解析", False))

    # 测试3: 提示词模块
    print("\n3. 测试提示词模块...")
    try:
        from src.prompts import (
            get_summary_prompt,
            get_keypoint_prompt,
            get_topic_prompt
        )
        print("   ✓ 提示词模块导入成功")
        tests.append(("提示词", True))
    except Exception as e:
        print(f"   ✗ 提示词模块导入失败: {e}")
        tests.append(("提示词", False))

    # 测试4: 工作流模块
    print("\n4. 测试工作流模块...")
    try:
        from src.workflow import PaperAnalysisWorkflow
        print("   ✓ 工作流模块导入成功")
        tests.append(("工作流", True))
    except Exception as e:
        print(f"   ✗ 工作流模块导入失败: {e}")
        tests.append(("工作流", False))

    # 测试5: 摘要生成模块
    print("\n5. 测试摘要生成模块...")
    try:
        from src.summary_generator import SummaryGenerator
        print("   ✓ 摘要生成模块导入成功")
        tests.append(("摘要生成", True))
    except Exception as e:
        print(f"   ✗ 摘要生成模块导入失败: {e}")
        tests.append(("摘要生成", False))

    # 测试6: 要点提取模块
    print("\n6. 测试要点提取模块...")
    try:
        from src.keypoint_extractor import KeypointExtractor
        print("   ✓ 要点提取模块导入成功")
        tests.append(("要点提取", True))
    except Exception as e:
        print(f"   ✗ 要点提取模块导入失败: {e}")
        tests.append(("要点提取", False))

    # 测试7: 主题聚类模块
    print("\n7. 测试主题聚类模块...")
    try:
        from src.topic_clustering import TopicClustering
        print("   ✓ 主题聚类模块导入成功")
        tests.append(("主题聚类", True))
    except Exception as e:
        print(f"   ✗ 主题聚类模块导入失败: {e}")
        tests.append(("主题聚类", False))

    # 测试8: Flask应用
    print("\n8. 测试Flask应用...")
    try:
        from app import app
        print("   ✓ Flask应用导入成功")
        tests.append(("Flask应用", True))
    except Exception as e:
        print(f"   ✗ Flask应用导入失败: {e}")
        tests.append(("Flask应用", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")

    if passed == total:
        print("\n✓ 所有模块导入测试通过！")
        return True
    else:
        print("\n✗ 部分模块导入失败")
        print("\n请检查：")
        print("1. 是否安装了所有依赖：pip install -r requirements.txt")
        print("2. Python版本是否 >= 3.8")
        return False


def test_configuration():
    """测试配置"""
    print("\n" + "=" * 60)
    print("配置测试")
    print("=" * 60)
    print()

    try:
        from src.config import settings

        print("API配置:")
        print(f"  - API密钥: {'✓ 已设置' if settings.glm_api_key else '✗ 未设置'}")
        print(f"  - Base URL: {settings.glm_base_url}")

        print("\n模型配置:")
        print(f"  - 默认模型: {settings.default_model}")
        print(f"  - 温度: {settings.default_temperature}")
        print(f"  - 最大Tokens: {settings.max_tokens}")

        print("\nFlask配置:")
        print(f"  - 主机: {settings.flask_host}")
        print(f"  - 端口: {settings.flask_port}")
        print(f"  - 调试模式: {settings.flask_debug}")

        print("\n输出目录:")
        print(f"  - 总输出: {settings.output_dir}")
        print(f"  - 摘要: {settings.summary_output_dir}")
        print(f"  - 要点: {settings.keypoints_output_dir}")
        print(f"  - 聚类: {settings.cluster_output_dir}")
        print(f"  - 上传: {settings.upload_dir}")

        # 检查目录是否可写
        print("\n目录权限检查:")
        test_file = settings.output_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("  ✓ 输出目录可写")
        except Exception as e:
            print(f"  ✗ 输出目录不可写: {e}")

        if not settings.glm_api_key:
            print("\n⚠️  警告: 未设置GLM_API_KEY")
            print("请在.env文件中设置API密钥")
            return False

        return True

    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n开始系统检查...\n")

    # 测试导入
    imports_ok = test_imports()

    # 测试配置
    config_ok = test_configuration()

    # 最终结果
    print("\n" + "=" * 60)
    print("最终结果")
    print("=" * 60)

    if imports_ok and config_ok:
        print("\n✓ 系统检查通过！可以开始使用")
        print("\n启动命令:")
        print("  Web模式: python app.py")
        print("  CLI模式: python main.py analyze <论文.pdf>")
        return True
    else:
        print("\n✗ 系统检查失败")
        if not imports_ok:
            print("\n请安装缺失的依赖:")
            print("  pip install -r requirements.txt")
        if not config_ok:
            print("\n请配置环境变量:")
            print("  1. 复制 .env.example 到 .env")
            print("  2. 编辑 .env 并填入 GLM_API_KEY")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
