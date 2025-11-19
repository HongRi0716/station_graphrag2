#!/usr/bin/env python3
"""
重置卡住的索引状态为PENDING，让reconciliation重新处理
"""

from sqlalchemy import select, and_, update, desc
from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus, Document
from aperag.config import get_sync_session
import sys
import os
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def find_document_by_name(document_name: str):
    """通过文件名查找文档"""
    for session in get_sync_session():
        stmt = select(Document).where(Document.name ==
                                      document_name).order_by(desc(Document.gmt_created))
        result = session.execute(stmt)
        documents = result.scalars().all()

        if not documents:
            stmt = select(Document).where(Document.name.like(
                f"%{document_name}%")).order_by(desc(Document.gmt_created))
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


def reset_stuck_indexes(document_id: str, index_type: str = None, min_stuck_minutes: float = 5.0):
    """
    重置卡住的索引状态为PENDING

    Args:
        document_id: 文档ID
        index_type: 索引类型（可选，如VISION、GRAPH等），如果为None则重置所有CREATING状态的索引
        min_stuck_minutes: 最小卡住时间（分钟），只有超过这个时间的索引才会被重置
    """
    print("=" * 80)
    print("重置卡住的索引状态")
    print("=" * 80)
    print(f"\n文档ID: {document_id}")
    if index_type:
        print(f"索引类型: {index_type}")
    print(f"最小卡住时间: {min_stuck_minutes} 分钟\n")

    for session in get_sync_session():
        # 构建查询条件
        conditions = [
            DocumentIndex.document_id == document_id,
            DocumentIndex.status == DocumentIndexStatus.CREATING
        ]

        if index_type:
            conditions.append(DocumentIndex.index_type ==
                              DocumentIndexType(index_type))

        # 查找所有CREATING状态的索引
        stuck_indexes = session.execute(
            select(DocumentIndex).where(and_(*conditions))
        ).scalars().all()

        if not stuck_indexes:
            print("✅ 没有找到卡住的索引")
            break

        # 过滤出超过最小卡住时间的索引
        now = datetime.now(timezone.utc)
        filtered_indexes = []
        for idx in stuck_indexes:
            if idx.gmt_updated:
                elapsed = now - idx.gmt_updated.replace(
                    tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
                elapsed_minutes = elapsed.total_seconds() / 60
                if elapsed_minutes >= min_stuck_minutes:
                    filtered_indexes.append((idx, elapsed_minutes))
                else:
                    index_type_str = idx.index_type.value if hasattr(
                        idx.index_type, 'value') else str(idx.index_type)
                    print(
                        f"⏳ {index_type_str} 索引卡住时间 {elapsed_minutes:.1f} 分钟，未达到最小阈值 {min_stuck_minutes} 分钟，跳过")

        if not filtered_indexes:
            print("✅ 没有超过最小卡住时间的索引")
            break

        print(f"找到 {len(filtered_indexes)} 个需要重置的索引:\n")
        for idx, elapsed_minutes in filtered_indexes:
            index_type_str = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)
            print(f"  - {index_type_str} (已卡住 {elapsed_minutes:.1f} 分钟)")

        # 确认
        print(f"\n⚠️  即将重置这些索引的状态为PENDING")
        print("   这将触发reconciliation重新处理这些索引")

        # 执行重置
        for idx, elapsed_minutes in filtered_indexes:
            index_type_str = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)
            session.execute(
                update(DocumentIndex)
                .where(and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType(
                        index_type_str)
                ))
                .values(status=DocumentIndexStatus.PENDING)
            )
            print(f"  ✅ 已重置 {index_type_str} 索引状态")

        session.commit()
        print(f"\n✅ 所有索引状态已重置为PENDING")
        print("   请等待reconciliation任务重新处理（通常1分钟内）")
        break


def main():
    parser = argparse.ArgumentParser(description="重置卡住的索引状态为PENDING")
    parser.add_argument("--document-id", type=str, help="文档ID")
    parser.add_argument("--document-name", type=str, help="文档名称（如：主接线.png）")
    parser.add_argument("--index-type", type=str, choices=["VECTOR", "VISION", "GRAPH", "FULLTEXT", "SUMMARY"],
                        help="索引类型（可选）")
    parser.add_argument("--min-stuck-minutes", type=float, default=5.0,
                        help="最小卡住时间（分钟），默认5分钟")

    args = parser.parse_args()

    # 确定文档ID
    document_id = args.document_id
    if not document_id and args.document_name:
        document = find_document_by_name(args.document_name)
        if not document:
            print(f"❌ 未找到文档: {args.document_name}")
            sys.exit(1)
        document_id = document.id
        print(f"找到文档: {document.name} (ID: {document_id})")

    if not document_id:
        print("❌ 必须提供 --document-id 或 --document-name")
        parser.print_help()
        sys.exit(1)

    reset_stuck_indexes(document_id, args.index_type, args.min_stuck_minutes)


if __name__ == "__main__":
    main()
