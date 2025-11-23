#!/usr/bin/env python3
"""
检查知识库（Collection）中所有文档的解析状态
用法: 
  python check_collection_documents_status.py <collection_id>
  python check_collection_documents_status.py <collection_name>
  python check_collection_documents_status.py --all  # 检查所有知识库
"""

import sys
import os
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_, func, desc
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
        DocumentStatus,
        Collection,
    )
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的Python环境中运行，或使用Docker容器:")
    print("  docker exec aperag-celeryworker python /app/check_collection_documents_status.py <collection_id>")
    sys.exit(1)


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_elapsed(elapsed_seconds):
    """格式化时间差"""
    if elapsed_seconds < 60:
        return f"{elapsed_seconds:.0f}秒"
    elif elapsed_seconds < 3600:
        return f"{elapsed_seconds / 60:.1f}分钟"
    else:
        return f"{elapsed_seconds / 3600:.1f}小时"


def get_status_icon(status):
    """获取状态图标"""
    icons = {
        DocumentIndexStatus.PENDING: "⏳",
        DocumentIndexStatus.CREATING: "🔄",
        DocumentIndexStatus.COMPLETED: "✅",
        DocumentIndexStatus.ACTIVE: "✅",
        DocumentIndexStatus.FAILED: "❌",
        DocumentIndexStatus.DELETION_IN_PROGRESS: "🗑️",
        DocumentIndexStatus.SKIPPED: "⏭️",
    }
    return icons.get(status, "❓")


