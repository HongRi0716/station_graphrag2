#!/usr/bin/env python3
"""
诊断脚本: 检查"主接线.png"的向量、Vision和知识图谱索引状态
分析为什么一直处于CREATING状态
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, and_, desc
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
        Collection,
    )
    from aperag.config import get_sync_session
    from aperag.schema.utils import parseCollectionConfig
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def find_document_by_name(document_name: str):
    """通过文件名查找文档"""
    for session in get_sync_session():
        # 尝试精确匹配
        stmt = select(Document).where(Document.name ==
                                      document_name).order_by(desc(Document.gmt_created))
        result = session.execute(stmt)
        documents = result.scalars().all()

        if not documents:
            # 尝试模糊匹配
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


def diagnose_index_status(document_id: str):
    """诊断索引状态"""
    print("=" * 80)
    print("主接线.png 索引状态诊断")
    print("=" * 80)

    for session in get_sync_session():
        # 查询文档
        doc = session.execute(select(Document).where(
            Document.id == document_id)).scalar_one_or_none()
        if not doc:
            print(f"❌ 未找到文档: {document_id}")
            return

        print(f"\n📄 文档信息:")
        print(f"   名称: {doc.name}")
        print(f"   ID: {doc.id}")
        print(f"   状态: {doc.status}")
        print(f"   大小: {doc.size} bytes")
        print(f"   创建时间: {doc.gmt_created}")
        print(f"   更新时间: {doc.gmt_updated}")

        # 计算更新时间距离现在的时间
        if doc.gmt_updated:
            now = datetime.now(timezone.utc)
            elapsed = now - doc.gmt_updated.replace(
                tzinfo=timezone.utc) if doc.gmt_updated.tzinfo is None else now - doc.gmt_updated
            print(
                f"   距离现在: {elapsed.total_seconds():.0f} 秒 ({elapsed.total_seconds()/60:.1f} 分钟)")

        # 查询Collection
        collection = session.execute(select(Collection).where(
            Collection.id == doc.collection_id)).scalar_one_or_none()
        if collection:
            print(f"\n📚 Collection信息:")
            print(f"   ID: {collection.id}")
            print(f"   标题: {collection.title}")
            try:
                config = parseCollectionConfig(collection.config)
                print(
                    f"   向量索引: {'✅ 已启用' if getattr(config, 'enable_vector', False) else '❌ 未启用'}")
                print(
                    f"   Vision索引: {'✅ 已启用' if getattr(config, 'enable_vision', False) else '❌ 未启用'}")
                print(
                    f"   知识图谱: {'✅ 已启用' if getattr(config, 'enable_knowledge_graph', False) else '❌ 未启用'}")
            except Exception as e:
                print(f"   ⚠️  解析配置失败: {e}")

        # 查询所有索引
        indexes = session.execute(
            select(DocumentIndex).where(
                DocumentIndex.document_id == document_id)
        ).scalars().all()

        print(f"\n{'='*80}")
        print("📊 索引状态详情")
        print("="*80)

        index_map = {idx.index_type: idx for idx in indexes}

        for index_type in [DocumentIndexType.VECTOR, DocumentIndexType.VISION, DocumentIndexType.GRAPH]:
            idx = index_map.get(index_type)
            if not idx:
                print(f"\n❓ {index_type.value} 索引: 未找到记录")
                continue

            status_icon_map = {
                DocumentIndexStatus.PENDING: "⏳",
                DocumentIndexStatus.CREATING: "🔄",
                DocumentIndexStatus.ACTIVE: "✅",
                DocumentIndexStatus.FAILED: "❌",
            }
            try:
                status_icon_map[DocumentIndexStatus.SKIPPED] = "⏭️"
            except AttributeError:
                pass

            status_icon = status_icon_map.get(idx.status, "❓")
            status_value = idx.status.value if hasattr(
                idx.status, 'value') else str(idx.status)

            # Handle both enum and string types for index_type
            index_type_value = idx.index_type.value if hasattr(
                idx.index_type, 'value') else str(idx.index_type)

            print(f"\n{status_icon} {index_type_value} 索引:")
            print(f"  - 状态: {status_value}")
            print(f"  - 版本: {idx.version} (已处理: {idx.observed_version})")
            print(f"  - 创建时间: {idx.gmt_created}")
            print(f"  - 更新时间: {idx.gmt_updated}")

            # 计算CREATING状态持续时间
            if idx.status == DocumentIndexStatus.CREATING and idx.gmt_updated:
                now = datetime.now(timezone.utc)
                elapsed = now - idx.gmt_updated.replace(
                    tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
                elapsed_minutes = elapsed.total_seconds() / 60
                print(f"  - ⚠️  CREATING状态已持续: {elapsed_minutes:.1f} 分钟")

                if elapsed_minutes > 10:
                    print(f"  - ❌ 警告: CREATING状态超过10分钟，可能已卡住！")

            if idx.error_message:
                print(f"  - ❌ 错误信息: {idx.error_message}")

        # 诊断分析
        print(f"\n{'='*80}")
        print("🔍 诊断分析")
        print("="*80)

        vector_idx = index_map.get(DocumentIndexType.VECTOR)
        vision_idx = index_map.get(DocumentIndexType.VISION)
        graph_idx = index_map.get(DocumentIndexType.GRAPH)

        # 检查VECTOR索引
        if not vector_idx:
            print("\n❌ VECTOR索引未创建")
            print("   建议: 检查文档解析是否成功")
        elif vector_idx.status == DocumentIndexStatus.CREATING:
            print("\n⚠️  VECTOR索引处于CREATING状态")
            print("   可能原因:")
            print("   - OCR处理时间过长")
            print("   - 向量化任务卡住")
            print("   建议: 查看Celery日志检查OCR和向量化任务")
        elif vector_idx.status == DocumentIndexStatus.FAILED:
            print("\n❌ VECTOR索引创建失败")
            if vector_idx.error_message:
                print(f"   错误: {vector_idx.error_message}")

        # 检查VISION索引
        if not vision_idx:
            print("\n❌ VISION索引未创建")
            print("   建议: 检查Collection配置中是否启用了Vision索引")
        elif vision_idx.status == DocumentIndexStatus.CREATING:
            print("\n⚠️  VISION索引处于CREATING状态（这是关键问题）")
            print("   可能原因:")
            print("   1. Vision LLM API调用超时或卡住")
            print("   2. Vision LLM服务不可用")
            print("   3. 网络连接问题")
            print("   4. Vision LLM配置错误（API密钥、base_url等）")
            print("\n   诊断步骤:")
            print("   1. 检查Vision LLM环境变量:")
            print("      docker exec aperag-celeryworker env | grep VISION_LLM")
            print("   2. 查看Celery日志:")
            print("      docker logs aperag-celeryworker --tail 500 | grep -i vision")
            print("   3. 检查是否有Vision LLM调用日志:")
            print(
                "      docker logs aperag-celeryworker --tail 500 | grep 'Vision LLM generate'")
            print("\n   解决方案:")
            print("   1. 如果Vision LLM调用卡住，等待超时（10分钟）后会自动失败")
            print("   2. 检查Vision LLM服务是否正常")
            print("   3. 检查网络连接和API密钥")
            print("   4. 如果确认卡住，可以手动重置索引状态:")
            print(
                f"      python reset_stuck_indexes.py --document-id {document_id} --index-type VISION")
        elif vision_idx.status == DocumentIndexStatus.FAILED:
            print("\n❌ VISION索引创建失败")
            if vision_idx.error_message:
                print(f"   错误: {vision_idx.error_message}")

        # 检查GRAPH索引
        if not graph_idx:
            print("\n❌ GRAPH索引未创建")
            print("   建议: 检查Collection配置中是否启用了知识图谱")
        elif graph_idx.status == DocumentIndexStatus.CREATING:
            print("\n⚠️  GRAPH索引处于CREATING状态")
            if vision_idx and vision_idx.status == DocumentIndexStatus.CREATING:
                print("   原因: 正在等待VISION索引完成")
                print("   - Graph索引需要等待Vision索引完成后才能继续")
                print("   - 如果Vision索引卡住，Graph索引也会一直等待")
                print("   建议: 先解决Vision索引的问题")
            elif vision_idx and vision_idx.status == DocumentIndexStatus.ACTIVE:
                print("   可能原因:")
                print("   1. 知识图谱构建任务卡住")
                print("   2. LLM服务不可用")
                print("   3. 内容为空，无法提取实体和关系")
                print("   建议: 查看Celery日志检查知识图谱构建任务")
            else:
                print("   可能原因:")
                print("   1. 知识图谱构建任务卡住")
                print("   2. LLM服务不可用")
                print("   建议: 查看Celery日志")
        elif graph_idx.status == DocumentIndexStatus.FAILED:
            print("\n❌ GRAPH索引创建失败")
            if graph_idx.error_message:
                print(f"   错误: {graph_idx.error_message}")

        # 综合建议
        print(f"\n{'='*80}")
        print("💡 综合建议")
        print("="*80)

        if vision_idx and vision_idx.status == DocumentIndexStatus.CREATING:
            print("\n🎯 主要问题: VISION索引卡在CREATING状态")
            print("\n推荐操作顺序:")
            print("1. 检查Vision LLM配置和日志")
            print("2. 如果确认卡住，等待超时（10分钟）或手动重置")
            print("3. 重置后，系统会自动重新创建索引")
        elif graph_idx and graph_idx.status == DocumentIndexStatus.CREATING:
            print("\n🎯 主要问题: GRAPH索引卡在CREATING状态")
            print("\n推荐操作:")
            print("1. 检查知识图谱构建任务的日志")
            print("2. 如果确认卡住，可以手动重置索引状态")
        else:
            print("\n✅ 所有索引状态正常或已失败（有明确错误信息）")

        break


def main():
    """主函数"""
    document_name = "主接线.png"

    print("=" * 80)
    print("主接线.png 索引状态诊断工具")
    print("=" * 80)
    print(f"\n查找文档: {document_name}\n")

    try:
        document = find_document_by_name(document_name)

        if not document:
            print(f"❌ 未找到文档: {document_name}")
            print("\n💡 提示: 如果在本地运行失败，请在Docker容器中运行:")
            print(
                f"   docker exec aperag-celeryworker python diagnose_main_wiring_status.py")
            sys.exit(1)

        diagnose_index_status(document.id)

        print(f"\n{'='*80}")
        print("✅ 诊断完成")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
