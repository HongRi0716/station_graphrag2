#!/usr/bin/env python3
"""
检查CREATING状态的索引详情
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select
    from aperag.db.models import Document, DocumentIndex, DocumentIndexStatus
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def check_creating_indexes():
    """检查CREATING状态的索引"""
    print("=" * 80)
    print("检查CREATING状态的索引")
    print("=" * 80)

    for session in get_sync_session():
        # 查询所有CREATING状态的索引
        index_stmt = select(DocumentIndex).where(
            DocumentIndex.status == DocumentIndexStatus.CREATING
        )
        index_result = session.execute(index_stmt)
        indexes = index_result.scalars().all()

        if not indexes:
            print("\n✅ 没有CREATING状态的索引")
            return

        print(f"\n找到 {len(indexes)} 个CREATING状态的索引:\n")

        now = datetime.now(timezone.utc)
        for idx in indexes:
            # 获取文档信息
            doc_stmt = select(Document).where(Document.id == idx.document_id)
            doc_result = session.execute(doc_stmt)
            doc = doc_result.scalar_one_or_none()

            # 计算等待时间
            if idx.gmt_updated:
                elapsed = now - (idx.gmt_updated.replace(tzinfo=timezone.utc)
                                 if idx.gmt_updated.tzinfo is None else idx.gmt_updated)
                elapsed_minutes = elapsed.total_seconds() / 60
                elapsed_hours = elapsed_minutes / 60
            else:
                elapsed_minutes = 0
                elapsed_hours = 0

            index_type = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)

            print(f"📄 文档: {doc.name if doc else '未知'} (ID: {idx.document_id})")
            print(f"   索引类型: {index_type}")
            print(
                f"   状态: {idx.status.value if hasattr(idx.status, 'value') else idx.status}")
            print(f"   版本: {idx.version}, 已观察版本: {idx.observed_version}")
            print(f"   更新时间: {idx.gmt_updated}")
            if elapsed_hours >= 1:
                print(
                    f"   ⚠️  已等待: {elapsed_hours:.1f} 小时 ({elapsed_minutes:.1f} 分钟)")
            else:
                print(f"   已等待: {elapsed_minutes:.1f} 分钟")
            if idx.error_message:
                print(f"   ❌ 错误信息: {idx.error_message[:200]}")
            print()

        # 统计
        stuck_count = sum(1 for idx in indexes if idx.gmt_updated and
                          (now - (idx.gmt_updated.replace(tzinfo=timezone.utc)
                                  if idx.gmt_updated.tzinfo is None else idx.gmt_updated)).total_seconds() > 300)
        if stuck_count > 0:
            print(f"\n⚠️  有 {stuck_count} 个索引可能卡住了（超过5分钟）")
            print("\n💡 建议:")
            print("  1. 检查Celery worker是否正常运行:")
            print("     docker ps | grep celeryworker")
            print("  2. 查看Celery worker日志:")
            print("     docker logs aperag-celeryworker --tail 100")
            print("  3. 检查是否有任务在执行:")
            print(
                "     docker exec aperag-celeryworker celery -A config.celery_app inspect active")
            print("  4. 如果索引确实卡住了，可以重置状态:")
            print(
                "     docker exec aperag-celeryworker python /app/reset_stuck_indexes.py")

        break


if __name__ == "__main__":
    try:
        check_creating_indexes()
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
