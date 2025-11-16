#!/usr/bin/env python3
"""
查看OCR文本和Vision-to-Text合并后的内容
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_
    from aperag.db.models import Document, DocumentIndex, DocumentIndexType, Collection
    from aperag.config import get_sync_session
    from aperag.utils.utils import generate_vector_db_collection_name
    from aperag.config import get_vector_db_connector
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)


def view_merged_content(document_id: str):
    """查看OCR和Vision-to-Text合并后的内容"""

    print("=" * 80)
    print("OCR文本与Vision-to-Text内容合并查看工具")
    print("=" * 80)
    print(f"\n文档ID: {document_id}\n")

    for session in get_sync_session():
        # 1. 获取文档信息
        doc = session.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

        if not doc:
            print("❌ 文档不存在")
            return

        collection = session.execute(
            select(Collection).where(Collection.id == doc.collection_id)
        ).scalar_one_or_none()

        if not collection:
            print("❌ Collection不存在")
            return

        print(f"📄 文档信息:")
        print(f"   名称: {doc.name}")
        print(f"   Collection: {collection.title}")
        print(f"   创建时间: {doc.gmt_created}")

        # 2. 获取向量索引（包含OCR文本）
        vector_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.VECTOR
                )
            )
        ).scalar_one_or_none()

        # 3. 获取Vision索引
        vision_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.VISION
                )
            )
        ).scalar_one_or_none()

        collection_name = generate_vector_db_collection_name(
            collection_id=collection.id
        )
        vector_store = get_vector_db_connector(collection=collection_name)
        qdrant_client = vector_store.connector.client

        # 4. 显示OCR文本（从向量索引）
        print(f"\n{'='*80}")
        print("📝 OCR文本内容（如果启用）")
        print("="*80)

        ocr_found = False
        if vector_index and vector_index.index_data:
            try:
                index_data = json.loads(vector_index.index_data)
                ctx_ids = index_data.get("context_ids", [])

                if ctx_ids:
                    points = qdrant_client.retrieve(
                        collection_name=collection_name,
                        ids=ctx_ids[:5],  # 只取前5个
                        with_payload=True,
                    )

                    for point in points:
                        if point.payload:
                            # 检查是否是OCR文本
                            node_content = point.payload.get("_node_content")
                            if node_content:
                                try:
                                    payload_data = json.loads(node_content)
                                    metadata = payload_data.get("metadata", {})

                                    # OCR文本的标识：source == "ocr"
                                    if metadata.get("source") == "ocr":
                                        ocr_found = True
                                        text = payload_data.get("text", "")
                                        print(f"\n✅ 找到OCR文本:")
                                        print(
                                            f"   来源: {metadata.get('ocr_method', 'unknown')}")
                                        print(f"   长度: {len(text)} 字符")
                                        print(f"\n   内容预览:")
                                        print(f"   {'-'*76}")
                                        # 显示前1000字符
                                        preview = text[:1000]
                                        for line in preview.split('\n'):
                                            print(f"   {line}")
                                        if len(text) > 1000:
                                            print(
                                                f"   ... (还有 {len(text) - 1000} 字符)")
                                        print(f"   {'-'*76}")
                                        break
                                except:
                                    pass
            except Exception as e:
                print(f"⚠️  获取OCR文本失败: {e}")

        if not ocr_found:
            print("\n⚠️  未找到OCR文本")
            print("   可能原因:")
            print("   - OCR未启用（OCR_ENABLED=False）")
            print("   - OCR处理失败")
            print("   - 向量索引尚未创建")

        # 5. 显示Vision-to-Text内容
        print(f"\n{'='*80}")
        print("👁️  Vision-to-Text内容")
        print("="*80)

        vision_found = False
        if vision_index and vision_index.index_data:
            try:
                index_data = json.loads(vision_index.index_data)
                ctx_ids = index_data.get("context_ids", [])

                if ctx_ids:
                    points = qdrant_client.retrieve(
                        collection_name=collection_name,
                        ids=ctx_ids,
                        with_payload=True,
                    )

                    print(f"\n✅ 找到 {len(points)} 个Vision-to-Text chunks\n")

                    for i, point in enumerate(points, 1):
                        if point.payload:
                            node_content = point.payload.get("_node_content")
                            if node_content:
                                try:
                                    payload_data = json.loads(node_content)
                                    metadata = payload_data.get("metadata", {})

                                    # Vision-to-Text的标识：index_method == "vision_to_text"
                                    if metadata.get("index_method") == "vision_to_text":
                                        vision_found = True
                                        text = payload_data.get("text", "")
                                        asset_id = metadata.get("asset_id", "")

                                        print(f"{'='*80}")
                                        print(f"Chunk {i}/{len(points)}")
                                        print(f"{'='*80}")
                                        print(f"Asset ID: {asset_id}")
                                        print(f"内容长度: {len(text)} 字符")
                                        print(f"\n内容:")
                                        print(f"{'-'*76}")
                                        # 显示完整内容
                                        for line in text.split('\n'):
                                            print(f"   {line}")
                                        print(f"{'-'*76}\n")
                                except Exception as e:
                                    print(f"⚠️  解析chunk {i}失败: {e}")
            except Exception as e:
                print(f"⚠️  获取Vision-to-Text失败: {e}")

        if not vision_found:
            print("\n⚠️  未找到Vision-to-Text内容")
            print("   可能原因:")
            print("   - Vision索引尚未创建")
            print("   - Vision索引创建失败")
            print("   - Vision模型未配置")

        # 6. 显示合并后的内容结构
        print(f"\n{'='*80}")
        print("🔗 合并后的内容结构")
        print("="*80)

        if ocr_found and vision_found:
            print("\n✅ 完整合并内容结构:")
            print("""
