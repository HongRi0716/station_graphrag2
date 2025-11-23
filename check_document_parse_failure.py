#!/usr/bin/env python3
"""
快速诊断文档解析失败原因
用法: python check_document_parse_failure.py "文档名称"
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_, or_
    from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus, DocumentStatus
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的Python环境中运行，或使用Docker容器:")
    print("  docker exec aperag-celeryworker python /app/check_document_parse_failure.py \"文档名称\"")
    sys.exit(1)


def check_document_parse_status(document_name_pattern: str):
    """检查文档解析状态"""
    print("=" * 80)
    print(f"检查文档解析状态: {document_name_pattern}")
    print("=" * 80)

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(
            Document.name.like(f"%{document_name_pattern}%")
        ).order_by(Document.gmt_created.desc())

        doc_result = session.execute(doc_stmt)
        documents = doc_result.scalars().all()

        if not documents:
            print(f"\n❌ 未找到匹配的文档: {document_name_pattern}")
            print("\n💡 建议:")
            print("  1. 检查文档名称是否正确")
            print("  2. 尝试使用文档名称的一部分进行搜索")
            return

        print(f"\n找到 {len(documents)} 个匹配的文档:\n")

        for doc in documents:
            print(f"\n{'='*80}")
            print(f"📄 文档信息:")
            print(f"   名称: {doc.name}")
            print(f"   ID: {doc.id}")
            print(
                f"   状态: {doc.status.value if hasattr(doc.status, 'value') else doc.status}")
            print(f"   文件大小: {doc.size:,} bytes ({doc.size/1024/1024:.2f} MB)")
            print(f"   创建时间: {doc.gmt_created}")
            print(f"   更新时间: {doc.gmt_updated}")

            # 计算等待时间
            if doc.gmt_updated:
                now = datetime.now(timezone.utc)
                elapsed = now - (doc.gmt_updated.replace(tzinfo=timezone.utc)
                                 if doc.gmt_updated.tzinfo is None else doc.gmt_updated)
                print(f"   已等待: {elapsed.total_seconds()/60:.1f} 分钟")

            print(f"\n📊 索引状态:")

            # 查询所有索引
            index_stmt = select(DocumentIndex).where(
                DocumentIndex.document_id == doc.id
            )
            index_result = session.execute(index_stmt)
            indexes = index_result.scalars().all()

            if not indexes:
                print("   ⚠️  未找到索引记录（可能还未开始解析）")
                continue

            has_failed = False
            for idx in indexes:
                status_icon = {
                    DocumentIndexStatus.PENDING: "⏳",
                    DocumentIndexStatus.CREATING: "🔄",
                    DocumentIndexStatus.ACTIVE: "✅",
                    DocumentIndexStatus.FAILED: "❌",
                    DocumentIndexStatus.DELETION_IN_PROGRESS: "🗑️",
                    DocumentIndexStatus.DELETING: "🗑️"
                }.get(idx.status, "❓")

                index_type = idx.index_type.value if hasattr(
                    idx.index_type, 'value') else str(idx.index_type)
                status = idx.status.value if hasattr(
                    idx.status, 'value') else str(idx.status)

                print(f"   {status_icon} {index_type}: {status}")

                if idx.error_message:
                    has_failed = True
                    print(f"      ❌ 错误: {idx.error_message[:200]}...")
                    if len(idx.error_message) > 200:
                        print(f"         (错误信息过长，已截断)")

            # 诊断建议
            if has_failed:
                print(f"\n🔍 诊断建议:")

                failed_indexes = [
                    idx for idx in indexes if idx.status == DocumentIndexStatus.FAILED]
                for idx in failed_indexes:
                    error_lower = idx.error_message.lower() if idx.error_message else ""

                    if "parse" in error_lower or "docray" in error_lower or "mineru" in error_lower:
                        print(f"\n   📋 解析失败 ({idx.index_type.value}):")
                        print(f"      可能原因:")
                        print(f"      1. DocRay/MinerU 服务未启动或不可访问")
                        print(f"      2. 文档格式损坏或不支持")
                        print(f"      3. 文档过大超过限制")
                        print(f"      4. 解析服务超时")
                        print(f"\n      解决方案:")
                        print(f"      1. 检查解析服务状态:")
                        print(f"         docker ps | grep -E 'docray|mineru'")
                        print(f"      2. 查看解析服务日志:")
                        print(f"         docker logs aperag-docray --tail 50")
                        print(f"      3. 检查文档是否可以正常打开")
                        print(f"      4. 尝试重新上传文档")

                    elif "embedding" in error_lower or "vector" in error_lower:
                        print(f"\n   🔢 向量化失败 ({idx.index_type.value}):")
                        print(f"      可能原因:")
                        print(f"      1. Embedding API 密钥无效或过期")
                        print(f"      2. API 配额不足或达到速率限制")
                        print(f"      3. 文本过长超过 token 限制")
                        print(f"      4. 网络无法访问 Embedding 服务")
                        print(f"\n      解决方案:")
                        print(f"      1. 检查 EMBEDDING_SERVICE_API_KEY 配置")
                        print(f"      2. 检查 API 配额和速率限制")
                        print(f"      3. 查看错误详情中的 token 限制信息")

                    elif "graph" in error_lower or "neo4j" in error_lower or "nebula" in error_lower:
                        print(f"\n   🕸️  知识图谱失败 ({idx.index_type.value}):")
                        print(f"      可能原因:")
                        print(f"      1. 图数据库未运行或连接失败")
                        print(f"      2. LLM 服务问题（用于实体提取）")
                        print(f"      3. 文档内容过长导致处理超时")
                        print(f"\n      解决方案:")
                        print(f"      1. 检查图数据库服务状态:")
                        print(f"         docker ps | grep -E 'neo4j|nebula'")
                        print(f"      2. 检查图数据库连接配置")
                        print(f"      3. 检查 LLM 服务配置")

                    elif "timeout" in error_lower:
                        print(f"\n   ⏱️  超时失败 ({idx.index_type.value}):")
                        print(f"      可能原因:")
                        print(f"      1. 文档过大，处理时间过长")
                        print(f"      2. 服务响应慢")
                        print(f"      3. 网络连接问题")
                        print(f"\n      解决方案:")
                        print(f"      1. 检查文档大小: {doc.size/1024/1024:.2f} MB")
                        print(f"      2. 增加超时配置")
                        print(f"      3. 尝试重新上传")

                print(f"\n   🔧 修复步骤:")
                print(f"      1. 查看详细错误日志:")
                print(
                    f"         docker logs aperag-celeryworker --tail 200 | grep '{doc.id}'")
                print(f"      2. 修复上述配置问题")
                print(f"      3. 重建失败的索引:")
                print(f"         在Web界面中点击文档的'重建索引'按钮")
                print(
                    f"         或使用API: POST /api/v1/collections/{{collection_id}}/documents/{doc.id}/rebuild-indexes")

            elif doc.status == DocumentStatus.RUNNING:
                creating_indexes = [
                    idx for idx in indexes if idx.status == DocumentIndexStatus.CREATING]
                if creating_indexes:
                    print(f"\n   ⏳ 解析进行中:")
                    print(f"      有 {len(creating_indexes)} 个索引正在创建中")
                    print(f"      请耐心等待，或查看日志了解进度")
                    print(
                        f"      docker logs aperag-celeryworker --tail 100 | grep '{doc.id}'")

            print(f"\n{'='*80}\n")

        break  # 只处理第一个session


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="诊断文档解析失败原因")
    parser.add_argument(
        "document_name",
        nargs="?",
        default="2-国家电网公司变电运维管理规",
        help="文档名称或名称的一部分(支持模糊匹配)"
    )

    args = parser.parse_args()

    try:
        check_document_parse_status(args.document_name)
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
