
import sys
import os
import logging
from sqlalchemy import select, and_

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from aperag.config import get_sync_session
from aperag.db.models import DocumentIndex, DocumentIndexStatus
from aperag.utils.constant import IndexAction

def debug_reconciler():
    print("Debugging reconciler logic...")
    
    for session in get_sync_session():
        # Check raw values
        stmt = select(DocumentIndex).where(DocumentIndex.document_id == 'doccced29fcc4927c9b')
        indexes = session.execute(stmt).scalars().all()
        print(f"Found {len(indexes)} indexes for document:")
        for idx in indexes:
            print(f"  Type: {idx.index_type}")
            print(f"  Status: {idx.status} (Type: {type(idx.status)})")
            print(f"  Version: {idx.version} (Type: {type(idx.version)})")
            print(f"  Observed Version: {idx.observed_version} (Type: {type(idx.observed_version)})")
            
            # Test condition manually
            is_pending = idx.status == DocumentIndexStatus.PENDING
            version_mismatch = idx.observed_version < idx.version
            is_version_1 = idx.version == 1
            
            print(f"  Condition Check:")
            print(f"    Status == PENDING: {is_pending} (Expected: {DocumentIndexStatus.PENDING})")
            print(f"    Observed < Version: {version_mismatch}")
            print(f"    Version == 1: {is_version_1}")
            
            if is_pending and version_mismatch and is_version_1:
                print("  MATCHES RECONCILER CONDITION!")
            else:
                print("  DOES NOT MATCH!")

if __name__ == "__main__":
    debug_reconciler()
