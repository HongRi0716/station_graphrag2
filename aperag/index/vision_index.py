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

        # Get model configuration to determine max_output_tokens
        max_tokens = None
        try:
            from aperag.db.models import APIType
            model_config = db_ops.query_llm_provider_model(
                provider_name=vision_llm_provider,
                api=APIType.COMPLETION,
                model=vision_llm_model
            )
            if model_config and model_config.max_output_tokens:
                # Use max_output_tokens from model config, with a reasonable default if too small
                # At least 8192 tokens for complex diagrams
                max_tokens = max(model_config.max_output_tokens, 8192)
                logger.info(
                    f"Using max_output_tokens={max_tokens} for Vision LLM {vision_llm_model} "
                    f"(from model config: {model_config.max_output_tokens})")
            else:
                # Default to 16384 tokens for vision-to-text (complex diagrams need more tokens)
                max_tokens = 16384
                logger.info(
                    f"Using default max_tokens={max_tokens} for Vision LLM {vision_llm_model} "
                    f"(model config not found or max_output_tokens not set)")
        except Exception as e:
            # Fallback to default if query fails
            max_tokens = 16384
            logger.warning(
                f"Failed to get max_output_tokens for Vision LLM {vision_llm_model}: {e}. "
                f"Using default max_tokens={max_tokens}")

        # Create completion service with vision=True flag, max_tokens, and timeout
        # Vision models need longer timeout (10 minutes) for complex image processing
        completion_service = CompletionService(
            provider=llm_provider.completion_dialect or "openai",
            model=vision_llm_model,
            base_url=base_url,
            api_key=api_key,
            vision=True,  # Explicitly mark as vision model
            max_tokens=max_tokens,  # Set max_tokens to allow longer outputs
            # 10 minutes timeout for vision models (complex images take longer)
            timeout=600,
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

                    prompt = """Extract key information from the image for RAG retrieval and knowledge graph extraction. Focus on precise entity and relationship extraction.
## Requirements
1. **Entities (Equipment & Components)**: Extract ALL unique entities with clear identification

2. **Relationships**: Extract ALL connection relationships with explicit entity pairs:
   - **Format**: Use clear subject-verb-object structure: "EntityA connects to EntityB" or "EntityA通过EntityB连接到EntityC"
   - **Relationship Types**: connects_to, passes_through, supplies, receives_from, controls, etc.
   - **Be explicit**: Always mention both entity names in each relationship
## Rules
- **Complete extraction** - extract all entities and relationships, no omissions
- **No duplicates** - each entity and relationship appears only once
- **Entity naming**: Use exact names/IDs as shown in the image, preserve original language
- **Relationship clarity**: Each relationship must explicitly mention both entities
- **Structured format**: Use consistent format for easy parsing"""

                    description = None
                    max_retries = 3
                    retry_delay = 5  # seconds
                    logger.info(
                        f"Starting Vision LLM generation for asset {part.asset_id} of document {document_id} "
                        f"(attempt 1/{max_retries})")
                    for attempt in range(max_retries):
                        try:
                            logger.info(
                                f"Calling Vision LLM generate() for asset {part.asset_id} (attempt {attempt + 1}/{max_retries})")
                            description = completion_svc.generate(
                                history=[], prompt=prompt, images=[data_uri])
                            logger.info(
                                f"Vision LLM generate() completed for asset {part.asset_id}, description length: {len(description) if description else 0}")
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
