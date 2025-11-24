import sys
import os
import json
from sqlalchemy import select

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aperag.config import get_sync_session
from aperag.db.models import Document, DocumentIndex, Collection

def diagnose(document_id):
    print(f"Diagnosing document: {document_id}")
    
    for session in get_sync_session():
        # Check Document
        doc = session.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
        if not doc:
            print("Document not found")
            return
            
        print(f"Document Status: {doc.status}")
        
        # Check Collection
        collection = session.execute(select(Collection).where(Collection.id == doc.collection_id)).scalar_one_or_none()
        if collection:
            print(f"Collection ID: {collection.id}")
            # print(f"Collection Name: {collection.name}") # Avoid printing name to prevent encoding issues
            print(f"Collection Config: {collection.config}")
        else:
            print("Collection not found")

        # Check Indexes
        indexes = session.execute(select(DocumentIndex).where(DocumentIndex.document_id == document_id)).scalars().all()
        print(f"Found {len(indexes)} indexes")
        
        for idx in indexes:
            print(f"Index Type: {idx.index_type}")
            print(f"  Status: {idx.status}")
            print(f"  Version: {idx.version}")
            print(f"  Observed Version: {idx.observed_version}")
            print(f"  Error Message: {idx.error_message}")
            print(f"  Last Reconciled: {idx.gmt_last_reconciled}")
            print("-" * 20)

if __name__ == "__main__":
    # Set stdout to utf-8 to avoid encoding errors if possible, though we avoided printing names
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    diagnose("doccced29fcc4927c9b")
