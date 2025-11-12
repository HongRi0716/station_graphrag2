#!/usr/bin/env python3
"""
诊断脚本:查看文档索引失败的详细错误信息
"""

from sqlalchemy import select, and_, desc
from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus
from aperag.config import get_sync_session
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def diagnose_document_failure(document_name_pattern: str = None):
    """诊断文档索引失败的原因"""

    print("=" * 80)
    print("文档索引失败诊断工具")
    print("=" * 80)

    for session in get_sync_session():
        # 查询文档
        if document_name_pattern:
            doc_stmt = select(Document).where(
                Document.name.like(f"%{document_name_pattern}%")
            ).order_by(desc(Document.gmt_created))
        else:
            doc_stmt = select(Document).order_by(
                desc(Document.gmt_created)).limit(10)

        doc_result = session.execute(doc_stmt)
        documents = doc_result.scalars().all()

        if not documents:
            print(f"\n未找到匹配的文档: {document_name_pattern}")
            return

        print(f"\n找到 {len(documents)} 个匹配的文档:\n")

        for doc in documents:
            print(f"\n{'='*80}")
            print(f"文档名称: {doc.name}")
            print(f"文档ID: {doc.id}")
            print(f"文档状态: {doc.status}")
            print(f"所属Collection: {doc.collection_id}")
            print(f"文件大小: {doc.size} bytes")
            print(f"创建时间: {doc.gmt_created}")
            print(f"更新时间: {doc.gmt_updated}")
            print(f"-" * 80)

            # 查询所有索引状态
            index_stmt = select(DocumentIndex).where(
                DocumentIndex.document_id == doc.id
            )
            index_result = session.execute(index_stmt)
            indexes = index_result.scalars().all()

            if not indexes:
                print("  ⚠️  未找到任何索引记录")
                continue

            print("\n索引状态详情:")
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

                if idx.error_message:
                    print(f"     ❌ 错误信息:")
                    print(f"        {idx.error_message}")

                if idx.index_data:
                    import json
                    try:
                        data = json.loads(idx.index_data)
                        print(f"     📊 索引数据摘要:")
                        if "context_ids" in data:
                            print(
                                f"        - 向量数量: {len(data['context_ids'])}")
                        if "chunk_count" in data:
                            print(f"        - 块数量: {data['chunk_count']}")
                        if "entity_count" in data:
                            print(f"        - 实体数量: {data['entity_count']}")
                        if "relationship_count" in data:
                            print(
                                f"        - 关系数量: {data['relationship_count']}")
                    except:
                        pass

            print(f"\n{'='*80}\n")

        # 提供诊断建议
        print("\n" + "="*80)
        print("诊断建议:")
        print("="*80)

        failed_indexes = [idx for doc in documents for idx in session.execute(
            select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == doc.id,
                    DocumentIndex.status == DocumentIndexStatus.FAILED
                )
            )
        ).scalars().all()]

        if failed_indexes:
            print("\n发现失败的索引:")
            for idx in failed_indexes:
                print(f"\n  类型: {idx.index_type.value}")
                print(f"  错误: {idx.error_message}")

                # 根据错误类型提供建议
                if "embedding" in idx.error_message.lower():
                    print("\n  💡 可能原因: 向量嵌入服务问题")
                    print("     - 检查 EMBEDDING_PROVIDER 和相关配置")
                    print("     - 检查向量服务(如OpenAI API)是否可访问")
                    print("     - 查看 envs/.env 中的嵌入服务配置")

                elif "graph" in idx.error_message.lower() or "knowledge" in idx.error_message.lower():
                    print("\n  💡 可能原因: 知识图谱构建问题")
                    print("     - 检查 Neo4j 或 NebulaGraph 连接配置")
                    print("     - 检查 LLM 服务是否正常(用于实体和关系提取)")
                    print("     - 查看图数据库是否运行正常")

                elif "qdrant" in idx.error_message.lower() or "vector" in idx.error_message.lower():
                    print("\n  💡 可能原因: 向量数据库连接问题")
                    print("     - 检查 Qdrant 服务是否运行")
                    print("     - 检查 VECTOR_DB_CONTEXT 配置")

                elif "llm" in idx.error_message.lower() or "api" in idx.error_message.lower():
                    print("\n  💡 可能原因: LLM API 调用失败")
                    print("     - 检查 LLM API Key 是否有效")
                    print("     - 检查 API 配额是否充足")
                    print("     - 检查网络连接")

                elif "parse" in idx.error_message.lower() or "docx" in idx.error_message.lower():
                    print("\n  💡 可能原因: 文档解析问题")
                    print("     - 文档可能损坏或格式不支持")
                    print("     - 检查文档是否可以正常打开")
                    print("     - 尝试重新上传文档")

                print("\n  🔧 修复建议:")
                print("     1. 修复上述配置问题")
                print("     2. 使用 rebuild_document_indexes API 重建失败的索引")
                print(
                    f"        POST /api/v1/collections/{{collection_id}}/documents/{idx.document_id}/rebuild-indexes")
                print(
                    f"        Body: {{\"index_types\": [\"{idx.index_type.value}\"]}}")
        else:
            print("\n✅ 未发现失败的索引")

        print("\n" + "="*80)
        print("更多信息:")
        print("  - 查看 Celery worker 日志以获取详细错误堆栈")
        print("  - 检查 envs/.env 配置文件")
        print("  - 运行: docker-compose logs celery-worker")
        print("="*80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="诊断文档索引失败原因")
    parser.add_argument(
        "document_name",
        nargs="?",
        default="变电站图纸档案智能化管理技术",
        help="文档名称或名称的一部分(支持模糊匹配)"
    )

    args = parser.parse_args()

    try:
        diagnose_document_failure(args.document_name)
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