------ OCR Text ------
[OCR提取的原始文本内容]

------ Vision Analysis (Asset: file.png) ------
[Vision-to-Text生成的详细分析内容]
            """)
            print("💡 说明:")
            print("   - OCR文本提供原始的文字识别结果")
            print("   - Vision-to-Text提供结构化的深度分析")
            print("   - 两者合并后用于知识图谱构建")
        elif vision_found:
            print("\n✅ 当前内容结构（仅Vision-to-Text）:")
            print("""
------ Vision Analysis (Asset: file.png) ------
[Vision-to-Text生成的详细分析内容]
            """)
            print("💡 说明:")
            print("   - OCR未启用，仅使用Vision-to-Text内容")
            print("   - Vision-to-Text内容用于知识图谱构建")
        elif ocr_found:
            print("\n⚠️  仅OCR文本可用:")
            print("   - Vision索引尚未创建或失败")
            print("   - 建议等待Vision索引创建完成")
        else:
            print("\n❌ 无可用内容")
            print("   - 请检查索引创建状态")

        # 7. 显示知识图谱摘要
        graph_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.GRAPH
                )
            )
        ).scalar_one_or_none()

        if graph_index and graph_index.index_data:
            try:
                index_data = json.loads(graph_index.index_data)
                entities = index_data.get("entities_extracted", 0)
                relations = index_data.get("relations_extracted", 0)
                chunks = index_data.get("chunks_created", 0)

                print(f"\n{'='*80}")
                print("🕸️  知识图谱摘要（基于合并内容构建）")
                print("="*80)
                print(f"\n   文本块数量: {chunks}")
                print(f"   实体数量: {entities}")
                print(f"   关系数量: {relations}")

                if entities > 0 or relations > 0:
                    print(f"\n   ✅ 知识图谱已成功从合并内容中提取实体和关系")
                else:
                    print(f"\n   ⚠️  知识图谱中未提取到实体和关系")
            except:
                pass

        break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="查看OCR文本和Vision-to-Text合并后的内容"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        required=True,
        help="文档ID"
    )

    args = parser.parse_args()

    try:
        view_merged_content(args.document_id)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
