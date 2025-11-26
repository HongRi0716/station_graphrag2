"""
简化版查询脚本 - 直接查询数据库
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func
from aperag.db.database import get_async_session
from aperag.db.models import Collection, Document, Chunk


async def check_data():
    """检查数据库中的数据"""
    user_id = "user5220eb7ee134ad0d"
    
    print(f"=" * 80)
    print(f"查询用户 {user_id} 的数据")
    print(f"=" * 80)
    
    async with get_async_session() as session:
        # 1. 查询知识库
        print("\n【1】查询知识库...")
        stmt = select(Collection).where(Collection.user_id == user_id)
        result = await session.execute(stmt)
        collections = result.scalars().all()
        
        if not collections:
            print("❌ 没有找到知识库")
            return
        
        print(f"✅ 找到 {len(collections)} 个知识库:\n")
        collection_ids = []
        
        for i, col in enumerate(collections, 1):
            print(f"{i}. ID: {col.id}")
            print(f"   标题: {col.title}")
            print(f"   描述: {col.description}")
            print(f"   类型: {col.type}")
            print()
            collection_ids.append(col.id)
        
        # 2. 查询每个知识库的文档
        print("\n【2】查询文档...")
        for col_id in collection_ids:
            stmt = select(func.count(Document.id)).where(
                Document.collection_id == col_id
            )
            result = await session.execute(stmt)
            doc_count = result.scalar()
            
            print(f"知识库 {col_id}: {doc_count} 个文档")
            
            # 获取前5个文档
            if doc_count > 0:
                stmt = select(Document).where(
                    Document.collection_id == col_id
                ).limit(5)
                result = await session.execute(stmt)
                docs = result.scalars().all()
                
                for doc in docs:
                    print(f"  - {doc.title}")
                    if doc.content:
                        preview = doc.content[:100].replace('\n', ' ')
                        print(f"    内容: {preview}...")
        
        # 3. 查询 chunks（向量化的文本块）
        print("\n【3】查询文本块（Chunks）...")
        for col_id in collection_ids:
            stmt = select(func.count(Chunk.id)).where(
                Chunk.collection_id == col_id
            )
            result = await session.execute(stmt)
            chunk_count = result.scalar()
            
            print(f"知识库 {col_id}: {chunk_count} 个文本块")
            
            # 获取示例 chunk
            if chunk_count > 0:
                stmt = select(Chunk).where(
                    Chunk.collection_id == col_id
                ).limit(3)
                result = await session.execute(stmt)
                chunks = result.scalars().all()
                
                for chunk in chunks:
                    preview = chunk.content[:80].replace('\n', ' ') if chunk.content else "无内容"
                    print(f"  - {preview}...")
                    print(f"    向量维度: {len(chunk.embedding) if chunk.embedding else 0}")
        
        # 4. 搜索测试
        print("\n【4】搜索关键词测试...")
        test_keywords = ["运维", "班组", "变电站", "设备"]
        
        for keyword in test_keywords:
            stmt = select(func.count(Chunk.id)).where(
                Chunk.collection_id.in_(collection_ids),
                Chunk.content.like(f"%{keyword}%")
            )
            result = await session.execute(stmt)
            count = result.scalar()
            
            print(f"关键词 '{keyword}': {count} 个匹配的文本块")


if __name__ == "__main__":
    asyncio.run(check_data())
