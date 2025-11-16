#!/usr/bin/env python3
"""
Docker环境图片处理失败诊断脚本

用于检查Vision索引创建失败的原因
"""

import sys
import os
import json
import base64
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from aperag.config import settings
    from aperag.db.models import Document, DocumentIndex, DocumentIndexType, DocumentIndexStatus, Collection
    from aperag.config import get_sync_session
    from aperag.schema.utils import parseCollectionConfig
    from aperag.llm.embed.base_embedding import get_collection_embedding_service_sync
    from aperag.llm.completion.base_completion import get_collection_completion_service_sync
    from aperag.llm.llm_error_types import InvalidConfigurationError, CompletionError
    from sqlalchemy import select, and_
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def check_environment_variables():
    """检查Vision相关的环境变量"""
    print("=" * 80)
    print("1. 检查环境变量配置")
    print("=" * 80)
    
    vision_vars = {
        "VISION_LLM_PROVIDER": os.environ.get("VISION_LLM_PROVIDER"),
        "VISION_LLM_MODEL": os.environ.get("VISION_LLM_MODEL"),
        "VISION_LLM_BASE_URL": os.environ.get("VISION_LLM_BASE_URL"),
        "VISION_LLM_API_KEY": os.environ.get("VISION_LLM_API_KEY"),
    }
    
    issues = []
    for var_name, var_value in vision_vars.items():
        if var_value:
            # 隐藏API密钥的敏感信息
            display_value = var_value if "KEY" not in var_name else ("*" * 20 if var_value else "未设置")
            print(f"  ✅ {var_name}: {display_value}")
        else:
            print(f"  ❌ {var_name}: 未设置")
            if "KEY" in var_name:
                issues.append(f"{var_name} 未配置（必需）")
            elif "PROVIDER" in var_name or "MODEL" in var_name:
                issues.append(f"{var_name} 未配置（建议配置）")
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个配置问题:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ 环境变量配置正常")
    
    return len(issues) == 0


def check_document_vision_index(document_id: str):
    """检查特定文档的Vision索引状态"""
    print("\n" + "=" * 80)
    print(f"2. 检查文档Vision索引状态 (Document ID: {document_id})")
    print("=" * 80)
    
    for session in get_sync_session():
        # 查询文档
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_result = session.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()
        
        if not document:
            print(f"❌ 未找到文档: {document_id}")
            return False
        
        print(f"\n📄 文档信息:")
        print(f"  名称: {document.name}")
        print(f"  状态: {document.status}")
        print(f"  大小: {document.size} bytes")
        
        # 查询Collection
        collection_stmt = select(Collection).where(Collection.id == document.collection_id)
        collection_result = session.execute(collection_stmt)
        collection = collection_result.scalar_one_or_none()
        
        if collection:
            print(f"\n📚 Collection信息:")
            print(f"  名称: {collection.name}")
            
            # 检查Vision是否启用
            try:
                config = parseCollectionConfig(collection.config)
                enable_vision = config.enable_vision if hasattr(config, 'enable_vision') else False
                print(f"  Vision索引启用: {'✅ 已启用' if enable_vision else '❌ 未启用'}")
                
                if not enable_vision:
                    print("\n⚠️  Vision索引未启用，无法处理图片")
                    return False
            except Exception as e:
                print(f"  ⚠️  解析配置失败: {e}")
        
        # 查询Vision索引
        index_stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.index_type == DocumentIndexType.VISION
            )
        )
        index_result = session.execute(index_stmt)
        vision_index = index_result.scalar_one_or_none()
        
        if not vision_index:
            print(f"\n❌ 未找到Vision索引记录")
            print("   可能原因:")
            print("   - Vision索引尚未创建")
            print("   - Vision索引创建失败但未记录")
            return False
        
        print(f"\n📊 Vision索引状态:")
        print(f"  状态: {vision_index.status.value}")
        print(f"  版本: {vision_index.version}")
        print(f"  创建时间: {vision_index.gmt_created}")
        print(f"  更新时间: {vision_index.gmt_updated}")
        
        if vision_index.error_message:
            print(f"\n❌ 错误信息:")
            print(f"   {vision_index.error_message}")
            return False
        
        if vision_index.index_data:
            try:
                index_data = json.loads(vision_index.index_data)
                ctx_ids = index_data.get("context_ids", [])
                print(f"\n✅ 索引数据:")
                print(f"  向量数量: {len(ctx_ids)}")
                if ctx_ids:
                    print(f"  前5个向量ID: {ctx_ids[:5]}")
            except:
                print(f"\n⚠️  无法解析索引数据")
        
        if vision_index.status == DocumentIndexStatus.FAILED:
            print(f"\n❌ Vision索引创建失败")
            return False
        elif vision_index.status == DocumentIndexStatus.COMPLETED:
            print(f"\n✅ Vision索引创建成功")
            return True
        else:
            print(f"\n⏳ Vision索引状态: {vision_index.status.value}")
            return False


