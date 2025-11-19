#!/usr/bin/env python3
"""检查颍州变接线图.pdf的Vision-to-Text文本内容"""

from sqlalchemy import select, and_, desc
from aperag.db.models import Document, Collection
from aperag.utils.utils import generate_vector_db_collection_name
from aperag.config import get_vector_db_connector
from aperag.db.models import DocumentIndex, DocumentIndexType
from aperag.config import get_sync_session
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_vision_text_by_name(document_name_pattern: str):
    """按文档名称检查Vision索引的内容"""

    print("=" * 80)
    print("Vision-to-Text文本内容检查工具")
    print("=" * 80)
    print(f"\n查找文档: {document_name_pattern}\n")

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(
            Document.name.like(f"%{document_name_pattern}%")
        ).order_by(desc(Document.gmt_created))

        doc_result = session.execute(doc_stmt)
        documents = doc_result.scalars().all()

        if not documents:
            print(f"❌ 未找到匹配的文档: {document_name_pattern}")
            return

        # 取最新的文档
        doc = documents[0]
        print(f"\n{'='*80}")
        print(f"文档名称: {doc.name}")
        print(f"文档ID: {doc.id}")
        print(f"文档状态: {doc.status}")
        print(f"所属Collection ID: {doc.collection_id}")
        print(f"创建时间: {doc.gmt_created}")
        print(f"-" * 80)

        collection = session.execute(select(Collection).where(
            Collection.id == doc.collection_id)).scalar_one_or_none()
        if not collection:
            print("❌ Collection不存在")
            return

        # 查询Vision索引
        vision_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == doc.id,
                    DocumentIndex.index_type == DocumentIndexType.VISION
                )
            )
        ).scalar_one_or_none()

        if not vision_index:
            print("\n❌ Vision索引不存在")
            print("\n💡 可能原因:")
            print("   - Vision索引尚未创建")
            print("   - Collection的enable_vision未启用")
            return

        print(f"\n📊 Vision索引状态: {vision_index.status}")
        print(f"  版本: {vision_index.version}")
        print(f"  创建时间: {vision_index.gmt_created}")

        if vision_index.index_data:
            try:
                index_data = json.loads(vision_index.index_data)
                ctx_ids = index_data.get("context_ids", [])
                print(f"\n📋 Context IDs数量: {len(ctx_ids)}")
                if not ctx_ids:
                    print("⚠️  没有Context IDs，Vision索引可能为空")
                    return

                # 查询向量存储中的内容
                collection_name = generate_vector_db_collection_name(
                    collection_id=collection.id)
                vector_store = get_vector_db_connector(
                    collection=collection_name)
                qdrant_client = vector_store.connector.client

                print(f"\n从向量存储检索Vision-to-Text内容...")
                print(f"Collection名称: {collection_name}")

                points = qdrant_client.retrieve(
                    collection_name=collection_name,
                    ids=ctx_ids,
                    with_payload=True,
                )

                print(f"✅ 检索到 {len(points)} 个点\n")

                vision_texts = []
                for i, point in enumerate(points, 1):
                    text = None
                    metadata = {}
                    asset_id = None
                    page_idx = None

                    if point.payload:
                        # 检查_node_content
                        node_content = point.payload.get("_node_content")
                        if node_content and isinstance(node_content, str):
                            try:
                                payload_data = json.loads(node_content)
                                metadata = payload_data.get("metadata", {})
                                if metadata.get("index_method") == "vision_to_text":
                                    text = payload_data.get("text", "")
                                    asset_id = metadata.get("asset_id", "")
                                    page_idx = metadata.get("page_idx")
                            except:
                                pass

                        # 检查直接payload结构
                        if not text or not text.strip():
                            direct_metadata = point.payload.get("metadata", {})
                            if direct_metadata.get("index_method") == "vision_to_text":
                                text = point.payload.get("text", "")
                                if not text and node_content:
                                    try:
                                        payload_data = json.loads(node_content)
                                        text = payload_data.get("text", "")
                                        metadata = payload_data.get(
                                            "metadata", {})
                                    except:
                                        pass
                                asset_id = direct_metadata.get(
                                    "asset_id") or metadata.get("asset_id")
                                page_idx = direct_metadata.get(
                                    "page_idx") if "page_idx" in direct_metadata else metadata.get("page_idx")

                    if text and text.strip():
                        section_info = f"\n{'='*80}\n"
                        section_info += f"Vision-to-Text内容 #{i}\n"
                        section_info += f"Point ID: {point.id}\n"
                        if asset_id:
                            section_info += f"Asset ID: {asset_id}\n"
                        if page_idx is not None:
                            section_info += f"Page: {int(page_idx) + 1}\n"
                        section_info += f"{'='*80}\n"
                        section_info += text.strip()
                        section_info += f"\n{'='*80}\n"

                        vision_texts.append(section_info)
                        print(
                            f"✅ 提取到Vision-to-Text内容 #{i} (长度: {len(text)} 字符)")

                if vision_texts:
                    print(f"\n{'='*80}")
                    print("Vision-to-Text完整内容:")
                    print("="*80)
                    print("\n".join(vision_texts))
                    print(f"\n{'='*80}")
                    print(f"总计: {len(vision_texts)} 个Vision-to-Text片段")
                    separator = '=' * 80
                    total_chars = sum(
                        len(t.split(separator)[-2]) if separator in t else len(t) for t in vision_texts)
                    print(f"总字符数: {total_chars}")

                    # 分析内容中是否包含连接关系描述
                    all_text = "\n".join(vision_texts)
                    connection_keywords = [
                        "连接", "通过", "连接到", "连接至", "连接关系", "电气连接", "接线", "通过...连接"]
                    found_connections = []
                    for keyword in connection_keywords:
                        if keyword in all_text:
                            found_connections.append(keyword)

                    if found_connections:
                        print(f"\n✅ 发现连接关系关键词: {', '.join(found_connections)}")
                        print("   这些关键词应该能被知识图谱提取为连接关系")
                    else:
                        print(f"\n⚠️  未发现明显的连接关系关键词")
                        print("   这可能是知识图谱没有连接关系的原因")
                        print("   建议检查Vision-to-Text的prompt是否包含连接关系描述")
                else:
                    print("\n⚠️  未找到Vision-to-Text文本内容")
                    print("\n💡 可能原因:")
                    print("   - Vision索引数据格式不正确")
                    print("   - 向量数据库中的metadata不匹配")
                    print("   - Vision索引已完成但内容为空")

            except Exception as e:
                print(f"❌ 解析索引数据失败: {e}")
                import traceback
                traceback.print_exc()

        break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="检查文档的Vision-to-Text文本内容")
    parser.add_argument(
        "document_name",
        nargs="?",
        default="颍州变接线图",
        help="文档名称或名称的一部分(支持模糊匹配)"
    )
    args = parser.parse_args()

    try:
        check_vision_text_by_name(args.document_name)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
