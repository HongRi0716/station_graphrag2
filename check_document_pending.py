#!/usr/bin/env python3
"""
检查文档解析pending状态的诊断脚本

用于检查为什么文档解析状态一直处于pending
"""

import sys
import os
from datetime import datetime, timezone
from collections import defaultdict

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from aperag.config import get_sync_session
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
        DocumentStatus,
        Collection,
    )
    from aperag.tasks.reconciler import DocumentIndexReconciler
    from aperag.utils.constant import IndexAction
    from sqlalchemy import select, and_, or_, func
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def find_document_by_name(document_name: str):
    """通过文件名查找文档"""
    print("=" * 80)
    print(f"1. 查找文档: {document_name}")
    print("=" * 80)

    for session in get_sync_session():
        # 尝试精确匹配
        stmt = select(Document).where(Document.name == document_name)
        result = session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            # 尝试模糊匹配
            stmt = select(Document).where(
                Document.name.like(f"%{document_name}%"))
            result = session.execute(stmt)
            documents = result.scalars().all()

            if len(documents) == 1:
                document = documents[0]
            elif len(documents) > 1:
                print(f"\n⚠️  找到 {len(documents)} 个匹配的文档:")
                for i, doc in enumerate(documents, 1):
                    print(
                        f"   {i}. {doc.name} (ID: {doc.id}, 状态: {doc.status})")
                print("\n请使用文档ID进行精确查询")
                return None

        if document:
            print(f"\n✅ 找到文档:")
            print(f"   ID: {document.id}")
            print(f"   名称: {document.name}")
            print(f"   状态: {document.status}")
            print(f"   大小: {document.size} bytes")
            print(f"   创建时间: {document.gmt_created}")
            print(f"   更新时间: {document.gmt_updated}")
            return document

    print(f"\n❌ 未找到文档: {document_name}")
    return None


def check_document_indexes(document_id: str):
    """检查文档的所有索引状态"""
    print("\n" + "=" * 80)
    print(f"2. 检查文档索引状态 (Document ID: {document_id})")
    print("=" * 80)

    for session in get_sync_session():
        # 查询所有索引
        stmt = select(DocumentIndex).where(
            DocumentIndex.document_id == document_id)
        result = session.execute(stmt)
        indexes = result.scalars().all()

        if not indexes:
            print("\n❌ 未找到任何索引记录")
            print("   可能原因:")
            print("   - 文档尚未创建索引记录")
            print("   - 索引记录已被删除")
            return None

        print(f"\n📊 找到 {len(indexes)} 个索引记录:")

        pending_indexes = []
        for index in indexes:
            status_icon = "⏳" if index.status == DocumentIndexStatus.PENDING else \
                "🔄" if index.status == DocumentIndexStatus.CREATING else \
                "✅" if index.status == DocumentIndexStatus.ACTIVE else \
                "❌" if index.status == DocumentIndexStatus.FAILED else "❓"

            index_type_str = index.index_type.value if hasattr(
                index.index_type, 'value') else str(index.index_type)
            status_str = index.status.value if hasattr(
                index.status, 'value') else str(index.status)

            print(f"\n   {status_icon} {index_type_str}:")
            print(f"      状态: {status_str}")
            print(f"      版本: {index.version} (已处理: {index.observed_version})")
            print(f"      创建时间: {index.gmt_created}")
            print(f"      更新时间: {index.gmt_updated}")
            if index.gmt_last_reconciled:
                print(f"      最后协调时间: {index.gmt_last_reconciled}")
            if index.error_message:
                print(f"      ❌ 错误信息: {index.error_message}")

            # 检查是否需要协调
            needs_reconciliation = False
            if index.status == DocumentIndexStatus.PENDING:
                if index.observed_version < index.version:
                    needs_reconciliation = True
                    if index.version == 1:
                        action = "CREATE"
                    else:
                        action = "UPDATE"
                    print(
                        f"      ⚠️  需要协调: {action} (version={index.version}, observed={index.observed_version})")

            if index.status == DocumentIndexStatus.PENDING:
                pending_indexes.append(index)

        if pending_indexes:
            print(f"\n⚠️  发现 {len(pending_indexes)} 个PENDING状态的索引:")
            for index in pending_indexes:
                index_type_str = index.index_type.value if hasattr(
                    index.index_type, 'value') else str(index.index_type)
                print(
                    f"   - {index_type_str}: version={index.version}, observed={index.observed_version}")

        return indexes

    return None