def check_vision_services(collection_id: str):
    """检查Vision相关的服务配置"""
    print("\n" + "=" * 80)
    print("3. 检查Vision服务配置")
    print("=" * 80)
    
    for session in get_sync_session():
        collection_stmt = select(Collection).where(Collection.id == collection_id)
        collection_result = session.execute(collection_stmt)
        collection = collection_result.scalar_one_or_none()
        
        if not collection:
            print(f"❌ 未找到Collection: {collection_id}")
            return False
        
        print(f"\n📚 Collection: {collection.name}")
        
        # 检查Embedding服务
        try:
            embedding_svc, vector_size = get_collection_embedding_service_sync(collection)
            is_multimodal = embedding_svc.is_multimodal()
            print(f"\n🔤 Embedding服务:")
            print(f"  向量维度: {vector_size}")
            print(f"  多模态支持: {'✅ 支持' if is_multimodal else '❌ 不支持'}")
            
            if not is_multimodal:
                print("  ⚠️  Embedding服务不支持多模态，无法直接处理图片")
        except Exception as e:
            print(f"  ❌ Embedding服务配置错误: {e}")
            return False
        
        # 检查Completion服务（Vision LLM）
        try:
            completion_svc = get_collection_completion_service_sync(collection)
            is_vision = completion_svc.is_vision_model() if completion_svc else False
            print(f"\n🧠 Completion服务 (Vision LLM):")
            if completion_svc:
                print(f"  模型: {completion_svc.model}")
                print(f"  Vision支持: {'✅ 支持' if is_vision else '❌ 不支持'}")
                
                if not is_vision:
                    print("  ⚠️  Completion服务不支持Vision，无法进行vision-to-text转换")
                    print("  💡 建议: 配置VISION_LLM环境变量")
            else:
                print("  ❌ Completion服务未配置")
        except (InvalidConfigurationError, CompletionError) as e:
            print(f"  ⚠️  Completion服务配置错误: {e}")
            print("  💡 建议: 配置VISION_LLM环境变量用于图片分析")
        except Exception as e:
            print(f"  ❌ 检查Completion服务时出错: {e}")
        
        # 检查是否至少有一种方式可以处理图片
        if not is_multimodal and not is_vision:
            print(f"\n❌ 无法处理图片:")
            print("   - Embedding服务不支持多模态")
            print("   - Completion服务不支持Vision")
            print("\n💡 解决方案:")
            print("   1. 配置多模态Embedding模型，或")
            print("   2. 配置VISION_LLM环境变量（推荐）")
            return False
        else:
            print(f"\n✅ 至少有一种方式可以处理图片")
            return True


def check_vector_store():
    """检查向量存储连接"""
    print("\n" + "=" * 80)
    print("4. 检查向量存储连接")
    print("=" * 80)
    
    try:
        from aperag.config import get_vector_db_connector
        from aperag.utils.utils import generate_vector_db_collection_name
        
        # 使用一个测试collection名称
        test_collection_name = generate_vector_db_collection_name(collection_id="test")
        vector_store_adaptor = get_vector_db_connector(collection=test_collection_name)
        
        print("✅ 向量存储连接成功")
        print(f"  类型: {settings.vector_db_type}")
        return True
    except Exception as e:
        print(f"❌ 向量存储连接失败: {e}")
        print("\n💡 检查:")
        print("   - VECTOR_DB_TYPE 配置是否正确")
        print("   - VECTOR_DB_CONTEXT 配置是否正确")
        print("   - 向量存储服务是否运行")
        return False


def check_docker_services():
    """检查Docker服务状态"""
    print("\n" + "=" * 80)
    print("5. 检查Docker服务状态（需要手动执行）")
    print("=" * 80)
    
    print("\n请执行以下命令检查服务状态:")
    print("\n1. 检查Celery Worker:")
    print("   docker ps | grep celeryworker")
    print("   docker logs aperag-celeryworker --tail 100 | grep -i vision")
    
    print("\n2. 检查向量存储:")
    print("   docker ps | grep qdrant")
    
    print("\n3. 检查网络连接:")
    print("   docker exec aperag-celeryworker ping -c 3 aperag-qdrant")
    
    print("\n4. 检查Vision LLM API连接:")
    vision_llm_url = os.environ.get("VISION_LLM_BASE_URL", "")
    if vision_llm_url:
        print(f"   docker exec aperag-celeryworker curl -f {vision_llm_url}/health")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="诊断Docker环境中图片处理失败的原因")
    parser.add_argument(
        "--document-id",
        type=str,
        help="要检查的文档ID（可选）"
    )
    parser.add_argument(
        "--collection-id",
        type=str,
        help="要检查的Collection ID（可选）"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Docker环境图片处理失败诊断工具")
    print("=" * 80)
    
    # 1. 检查环境变量
    env_ok = check_environment_variables()
    
    # 2. 检查向量存储
    vector_store_ok = check_vector_store()
    
    # 3. 检查文档Vision索引（如果提供了document_id）
    if args.document_id:
        doc_ok = check_document_vision_index(args.document_id)
    else:
        doc_ok = None
        print("\n💡 提示: 使用 --document-id 参数检查特定文档的Vision索引状态")
    
    # 4. 检查Vision服务配置（如果提供了collection_id）
    if args.collection_id:
        service_ok = check_vision_services(args.collection_id)
    else:
        service_ok = None
        print("\n💡 提示: 使用 --collection-id 参数检查Collection的Vision服务配置")
    
    # 5. Docker服务检查提示
    check_docker_services()
    
    # 总结
    print("\n" + "=" * 80)
    print("诊断总结")
    print("=" * 80)
    
    issues = []
    if not env_ok:
        issues.append("环境变量配置问题")
    if not vector_store_ok:
        issues.append("向量存储连接问题")
    if doc_ok is False:
        issues.append("文档Vision索引问题")
    if service_ok is False:
        issues.append("Vision服务配置问题")
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 建议:")
        print("   1. 检查并修复上述问题")
        print("   2. 查看Celery Worker日志获取详细错误信息")
        print("   3. 确保VISION_LLM环境变量已正确配置")
        print("   4. 重启Celery Worker: docker restart aperag-celeryworker")
    else:
        print("\n✅ 未发现明显问题")
        print("   如果图片处理仍然失败，请查看Celery Worker日志获取详细错误信息")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

