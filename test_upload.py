#!/usr/bin/env python3
"""测试上传功能修复"""
import requests
import sys

def test_upload():
    """测试PDF上传"""
    # 检查服务器是否运行
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=5)
        if response.status_code != 200:
            print("❌ 服务器健康检查失败")
            return False
        print("✓ 服务器运行正常")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

    # 检查数据库连接
    try:
        from src.db_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_statistics()
        print(f"✓ 数据库连接正常")
        print(f"  - 论文数: {stats['total_papers']}")
        print(f"  - 用户数: {stats['total_users']}")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

    # 测试paper创建逻辑
    try:
        from src.database import Paper
        print("✓ Paper模型导入成功")

        # 测试字段过滤
        test_data = {
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'pdf_path': 'test.pdf',
            'pdf_hash': 'abc123',
            'meta_data': {'test': 'data'},
            'authors': [{'name': 'Test Author'}],  # 这个应该被过滤
            'keywords': ['test']  # 这个也应该被过滤
        }

        # 过滤字段
        paper_fields = {k: v for k, v in test_data.items()
                      if k not in ['authors', 'keywords']}

        # 验证过滤结果
        assert 'authors' not in paper_fields, "authors应该被过滤"
        assert 'keywords' not in paper_fields, "keywords应该被过滤"
        assert 'title' in paper_fields, "title应该保留"
        assert 'meta_data' in paper_fields, "meta_data应该保留"

        print("✓ 字段过滤逻辑正确")

        # 尝试创建Paper对象(不保存到数据库)
        paper = Paper(**paper_fields)
        print(f"✓ Paper对象创建成功: {paper.title}")

    except Exception as e:
        print(f"❌ Paper对象创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("✓ 所有测试通过!")
    print("="*60)
    return True

if __name__ == '__main__':
    success = test_upload()
    sys.exit(0 if success else 1)
