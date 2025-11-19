#!/usr/bin/env python3
"""列出所有有Vision索引的文档"""

from sqlalchemy import select, and_
from aperag.db.models import Document, Collection, DocumentIndex, DocumentIndexType
from aperag.config import get_sync_session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def list_vision_documents():
    """列出所有有Vision索引的文档"""
    
    print("=" * 80)
    print("查找有Vision索引的文档")
    print("=" * 80)
    
    for session in get_sync_session():
        # 查询所有有Vision索引的文档
        vision_indices = session.execute(
            select(DocumentIndex).where(
                DocumentIndex.index_type == DocumentIndexType.VISION
            ).order_by(DocumentIndex.gmt_created.desc())
        ).scalars().all()
        
        if not vision_indices:
            print("\n❌ 未找到任何Vision索引")
            return
        
        print(f"\n找到 {len(vision_indices)} 个Vision索引\n")
        
        for i, vision_index in enumerate(vision_indices[:20], 1):  # 只显示前20个
            doc = session.execute(
                select(Document).where(Document.id == vision_index.document_id)
            ).scalar_one_or_none()
            
            if doc:
                collection = session.execute(
                    select(Collection).where(Collection.id == doc.collection_id)
                ).scalar_one_or_none()
                
                print(f"{i}. 文档名称: {doc.name}")
                print(f"   文档ID: {doc.id}")
                print(f"   Collection: {collection.name if collection else 'N/A'}")
                print(f"   Vision索引状态: {vision_index.status}")
                print(f"   创建时间: {vision_index.gmt_created}")
                print()
        
        if len(vision_indices) > 20:
            print(f"... 还有 {len(vision_indices) - 20} 个文档未显示")
        
        break


if __name__ == "__main__":
    try:
        list_vision_documents()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

