#!/usr/bin/env python3
"""
检查颍州变接线图.pdf的VISION索引详细状态
"""

from aperag.config import get_sync_session
from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus
from sqlalchemy import select
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


document_id = "doce41ca09d2a67d857"

for session in get_sync_session():
    # 查询文档
    doc = session.execute(select(Document).where(
        Document.id == document_id)).scalar_one_or_none()

    if not doc:
        print(f"❌ 未找到文档: {document_id}")
        break

    print("=" * 80)
    print(f"📄 文档信息: {doc.name}")
    print(f"   文档ID: {doc.id}")
    print(f"   状态: {doc.status}")
    print(f"   大小: {doc.size:,} bytes")
    print("=" * 80)

    # 查询VISION索引
    vision_idx = session.execute(
        select(DocumentIndex).where(
            DocumentIndex.document_id == document_id,
            DocumentIndex.index_type == DocumentIndexType.VISION
        )
    ).scalar_one_or_none()

    if vision_idx:
        print(f"\n🖼️  VISION索引状态:")
        print(f"   状态: {vision_idx.status}")
        print(
            f"   版本: {vision_idx.version} (已处理: {vision_idx.observed_version})")
        print(f"   创建时间: {vision_idx.gmt_created}")
        print(f"   更新时间: {vision_idx.gmt_updated}")
        print(f"   最后协调时间: {vision_idx.gmt_last_reconciled}")

        if vision_idx.error_message:
            print(f"\n   ❌ 错误信息:")
            print(f"   {vision_idx.error_message}")

        if vision_idx.index_data:
            try:
                data = json.loads(vision_idx.index_data)
                print(f"\n   📊 索引数据:")
                for key, value in data.items():
                    if key == 'context_ids' and isinstance(value, list):
                        print(f"      - {key}: {len(value)} 个向量")
                    else:
                        print(f"      - {key}: {value}")
            except Exception as e:
                print(f"\n   ⚠️  无法解析索引数据: {e}")
                print(f"   原始数据: {str(vision_idx.index_data)[:500]}...")
    else:
        print("\n❌ 未找到VISION索引记录")

    # 查询GRAPH索引
    graph_idx = session.execute(
        select(DocumentIndex).where(
            DocumentIndex.document_id == document_id,
            DocumentIndex.index_type == DocumentIndexType.GRAPH
        )
    ).scalar_one_or_none()

    if graph_idx:
        print(f"\n📊 GRAPH索引状态:")
        print(f"   状态: {graph_idx.status}")
        print(
            f"   版本: {graph_idx.version} (已处理: {graph_idx.observed_version})")
        print(f"   创建时间: {graph_idx.gmt_created}")
        print(f"   更新时间: {graph_idx.gmt_updated}")

        if graph_idx.error_message:
            print(f"\n   ❌ 错误信息:")
            print(f"   {graph_idx.error_message}")

        if graph_idx.index_data:
            try:
                data = json.loads(graph_idx.index_data)
                print(f"\n   📊 索引数据:")
                for key, value in data.items():
                    print(f"      - {key}: {value}")
            except Exception as e:
                print(f"\n   ⚠️  无法解析索引数据: {e}")
    else:
        print("\n❌ 未找到GRAPH索引记录")

    print("\n" + "=" * 80)

    # 诊断
    if vision_idx and vision_idx.status == DocumentIndexStatus.CREATING:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if vision_idx.gmt_updated:
            elapsed = (now - vision_idx.gmt_updated).total_seconds()
            print(f"\n⚠️  VISION索引已处于CREATING状态超过 {int(elapsed)} 秒")
            print(f"   可能原因:")
            print(f"   1. Vision LLM调用超时或卡住")
            print(f"   2. Vision LLM服务不可用")
            print(f"   3. 任务被中断但状态未更新")
            print(f"\n   建议:")
            print(f"   1. 检查Vision LLM服务状态")
            print(f"   2. 查看Celery Worker日志: docker logs aperag-celeryworker --tail 500 | Select-String 'doce41ca09d2a67d857'")
            print(f"   3. 如果确认卡住，可以手动重建VISION索引")

    if graph_idx and graph_idx.status == DocumentIndexStatus.CREATING:
        print(f"\n⚠️  GRAPH索引正在等待VISION索引完成")
        if vision_idx and vision_idx.status == DocumentIndexStatus.CREATING:
            print(f"   VISION索引尚未完成，GRAPH索引无法继续")

    break
