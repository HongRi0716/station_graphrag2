# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from aperag.db.models import Collection
from aperag.db.ops import async_db_ops
from aperag.flow.base.models import BaseNodeRunner, SystemInput, register_node_runner
from aperag.query.query import DocumentWithScore
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)


# User input model for graph search node
class GraphSearchInput(BaseModel):
    top_k: int = Field(5, description="Number of top results to return")
    collection_ids: Optional[list[str]] = Field(default_factory=list, description="Collection IDs")
    query_mode: str = Field("contextual", description="Query mode: 'contextual' or 'global'")


# User output model for graph search node
class GraphSearchOutput(BaseModel):
    docs: List[DocumentWithScore]


# Database operations interface
class GraphSearchRepository:
    """Repository interface for graph search database operations"""

    async def get_collection(self, user, collection_id: str) -> Optional[Collection]:
        """Get collection by ID for the user"""
        return await async_db_ops.query_collection(user, collection_id)

    async def get_first_collection(self, user) -> Optional[Collection]:
        """Get the first collection for the user (for config context)"""
        collections = await async_db_ops.query_collections(user, page=1, page_size=1)
        return collections[0] if collections else None


# Business logic service
class GraphSearchService:
    """Service class containing graph search business logic"""

    def __init__(self, repository: GraphSearchRepository):
        self.repository = repository

    async def execute_graph_search(
        self, user, query: str, top_k: int, collection_ids: List[str], query_mode: str = "contextual"
    ) -> List[DocumentWithScore]:
        """Execute graph search with given parameters"""
        collection = None
        if collection_ids:
            collection = await self.repository.get_collection(user, collection_ids[0])
        elif query_mode == "global":
            # For global search, if no collection specified, use any collection to get LLM config
            collection = await self.repository.get_first_collection(user)

        if not collection:
            return []

        config = parseCollectionConfig(collection.config)
        # For global search, we might relax the check, but generally we need graph config
        if not config.enable_knowledge_graph:
            logger.warning(f"Collection {collection.id} does not have knowledge graph enabled")
            if query_mode == "contextual":
                return []

        # Import LightRAG and run as in _run_light_rag
        from aperag.graph import lightrag_manager
        from aperag.graph.lightrag import QueryParam

        rag = await lightrag_manager.create_lightrag_instance(collection)

        if query_mode == "global":
            # Execute global search
            entities = await rag.query_global(query=query, top_k=top_k)
            if not entities:
                return []
            
            # Format result
            import json
            # Create a readable summary for the text field
            text_summary = f"Found {len(entities)} global entities:\n"
            for entity in entities[:10]: # Show top 10 in text summary
                text_summary += f"- {entity.get('entity_name')} (Workspace: {entity.get('workspace')})\n"
            
            return [
                DocumentWithScore(
                    text=text_summary, 
                    metadata={
                        "recall_type": "graph_search_global",
                        "entities": entities
                    }
                )
            ]
        else:
            # Execute contextual search (hybrid)
            param: QueryParam = QueryParam(
                mode="hybrid",
                only_need_context=True,
                top_k=top_k,
            )
            context = await rag.aquery_context(query=query, param=param)
            if not context:
                return []

            # Return documents with graph search metadata
            return [DocumentWithScore(text=context, metadata={"recall_type": "graph_search"})]


@register_node_runner(
    "graph_search",
    input_model=GraphSearchInput,
    output_model=GraphSearchOutput,
)
class GraphSearchNodeRunner(BaseNodeRunner):
    def __init__(self):
        self.repository = GraphSearchRepository()
        self.service = GraphSearchService(self.repository)

    async def run(self, ui: GraphSearchInput, si: SystemInput) -> Tuple[GraphSearchOutput, dict]:
        """
        Run graph search node. ui: user configurable params; si: system injected params (SystemInput).
        Returns (uo, so)
        """
        docs = await self.service.execute_graph_search(
            user=si.user, query=si.query, top_k=ui.top_k, collection_ids=ui.collection_ids or []
        )

        return GraphSearchOutput(docs=docs), {}
