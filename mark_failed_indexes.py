#!/usr/bin/env python3
"""
将有错误信息的CREATING状态索引标记为FAILED
"""

import sys
import os
from sqlalchemy import select, update, and_

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from aperag.db.models import DocumentIndex, DocumentIndexStatus
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def mark_failed_indexes(auto_confirm=False):
    """将有错误信息的CREATING状态索引标记为FAILED"""
    print("=" * 80)
    print("将有错误信息的CREATING状态索引标记为FAILED")
    print("=" * 80)

    for session in get_sync_session():
        # 查询所有CREATING状态且有错误信息的索引
        index_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.status == DocumentIndexStatus.CREATING,
                DocumentIndex.error_message.isnot(None),
                DocumentIndex.error_message != ""
            )
        )
        index_result = session.execute(index_stmt)
        indexes = index_result.scalars().all()

        if not indexes:
            print("\n✅ 没有找到需要标记为FAILED的索引")
            return

        print(f"\n找到 {len(indexes)} 个有错误信息的CREATING状态索引:\n")

        for idx in indexes:
            index_type = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)
            error_msg = idx.error_message[:100] + "..." if len(
                idx.error_message) > 100 else idx.error_message
            print(f"  - 文档ID: {idx.document_id}, 类型: {index_type}")
            print(f"    错误: {error_msg}\n")

        # 确认
        print(f"⚠️  即将将这些索引标记为FAILED状态")
        if not auto_confirm:
            try:
                response = input("确认继续? (y/n): ").strip().lower()
                if response != 'y':
                    print("操作已取消")
                    return
            except EOFError:
                print("⚠️  非交互式环境，自动确认执行")
        else:
            print("自动确认执行...")

        # 执行更新
        updated_count = 0
        for idx in indexes:
            update_stmt = (
                update(DocumentIndex)
                .where(
                    and_(
                        DocumentIndex.document_id == idx.document_id,
                        DocumentIndex.index_type == idx.index_type,
                        DocumentIndex.status == DocumentIndexStatus.CREATING
                    )
                )
                .values(
                    status=DocumentIndexStatus.FAILED,
                    gmt_updated=idx.gmt_updated  # 保持原更新时间
                )
            )
            result = session.execute(update_stmt)
            if result.rowcount > 0:
                updated_count += 1
                index_type = idx.index_type.value if hasattr(
                    idx.index_type, 'value') else str(idx.index_type)
                print(f"  ✅ 已标记 {idx.document_id}:{index_type} 为FAILED")

        session.commit()
        print(f"\n✅ 成功标记 {updated_count} 个索引为FAILED状态")
        break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="将有错误信息的CREATING状态索引标记为FAILED")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，跳过交互")
    args = parser.parse_args()

    try:
        mark_failed_indexes(auto_confirm=args.yes)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
