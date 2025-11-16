#!/usr/bin/env python3
"""
检查文档的向量索引和知识图谱索引状态
用于检查docker中"主接线.png"的向量和graph运行状态
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_, desc
    from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus, Collection
    from aperag.config import get_sync_session
    from aperag.schema.utils import parseCollectionConfig
    import json
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def check_document_vector_graph_status(document_name_pattern: str):
    """检查文档的向量索引和知识图谱索引状态"""

    print("=" * 80)
    print("文档向量索引和知识图谱索引状态检查工具")
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
            print("\n💡 提示: 如果在本地运行失败，请在Docker容器中运行:")
            print(
                f"   docker exec aperag-celeryworker python check_vector_graph_status.py '{document_name_pattern}'")
            return

        for doc in documents:
            print(f"\n{'='*80}")
            print(f"📄 文档信息")
            print(f"{'='*80}")
            print(f"文档名称: {doc.name}")
            print(f"文档ID: {doc.id}")
            print(f"文档状态: {doc.status}")
            print(f"所属Collection ID: {doc.collection_id}")
            print(f"文件大小: {doc.size} bytes")
            print(f"创建时间: {doc.gmt_created}")
            print(f"更新时间: {doc.gmt_updated}")
            print(f"-" * 80)

            # 查询Collection配置
            collection_stmt = select(Collection).where(
                Collection.id == doc.collection_id)
            collection_result = session.execute(collection_stmt)
            collection = collection_result.scalar_one_or_none()

            if collection:
                print(f"\n📚 Collection信息:")
                print(f"  Collection名称: {collection.title}")
                print(f"  Collection状态: {collection.status}")

                # 检查索引配置
                try:
                    config = parseCollectionConfig(collection.config)
                    enable_vector = config.enable_vector if hasattr(
                        config, 'enable_vector') else False
                    enable_kg = config.enable_knowledge_graph if hasattr(
                        config, 'enable_knowledge_graph') else False
                    print(f"  向量索引启用: {'✅ 已启用' if enable_vector else '❌ 未启用'}")
                    print(f"  知识图谱启用: {'✅ 已启用' if enable_kg else '❌ 未启用'}")

                    if hasattr(config, 'knowledge_graph_config'):
                        kg_config = config.knowledge_graph_config
                        print(f"  知识图谱配置:")
                        if hasattr(kg_config, 'language'):
                            print(f"    - 语言: {kg_config.language}")
                        if hasattr(kg_config, 'entity_types'):
                            print(f"    - 实体类型: {kg_config.entity_types}")
                except Exception as e:
                    print(f"  ⚠️  解析Collection配置失败: {e}")
                    print(f"  原始配置: {collection.config}")
            else:
                print(f"\n⚠️  未找到Collection: {doc.collection_id}")

            # 查询所有索引状态
            index_stmt = select(DocumentIndex).where(
                DocumentIndex.document_id == doc.id
            )
            index_result = session.execute(index_stmt)
            indexes = index_result.scalars().all()

            if not indexes:
                print("\n⚠️  未找到任何索引记录")
                continue

            print("\n" + "=" * 80)
            print("📊 索引状态详情")
            print("=" * 80)

            vector_index = None
            graph_index = None

            for idx in indexes:
                status_icon = {
                    DocumentIndexStatus.PENDING: "⏳",
                    DocumentIndexStatus.CREATING: "🔄",
                    DocumentIndexStatus.ACTIVE: "✅",
                    DocumentIndexStatus.FAILED: "❌",
                    DocumentIndexStatus.DELETION_IN_PROGRESS: "🗑️",
                }.get(idx.status, "❓")
                # 处理SKIPPED状态（字符串值，不在枚举中）
                if idx.status.value == "SKIPPED" if hasattr(idx.status, 'value') else str(idx.status) == "SKIPPED":
                    status_icon = "⏭️"

                index_type_str = idx.index_type.value if hasattr(idx.index_type, 'value') else str(idx.index_type)
                status_str = idx.status.value if hasattr(idx.status, 'value') else str(idx.status)
                print(f"\n  {status_icon} {index_type_str} 索引:")
                print(f"     状态: {status_str}")
                print(f"     版本: {idx.version} (已处理: {idx.observed_version})")
                print(f"     创建时间: {idx.gmt_created}")
                print(f"     更新时间: {idx.gmt_updated}")
                if idx.gmt_last_reconciled:
                    print(f"     最后协调时间: {idx.gmt_last_reconciled}")

                if idx.error_message:
                    print(f"     ❌ 错误信息:")
                    print(f"        {idx.error_message}")

                # 保存向量和graph索引引用
                if idx.index_type == DocumentIndexType.VECTOR:
                    vector_index = idx
                    if idx.index_data:
                        try:
                            data = json.loads(idx.index_data)
                            print(f"     📊 向量索引数据摘要:")
                            if "chunks_created" in data:
                                print(
                                    f"        - 块数量: {data['chunks_created']}")
                            if "context_ids" in data:
                                ctx_ids = data.get("context_ids", [])
                                print(f"        - 向量数量: {len(ctx_ids)}")
                                if ctx_ids:
                                    print(f"        - 前5个向量ID: {ctx_ids[:5]}")
                        except:
                            print(
                                f"     📊 索引数据: {str(idx.index_data)[:200]}...")

                elif idx.index_type == DocumentIndexType.GRAPH:
                    graph_index = idx
                    if idx.index_data:
                        try:
                            data = json.loads(idx.index_data)
                            print(f"     📊 知识图谱数据摘要:")
                            if "chunks_created" in data:
                                print(
                                    f"        - 块数量: {data['chunks_created']}")
                            if "entities_extracted" in data:
                                print(
                                    f"        - 实体数量: {data['entities_extracted']}")
                            if "relations_extracted" in data:
                                print(
                                    f"        - 关系数量: {data['relations_extracted']}")
                            if "status" in data:
                                print(f"        - 处理状态: {data['status']}")
                        except:
                            print(
                                f"     📊 索引数据: {str(idx.index_data)[:200]}...")

            # 诊断结果
            print(f"\n{'='*80}")
            print("🔍 诊断结果")
            print("=" * 80)

            # 向量索引诊断
            print("\n📌 向量索引状态:")
            if not collection:
                print("   ❌ Collection不存在，无法创建向量索引")
            elif not enable_vector:
                print("   ❌ 向量索引未启用")
            elif not vector_index:
                print("   ❌ 未找到VECTOR索引记录")
                print("   💡 可能原因:")
                print("      - 索引创建任务尚未执行")
                print("      - 索引创建失败但未记录错误")
            else:
                if vector_index.status == DocumentIndexStatus.FAILED:
                    print(f"   ❌ 向量索引创建失败")
                    print(f"      错误: {vector_index.error_message}")
                elif vector_index.status == DocumentIndexStatus.PENDING:
                    print(f"   ⏳ 向量索引等待处理中")
                    print(
                        f"      version={vector_index.version}, observed={vector_index.observed_version}")
                elif vector_index.status == DocumentIndexStatus.CREATING:
                    print(f"   🔄 向量索引正在创建中")
                elif vector_index.status == DocumentIndexStatus.ACTIVE:
                    print(f"   ✅ 向量索引已成功创建")
                elif (hasattr(vector_index.status, 'value') and vector_index.status.value == "SKIPPED") or str(vector_index.status) == "SKIPPED":
                    print(f"   ⏭️  向量索引被跳过")
                    print(f"      原因: {vector_index.error_message or '未知'}")

            # 知识图谱索引诊断
            print("\n📌 知识图谱索引状态:")
            if not collection:
                print("   ❌ Collection不存在，无法创建知识图谱")
            elif not enable_kg:
                print("   ❌ 知识图谱未启用")
            elif not graph_index:
                print("   ❌ 未找到GRAPH索引记录")
                print("   💡 可能原因:")
                print("      - 索引创建任务尚未执行")
                print("      - 索引创建失败但未记录错误")
            else:
                if graph_index.status == DocumentIndexStatus.FAILED:
                    print(f"   ❌ 知识图谱索引创建失败")
                    print(f"      错误: {graph_index.error_message}")
                elif graph_index.status == DocumentIndexStatus.PENDING:
                    print(f"   ⏳ 知识图谱索引等待处理中")
                    print(
                        f"      version={graph_index.version}, observed={graph_index.observed_version}")
                elif graph_index.status == DocumentIndexStatus.CREATING:
                    print(f"   🔄 知识图谱索引正在创建中")
                elif graph_index.status == DocumentIndexStatus.ACTIVE:
                    print(f"   ✅ 知识图谱索引已成功创建")
                elif (hasattr(graph_index.status, 'value') and graph_index.status.value == "SKIPPED") or str(graph_index.status) == "SKIPPED":
                    print(f"   ⏭️  知识图谱索引被跳过")
                    print(f"      原因: {graph_index.error_message or '未知'}")

            # 解决方案建议
            print(f"\n{'='*80}")
            print("💡 解决方案建议")
            print("=" * 80)

            if vector_index and vector_index.status == DocumentIndexStatus.PENDING:
                print("\n📌 向量索引处于PENDING状态:")
                print("   1. 检查Celery Worker是否运行:")
                print("      docker ps | grep celeryworker")
                print("   2. 检查Celery Beat是否运行:")
                print("      docker ps | grep celerybeat")
                print("   3. 手动触发reconciliation:")
                print("      docker exec aperag-celeryworker python -c \\")
                print(
                    "        'from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()'")
                print("   4. 查看Celery日志:")
                print(
                    "      docker logs aperag-celeryworker --tail 200 | grep -i 'vector\\|reconcile'")

            if graph_index and graph_index.status == DocumentIndexStatus.PENDING:
                print("\n📌 知识图谱索引处于PENDING状态:")
                print("   1. 检查Celery Worker是否运行")
                print("   2. 检查LLM服务配置（用于实体和关系提取）")
                print("   3. 检查图数据库连接（如果使用Neo4j/NebulaGraph）")
                print("   4. 手动触发reconciliation（同上）")
                print("   5. 查看Celery日志:")
                print(
                    "      docker logs aperag-celeryworker --tail 200 | grep -i 'graph\\|reconcile'")

            if vector_index and vector_index.status == DocumentIndexStatus.FAILED:
                print("\n📌 向量索引创建失败:")
                print("   1. 检查向量数据库连接")
                print("   2. 检查embedding服务配置")
                print("   3. 查看详细错误信息（见上方）")
                print("   4. 通过API或Web界面重建向量索引")

            if graph_index and graph_index.status == DocumentIndexStatus.FAILED:
                print("\n📌 知识图谱索引创建失败:")
                print("   1. 检查LLM服务配置（用于实体和关系提取）")
                print("   2. 检查图数据库连接")
                print("   3. 查看详细错误信息（见上方）")
                print("   4. 通过API或Web界面重建GRAPH索引")

            if (vector_index and vector_index.status == DocumentIndexStatus.ACTIVE) and \
               (graph_index and graph_index.status == DocumentIndexStatus.ACTIVE):
                print("\n✅ 向量索引和知识图谱索引都已成功创建！")

            print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="检查文档的向量索引和知识图谱索引状态")
    parser.add_argument(
        "document_name",
        nargs="?",
        default="主接线.png",
        help="文档名称或名称的一部分(支持模糊匹配)"
    )

    args = parser.parse_args()

    try:
        check_document_vector_graph_status(args.document_name)
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
