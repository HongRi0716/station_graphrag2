#!/usr/bin/env python3
"""
检查文档解析状态和索引创建流程
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_
    from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus, DocumentStatus
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def check_parse_and_index_status(document_id: str):
    """检查文档解析状态和索引创建状态"""
    print("=" * 80)
    print(f"检查文档解析和索引状态: {document_id}")
    print("=" * 80)

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_result = session.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()

        if not document:
            print(f"❌ 未找到文档: {document_id}")
            return

        print(f"\n📄 文档信息:")
        print(f"   名称: {document.name}")
        print(f"   状态: {document.status}")
        print(f"   创建时间: {document.gmt_created}")
        print(f"   更新时间: {document.gmt_updated}")

        # 计算文档更新时间距离现在的时间
        if document.gmt_updated:
            now = datetime.now(timezone.utc)
            elapsed = now - document.gmt_updated.replace(
                tzinfo=timezone.utc) if document.gmt_updated.tzinfo is None else now - document.gmt_updated
            print(
                f"   距离现在: {elapsed.total_seconds():.0f} 秒 ({elapsed.total_seconds()/60:.1f} 分钟)")

        # 查询所有索引
        index_stmt = select(DocumentIndex).where(
            DocumentIndex.document_id == document_id
        )
        index_result = session.execute(index_stmt)
        indexes = index_result.scalars().all()

        if not indexes:
            print(f"\n⚠️  未找到索引记录")
            return

        print(f"\n📊 索引状态:")
        for idx in indexes:
            index_type_str = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)
            status_str = idx.status.value if hasattr(
                idx.status, 'value') else str(idx.status)

            # 计算索引更新时间距离现在的时间
            elapsed_str = ""
            if idx.gmt_updated:
                now = datetime.now(timezone.utc)
                elapsed = now - idx.gmt_updated.replace(
                    tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
                elapsed_str = f" (已等待 {elapsed.total_seconds():.0f} 秒 / {elapsed.total_seconds()/60:.1f} 分钟)"

            print(f"   {index_type_str}: {status_str}{elapsed_str}")
            print(
                f"      version={idx.version}, observed={idx.observed_version}")
            print(f"      更新时间: {idx.gmt_updated}")
            if idx.error_message:
                print(f"      ❌ 错误: {idx.error_message}")

        # 分析状态
        print(f"\n🔍 状态分析:")

        creating_indexes = [
            idx for idx in indexes if idx.status == DocumentIndexStatus.CREATING]
        if creating_indexes:
            print(f"   ⚠️  有 {len(creating_indexes)} 个索引处于CREATING状态")
            for idx in creating_indexes:
                index_type_str = idx.index_type.value if hasattr(
                    idx.index_type, 'value') else str(idx.index_type)
                if idx.gmt_updated:
                    now = datetime.now(timezone.utc)
                    elapsed = now - idx.gmt_updated.replace(
                        tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
                    if elapsed.total_seconds() > 300:  # 超过5分钟
                        print(
                            f"      - {index_type_str}: 已等待 {elapsed.total_seconds()/60:.1f} 分钟，可能卡住了")

        # 检查是否需要重新解析
        if document.status == DocumentStatus.RUNNING:
            print(f"\n   ⚠️  文档状态为RUNNING，解析可能还在进行中或已卡住")
            if document.gmt_updated:
                now = datetime.now(timezone.utc)
                elapsed = now - document.gmt_updated.replace(
                    tzinfo=timezone.utc) if document.gmt_updated.tzinfo is None else now - document.gmt_updated
                if elapsed.total_seconds() > 600:  # 超过10分钟
                    print(
                        f"      ⚠️  文档已等待 {elapsed.total_seconds()/60:.1f} 分钟，解析可能已卡住")

        print(f"\n💡 建议:")
        creating_stuck = [idx for idx in creating_indexes if idx.gmt_updated and
                          (datetime.now(timezone.utc) - (idx.gmt_updated.replace(tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else idx.gmt_updated)).total_seconds() > 300]
        if creating_stuck:
            print(f"   1. 重置卡住的索引状态:")
            print(
                f"      docker exec aperag-celeryworker python /app/reset_stuck_indexes.py --document-id {document_id} --stuck-minutes 5")
            print(f"   2. 手动触发reconciliation:")
            print(f"      docker exec aperag-celeryworker python -c \"from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()\"")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="检查文档解析状态和索引创建状态")
    parser.add_argument("document_id", help="文档ID")

    args = parser.parse_args()

    try:
        check_parse_and_index_status(args.document_id)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
