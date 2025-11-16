#!/usr/bin/env python3
"""
检查文档知识图谱建立状态及产生文本的诊断脚本
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
        Collection,
    )
    from aperag.config import get_sync_session
    from aperag.schema.utils import parseCollectionConfig
    from aperag.graph import lightrag_manager
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def check_document_graph_status(document_id: str):
    """检查文档的知识图谱状态和产生的文本"""

    print("=" * 80)
    print("文档知识图谱状态检查工具")
    print("=" * 80)
    print(f"\n文档ID: {document_id}\n")

    # 1. 查询文档基本信息
    document = None
    collection = None
    graph_index = None

    from aperag.config import get_sync_session

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_result = session.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()

        if not document:
            print(f"❌ 未找到文档: {document_id}")
            return

        print(f"📄 文档信息:")
        print(f"   名称: {document.name}")
        print(f"   状态: {document.status}")
        print(f"   大小: {document.size} bytes")
        print(f"   Collection ID: {document.collection_id}")
        print(f"   创建时间: {document.gmt_created}")
        print(f"   更新时间: {document.gmt_updated}")

        # 查询Collection
        collection_stmt = select(Collection).where(
            Collection.id == document.collection_id)
        collection_result = session.execute(collection_stmt)
        collection = collection_result.scalar_one_or_none()

        if collection:
            print(f"\n📚 Collection信息:")
            print(f"   ID: {collection.id}")
            print(f"   标题: {collection.title}")
            print(f"   状态: {collection.status}")

            # 检查知识图谱配置
            try:
                config = parseCollectionConfig(collection.config)
                enable_kg = getattr(config, 'enable_knowledge_graph', False)
                print(f"   知识图谱启用: {'✅ 已启用' if enable_kg else '❌ 未启用'}")
            except Exception as e:
                print(f"   ⚠️  解析配置失败: {e}")

        # 查询GRAPH索引状态
        graph_index_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.index_type == DocumentIndexType.GRAPH
            )
        )
        graph_index_result = session.execute(graph_index_stmt)
        graph_index = graph_index_result.scalar_one_or_none()

        print(f"\n{'='*80}")
        print("📊 GRAPH索引状态")
        print("="*80)

        if not graph_index:
            print("\n❌ 未找到GRAPH索引记录")
            print("   可能原因:")
            print("   - 索引尚未创建")
            print("   - 索引创建失败但未记录")
            return

        # 安全地获取状态图标
        status_icon_map = {
            DocumentIndexStatus.PENDING: "⏳",
            DocumentIndexStatus.CREATING: "🔄",
            DocumentIndexStatus.ACTIVE: "✅",
            DocumentIndexStatus.FAILED: "❌",
        }
        # 尝试添加SKIPPED（如果存在）
        try:
            status_icon_map[DocumentIndexStatus.SKIPPED] = "⏭️"
        except AttributeError:
            pass

        status_icon = status_icon_map.get(graph_index.status, "❓")

        status_str = graph_index.status.value if hasattr(
            graph_index.status, 'value') else str(graph_index.status)

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

        if graph_index.index_data:
            try:
                index_data = json.loads(graph_index.index_data)
                print(f"\n📊 索引数据摘要:")
                for key, value in index_data.items():
                    if key not in ['context_ids']:  # 跳过context_ids，太长了
                        print(f"   - {key}: {value}")
            except Exception as e:
                print(f"\n⚠️  无法解析索引数据: {e}")
                print(f"   原始数据: {str(graph_index.index_data)[:200]}...")

        # 如果索引是ACTIVE状态，提供查询知识图谱的建议
        if graph_index.status == DocumentIndexStatus.ACTIVE and collection:
            print(f"\n{'='*80}")
            print("🔍 知识图谱数据查询")
            print("="*80)

            print("\n💡 知识图谱已成功创建，可以通过以下方式查看:")
            print(
                f"   1. 通过API查询: GET /api/v1/collections/{collection.id}/knowledge-graph")
            print(f"   2. 通过Web界面查看知识图谱可视化")
            print(f"   3. 查看下面的日志信息了解处理过程")

        break  # 只处理第一个session


def check_celery_logs(document_id: str):
    """检查Celery日志中关于该文档的信息"""
    print(f"\n{'='*80}")
    print("📋 Celery日志检查（需要手动执行）")
    print("="*80)

    print("\n请执行以下命令查看相关日志:")
    print(f"\n1. 查看文档处理日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -i '{document_id}'")

    print(f"\n2. 查看知识图谱相关日志:")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep -i 'graph\\|entity\\|relation'")

    print(f"\n3. 查看最近的错误日志:")
    print(f"   docker logs aperag-celeryworker --tail 200 | grep -i 'error\\|fail\\|exception'")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查文档知识图谱状态和产生的文本")
    parser.add_argument(
        "--document-id",
        type=str,
        required=True,
        help="文档ID"
    )

    args = parser.parse_args()

    try:
        check_document_graph_status(args.document_id)
        check_celery_logs(args.document_id)

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
