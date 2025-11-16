#!/usr/bin/env python3
"""
重新构建文档的GRAPH索引
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from aperag.config import get_sync_session
    from aperag.db.models import DocumentIndex, DocumentIndexType
    from aperag.index.manager import DocumentIndexManager
    from sqlalchemy import select, and_
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)


def rebuild_graph_index(document_id: str):
    """重新构建文档的GRAPH索引"""

    print("=" * 80)
    print("重新构建GRAPH索引")
    print("=" * 80)
    print(f"\n文档ID: {document_id}\n")

    for session in get_sync_session():
        # 查询GRAPH索引
        stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.index_type == DocumentIndexType.GRAPH
            )
        )
        result = session.execute(stmt)
        graph_index = result.scalar_one_or_none()

        if not graph_index:
            print("❌ 未找到GRAPH索引记录")
            return

        print(f"当前状态: {graph_index.status}")
        print(f"当前版本: {graph_index.version}")
        print(f"已处理版本: {graph_index.observed_version}")

        # 更新版本以触发重新构建
        graph_index.update_version()
        session.add(graph_index)
        session.commit()

        print(f"\n✅ 已更新GRAPH索引版本: {graph_index.version}")
        print("   索引将在下次reconciliation时重新构建")
        print("   或者可以手动触发reconciliation:")
        print("   docker exec aperag-celeryworker python -c \"from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()\"")

        break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="重新构建文档的GRAPH索引")
    parser.add_argument("--document-id", type=str, required=True, help="文档ID")

    args = parser.parse_args()

    try:
        rebuild_graph_index(args.document_id)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
