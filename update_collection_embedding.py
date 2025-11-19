#!/usr/bin/env python3
"""更新 Collection 的 embedding 模型为 Qwen/Qwen3-Embedding-0.6B"""

from sqlalchemy import select
from aperag.db.models import Collection
from aperag.config import get_sync_session
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def update_collection_embedding(collection_id: str, embedding_model: str = "Qwen/Qwen3-Embedding-0.6B",
                                model_service_provider: str = None, custom_llm_provider: str = None):
    """更新 Collection 的 embedding 模型配置"""

    print("=" * 80)
    print("更新 Collection Embedding 模型")
    print("=" * 80)
    print(f"\nCollection ID: {collection_id}")
    print(f"新 Embedding 模型: {embedding_model}\n")

    for session in get_sync_session():
        # 查询 Collection
        collection = session.execute(select(Collection).where(
            Collection.id == collection_id)).scalar_one_or_none()

        if not collection:
            print("❌ Collection 不存在")
            return False

        print(f"Collection 名称: {collection.id}")
        print(f"用户: {collection.user}\n")

        # 解析现有配置
        try:
            config = json.loads(collection.config) if isinstance(
                collection.config, str) else collection.config
        except Exception as e:
            print(f"❌ 解析 Collection 配置失败: {e}")
            return False

        # 显示当前配置
        current_embedding = config.get("embedding", {})
        print("当前 Embedding 配置:")
        print(f"  模型: {current_embedding.get('model', 'N/A')}")
        print(
            f"  Model Service Provider: {current_embedding.get('model_service_provider', 'N/A')}")
        print(
            f"  Custom LLM Provider: {current_embedding.get('custom_llm_provider', 'N/A')}\n")

        # 更新 embedding 配置
        if "embedding" not in config:
            config["embedding"] = {}

        config["embedding"]["model"] = embedding_model

        # 如果提供了 model_service_provider，则更新
        if model_service_provider:
            config["embedding"]["model_service_provider"] = model_service_provider
        elif "model_service_provider" not in config["embedding"]:
            # 如果没有提供且配置中也没有，需要用户指定
            print("⚠️  警告: 未指定 model_service_provider")
            print("   请确保在配置中已设置，或通过参数提供\n")

        # 如果提供了 custom_llm_provider，则更新
        if custom_llm_provider:
            config["embedding"]["custom_llm_provider"] = custom_llm_provider
        elif "custom_llm_provider" not in config["embedding"]:
            # 如果没有提供且配置中也没有，需要用户指定
            print("⚠️  警告: 未指定 custom_llm_provider")
            print("   请确保在配置中已设置，或通过参数提供\n")

        # 更新 Collection
        collection.config = json.dumps(config, ensure_ascii=False)
        session.add(collection)
        session.commit()
        session.refresh(collection)

        # 验证更新结果
        updated_config = json.loads(collection.config)
        updated_embedding = updated_config.get("embedding", {})

        print("✅ 更新成功！")
        print("\n更新后的 Embedding 配置:")
        print(f"  模型: {updated_embedding.get('model', 'N/A')}")
        print(
            f"  Model Service Provider: {updated_embedding.get('model_service_provider', 'N/A')}")
        print(
            f"  Custom LLM Provider: {updated_embedding.get('custom_llm_provider', 'N/A')}\n")

        return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="更新 Collection 的 embedding 模型")
    parser.add_argument("--collection-id", required=True, help="Collection ID")
    parser.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-0.6B",
                        help="Embedding 模型名称 (默认: Qwen/Qwen3-Embedding-0.6B)")
    parser.add_argument("--model-service-provider",
                        help="Model Service Provider 名称")
    parser.add_argument("--custom-llm-provider", help="Custom LLM Provider 名称")
    args = parser.parse_args()

    try:
        success = update_collection_embedding(
            collection_id=args.collection_id,
            embedding_model=args.embedding_model,
            model_service_provider=args.model_service_provider,
            custom_llm_provider=args.custom_llm_provider
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