def check_reconciler_detection(document_id: str):
    """检查reconciler是否能检测到这个文档需要处理"""
    print("\n" + "=" * 80)
    print(f"3. 检查Reconciler检测状态 (Document ID: {document_id})")
    print("=" * 80)

    for session in get_sync_session():
        # 模拟reconciler的检测逻辑
        operations = defaultdict(
            lambda: {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []})

        # CREATE条件: status=PENDING, observed_version < version, version=1
        create_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.status == DocumentIndexStatus.PENDING,
                DocumentIndex.observed_version < DocumentIndex.version,
                DocumentIndex.version == 1,
            )
        )
        create_result = session.execute(create_stmt)
        create_indexes = create_result.scalars().all()

        # UPDATE条件: status=PENDING, observed_version < version, version > 1
        update_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.status == DocumentIndexStatus.PENDING,
                DocumentIndex.observed_version < DocumentIndex.version,
                DocumentIndex.version > 1,
            )
        )
        update_result = session.execute(update_stmt)
        update_indexes = update_result.scalars().all()

        # DELETE条件: status=DELETING
        delete_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.status == DocumentIndexStatus.DELETING,
            )
        )
        delete_result = session.execute(delete_stmt)
        delete_indexes = delete_result.scalars().all()

        for index in create_indexes:
            operations[document_id][IndexAction.CREATE].append(index)
        for index in update_indexes:
            operations[document_id][IndexAction.UPDATE].append(index)
        for index in delete_indexes:
            operations[document_id][IndexAction.DELETE].append(index)

        doc_operations = operations.get(document_id, {})

        total_ops = sum(len(ops) for ops in doc_operations.values())

        if total_ops == 0:
            print("\n❌ Reconciler未检测到需要处理的操作")
            print("   可能原因:")
            print("   - 索引状态不是PENDING")
            print("   - version和observed_version已同步")
            print("   - 索引记录不存在")
        else:
            print(f"\n✅ Reconciler检测到 {total_ops} 个需要处理的操作:")
            if doc_operations[IndexAction.CREATE]:
                print(
                    f"   - CREATE: {len(doc_operations[IndexAction.CREATE])} 个")
                for idx in doc_operations[IndexAction.CREATE]:
                    idx_type_str = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    print(f"     * {idx_type_str} (version={idx.version})")
            if doc_operations[IndexAction.UPDATE]:
                print(
                    f"   - UPDATE: {len(doc_operations[IndexAction.UPDATE])} 个")
                for idx in doc_operations[IndexAction.UPDATE]:
                    idx_type_str = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    print(
                        f"     * {idx_type_str} (version={idx.version}, observed={idx.observed_version})")
            if doc_operations[IndexAction.DELETE]:
                print(
                    f"   - DELETE: {len(doc_operations[IndexAction.DELETE])} 个")
                for idx in doc_operations[IndexAction.DELETE]:
                    idx_type_str = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    print(f"     * {idx_type_str}")

        return doc_operations


def check_celery_status():
    """检查Celery服务状态（需要手动执行）"""
    print("\n" + "=" * 80)
    print("4. 检查Celery服务状态（需要手动执行）")
    print("=" * 80)

    print("\n请执行以下命令检查Celery服务:")
    print("\n1. 检查Celery Worker是否运行:")
    print("   docker ps | grep celeryworker")

    print("\n2. 检查Celery Beat是否运行:")
    print("   docker ps | grep celerybeat")

    print("\n3. 检查活跃任务:")
    print("   docker exec aperag-celeryworker celery -A config.celery inspect active")

    print("\n4. 检查保留任务:")
    print("   docker exec aperag-celeryworker celery -A config.celery inspect reserved")

    print("\n5. 查看最近的日志:")
    print("   docker logs aperag-celeryworker --tail 200 | grep -i 'reconcile\\|parse\\|index'")

    print("\n6. 手动触发reconciliation:")
    print("   docker exec aperag-celeryworker python -c \"")
    print("   from config.celery_tasks import reconcile_indexes_task")
    print("   reconcile_indexes_task()")
    print("   \"")


def check_collection_config(document_id: str):
    """检查Collection配置"""
    print("\n" + "=" * 80)
    print(f"5. 检查Collection配置")
    print("=" * 80)

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_result = session.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()

        if not document:
            print("\n❌ 未找到文档")
            return

        # 查询Collection
        collection_stmt = select(Collection).where(
            Collection.id == document.collection_id)
        collection_result = session.execute(collection_stmt)
        collection = collection_result.scalar_one_or_none()

        if not collection:
            print("\n❌ 未找到Collection")
            return

        print(f"\n📚 Collection信息:")
        print(f"   ID: {collection.id}")
        print(f"   名称: {collection.name}")
        print(f"   状态: {collection.status}")

        # 检查配置
        try:
            from aperag.schema.utils import parseCollectionConfig
            config = parseCollectionConfig(collection.config)

            print(f"\n📋 索引配置:")
            print(f"   Vector索引: {'✅ 启用' if config.enable_vector else '❌ 禁用'}")
            print(
                f"   Fulltext索引: {'✅ 启用' if config.enable_fulltext else '❌ 禁用'}")
            print(f"   Graph索引: {'✅ 启用' if config.enable_graph else '❌ 禁用'}")
            print(f"   Vision索引: {'✅ 启用' if config.enable_vision else '❌ 禁用'}")
            print(
                f"   Summary索引: {'✅ 启用' if config.enable_summary else '❌ 禁用'}")
        except Exception as e:
            print(f"\n⚠️  解析配置失败: {e}")


