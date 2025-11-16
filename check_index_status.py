#!/usr/bin/env python3
"""检查索引状态和错误信息"""

from aperag.config import get_sync_session
from aperag.db.models import DocumentIndex, DocumentIndexType, Document
from sqlalchemy import select, and_
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


document_id = "doc8487f14105fb5d97"

for session in get_sync_session():
    doc = session.execute(select(Document).where(
        Document.id == document_id)).scalar_one_or_none()
    if doc:
        print(f"文档: {doc.name}")
        print(f"状态: {doc.status}")

    indexes = session.execute(
        select(DocumentIndex).where(DocumentIndex.document_id == document_id)
    ).scalars().all()

    for idx in indexes:
        print(f"\n{idx.index_type}:")
        print(f"  状态: {idx.status}")
        print(f"  版本: {idx.version} (已处理: {idx.observed_version})")
        print(f"  创建: {idx.gmt_created}")
        print(f"  更新: {idx.gmt_updated}")
        if idx.error_message:
            print(f"  错误: {idx.error_message}")
    break
