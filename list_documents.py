import sys
import os
from sqlalchemy import select

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aperag.config import get_sync_session
from aperag.db.models import Document

def list_documents(name_query):
    print(f"Searching for documents matching: {name_query}")
    for session in get_sync_session():
        stmt = select(Document).where(Document.name.like(f"%{name_query}%"))
        result = session.execute(stmt)
        documents = result.scalars().all()
        
        for doc in documents:
            print(f"ID: {doc.id}")
            print(f"Name: {doc.name}")
            print(f"Status: {doc.status}")
            print("-" * 20)

if __name__ == "__main__":
    list_documents("变电倒闸操作现场作业风险管控")
