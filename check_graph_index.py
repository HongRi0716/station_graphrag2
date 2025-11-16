#!/usr/bin/env python3
"""
诊断脚本：检查特定文档的知识图谱索引状态
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


def check_document_graph_index(document_name_pattern: str):
    """检查文档的知识图谱索引状态"""

    print("=" * 80)
    print("文档知识图谱索引诊断工具")
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

        for doc in documents:
            print(f"\n{'='*80}")
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
                print(f"  Collection名称: {collection.name}")
                print(f"  Collection状态: {collection.status}")

                # 检查知识图谱是否启用
                try:
                    config = parseCollectionConfig(collection.config)
                    enable_kg = config.enable_knowledge_graph if hasattr(
                        config, 'enable_knowledge_graph') else False
                    print(f"  知识图谱启用状态: {'✅ 已启用' if enable_kg else '❌ 未启用'}")

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

            print("\n📊 索引状态详情:")
            graph_index_found = False

            for idx in indexes:
                status_icon = {
                    DocumentIndexStatus.PENDING: "⏳",
                    DocumentIndexStatus.CREATING: "🔄",
                    DocumentIndexStatus.COMPLETED: "✅",
                    DocumentIndexStatus.FAILED: "❌",
                    DocumentIndexStatus.DELETION_IN_PROGRESS: "🗑️",
                    DocumentIndexStatus.SKIPPED: "⏭️"
                }.get(idx.status, "❓")

                print(f"\n  {status_icon} {idx.index_type.value} 索引:")
                print(f"     状态: {idx.status.value}")
                print(f"     版本: {idx.version}")
                print(f"     创建时间: {idx.gmt_created}")
                print(f"     更新时间: {idx.gmt_updated}")

                if idx.index_type == DocumentIndexType.GRAPH:
                    graph_index_found = True
                    if idx.error_message:
                        print(f"     ❌ 错误信息:")
                        print(f"        {idx.error_message}")

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

            # 诊断建议
            print(f"\n{'='*80}")
            print("🔍 诊断结果:")
            print("="*80)

            if not collection:
                print("\n❌ Collection不存在，无法创建知识图谱")
            elif not enable_kg:
                print("\n❌ 知识图谱未启用")
                print("\n💡 解决方案:")
                print("   1. 通过Web界面进入Collection设置")
                print("   2. 启用'知识图谱'选项")
                print("   3. 重新上传文档或重建索引")
            elif not graph_index_found:
                print("\n❌ 未找到GRAPH索引记录")
                print("\n💡 可能原因:")
                print("   - 索引创建任务尚未执行")
                print("   - 索引创建失败但未记录错误")
                print("\n💡 解决方案:")
                print("   1. 检查celery worker日志")
                print("   2. 通过API重建GRAPH索引")
            else:
                graph_idx = next(
                    (idx for idx in indexes if idx.index_type == DocumentIndexType.GRAPH), None)
                if graph_idx:
                    if graph_idx.status == DocumentIndexStatus.FAILED:
                        print(f"\n❌ 知识图谱索引创建失败")
                        print(f"   错误: {graph_idx.error_message}")
                        print("\n💡 解决方案:")
                        print("   1. 检查LLM服务配置（用于实体和关系提取）")
                        print("   2. 检查图数据库连接（如果使用Neo4j/NebulaGraph）")
                        print("   3. 查看celery worker日志获取详细错误")
                        print("   4. 通过API重建GRAPH索引")
                    elif graph_idx.status == DocumentIndexStatus.PENDING:
                        print(f"\n⏳ 知识图谱索引等待处理中")
                        print("\n💡 说明:")
                        print("   - 索引任务已创建，等待celery worker处理")
                        print("   - 通常会在30秒内开始处理")
                    elif graph_idx.status == DocumentIndexStatus.CREATING:
                        print(f"\n🔄 知识图谱索引正在创建中")
                        print("\n💡 说明:")
                        print("   - 索引正在处理，请耐心等待")
                        print("   - 大文档可能需要较长时间")
                    elif graph_idx.status == DocumentIndexStatus.COMPLETED:
                        print(f"\n✅ 知识图谱索引已成功创建")
                        print("\n💡 如果仍看不到知识图谱:")
                        print("   1. 检查前端是否正确加载")
                        print("   2. 检查知识图谱查询API")
                        print("   3. 查看是否有实体和关系数据")
                    elif graph_idx.status == DocumentIndexStatus.SKIPPED:
                        print(f"\n⏭️  知识图谱索引被跳过")
                        print(f"   原因: {graph_idx.error_message or '未知'}")

            print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="检查文档的知识图谱索引状态")
    parser.add_argument(
        "document_name",
        nargs="?",
        default="B5391S-T0102-土建总平面布置图",
        help="文档名称或名称的一部分(支持模糊匹配)"
    )

    args = parser.parse_args()

    try:
        check_document_graph_index(args.document_name)
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
