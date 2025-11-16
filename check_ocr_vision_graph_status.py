#!/usr/bin/env python3
"""
检查docker中"主接线.png"通过OCR和visiontotext构建知识图谱的运行状态
综合检查OCR、Vision索引和Graph索引的状态
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_, desc
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
        Collection,
    )
    from aperag.config import get_sync_session
    from aperag.schema.utils import parseCollectionConfig
    from aperag.utils.utils import generate_vector_db_collection_name
    from aperag.config import get_vector_db_connector
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def find_document_by_name(document_name: str):
    """通过文件名查找文档"""
    for session in get_sync_session():
        # 尝试精确匹配
        stmt = select(Document).where(Document.name ==
                                      document_name).order_by(desc(Document.gmt_created))
        result = session.execute(stmt)
        documents = result.scalars().all()

        if not documents:
            # 尝试模糊匹配
            stmt = select(Document).where(
                Document.name.like(f"%{document_name}%")
            ).order_by(desc(Document.gmt_created))
            result = session.execute(stmt)
            documents = result.scalars().all()

        if len(documents) == 0:
            return None
        elif len(documents) == 1:
            return documents[0]
        else:
            print(f"\n⚠️  找到 {len(documents)} 个匹配的文档:")
            for i, doc in enumerate(documents, 1):
                print(
                    f"   {i}. {doc.name} (ID: {doc.id}, 状态: {doc.status}, 创建时间: {doc.gmt_created})")
            print("\n使用最新的文档")
            return documents[0]


def check_ocr_status(document_id: str):
    """检查OCR处理状态"""
    print(f"\n{'='*80}")
    print("🔍 OCR处理状态检查")
    print("="*80)

    for session in get_sync_session():
        # 查询文档的解析内容（通过VECTOR索引查看OCR结果）
        vector_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.VECTOR
                )
            )
        ).scalar_one_or_none()

        if vector_index and vector_index.index_data:
            try:
                index_data = json.loads(vector_index.index_data)
                chunks_created = index_data.get("chunks_created", 0)
                print(f"\n✅ 向量索引已创建，包含 {chunks_created} 个文本块")

                # 尝试从向量存储中获取OCR文本内容
                doc = session.execute(
                    select(Document).where(Document.id == document_id)
                ).scalar_one_or_none()

                if doc:
                    collection = session.execute(
                        select(Collection).where(
                            Collection.id == doc.collection_id)
                    ).scalar_one_or_none()

                    if collection and chunks_created > 0:
                        try:
                            collection_name = generate_vector_db_collection_name(
                                collection_id=collection.id
                            )
                            vector_store = get_vector_db_connector(
                                collection=collection_name)
                            qdrant_client = vector_store.connector.client

                            ctx_ids = index_data.get("context_ids", [])
                            if ctx_ids:
                                points = qdrant_client.retrieve(
                                    collection_name=collection_name,
                                    ids=ctx_ids[:3],  # 只取前3个
                                    with_payload=True,
                                )

                                ocr_text_found = False
                                for point in points:
                                    if point.payload:
                                        # 检查_node_content中的文本
                                        node_content = point.payload.get(
                                            "_node_content")
                                        if node_content:
                                            try:
                                                payload_data = json.loads(
                                                    node_content)
                                                text = payload_data.get(
                                                    "text", "")
                                                if text:
                                                    ocr_text_found = True
                                                    print(
                                                        f"\n📝 OCR文本预览（前500字符）:")
                                                    print(
                                                        f"   {text[:500]}...")
                                                    print(
                                                        f"\n   文本总长度: {len(text)} 字符")
                                                    break
                                            except:
                                                pass

                                        # 检查直接text字段
                                        text = point.payload.get("text", "")
                                        if text:
                                            ocr_text_found = True
                                            print(f"\n📝 OCR文本预览（前500字符）:")
                                            print(f"   {text[:500]}...")
                                            print(
                                                f"\n   文本总长度: {len(text)} 字符")
                                            break

                                if not ocr_text_found:
                                    print("\n⚠️  未在向量存储中找到OCR文本内容")
                                    print("   可能原因:")
                                    print("   - OCR处理失败")
                                    print("   - 文本内容为空")
                        except Exception as e:
                            print(f"\n⚠️  无法从向量存储获取OCR内容: {e}")
            except Exception as e:
                print(f"\n⚠️  解析向量索引数据失败: {e}")
        else:
            print("\n⚠️  向量索引尚未创建或数据为空")
            print("   可能原因:")
            print("   - OCR处理尚未完成")
            print("   - 向量索引创建失败")

        break


def check_vision_index_status(document_id: str):
    """检查Vision索引状态（visiontotext处理）"""
    print(f"\n{'='*80}")
    print("👁️  Vision索引状态检查（Vision-to-Text）")
    print("="*80)

    for session in get_sync_session():
        vision_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.VISION
                )
            )
        ).scalar_one_or_none()

        if not vision_index:
            print("\n❌ 未找到VISION索引记录")
            print("   可能原因:")
            print("   - Vision索引尚未创建")
            print("   - Vision索引创建失败但未记录")
            return

        status_icon_map = {
            DocumentIndexStatus.PENDING: "⏳",
            DocumentIndexStatus.CREATING: "🔄",
            DocumentIndexStatus.ACTIVE: "✅",
            DocumentIndexStatus.FAILED: "❌",
        }
        try:
            status_icon_map[DocumentIndexStatus.SKIPPED] = "⏭️"
        except AttributeError:
            pass

        status_str = vision_index.status.value if hasattr(
            vision_index.status, 'value') else str(vision_index.status)
        status_icon = status_icon_map.get(vision_index.status, "❓")

        print(f"\n{status_icon} 状态: {status_str}")
        print(
            f"   版本: {vision_index.version} (已处理: {vision_index.observed_version})")
        print(f"   创建时间: {vision_index.gmt_created}")
        print(f"   更新时间: {vision_index.gmt_updated}")

        if vision_index.error_message:
            print(f"\n❌ 错误信息:")
            print(f"   {vision_index.error_message}")

        # 检查Vision索引内容
        if vision_index.index_data:
            try:
                index_data = json.loads(vision_index.index_data)
                ctx_ids = index_data.get("context_ids", [])
                print(f"\n📊 Vision索引数据摘要:")
                print(f"   - Context IDs数量: {len(ctx_ids)}")

                if ctx_ids and vision_index.status == DocumentIndexStatus.ACTIVE:
                    # 尝试获取vision-to-text内容
                    doc = session.execute(
                        select(Document).where(Document.id == document_id)
                    ).scalar_one_or_none()

                    if doc:
                        collection = session.execute(
                            select(Collection).where(
                                Collection.id == doc.collection_id)
                        ).scalar_one_or_none()

                        if collection:
                            try:
                                collection_name = generate_vector_db_collection_name(
                                    collection_id=collection.id
                                )
                                vector_store = get_vector_db_connector(
                                    collection=collection_name)
                                qdrant_client = vector_store.connector.client

                                points = qdrant_client.retrieve(
                                    collection_name=collection_name,
                                    ids=ctx_ids[:1],  # 只取第一个
                                    with_payload=True,
                                )

                                if points:
                                    point = points[0]
                                    if point.payload:
                                        node_content = point.payload.get(
                                            "_node_content")
                                        if node_content:
                                            try:
                                                payload_data = json.loads(
                                                    node_content)
                                                text = payload_data.get(
                                                    "text", "")
                                                if text:
                                                    print(
                                                        f"\n📝 Vision-to-Text内容预览（前500字符）:")
                                                    print(
                                                        f"   {text[:500]}...")
                                                    print(
                                                        f"\n   内容总长度: {len(text)} 字符")
                                            except:
                                                pass
                            except Exception as e:
                                print(f"\n⚠️  无法从向量存储获取Vision内容: {e}")
            except Exception as e:
                print(f"\n⚠️  解析Vision索引数据失败: {e}")

        break


def check_graph_index_status(document_id: str):
    """检查Graph索引状态（知识图谱构建）"""
    print(f"\n{'='*80}")
    print("🕸️  知识图谱索引状态检查")
    print("="*80)

    for session in get_sync_session():
        graph_index = session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType.GRAPH
                )
            )
        ).scalar_one_or_none()

        if not graph_index:
            print("\n❌ 未找到GRAPH索引记录")
            print("   可能原因:")
            print("   - 知识图谱索引尚未创建")
            print("   - 知识图谱索引创建失败但未记录")
            return

        status_icon_map = {
            DocumentIndexStatus.PENDING: "⏳",
            DocumentIndexStatus.CREATING: "🔄",
            DocumentIndexStatus.ACTIVE: "✅",
            DocumentIndexStatus.FAILED: "❌",
        }
        try:
            status_icon_map[DocumentIndexStatus.SKIPPED] = "⏭️"
        except AttributeError:
            pass

        status_str = graph_index.status.value if hasattr(
            graph_index.status, 'value') else str(graph_index.status)
        status_icon = status_icon_map.get(graph_index.status, "❓")

        print(f"\n{status_icon} 状态: {status_str}")
        print(
            f"   版本: {graph_index.version} (已处理: {graph_index.observed_version})")
        print(f"   创建时间: {graph_index.gmt_created}")
        print(f"   更新时间: {graph_index.gmt_updated}")
        if graph_index.gmt_last_reconciled:
            print(f"   最后协调时间: {graph_index.gmt_last_reconciled}")

        if graph_index.error_message:
            print(f"\n❌ 错误信息:")
            print(f"   {graph_index.error_message}")

        # 检查Graph索引数据
        if graph_index.index_data:
            try:
                index_data = json.loads(graph_index.index_data)
                print(f"\n📊 知识图谱数据摘要:")

                chunks_created = index_data.get("chunks_created", 0)
                entities_extracted = index_data.get("entities_extracted", 0)
                relations_extracted = index_data.get("relations_extracted", 0)

                print(f"   - 文本块数量: {chunks_created}")
                print(f"   - 实体数量: {entities_extracted}")
                print(f"   - 关系数量: {relations_extracted}")

                if graph_index.status == DocumentIndexStatus.ACTIVE:
                    if entities_extracted == 0 and relations_extracted == 0:
                        print(f"\n⚠️  警告: 知识图谱已创建，但未提取到实体和关系")
                        print("   可能原因:")
                        print("   - OCR和Vision-to-Text内容为空或质量不佳")
                        print("   - LLM无法从内容中提取实体和关系")
                        print("   - 内容格式不符合知识图谱提取要求")
                    else:
                        print(f"\n✅ 知识图谱构建成功!")
                        print(
                            f"   已提取 {entities_extracted} 个实体和 {relations_extracted} 个关系")
            except Exception as e:
                print(f"\n⚠️  解析Graph索引数据失败: {e}")

        break


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="检查docker中图片文件通过OCR和visiontotext构建知识图谱的运行状态"
    )
    parser.add_argument(
        "--document-name",
        type=str,
        default="主接线.png",
        help="文档名称（默认: 主接线.png）"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("OCR和Vision-to-Text知识图谱构建状态检查工具")
    print("=" * 80)
    print(f"\n查找文档: {args.document_name}\n")

    try:
        # 1. 查找文档
        document = find_document_by_name(args.document_name)

        if not document:
            print(f"❌ 未找到文档: {args.document_name}")
            print("\n💡 提示: 如果在本地运行失败，请在Docker容器中运行:")
            print(
                f"   docker exec aperag-celeryworker python check_ocr_vision_graph_status.py --document-name '{args.document_name}'")
            sys.exit(1)

        print(f"\n{'='*80}")
        print("📄 文档信息")
        print("="*80)
        print(f"文档名称: {document.name}")
        print(f"文档ID: {document.id}")
        print(f"文档状态: {document.status}")
        print(f"文件大小: {document.size} bytes")
        print(f"创建时间: {document.gmt_created}")
        print(f"更新时间: {document.gmt_updated}")

        # 计算更新时间距离现在的时间
        if document.gmt_updated:
            now = datetime.now(timezone.utc)
            elapsed = now - document.gmt_updated.replace(
                tzinfo=timezone.utc) if document.gmt_updated.tzinfo is None else now - document.gmt_updated
            print(
                f"距离现在: {elapsed.total_seconds():.0f} 秒 ({elapsed.total_seconds()/60:.1f} 分钟)")

        # 查询Collection信息
        for session in get_sync_session():
            collection = session.execute(
                select(Collection).where(
                    Collection.id == document.collection_id)
            ).scalar_one_or_none()

            if collection:
                print(f"\n📚 Collection信息:")
                print(f"   ID: {collection.id}")
                print(f"   标题: {collection.title}")
                print(f"   状态: {collection.status}")

                # 检查配置
                try:
                    config = parseCollectionConfig(collection.config)
                    enable_kg = getattr(
                        config, 'enable_knowledge_graph', False)
                    enable_vision = getattr(config, 'enable_vision', False)
                    print(f"   知识图谱启用: {'✅ 已启用' if enable_kg else '❌ 未启用'}")
                    print(
                        f"   Vision索引启用: {'✅ 已启用' if enable_vision else '❌ 未启用'}")
                except Exception as e:
                    print(f"   ⚠️  解析配置失败: {e}")
            break

        # 2. 检查OCR状态
        check_ocr_status(document.id)

        # 3. 检查Vision索引状态
        check_vision_index_status(document.id)

        # 4. 检查Graph索引状态
        check_graph_index_status(document.id)

        # 5. 综合诊断
        print(f"\n{'='*80}")
        print("🔍 综合诊断")
        print("="*80)

        for session in get_sync_session():
            # 获取所有索引状态
            indexes = session.execute(
                select(DocumentIndex).where(
                    DocumentIndex.document_id == document.id
                )
            ).scalars().all()

            vision_index = None
            graph_index = None
            vector_index = None

            for idx in indexes:
                if idx.index_type == DocumentIndexType.VISION:
                    vision_index = idx
                elif idx.index_type == DocumentIndexType.GRAPH:
                    graph_index = idx
                elif idx.index_type == DocumentIndexType.VECTOR:
                    vector_index = idx

            print("\n📋 处理流程状态:")

            # OCR状态
            if vector_index:
                vector_status = vector_index.status.value if hasattr(
                    vector_index.status, 'value') else str(vector_index.status)
                print(f"   1. OCR处理 (VECTOR索引): {vector_status}")
            else:
                print(f"   1. OCR处理 (VECTOR索引): ❌ 未创建")

            # Vision-to-Text状态
            if vision_index:
                vision_status = vision_index.status.value if hasattr(
                    vision_index.status, 'value') else str(vision_index.status)
                print(f"   2. Vision-to-Text处理 (VISION索引): {vision_status}")
            else:
                print(f"   2. Vision-to-Text处理 (VISION索引): ❌ 未创建")

            # 知识图谱状态
            if graph_index:
                graph_status = graph_index.status.value if hasattr(
                    graph_index.status, 'value') else str(graph_index.status)
                print(f"   3. 知识图谱构建 (GRAPH索引): {graph_status}")
            else:
                print(f"   3. 知识图谱构建 (GRAPH索引): ❌ 未创建")

            # 诊断建议
            print("\n💡 诊断建议:")

            if not vector_index or vector_index.status != DocumentIndexStatus.ACTIVE:
                print("   ⚠️  OCR处理未完成，请检查:")
                print("      - PaddleOCR服务是否运行")
                print(
                    "      - 查看日志: docker logs aperag-celeryworker --tail 200 | grep -i 'ocr\\|image'")

            if not vision_index or vision_index.status != DocumentIndexStatus.ACTIVE:
                print("   ⚠️  Vision-to-Text处理未完成，请检查:")
                print("      - Vision模型配置是否正确")
                print(
                    "      - 查看日志: docker logs aperag-celeryworker --tail 200 | grep -i 'vision'")

            if not graph_index or graph_index.status != DocumentIndexStatus.ACTIVE:
                print("   ⚠️  知识图谱构建未完成，请检查:")
                print("      - 知识图谱是否已启用")
                print("      - LLM服务配置是否正确")
                print(
                    "      - 查看日志: docker logs aperag-celeryworker --tail 200 | grep -i 'graph\\|entity\\|relation'")

            if (vector_index and vector_index.status == DocumentIndexStatus.ACTIVE) and \
               (vision_index and vision_index.status == DocumentIndexStatus.ACTIVE) and \
               (graph_index and graph_index.status == DocumentIndexStatus.ACTIVE):
                print("   ✅ 所有处理流程已完成!")

                # 检查知识图谱是否有实际内容
                if graph_index.index_data:
                    try:
                        index_data = json.loads(graph_index.index_data)
                        entities = index_data.get("entities_extracted", 0)
                        relations = index_data.get("relations_extracted", 0)
                        if entities == 0 and relations == 0:
                            print("   ⚠️  但知识图谱中未提取到实体和关系，可能需要:")
                            print("      - 检查OCR和Vision-to-Text的内容质量")
                            print("      - 调整知识图谱提取的prompt")
                    except:
                        pass

            break

        print(f"\n{'='*80}")
        print("✅ 检查完成")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
