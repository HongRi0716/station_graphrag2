#!/usr/bin/env python3
"""检查Vision索引的内容"""

from sqlalchemy import select, and_
from aperag.db.models import Document, Collection
from aperag.utils.utils import generate_vector_db_collection_name
from aperag.config import get_vector_db_connector
from aperag.db.models import DocumentIndex, DocumentIndexType
from aperag.config import get_sync_session
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_vision_content(document_id: str):
    """检查Vision索引的内容"""

    print("=" * 80)
    print("Vision索引内容检查")
    print("=" * 80)
    print(f"\n文档ID: {document_id}\n")

    for session in get_sync_session():
        # 查询文档和Collection
        doc = session.execute(select(Document).where(
            Document.id == document_id)).scalar_one_or_none()
        if not doc:
            print("❌ 文档不存在")
            return

        collection = session.execute(select(Collection).where(
            Collection.id == doc.collection_id)).scalar_one_or_none()
        if not collection:
            print("❌ Collection不存在")
            return

        # 查询Vision索引
        vision_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.VISION
                )
            )
        ).scalar_one_or_none()

        if not vision_index:
            print("❌ Vision索引不存在")
            return

        print(f"Vision索引状态: {vision_index.status}")

        if vision_index.index_data:
            try:
                index_data = json.loads(vision_index.index_data)
                ctx_ids = index_data.get("context_ids", [])
                print(f"\nContext IDs数量: {len(ctx_ids)}")
                if ctx_ids:
                    print(f"Context IDs: {ctx_ids[:5]}...")

                    # 查询向量存储中的内容
                    collection_name = generate_vector_db_collection_name(
                        collection_id=collection.id)
                    vector_store = get_vector_db_connector(
                        collection=collection_name)
                    qdrant_client = vector_store.connector.client

                    points = qdrant_client.retrieve(
                        collection_name=collection_name,
                        ids=ctx_ids,
                        with_payload=True,
                    )

                    print(f"\n从向量存储检索到 {len(points)} 个点")

                    for i, point in enumerate(points[:3], 1):  # 只显示前3个
                        print(f"\n--- 点 {i} (ID: {point.id}) ---")
                        if point.payload:
                            # 检查_node_content
                            node_content = point.payload.get("_node_content")
                            if node_content:
                                try:
                                    payload_data = json.loads(node_content)
                                    text = payload_data.get("text", "")
                                    metadata = payload_data.get("metadata", {})
                                    print(f"  文本长度: {len(text)} 字符")
                                    print(f"  元数据: {metadata}")
                                    if text:
                                        print(f"  文本预览: {text[:200]}...")
                                except:
                                    print(
                                        f"  无法解析_node_content: {node_content[:100]}...")

                            # 检查直接metadata
                            metadata = point.payload.get("metadata", {})
                            if metadata:
                                print(f"  直接metadata: {metadata}")

                            # 检查直接text
                            text = point.payload.get("text", "")
                            if text:
                                print(f"  直接text长度: {len(text)} 字符")
                                print(f"  直接text预览: {text[:200]}...")
            except Exception as e:
                print(f"❌ 解析索引数据失败: {e}")
                import traceback
                traceback.print_exc()

        break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    args = parser.parse_args()

    try:
        check_vision_content(args.document_id)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
