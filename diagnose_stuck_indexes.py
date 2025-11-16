#!/usr/bin/env python3
"""
诊断卡住的索引创建任务
"""

from aperag.config import get_sync_session
from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus, Document
from sqlalchemy import select, and_, update
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


document_id = "doc8487f14105fb5d97"

print("=" * 80)
print("诊断卡住的索引创建任务")
print("=" * 80)

for session in get_sync_session():
    doc = session.execute(select(Document).where(
        Document.id == document_id)).scalar_one_or_none()
    if doc:
        print(f"\n文档: {doc.name}")
        print(f"文档状态: {doc.status}")

    indexes = session.execute(
        select(DocumentIndex).where(DocumentIndex.document_id == document_id)
    ).scalars().all()

    stuck_indexes = []
    now = datetime.now(timezone.utc)

    for idx in indexes:
        status_str = idx.status.value if hasattr(
            idx.status, 'value') else str(idx.status)
        print(f"\n{idx.index_type}:")
        print(f"  状态: {status_str}")
        print(f"  版本: {idx.version} (已处理: {idx.observed_version})")
        print(f"  创建: {idx.gmt_created}")
        print(f"  更新: {idx.gmt_updated}")

        # 检查是否卡住（CREATING状态超过10分钟）
        if idx.status == DocumentIndexStatus.CREATING:
            if idx.gmt_updated:
                elapsed = now - idx.gmt_updated.replace(
                    tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
                elapsed_minutes = elapsed.total_seconds() / 60
                print(f"  已CREATING状态: {elapsed_minutes:.1f} 分钟")

                if elapsed_minutes > 10:
                    stuck_indexes.append(idx)
                    print(f"  ⚠️  该索引可能卡住了（超过10分钟）")

        if idx.error_message:
            print(f"  错误: {idx.error_message}")

    # 如果发现卡住的索引，提供解决方案
    if stuck_indexes:
        print(f"\n{'='*80}")
        print("💡 解决方案建议")
        print("="*80)

        print("\n1. 重置卡住的索引状态（谨慎使用）:")
        print("   这将把CREATING状态重置为PENDING，让reconciliation重新处理")
        print("\n   执行以下代码:")
        print("   ```python")
        print("   from aperag.db.models import DocumentIndex, DocumentIndexStatus, DocumentIndexType")
        print("   from aperag.config import get_sync_session")
        print("   from sqlalchemy import update, and_")
        print("   ")
        print("   for session in get_sync_session():")
        for idx in stuck_indexes:
            index_type_str = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)
            print(f"       # Reset {index_type_str} index")
            print(f"       session.execute(")
            print(f"           update(DocumentIndex)")
            print(f"           .where(and_(")
            print(
                f"               DocumentIndex.document_id == '{document_id}',")
            print(
                f"               DocumentIndex.index_type == DocumentIndexType.{index_type_str}")
            print(f"           )).values(status=DocumentIndexStatus.PENDING)")
            print(f"       )")
        print("       session.commit()")
        print("       break")
        print("   ```")

        print("\n2. 手动触发reconciliation:")
        print("   docker exec aperag-celeryworker python -c \\")
        print("       'from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()'")

        print("\n3. 检查Celery任务是否真的在执行:")
        print("   docker exec aperag-celeryworker celery -A config.celery inspect active")

        print("\n4. 查看详细日志:")
        print(
            f"   docker logs aperag-celeryworker --tail 1000 | grep '{document_id}'")

    break
