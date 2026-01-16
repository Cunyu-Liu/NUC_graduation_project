#!/usr/bin/env python3
"""
数据库检查和测试数据生成脚本
用于诊断研究空白加载问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.db_manager import DatabaseManager
from src.database import ResearchGap, Analysis, Paper
from datetime import datetime, timezone

def check_database():
    """检查数据库状态"""
    print("\n" + "="*60)
    print("📊 数据库状态检查")
    print("="*60)

    db = DatabaseManager()

    try:
        with db.get_session() as session:
            # 检查论文数量
            paper_count = session.query(Paper).count()
            print(f"\n✅ 论文数量: {paper_count}")

            # 检查分析数量
            analysis_count = session.query(Analysis).count()
            print(f"✅ 分析记录数量: {analysis_count}")

            # 检查研究空白数量
            gap_count = session.query(ResearchGap).count()
            print(f"✅ 研究空白数量: {gap_count}")

            if gap_count == 0:
                print("\n⚠️  数据库中没有研究空白数据！")
                print("\n可能的原因:")
                print("  1. 还没有分析过论文")
                print("  2. 分析过程没有生成研究空白")
                print("  3. 研究空白没有被正确保存到数据库")
                return False

            # 显示研究空白详情
            print("\n" + "-"*60)
            print("📋 研究空白列表:")
            print("-"*60)

            gaps = session.query(ResearchGap).order_by(ResearchGap.created_at.desc()).limit(10).all()

            for i, gap in enumerate(gaps, 1):
                print(f"\n{i}. 空白ID: {gap.id}")
                print(f"   类型: {gap.gap_type}")
                print(f"   重要性: {gap.importance}")
                print(f"   状态: {gap.status}")
                print(f"   描述: {gap.description[:100]}...")

            return True

    except Exception as e:
        print(f"\n❌ 数据库检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_test_gaps():
    """创建测试数据"""
    print("\n" + "="*60)
    print("🔧 创建测试数据")
    print("="*60)

    db = DatabaseManager()

    try:
        with db.get_session() as session:
            # 检查是否已有分析记录
            analysis = session.query(Analysis).first()

            if not analysis:
                print("\n⚠️  没有分析记录，需要先创建测试分析...")
                # 创建测试分析
                paper = session.query(Paper).first()
                if not paper:
                    print("❌ 没有论文数据，请先上传论文")
                    return False

                analysis = Analysis(
                    paper_id=paper.id,
                    summary_text="这是一个测试摘要",
                    keypoints={},
                    status='completed'
                )
                session.add(analysis)
                session.commit()
                session.refresh(analysis)
                print(f"✅ 创建测试分析记录 ID: {analysis.id}")

            # 创建测试研究空白
            test_gaps_data = [
                {
                    'gap_type': 'methodological',
                    'description': '现有方法在处理大规模数据时存在性能瓶颈，需要设计更高效的算法',
                    'importance': 'high',
                    'difficulty': 'medium',
                    'potential_approach': '可以结合分布式计算和增量学习技术来优化性能',
                    'expected_impact': '预计可以将处理速度提升3-5倍',
                    'status': 'identified',
                    'analysis_id': analysis.id
                },
                {
                    'gap_type': 'theoretical',
                    'description': '当前理论框架缺乏对非线性关系的充分解释',
                    'importance': 'medium',
                    'difficulty': 'high',
                    'potential_approach': '可以引入新的数学模型来描述非线性交互',
                    'expected_impact': '将为理解复杂系统提供新的理论视角',
                    'status': 'identified',
                    'analysis_id': analysis.id
                },
                {
                    'gap_type': 'data',
                    'description': '缺少特定领域的高质量标注数据集',
                    'importance': 'high',
                    'difficulty': 'low',
                    'potential_approach': '可以通过半监督学习和主动学习来减少对标注数据的依赖',
                    'expected_impact': '将使模型能够在更多场景下应用',
                    'status': 'identified',
                    'analysis_id': analysis.id
                },
                {
                    'gap_type': 'application',
                    'description': '现有技术在实际应用场景中的鲁棒性有待提高',
                    'importance': 'medium',
                    'difficulty': 'medium',
                    'potential_approach': '需要引入对抗训练和领域自适应技术',
                    'expected_impact': '将显著提升系统的实用性和可靠性',
                    'status': 'identified',
                    'analysis_id': analysis.id
                },
                {
                    'gap_type': 'evaluation',
                    'description': '缺乏标准化的评估指标来全面衡量模型性能',
                    'importance': 'low',
                    'difficulty': 'low',
                    'potential_approach': '可以设计多维度的评估体系，包括准确性、效率、可解释性等',
                    'expected_impact': '将有助于更客观地比较不同方法的优劣',
                    'status': 'identified',
                    'analysis_id': analysis.id
                }
            ]

            created_count = 0
            for gap_data in test_gaps_data:
                # 检查是否已存在类似的研究空白
                existing = session.query(ResearchGap).filter(
                    ResearchGap.analysis_id == gap_data['analysis_id'],
                    ResearchGap.gap_type == gap_data['gap_type']
                ).first()

                if not existing:
                    gap = ResearchGap(**gap_data)
                    session.add(gap)
                    created_count += 1

            session.commit()
            print(f"\n✅ 成功创建 {created_count} 个测试研究空白")

            if created_count > 0:
                print("\n📝 已创建的研究空白类型:")
                for gap_data in test_gaps_data:
                    type_labels = {
                        'methodological': '方法论',
                        'theoretical': '理论',
                        'data': '数据',
                        'application': '应用',
                        'evaluation': '评估'
                    }
                    print(f"  - {type_labels.get(gap_data['gap_type'], gap_data['gap_type'])}: {gap_data['description'][:50]}...")

            return True

    except Exception as e:
        print(f"\n❌ 创建测试数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n🔍 科研文献摘要提取系统 - 数据库诊断工具")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查数据库
    has_data = check_database()

    if not has_data:
        print("\n" + "="*60)
        print("是否要创建测试数据？(y/n): ", end='')
        choice = input().strip().lower()

        if choice == 'y' or choice == 'yes':
            if create_test_gaps():
                print("\n✅ 测试数据创建成功！")
                print("\n下一步:")
                print("  1. 刷新前端页面")
                print("  2. 进入'研究空白管理'页面")
                print("  3. 应该可以看到测试数据了")
            else:
                print("\n❌ 测试数据创建失败")
        else:
            print("\n提示:")
            print("  1. 先上传PDF论文")
            print("  2. 分析论文（选择'研究空白挖掘'）")
            print("  3. 等待分析完成")
            print("  4. 再次访问研究空白页面")
    else:
        print("\n✅ 数据库状态正常！")
        print("\n如果前端仍然无法加载，请检查:")
        print("  1. 后端服务是否正在运行（python app.py）")
        print("  2. 前端是否已重启（cd frontend && npm run serve）")
        print("  3. 浏览器控制台是否有错误信息")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
