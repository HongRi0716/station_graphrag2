#!/usr/bin/env python3
"""
诊断脚本: 检查颍州变接线图.pdf的向量索引失败原因
"""

from sqlalchemy import select, and_, desc
from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus, Collection
from aperag.config import get_sync_session
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def diagnose_yingzhou_vector_failure():
    """诊断颍州变接线图.pdf的向量索引失败原因"""

    print("=" * 80)
    print("颍州变接线图.pdf 向量索引失败诊断工具")
    print("=" * 80)

    document_name_pattern = "颍州变接线图"

    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(
            Document.name.like(f"%{document_name_pattern}%")
        ).order_by(desc(Document.gmt_created))

        doc_result = session.execute(doc_stmt)
        documents = doc_result.scalars().all()

        if not documents:
            print(f"\n❌ 未找到匹配的文档: {document_name_pattern}")
            print("\n💡 提示: 请确认文档名称是否正确")
            return

        # 取最新的文档
        doc = documents[0]
        print(f"\n{'='*80}")
        print(f"文档名称: {doc.name}")
        print(f"文档ID: {doc.id}")
        print(f"文档状态: {doc.status}")
        print(f"所属Collection ID: {doc.collection_id}")
        print(f"文件大小: {doc.size:,} bytes ({doc.size / 1024 / 1024:.2f} MB)")
        print(f"创建时间: {doc.gmt_created}")
        print(f"更新时间: {doc.gmt_updated}")
        print(f"-" * 80)

        # 查询Collection信息
        collection = session.execute(select(Collection).where(
            Collection.id == doc.collection_id)).scalar_one_or_none()
        
        if collection:
            print(f"\nCollection信息:")
            print(f"  Collection名称: {collection.name}")
            print(f"  Collection ID: {collection.id}")
            print(f"  启用向量索引: {collection.config.get('enable_vector_index', True) if collection.config else True}")

        # 查询所有索引状态
        index_stmt = select(DocumentIndex).where(
            DocumentIndex.document_id == doc.id
        ).order_by(DocumentIndex.index_type)
        index_result = session.execute(index_stmt)
        indexes = index_result.scalars().all()

        if not indexes:
            print("\n⚠️  未找到任何索引记录")
            print("💡 可能原因: 文档尚未开始索引处理")
            return

        print(f"\n索引状态详情:")
        vector_index = None
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
            print(f"     版本: {idx.version} (已处理: {idx.observed_version})")
            print(f"     创建时间: {idx.gmt_created}")
            print(f"     更新时间: {idx.gmt_updated}")

            if idx.index_type == DocumentIndexType.VECTOR:
                vector_index = idx

            if idx.error_message:
                print(f"     ❌ 错误信息:")
                # 格式化错误信息，每行缩进
                error_lines = idx.error_message.split('\n')
                for line in error_lines:
                    print(f"        {line}")

            if idx.index_data:
                try:
                    data = json.loads(idx.index_data)
                    print(f"     📊 索引数据摘要:")
                    if "context_ids" in data:
                        print(f"        - 向量数量: {len(data['context_ids'])}")
                    if "chunk_count" in data:
                        print(f"        - 块数量: {data['chunk_count']}")
                    if "vector_count" in data:
                        print(f"        - 向量数量: {data['vector_count']}")
                    if "vector_size" in data:
                        print(f"        - 向量维度: {data['vector_size']}")
                except:
                    pass

        # 重点分析向量索引失败原因
        if vector_index and vector_index.status == DocumentIndexStatus.FAILED:
            print(f"\n{'='*80}")
            print("向量索引失败分析:")
            print("="*80)

            error_msg = vector_index.error_message or ""
            error_lower = error_msg.lower()

            # 分析错误类型
            if "embedding" in error_lower or "api key" in error_lower or "rate limit" in error_lower:
                print("\n🔍 错误类型: 向量嵌入服务问题")
                print("\n可能原因:")
                print("  1. Embedding API密钥无效或过期")
                print("  2. API配额不足或达到速率限制")
                print("  3. 网络无法访问Embedding服务")
                print("  4. Embedding服务配置错误")
                print("\n解决方案:")
                print("  1. 检查环境配置文件 envs/.env 或 envs/docker.env.overrides:")
                print("     - EMBEDDING_PROVIDER")
                print("     - EMBEDDING_MODEL")
                print("     - EMBEDDING_SERVICE_URL")
                print("     - EMBEDDING_SERVICE_API_KEY")
                print("  2. 验证API密钥是否有效")
                print("  3. 检查API配额和余额")
                print("  4. 测试网络连接")

            elif "qdrant" in error_lower or "vector database" in error_lower or "connection" in error_lower:
                print("\n🔍 错误类型: 向量数据库连接问题")
                print("\n可能原因:")
                print("  1. Qdrant服务未运行")
                print("  2. Qdrant连接配置错误")
                print("  3. 向量维度不匹配")
                print("  4. 网络连接问题")
                print("\n解决方案:")
                print("  1. 检查Qdrant服务状态:")
                print("     docker ps | grep qdrant")
                print("  2. 检查Qdrant配置:")
                print("     - VECTOR_DB_TYPE=qdrant")
                print("     - VECTOR_DB_CONTEXT")
                print("  3. 测试Qdrant连接:")
                print("     curl http://localhost:6333/collections")
                print("  4. 重启Qdrant服务:")
                print("     docker-compose restart qdrant")

            elif "parse" in error_lower or "docray" in error_lower or "failed to parse" in error_lower:
                print("\n🔍 错误类型: 文档解析问题")
                print("\n可能原因:")
                print("  1. DocRay服务未启动")
                print("  2. 文档格式损坏或不支持")
                print("  3. 文档过大")
                print("  4. OCR处理失败")
                print("\n解决方案:")
                print("  1. 检查DocRay服务状态:")
                print("     docker ps | grep docray")
                print("  2. 如果DocRay未运行，启动它:")
                print("     docker-compose up -d docray")
                print("  3. 查看DocRay日志:")
                print("     docker logs aperag-docray --tail 100")
                print("  4. 检查文档是否可以正常打开")

            elif "timeout" in error_lower or "timed out" in error_lower:
                print("\n🔍 错误类型: 超时问题")
                print("\n可能原因:")
                print("  1. 文档过大，处理时间过长")
                print("  2. API响应慢")
                print("  3. 网络延迟")
                print("\n解决方案:")
                print("  1. 增加超时设置")
                print("  2. 检查网络连接")
                print("  3. 考虑分批处理大文档")

            elif "content" in error_lower or "empty" in error_lower or "no text" in error_lower:
                print("\n🔍 错误类型: 文档内容为空")
                print("\n可能原因:")
                print("  1. PDF是纯图片型（扫描版），没有文本层")
                print("  2. OCR未执行或失败")
                print("  3. 文档解析后content字段为空")
                print("\n解决方案:")
                print("  1. 检查Vision索引是否成功创建（用于图片分析）")
                print("  2. 确保DocRay OCR功能正常工作")
                print("  3. 检查文档解析日志")

            else:
                print("\n🔍 错误类型: 未知错误")
                print(f"\n完整错误信息:")
                print(f"  {error_msg}")

            print(f"\n{'='*80}")
            print("修复步骤:")
            print("="*80)
            print("\n1. 根据上述分析修复配置问题")
            print("\n2. 重启相关服务:")
            print("   docker-compose restart celeryworker")
            if "docray" in error_lower:
                print("   docker-compose restart docray")
            if "qdrant" in error_lower:
                print("   docker-compose restart qdrant")
            print("\n3. 重建向量索引:")
            print("   方法A: 通过Web界面")
            print("     - 进入文档详情页")
            print("     - 找到VECTOR索引")
            print("     - 点击'重建索引'按钮")
            print("\n   方法B: 通过API")
            print(f"     curl -X POST \"http://localhost:8000/api/v1/collections/{doc.collection_id}/documents/{doc.id}/rebuild-indexes\" \\")
            print("       -H \"Content-Type: application/json\" \\")
            print("       -H \"Authorization: Bearer YOUR_TOKEN\" \\")
            print("       -d '{\"index_types\": [\"VECTOR\"]}'")
            print("\n4. 查看重建日志:")
            print("   docker logs aperag-celeryworker --tail 200 -f")

        elif vector_index and vector_index.status == DocumentIndexStatus.COMPLETED:
            print(f"\n{'='*80}")
            print("✅ 向量索引已成功创建")
            print("="*80)
            if vector_index.index_data:
                try:
                    data = json.loads(vector_index.index_data)
                    if "context_ids" in data:
                        print(f"\n向量数量: {len(data['context_ids'])}")
                    if "vector_count" in data:
                        print(f"向量数量: {data['vector_count']}")
                except:
                    pass

        elif not vector_index:
            print(f"\n⚠️  未找到向量索引记录")
            print("💡 可能原因: 向量索引尚未创建或已被删除")

        print(f"\n{'='*80}")
        print("其他检查建议:")
        print("="*80)
        print("\n1. 查看Celery Worker日志:")
        print("   docker logs aperag-celeryworker --tail 500 | grep -i \"vector\\|embedding\\|{doc.id}\"")
        print("\n2. 检查环境配置:")
        print("   docker exec aperag-celeryworker env | grep -i \"EMBEDDING\\|VECTOR\"")
        print("\n3. 检查服务状态:")
        print("   docker-compose ps")
        print("\n4. 查看相关文档:")
        print("   - DOCUMENT_INDEX_TROUBLESHOOTING.md")
        print("   - DOCKER_VECTOR_FAILURE_DIAGNOSIS.md")
        print("="*80 + "\n")

        break


if __name__ == "__main__":
    try:
        diagnose_yingzhou_vector_failure()
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