def provide_solutions(document_id: str, indexes):
    """提供解决方案"""
    print("\n" + "=" * 80)
    print("6. 解决方案建议")
    print("=" * 80)

    if not indexes:
        print("\n💡 建议:")
        print("   1. 检查文档是否已正确上传")
        print("   2. 检查Collection配置是否正确")
        print("   3. 尝试重新确认文档（如果状态是UPLOADED）")
        return

    pending_count = sum(1 for idx in indexes if idx.status ==
                        DocumentIndexStatus.PENDING)
    creating_count = sum(1 for idx in indexes if idx.status ==
                         DocumentIndexStatus.CREATING)
    failed_count = sum(1 for idx in indexes if idx.status ==
                       DocumentIndexStatus.FAILED)

    if pending_count > 0:
        print(f"\n⚠️  发现 {pending_count} 个PENDING状态的索引")
        print("\n💡 解决方案:")
        print("   1. 检查Celery Beat是否正常运行（每30秒运行reconcile_indexes_task）")
        print("   2. 检查Celery Worker是否正常运行")
        print("   3. 手动触发reconciliation:")
        print("      docker exec aperag-celeryworker python -c \\")
        print("        'from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()'")
        print("   4. 检查是否有足够的worker资源处理任务")
        print("   5. 查看Celery日志查找错误信息")

    if creating_count > 0:
        print(f"\n🔄 发现 {creating_count} 个CREATING状态的索引")
        print("   这些索引正在处理中，请等待完成")
        print("   如果长时间处于CREATING状态，可能是:")
        print("   - 任务执行失败但未正确更新状态")
        print("   - Worker资源不足")
        print("   - 网络或API连接问题")

    if failed_count > 0:
        print(f"\n❌ 发现 {failed_count} 个FAILED状态的索引")
        print("   需要查看错误信息并修复后重新创建索引")
        print("   可以通过API或Web界面重建索引")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查文档解析pending状态的诊断工具")
    parser.add_argument(
        "--document-name",
        type=str,
        help="文档名称（支持部分匹配）"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="文档ID（精确查询）"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("文档解析Pending状态诊断工具")
    print("=" * 80)
    print("\n💡 提示: 如果在本地运行失败，请在Docker容器中运行:")
    print("   docker exec aperag-celeryworker python check_document_pending.py --document-name '颍州变接线图'")
    print("=" * 80)

    document = None

    # 查找文档
    if args.document_id:
        for session in get_sync_session():
            stmt = select(Document).where(Document.id == args.document_id)
            result = session.execute(stmt)
            document = result.scalar_one_or_none()
            if document:
                print(f"\n✅ 找到文档: {document.name} (ID: {document.id})")
                break
    elif args.document_name:
        document = find_document_by_name(args.document_name)
    else:
        print("\n❌ 请提供 --document-name 或 --document-id 参数")
        parser.print_help()
        return

    if not document:
        print("\n❌ 未找到文档，无法继续诊断")
        return

    document_id = document.id

    # 检查索引状态
    indexes = check_document_indexes(document_id)

    # 检查reconciler检测
    doc_operations = check_reconciler_detection(document_id)

    # 检查Collection配置
    check_collection_config(document_id)

    # 检查Celery状态
    check_celery_status()

    # 提供解决方案
    provide_solutions(document_id, indexes)

    # 总结
    print("\n" + "=" * 80)
    print("诊断总结")
    print("=" * 80)

    if indexes:
        status_summary = defaultdict(int)
        for idx in indexes:
            status_summary[idx.status.value] += 1

        print(f"\n索引状态统计:")
        for status, count in status_summary.items():
            print(f"   {status}: {count}")

    if doc_operations:
        total_ops = sum(len(ops) for ops in doc_operations.values())
        if total_ops > 0:
            print(f"\n✅ Reconciler可以检测到 {total_ops} 个待处理操作")
            print("   如果索引仍然处于PENDING状态，可能原因:")
            print("   - Celery Beat未运行或未正确调度reconcile_indexes_task")
            print("   - Celery Worker未运行或资源不足")
            print("   - 任务执行失败但未正确更新状态")
        else:
            print("\n⚠️  Reconciler未检测到需要处理的操作")
            print("   可能原因:")
            print("   - 索引状态不是PENDING")
            print("   - version和observed_version已同步")
    else:
        print("\n⚠️  Reconciler未检测到需要处理的操作")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
