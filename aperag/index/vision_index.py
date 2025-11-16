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

import base64
import json
import logging
import time
from typing import Any, List

from llama_index.core.schema import TextNode
from sqlalchemy import and_, select

from aperag.config import get_vector_db_connector
from aperag.db.models import Collection
from aperag.index.base import BaseIndexer, IndexResult, IndexType
from aperag.llm.completion.base_completion import get_collection_completion_service_sync
from aperag.llm.embed.base_embedding import get_collection_embedding_service_sync
from aperag.llm.llm_error_types import (
    CompletionError,
    InvalidConfigurationError,
    LLMError,
    is_retryable_error,
)
from aperag.schema.utils import parseCollectionConfig
from aperag.utils.utils import generate_vector_db_collection_name

logger = logging.getLogger(__name__)


def _get_vision_llm_completion_service(collection: Collection):
    """
    Get Vision LLM completion service from environment variables.

    Returns:
        CompletionService if VISION_LLM is configured, None otherwise
    """
    import os
    from aperag.llm.completion.completion_service import CompletionService
    from aperag.db.ops import db_ops

    # Check if VISION_LLM is configured via environment variables
    vision_llm_provider = os.environ.get("VISION_LLM_PROVIDER")
    vision_llm_model = os.environ.get("VISION_LLM_MODEL")
    vision_llm_base_url = os.environ.get("VISION_LLM_BASE_URL")
    vision_llm_api_key = os.environ.get("VISION_LLM_API_KEY")

    if not all([vision_llm_provider, vision_llm_model, vision_llm_base_url, vision_llm_api_key]):
        return None

    try:
        # Get provider information
        llm_provider = db_ops.query_llm_provider_by_name(vision_llm_provider)
        if not llm_provider:
            logger.warning(
                f"Vision LLM provider '{vision_llm_provider}' not found in database")
            return None

        # Get API key (try user's key first, then use environment variable)
        api_key = db_ops.query_provider_api_key(
            vision_llm_provider, collection.user, need_public=True)
        if not api_key:
            api_key = vision_llm_api_key

        if not api_key:
            logger.warning(
                f"Vision LLM API key not found for provider '{vision_llm_provider}'")
            return None

        # Use provider's base_url if available, otherwise use environment variable
        base_url = llm_provider.base_url or vision_llm_base_url

        # Create completion service with vision=True flag
        completion_service = CompletionService(
            provider=llm_provider.completion_dialect or "openai",
            model=vision_llm_model,
            base_url=base_url,
            api_key=api_key,
            vision=True,  # Explicitly mark as vision model
        )

        return completion_service
    except Exception as e:
        logger.warning(f"Failed to create Vision LLM completion service: {e}")
        return None


