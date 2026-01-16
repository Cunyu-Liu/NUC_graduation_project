#!/usr/bin/env python3
"""
数据库ORM修复工具
用于修复ResearchGap和GeneratedCode之间的外键关系问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def fix_database():
    """修复数据库关系"""
    print("\n" + "="*60)
    print("🔧 数据库ORM修复工具")
    print("="*60)

    try:
        print("\n步骤1: 导入数据库模块...")
        from src.database import Base, engine
        from src.db_manager import DatabaseManager

        print("✅ 模块导入成功")

        print("\n步骤2: 删除所有旧表...")
        answer = input("⚠️  这将删除所有数据！确认继续？(yes/no): ").strip().lower()

        if answer not in ['yes', 'y']:
            print("❌ 操作已取消")
            return False

        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        print("✅ 旧表已删除")

        print("\n步骤3: 创建新表（使用修复后的ORM关系）...")
        Base.metadata.create_all(bind=engine)
        print("✅ 新表创建成功")

        print("\n步骤4: 验证表结构...")
        db = DatabaseManager()

        with db.get_session() as session:
            # 测试查询
            from src.database import ResearchGap, GeneratedCode

            # 测试关系
            try:
                # 这个查询会触发ORM关系加载
                gaps = session.query(ResearchGap).all()
                print(f"✅ ResearchGap表正常，可以查询")

                codes = session.query(GeneratedCode).all()
                print(f"✅ GeneratedCode表正常，可以查询")

                print("\n✅ 所有表和关系验证通过！")

            except Exception as e:
                print(f"\n❌ 关系验证失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

        print("\n" + "="*60)
        print("✅ 数据库修复完成！")
        print("="*60)
        print("\n下一步:")
        print("  1. 重启后端服务: python app.py")
        print("  2. 运行测试: python test_api.py")
        print("  3. 创建测试数据: python check_gaps.py")

        return True

    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n🔍 科研文献摘要提取系统 - 数据库ORM修复")
    print(f"运行时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n问题说明:")
    print("  ResearchGap和GeneratedCode之间的外键关系存在歧义")
    print("  需要重新创建数据库表以应用修复")

    if fix_database():
        print("\n🎉 修复成功！")
        return 0
    else:
        print("\n⚠️  修复失败，请查看错误信息")
        return 1

if __name__ == "__main__":
    exit(main())
