#!/usr/bin/env python3
"""修复数据库中 embedding 模型被错误分类为 completion 的问题"""

from sqlalchemy import select, and_
from aperag.db.models import LLMProviderModel, APIType
from aperag.config import get_sync_session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def fix_embedding_models():
    """查找并修复被错误分类为 completion 的 embedding 模型"""

    print("=" * 80)
    print("修复 Embedding 模型分类问题")
    print("=" * 80)
    print("\n查找被错误分类为 completion 的 embedding 模型...\n")

    # 明确的 embedding 模型名称模式（必须包含这些关键词）
    embedding_keywords = [
        'embedding', 'embed', 'bge-', 'e5-', 'text-embedding',
        'ada-002', 'text-embedding-ada', 'jina-embeddings',
        'instructor-', 'multilingual-e5'
    ]

    # 明确的 embedding 模型完整名称模式
    embedding_exact_patterns = [
        'qwen3-embedding', 'qwen/embedding', 'bge-m3', 'bge-large',
        'text-embedding-3', 'text-embedding-ada-002'
    ]

    fixed_count = 0

    for session in get_sync_session():
        # 查找所有 completion 类型的模型
        completion_models = session.execute(
            select(LLMProviderModel).where(
                and_(
                    LLMProviderModel.api == APIType.COMPLETION,
                    LLMProviderModel.gmt_deleted.is_(None)
                )
            )
        ).scalars().all()

        print(f"找到 {len(completion_models)} 个 completion 模型\n")

        for model in completion_models:
            model_name_lower = model.model.lower()

            # 检查是否是明确的 embedding 模型
            # 1. 检查完整模式匹配
            is_embedding = any(
                pattern in model_name_lower for pattern in embedding_exact_patterns)

            # 2. 检查关键词（但排除 completion 模型的特征）
            if not is_embedding:
                # 必须包含 embedding 相关关键词，且不包含 completion 特征
                has_embedding_keyword = any(
                    keyword in model_name_lower for keyword in embedding_keywords)
                # 排除明显的 completion 模型特征
                is_completion_model = any(
                    keyword in model_name_lower for keyword in [
                        'chat', 'instruct', 'completion', 'generation',
                        'distill', 'r1', 'reasoning'
                    ])

                if has_embedding_keyword and not is_completion_model:
                    is_embedding = True

            if is_embedding:
                print(f"⚠️  发现错误分类的模型:")
                print(f"   Provider: {model.provider_name}")
                print(f"   模型名称: {model.model}")
                # Handle both enum and string types
                api_value = model.api.value if hasattr(
                    model.api, 'value') else str(model.api)
                print(f"   当前 API 类型: {api_value}")
                print(f"   应该为: embedding")

                # 检查是否已经存在正确的 embedding 记录
                existing_embedding = session.execute(
                    select(LLMProviderModel).where(
                        and_(
                            LLMProviderModel.provider_name == model.provider_name,
                            LLMProviderModel.api == APIType.EMBEDDING,
                            LLMProviderModel.model == model.model,
                            LLMProviderModel.gmt_deleted.is_(None)
                        )
                    )
                ).scalar_one_or_none()

                if existing_embedding:
                    print(f"   ✅ 已存在正确的 embedding 记录，删除错误的 completion 记录")
                    # 软删除错误的 completion 记录
                    from datetime import datetime, timezone
                    model.gmt_deleted = datetime.now(timezone.utc)
                    session.add(model)
                else:
                    print(f"   🔧 修复: 将 API 类型从 completion 改为 embedding")
                    # 更新 API 类型
                    model.api = APIType.EMBEDDING
                    session.add(model)
                    fixed_count += 1

                print()

        if fixed_count > 0:
            session.commit()
            print(f"✅ 已修复 {fixed_count} 个模型的分类")
        else:
            print("✅ 未发现需要修复的模型")

        break


if __name__ == "__main__":
    try:
        fix_embedding_models()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
