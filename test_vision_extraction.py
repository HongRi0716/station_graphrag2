#!/usr/bin/env python3
"""测试Vision内容提取"""

from sqlalchemy import select
from aperag.graph import lightrag_manager
from aperag.db.models import Collection, Document
from aperag.config import get_sync_session
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_vision_extraction():
    document_id = "docf83852b7578bb718"

    # 获取文档和Collection
    for session in get_sync_session():
        doc = session.execute(select(Document).where(
            Document.id == document_id)).scalar_one_or_none()
        if not doc:
            print("文档不存在")
            return

        collection = session.execute(select(Collection).where(
            Collection.id == doc.collection_id)).scalar_one_or_none()
        if not collection:
            print("Collection不存在")
            return

        # 测试Vision内容提取
        print("=" * 80)
        print("测试Vision内容提取")
        print("=" * 80)

        content = await lightrag_manager._enrich_content_with_vision_analysis(collection, document_id)

        print(f"\n提取的内容长度: {len(content)} 字符")
        if content:
            print(f"\n内容预览（前1000字符）:")
            print(content[:1000])
            print("\n...")
        else:
            print("\n❌ 未提取到内容")

        break

if __name__ == "__main__":
    asyncio.run(test_vision_extraction())