class VisionIndexer(BaseIndexer):
    """Indexer for creating vision-based indexes."""

    def __init__(self):
        super().__init__(IndexType.VISION)

    def is_enabled(self, collection: Collection) -> bool:
        """Check if vision index is enabled for the collection."""
        try:
            config = parseCollectionConfig(collection.config)
            return config.enable_vision
        except Exception:
            return False

    def create_index(
        self, document_id: str, content: str, doc_parts: List[Any], collection: Collection, **kwargs
    ) -> IndexResult:
        """Create vision index for a document."""
        if not self.is_enabled(collection):
            return IndexResult(
                success=True,
                index_type=self.index_type,
                metadata={"message": "Vision index is disabled.",
                          "status": "skipped"},
            )

        embedding_svc, vector_size = get_collection_embedding_service_sync(
            collection)

        # Try to get Vision LLM from environment variables first, fallback to collection LLM
        completion_svc = None

        # Priority 1: Try VISION_LLM from environment variables
        completion_svc = _get_vision_llm_completion_service(collection)
        if completion_svc:
            logger.info(
                f"Using VISION_LLM from environment variables: {completion_svc.model}")
        else:
            # Priority 2: Fallback to collection's completion service
            try:
                completion_svc = get_collection_completion_service_sync(
                    collection)
                if completion_svc and completion_svc.is_vision_model():
                    logger.info(
                        f"Using collection's completion service for vision: {completion_svc.model}")
            except (InvalidConfigurationError, CompletionError):
                pass

        if not embedding_svc.is_multimodal() and (completion_svc is None or not completion_svc.is_vision_model()):
            return IndexResult(
                success=True,
                index_type=self.index_type,
                metadata={
                    "message": "Neither multimodal embedding nor vision completion model is configured.",
                    "status": "skipped",
                },
            )

        # Type info are lost, can't just check `isinstance(part, AssetBinPart)`
        image_parts = [
            part for part in doc_parts if hasattr(part, "mime_type") and (part.mime_type or "").startswith("image/")
        ]
        if not image_parts:
            return IndexResult(
                success=True, index_type=self.index_type, metadata={"message": "No images found to index."}
            )

        vector_store_adaptor = get_vector_db_connector(
            collection=generate_vector_db_collection_name(
                collection_id=collection.id)
        )
        all_ctx_ids = []

        # Path A: Pure Vision Embedding
        if embedding_svc.is_multimodal():
            try:
                nodes: List[TextNode] = []
                image_uris = []
                for part in image_parts:
                    b64_image = base64.b64encode(part.data).decode("utf-8")
                    mime_type = part.mime_type or "image/png"
                    data_uri = f"data:{mime_type};base64,{b64_image}"
                    image_uris.append(data_uri)
                    metadata = part.metadata.copy()
                    metadata["collection_id"] = collection.id
                    metadata["document_id"] = document_id
                    metadata["source"] = metadata.get("name", "")
                    metadata["asset_id"] = part.asset_id
                    metadata["mimetype"] = mime_type
                    metadata["indexer"] = "vision"
                    metadata["index_method"] = "multimodal_embedding"
                    nodes.append(TextNode(text="", metadata=metadata))

                vectors = embedding_svc.embed_documents(image_uris)
                for i, node in enumerate(nodes):
                    node.embedding = vectors[i]

                ctx_ids = vector_store_adaptor.connector.store.add(nodes)
                all_ctx_ids.extend(ctx_ids)
                logger.info(
                    f"Created {len(ctx_ids)} direct vision vectors for document {document_id}")
            except Exception as e:
                logger.error(
                    f"Failed to create pure vision embedding for document {document_id}: {e}", exc_info=True)
                return IndexResult(
                    success=False,
                    index_type=self.index_type,
                    metadata={
                        "message": f"Failed to create pure vision embedding for document {document_id}: {e}",
                        "status": "failed",
                    },
                )

        # Path B: Vision-to-Text
        if completion_svc and completion_svc.is_vision_model():
            try:
                text_nodes: List[TextNode] = []
                for part in image_parts:
                    b64_image = base64.b64encode(part.data).decode("utf-8")
                    mime_type = part.mime_type or "image/png"
                    data_uri = f"data:{mime_type};base64,{b64_image}"

                    prompt = """Extract image content with high fidelity. Use Markdown. **CRITICAL: Be concise, group items, use natural language for relationships, optimize for RAG.**

**1. Content Type**: Pure Diagram / Pure Document / Mixed Content / Hybrid Page

**2. Overall Summary**: One paragraph. For electrical diagrams: facility name, voltage levels, date, topology. For documents: category, key topics.

**3. Text Extraction**: Extract ALL text labels, names, identifiers. Preserve original language and reading order. Use Markdown, LaTeX for formulas (`$$...$$`), GFM for tables.

**4. Specialized Analysis**:

**For Electrical Single-Line Diagrams (主接线图)**:
- **System Overview**: Facility name, voltage levels (e.g., 500kV/220kV/35kV), date, topology (e.g., "双主变配置"), main transformer voltage ratios
  
- **Voltage Level Sections** (describe each separately):
  - **500kV**: Busbars, lines (full names), circuit breakers (all IDs), connections to transformers
  - **220kV**: All busbars, all lines (full names), circuit breakers/disconnectors (all IDs), connections
  - **35kV**: Busbars, station service transformers (站用变, all numbers), reactors (低抗, with associations), lines, all component IDs

- **Key Equipment** (comprehensive, use ranges only when >20 items):
  - Main Transformers: All with voltage ratios
  - Circuit Breakers: Grouped by voltage, list all IDs (use ranges if >20)
  - Busbars: All full names
  - Lines: All line names grouped by voltage
  - Station Service Transformers: All (0号/1号/2号站用变)
  - Reactors: All with associations (e.g., "1号主变1号低抗")
  - Other: Disconnectors, CTs, VTs, grounding switches

- **Connection Relationships** (natural language, complete):
  - Main Transformer Connections: How each connects to voltage levels (e.g., "1号主变高压侧通过断路器50132连接500kV I母，中压侧通过断路器20140连接220kV IB母，低压侧连接35kV I母")
  - Line Connections: Connection paths for major lines (e.g., "汤州5354线通过断路器5013、隔离开关50132连接500kV I母")
  - Busbar Connections: How busbars connect to transformers and lines
  - Power Flow: Complete flow from input to output (e.g., "500kV进线→500kV母线→主变→220kV母线→220kV出线，同时主变→35kV母线→站用变/35kV出线")
  - Redundancy: Backup paths and redundancy configuration
  - Equipment Associations: Which equipment belongs to which line

- **Component Identifiers**: Extract all numerical IDs, group by equipment type, note naming patterns

**For Other Diagram Types**: Adapt structure to diagram type

**Document/Text/Table/Chart Regions**: Structure, key terms, main content, relationships

**5. Object Recognition**: List significant objects/entities (grouped, no repetition)

**Output Format:**
```markdown
## Content Type: [type]

## Overall Summary
[Facility name, voltage levels, date, topology]

## Detailed Text Extraction
[ALL text labels, names, identifiers]

## Diagram Regions (if applicable)
### Diagram 1: [Type/Title]
**System Overview**: [Facility, voltages, date, topology]

**Voltage Level Sections**:
- **500kV**: [Busbars, lines, equipment, connections]
- **220kV**: [Busbars, lines, equipment, connections]
- **35kV**: [Busbars, lines, equipment, connections]

**Key Equipment**: 
- Main Transformers: [all with ratios]
- Circuit Breakers: [grouped by voltage, all IDs]
- Busbars: [all names]
- Lines: [all names by voltage]
- Station Service Transformers: [all]
- Reactors: [all with associations]
- Other: [disconnectors, CTs, VTs, etc.]

**Connection Relationships**: 
- Main Transformer Connections: [how each connects]
- Line Connections: [paths for major lines]
- Busbar Connections: [how busbars connect]
- Power Flow: [complete flow description]
- Redundancy: [backup paths]
- Equipment Associations: [equipment-line mappings]

**Component Identifiers**: [All IDs grouped by type]

## Document/Table/Chart Regions (if applicable)
[Structured content]

## Object Recognition
[Grouped list]
```

**Rules**: 
- Max 3000 words (balance completeness and efficiency)
- Extract ALL equipment names, line names, identifiers - completeness critical
- Group using ranges only when >20 items of same type
- Natural language for relationships (no symbols)
- Prioritize relationships, but list all key equipment
- No repetition, ensure nothing missed
- For electrical diagrams: complete extraction of all components and connections"""

                    description = None
                    max_retries = 3
                    retry_delay = 5  # seconds
                    for attempt in range(max_retries):
                        try:
                            description = completion_svc.generate(
                                history=[], prompt=prompt, images=[data_uri])
                            break  # Success
                        except LLMError as e:
                            if attempt < max_retries - 1 and is_retryable_error(e):
                                logger.warning(
                                    f"Retryable error generating vision-to-text for asset {part.asset_id}: {e}. "
                                    f"Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                                )
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                            else:
                                logger.error(
                                    f"Non-retryable error or max retries exceeded for asset {part.asset_id}: {e}",
                                    exc_info=True,
                                )
                                return IndexResult(
                                    success=False,
                                    index_type=self.index_type,
                                    metadata={
                                        "message": f"Non-retryable error or max retries exceeded for asset {part.asset_id}: {e}",
                                        "status": "failed",
                                    },
                                )
                        except Exception as e:
                            logger.error(
                                f"Unexpected error generating vision-to-text for asset {part.asset_id}: {e}",
                                exc_info=True,
                            )
                            return IndexResult(
                                success=False,
                                index_type=self.index_type,
                                metadata={
                                    "message": f"Unexpected error generating vision-to-text for asset {part.asset_id}: {e}",
                                    "status": "failed",
                                },
                            )

                    if description:
                        metadata = part.metadata.copy()
                        metadata["collection_id"] = collection.id
                        metadata["document_id"] = document_id
                        metadata["source"] = metadata.get("name", "")
                        metadata["asset_id"] = part.asset_id
                        metadata["mimetype"] = mime_type
                        metadata["indexer"] = "vision"
                        metadata["index_method"] = "vision_to_text"
                        text_nodes.append(
                            TextNode(text=description, metadata=metadata))

                vectors = embedding_svc.embed_documents(
                    [node.get_content() for node in text_nodes])
                for i, node in enumerate(text_nodes):
                    node.embedding = vectors[i]

                ctx_ids = vector_store_adaptor.connector.store.add(text_nodes)
                all_ctx_ids.extend(ctx_ids)
                logger.info(
                    f"Created {len(ctx_ids)} vision-to-text vectors for document {document_id}")
            except Exception as e:
                logger.error(
                    f"Failed to create vision-to-text embedding for document {document_id}: {e}", exc_info=True
                )
                return IndexResult(
                    success=False,
                    index_type=self.index_type,
                    metadata={
                        "message": f"Failed to create vision-to-text embedding for document {document_id}: {e}",
                        "status": "failed",
                    },
                )

        return IndexResult(
            success=True,
            index_type=self.index_type,
            data={"context_ids": all_ctx_ids},
            metadata={"vector_count": len(
                all_ctx_ids), "vector_size": vector_size},
        )

    def update_index(
        self, document_id: str, content: str, doc_parts: List[Any], collection: Collection, **kwargs
    ) -> IndexResult:
        """Update vision index for a document."""
        result = self.delete_index(document_id, collection)
        if not result.success:
            return result
        return self.create_index(document_id, content, doc_parts, collection, **kwargs)

    def delete_index(self, document_id: str, collection: Collection, **kwargs) -> IndexResult:
        """Delete vision index for a document."""

        try:
            # Get existing vector index data from DocumentIndex
            from aperag.config import get_sync_session
            from aperag.db.models import DocumentIndex, DocumentIndexType

            ctx_ids = []
            for session in get_sync_session():
                stmt = select(DocumentIndex).where(
                    and_(DocumentIndex.document_id == document_id,
                         DocumentIndex.index_type == DocumentIndexType.VISION)
                )
                result = session.execute(stmt)
                doc_index = result.scalar_one_or_none()

                if not doc_index or not doc_index.index_data:
                    return IndexResult(
                        success=True, index_type=self.index_type, metadata={"message": "No vision index to delete"}
                    )

                index_data = json.loads(doc_index.index_data)
                ctx_ids = index_data.get("context_ids", [])

            if not ctx_ids:
                return IndexResult(
                    success=True, index_type=self.index_type, metadata={"message": "No context IDs to delete"}
                )

            # Delete vectors from vector database
            vector_db = get_vector_db_connector(
                collection=generate_vector_db_collection_name(
                    collection_id=collection.id)
            )
            vector_db.connector.delete(ids=ctx_ids)

            logger.info(
                f"Deleted {len(ctx_ids)} vectors for document {document_id}")

            return IndexResult(
                success=True,
                index_type=self.index_type,
                data={"deleted_context_ids": ctx_ids},
                metadata={"deleted_vector_count": len(ctx_ids)},
            )

        except Exception as e:
            logger.error(
                f"Vision index deletion failed for document {document_id}: {str(e)}")
            return IndexResult(
                success=False, index_type=self.index_type, error=f"Vector index deletion failed: {str(e)}"
            )


# Global instance
vision_indexer = VisionIndexer()
