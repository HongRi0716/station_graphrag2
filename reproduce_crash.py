
import asyncio
import os
import logging
import sys
from unittest.mock import MagicMock

# Add /app to python path
sys.path.append("/app")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("🚀 Starting reproduction script...")
    
    try:
        from aperag.service.global_graph_service import GlobalGraphService
        from aperag.db.models import User, Collection, CollectionType
        from aperag.db.ops import async_db_ops
        from aperag.graph import lightrag_manager
        
        print("✅ Imports successful")
        
        # Mock services
        collection_service = MagicMock()
        search_service = MagicMock()
        
        service = GlobalGraphService(
            collection_service=collection_service,
            search_service=search_service
        )
        
        # Mock user
        user = User(id="test_user_id", username="test_user")
        
        # Mock Collection
        col = Collection(id="test_col", title="Test Col", type=CollectionType.DOCUMENT)
        col.config = '{"enable_knowledge_graph": true}'
        
        # Mock async_db_ops.query_collections
        # We need to patch it on the module that uses it, which is global_graph_service
        # But since we imported it, we can patch the instance or the function.
        # global_graph_service imports async_db_ops.
        
        # Let's use unittest.mock.patch
        from unittest.mock import patch
        
        print("🔄 Patching dependencies...")
        
        with patch('aperag.db.ops.async_db_ops') as mock_db_ops, \
             patch('aperag.graph.lightrag_manager.create_lightrag_instance') as mock_create_rag:
            
            # Setup mocks
            f = asyncio.Future()
            f.set_result([col])
            mock_db_ops.query_collections.return_value = f
            
            # Mock RAG instance
            mock_rag = MagicMock()
            # Mock entities_vdb.query to return dummy data
            mock_rag.entities_vdb.query.return_value = [
                {
                    "entity_name": "Test Entity",
                    "distance": 0.1,
                    "content": "Test Content",
                    "source_id": "doc_1",
                    "metadata": {"workspace": "Test Col"}
                }
            ]
            
            # Mock chunk_entity_relation_graph.get_node_edges
            mock_rag.chunk_entity_relation_graph.get_node_edges.return_value = {
                "nodes": [],
                "edges": []
            }
            
            mock_create_rag.return_value = mock_rag
            
            print("▶️ Calling federated_graph_search...")
            result = await service.federated_graph_search(user, "test", top_k=10)
            
            print(f"✅ Result: {result.keys()}")
            print("🎉 Success! No crash with mocked RAG.")
            
    except Exception as e:
        print(f"❌ Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