def check_collection_documents(collection_id_or_name: str = None, check_all: bool = False):
    """检查知识库中所有文档的解析状态"""

    print("=" * 80)
    if check_all:
        print("检查所有知识库的文档解析状态")
    else:
        print(f"检查知识库文档解析状态: {collection_id_or_name}")
    print("=" * 80)

    for session in get_sync_session():
        collections = []

        if check_all:
            # 查询所有知识库
            collection_stmt = select(Collection).order_by(
                Collection.gmt_created.desc())
            collection_result = session.execute(collection_stmt)
            collections = collection_result.scalars().all()
        else:
            # 查询指定知识库（支持ID或名称）
            collection_stmt = select(Collection).where(
                (Collection.id == collection_id_or_name) |
                (Collection.name.like(f"%{collection_id_or_name}%")) |
                (Collection.title.like(f"%{collection_id_or_name}%"))
            )
            collection_result = session.execute(collection_stmt)
            collections = collection_result.scalars().all()

            if not collections:
                print(f"\n❌ 未找到知识库: {collection_id_or_name}")
                print("\n💡 建议:")
                print("  1. 检查知识库ID或名称是否正确")
                print("  2. 使用 --all 参数查看所有知识库")
                return

        for collection in collections:
            print(f"\n{'='*80}")
            print(f"📚 知识库信息:")
            print(f"   ID: {collection.id}")
            print(f"   名称: {collection.name}")
            print(f"   标题: {collection.title}")
            print(
                f"   状态: {collection.status.value if hasattr(collection.status, 'value') else collection.status}")
            print(f"   创建时间: {collection.gmt_created}")

            # 查询该知识库的所有文档
            doc_stmt = select(Document).where(
                Document.collection_id == collection.id
            ).order_by(desc(Document.gmt_created))
            doc_result = session.execute(doc_stmt)
            documents = doc_result.scalars().all()

            if not documents:
                print(f"\n⚠️  该知识库中没有文档")
                continue

            print(f"\n📊 文档统计:")
            print(f"   总文档数: {len(documents)}")

            # 统计文档状态
            status_count = defaultdict(int)
            for doc in documents:
                status = doc.status.value if hasattr(
                    doc.status, 'value') else str(doc.status)
                status_count[status] += 1

            print(f"\n   文档状态分布:")
            for status, count in sorted(status_count.items()):
                icon = "✅" if status == "COMPLETE" else "🔄" if status == "RUNNING" else "❌" if status == "FAILED" else "⏳"
                print(f"     {icon} {status}: {count}")

            # 统计索引状态
            print(f"\n📈 索引状态统计:")
            index_stats = defaultdict(
                lambda: {"total": 0, "completed": 0, "failed": 0, "creating": 0, "pending": 0})

            for doc in documents:
                index_stmt = select(DocumentIndex).where(
                    DocumentIndex.document_id == doc.id
                )
                index_result = session.execute(index_stmt)
                indexes = index_result.scalars().all()

                for idx in indexes:
                    index_type = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    status = idx.status.value if hasattr(
                        idx.status, 'value') else str(idx.status)

                    index_stats[index_type]["total"] += 1
                    if status == "COMPLETED" or status == "ACTIVE":
                        index_stats[index_type]["completed"] += 1
                    elif status == "FAILED":
                        index_stats[index_type]["failed"] += 1
                    elif status == "CREATING":
                        index_stats[index_type]["creating"] += 1
                    elif status == "PENDING":
                        index_stats[index_type]["pending"] += 1

            for index_type, stats in sorted(index_stats.items()):
                total = stats["total"]
                completed = stats["completed"]
                failed = stats["failed"]
                creating = stats["creating"]
                pending = stats["pending"]

                completion_rate = (completed / total * 100) if total > 0 else 0
                print(f"   {index_type}:")
                print(f"     总计: {total}, 完成: {completed} ({completion_rate:.1f}%), "
                      f"失败: {failed}, 创建中: {creating}, 等待: {pending}")

            # 显示文档详情
            print(f"\n📄 文档详情:")
            print(f"{'文档名称':<50} {'状态':<12} {'大小':<12} {'索引状态':<30}")
            print("-" * 110)

            for doc in documents:
                # 查询文档的所有索引
                index_stmt = select(DocumentIndex).where(
                    DocumentIndex.document_id == doc.id
                )
                index_result = session.execute(index_stmt)
                indexes = index_result.scalars().all()

                # 格式化索引状态
                index_statuses = []
                for idx in indexes:
                    index_type = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    status = idx.status.value if hasattr(
                        idx.status, 'value') else str(idx.status)
                    icon = get_status_icon(idx.status)
                    index_statuses.append(f"{icon}{index_type[:4]}")

                index_status_str = " ".join(
                    index_statuses) if index_statuses else "无索引"

                doc_status = doc.status.value if hasattr(
                    doc.status, 'value') else str(doc.status)
                doc_status_icon = "✅" if doc_status == "COMPLETE" else "🔄" if doc_status == "RUNNING" else "❌" if doc_status == "FAILED" else "⏳"

                # 截断文档名称
                doc_name = doc.name[:47] + \
                    "..." if len(doc.name) > 50 else doc.name

                print(
                    f"{doc_name:<50} {doc_status_icon}{doc_status:<11} {format_size(doc.size):<12} {index_status_str:<30}")

            # 检查失败的文档
            failed_docs = [
                doc for doc in documents if doc.status == DocumentStatus.FAILED]
            if failed_docs:
                print(f"\n❌ 失败的文档 ({len(failed_docs)} 个):")
                for doc in failed_docs:
                    print(f"   - {doc.name} (ID: {doc.id})")
                    # 查询失败索引
                    failed_index_stmt = select(DocumentIndex).where(
                        and_(
                            DocumentIndex.document_id == doc.id,
                            DocumentIndex.status == DocumentIndexStatus.FAILED
                        )
                    )
                    failed_index_result = session.execute(failed_index_stmt)
                    failed_indexes = failed_index_result.scalars().all()
                    for idx in failed_indexes:
                        index_type = idx.index_type.value if hasattr(
                            idx.index_type, 'value') else str(idx.index_type)
                        error = idx.error_message[:100] + "..." if idx.error_message and len(
                            idx.error_message) > 100 else idx.error_message or "未知错误"
                        print(f"     {index_type}: {error}")

            # 检查卡住的文档（CREATING状态超过5分钟）
            now = datetime.now(timezone.utc)
            stuck_docs = []
            for doc in documents:
                if doc.status == DocumentStatus.RUNNING:
                    if doc.gmt_updated:
                        elapsed = now - (doc.gmt_updated.replace(tzinfo=timezone.utc)
                                         if doc.gmt_updated.tzinfo is None else doc.gmt_updated)
                        if elapsed.total_seconds() > 300:  # 5分钟
                            stuck_docs.append((doc, elapsed.total_seconds()))

            if stuck_docs:
                print(f"\n⚠️  可能卡住的文档 ({len(stuck_docs)} 个):")
                for doc, elapsed_seconds in stuck_docs:
                    print(
                        f"   - {doc.name} (已等待 {format_elapsed(elapsed_seconds)})")

            print(f"\n{'='*80}\n")

        break  # 只处理第一个session


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="检查知识库中所有文档的解析状态")
    parser.add_argument(
        "collection",
        nargs="?",
        help="知识库ID或名称（支持模糊匹配）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="检查所有知识库",
    )

    args = parser.parse_args()

    if not args.collection and not args.all:
        parser.print_help()
        sys.exit(1)

    try:
        check_collection_documents(args.collection, args.all)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
