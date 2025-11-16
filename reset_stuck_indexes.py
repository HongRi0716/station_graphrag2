#!/usr/bin/env python3
"""
重置卡住的索引状态为PENDING，让reconciliation重新处理
"""

from aperag.config import get_sync_session
from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus
from sqlalchemy import select, and_, update
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


document_id = "doc8487f14105fb5d97"

print("=" * 80)
print("重置卡住的索引状态")
print("=" * 80)
print(f"\n文档ID: {document_id}\n")

for session in get_sync_session():
    # 查找所有CREATING状态的索引
    stuck_indexes = session.execute(
        select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.status == DocumentIndexStatus.CREATING
            )
        )
    ).scalars().all()

    if not stuck_indexes:
        print("✅ 没有卡住的索引")
        break

    print(f"找到 {len(stuck_indexes)} 个卡住的索引:\n")
    for idx in stuck_indexes:
        index_type_str = idx.index_type.value if hasattr(
            idx.index_type, 'value') else str(idx.index_type)
        print(f"  - {index_type_str}")

    # 确认
    print(f"\n⚠️  即将重置这些索引的状态为PENDING")
    print("   这将触发reconciliation重新处理这些索引")

    # 执行重置
    for idx in stuck_indexes:
        index_type_str = idx.index_type.value if hasattr(
            idx.index_type, 'value') else str(idx.index_type)
        session.execute(
            update(DocumentIndex)
            .where(and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.index_type == DocumentIndexType(index_type_str)
            ))
            .values(status=DocumentIndexStatus.PENDING)
        )
        print(f"  ✅ 已重置 {index_type_str} 索引状态")

    session.commit()
    print(f"\n✅ 所有索引状态已重置为PENDING")
    print("   请等待reconciliation任务重新处理（通常1分钟内）")
    break
