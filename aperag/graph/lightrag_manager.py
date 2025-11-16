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

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import numpy

from aperag.db.models import Collection
from aperag.db.ops import db_ops
from aperag.graph.lightrag import LightRAG
from aperag.graph.lightrag.prompt import PROMPTS
from aperag.graph.lightrag.utils import EmbeddingFunc
from aperag.llm.embed.base_embedding import get_collection_embedding_service_sync
from aperag.llm.llm_error_types import (
    EmbeddingError,
    ProviderNotFoundError,
)
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)


# Configuration constants
class LightRAGConfig:
    """Centralized configuration for LightRAG"""

    CHUNK_TOKEN_SIZE = 1200
    CHUNK_OVERLAP_TOKEN_SIZE = 100
    LLM_MODEL_MAX_ASYNC = 20
    COSINE_BETTER_THAN_THRESHOLD = 0.2
    MAX_BATCH_SIZE = 32
    ENTITY_EXTRACT_MAX_GLEANING = 0
    SUMMARY_TO_MAX_TOKENS = 2000
    FORCE_LLM_SUMMARY_ON_MERGE = 10
    EMBEDDING_MAX_TOKEN_SIZE = 8192
    DEFAULT_LANGUAGE = "The same language like input text"


class LightRAGError(Exception):
    """Base exception for LightRAG operations"""

    pass


async def create_lightrag_instance(collection: Collection) -> LightRAG:
    """
    Create a new LightRAG instance for the given collection.
    Since LightRAG is now stateless, we create a fresh instance each time.
    """
    collection_id = str(collection.id)

    try:
        # Generate embedding and LLM functions
        embed_func, embed_dim = await _gen_embed_func(collection)
        llm_func = await _gen_llm_func(collection)

        # Get storage configuration from environment
        kv_storage = os.environ.get("GRAPH_INDEX_KV_STORAGE")
        vector_storage = os.environ.get("GRAPH_INDEX_VECTOR_STORAGE")
        graph_storage = os.environ.get("GRAPH_INDEX_GRAPH_STORAGE")

        # Configure storage backends
        await _configure_storage_backends(kv_storage, vector_storage, graph_storage)

        # Parse knowledge graph config from collection config
        from aperag.schema.utils import parseCollectionConfig

        config = parseCollectionConfig(collection.config)
        kg_config = config.knowledge_graph_config
        language = LightRAGConfig.DEFAULT_LANGUAGE
        entity_types = PROMPTS["DEFAULT_ENTITY_TYPES"]
        if kg_config:
            if kg_config.language:
                language = kg_config.language
            if kg_config.entity_types:
                entity_types = kg_config.entity_types

        # Create LightRAG instance
        rag = LightRAG(
            workspace=collection_id,
            chunk_token_size=LightRAGConfig.CHUNK_TOKEN_SIZE,
            chunk_overlap_token_size=LightRAGConfig.CHUNK_OVERLAP_TOKEN_SIZE,
            llm_model_func=llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=embed_dim,
                max_token_size=LightRAGConfig.EMBEDDING_MAX_TOKEN_SIZE,
                func=embed_func,
            ),
            cosine_better_than_threshold=LightRAGConfig.COSINE_BETTER_THAN_THRESHOLD,
            max_batch_size=LightRAGConfig.MAX_BATCH_SIZE,
            llm_model_max_async=LightRAGConfig.LLM_MODEL_MAX_ASYNC,
            entity_extract_max_gleaning=LightRAGConfig.ENTITY_EXTRACT_MAX_GLEANING,
            summary_to_max_tokens=LightRAGConfig.SUMMARY_TO_MAX_TOKENS,
            force_llm_summary_on_merge=LightRAGConfig.FORCE_LLM_SUMMARY_ON_MERGE,
            language=language,
            entity_types=entity_types,
            kv_storage=kv_storage,
            vector_storage=vector_storage,
            graph_storage=graph_storage,
        )

        await rag.initialize_storages()
        return rag

    except Exception as e:
        logger.error(
            f"Failed to create LightRAG instance for collection '{collection_id}': {str(e)}")
        raise LightRAGError(
            f"Failed to create LightRAG instance: {str(e)}") from e


# --- Celery Support Functions ---


def process_document_for_celery(collection: Collection, content: str, doc_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process a document in a synchronous context (for Celery).
    Creates a new event loop and LightRAG instance for each call.
    """
    return _run_in_new_loop(_process_document_async(collection, content, doc_id, file_path))


def delete_document_for_celery(collection: Collection, doc_id: str) -> Dict[str, Any]:
    """
    Delete a document in a synchronous context (for Celery).
    Creates a new event loop and LightRAG instance for each call.
    """
    return _run_in_new_loop(_delete_document_async(collection, doc_id))


async def _enrich_content_with_vision_analysis(
    collection: Collection,
    doc_id: str,
    max_wait_time: int = 120,
    check_interval: int = 2,
) -> str:
    """
    Enrich empty content with vision analysis text from vision index.

    This function will wait for Vision index to complete if it's still in progress,
    ensuring that Vision-to-Text content is available for knowledge graph construction.

    Args:
        collection: Collection object
        doc_id: Document ID
        max_wait_time: Maximum time to wait for Vision index to complete (seconds)
        check_interval: Interval between status checks (seconds)

    Returns:
        Enriched content string, or empty string if no vision analysis found
    """
    try:
        from aperag.config import get_sync_session
        from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus
        from aperag.config import get_vector_db_connector
        from aperag.utils.utils import generate_vector_db_collection_name
        from sqlalchemy import select, and_
        import json
        import asyncio

        # Get vision index data with retry mechanism
        vision_chunks_text = []
        waited_time = 0

        vision_ready = False
        while waited_time < max_wait_time and not vision_ready:
            for session in get_sync_session():
                stmt = select(DocumentIndex).where(
                    and_(
                        DocumentIndex.document_id == doc_id,
                        DocumentIndex.index_type == DocumentIndexType.VISION
                    )
                )
                result = session.execute(stmt)
                doc_index = result.scalar_one_or_none()

                if not doc_index:
                    if waited_time == 0:
                        logger.debug(
                            f"No vision index found for document {doc_id}")
                    else:
                        logger.debug(
                            f"Vision index not found for document {doc_id} after waiting {waited_time}s")
                    return ""

                # Check if Vision index is still in progress
                status_str = doc_index.status.value if hasattr(
                    doc_index.status, 'value') else str(doc_index.status)

                if doc_index.status in [DocumentIndexStatus.PENDING, DocumentIndexStatus.CREATING]:
                    # Log every 10 seconds or on first check
                    if waited_time == 0 or waited_time % 10 == 0:
                        logger.info(
                            f"Vision index for document {doc_id} is still in progress ({status_str}), "
                            f"waited {waited_time}s / {max_wait_time}s, continuing to wait...")
                    await asyncio.sleep(check_interval)
                    waited_time += check_interval
                    break  # Break inner loop to retry

                # Vision index is complete (or failed/skipped)
                logger.info(
                    f"Vision index for document {doc_id} status check: {status_str} "
                    f"(waited {waited_time}s)")

                if status_str == DocumentIndexStatus.FAILED.value or status_str == "FAILED":
                    logger.warning(
                        f"Vision index for document {doc_id} failed, cannot enrich content")
                    return ""

                # SKIPPED status doesn't exist in DocumentIndexStatus enum, but check for it anyway
                if status_str == "SKIPPED":
                    logger.debug(
                        f"Vision index for document {doc_id} was skipped")
                    return ""

                # Vision index is complete, check if it has data
                logger.info(
                    f"Vision index for document {doc_id} completed with status {status_str}, "
                    f"checking for index data...")

                if not doc_index.index_data:
                    logger.debug(
                        f"Vision index for document {doc_id} completed but has no data")
                    return ""

                # Vision index is complete and has data, proceed to extract content
                try:
                    index_data = json.loads(doc_index.index_data)
                    ctx_ids = index_data.get("context_ids", [])
                    logger.info(
                        f"Vision index for document {doc_id} has {len(ctx_ids)} context IDs: {ctx_ids}")
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(
                        f"Failed to parse vision index data for document {doc_id}: {e}")
                    return ""

                if not ctx_ids:
                    logger.debug(
                        f"No context IDs found in vision index for document {doc_id}")
                    return ""

                # Mark vision as ready and break out of both loops
                logger.info(
                    f"Vision index for document {doc_id} is ready, proceeding to extract vision content...")
                vision_ready = True
                break
            else:
                # If we didn't break, continue waiting
                continue

        # Check if we timed out
        if waited_time >= max_wait_time:
            logger.warning(
                f"Timeout waiting for Vision index to complete for document {doc_id} after {max_wait_time}s")
            return ""

        # If we got here, we should have ctx_ids from the break above
        if 'ctx_ids' not in locals():
            logger.warning(
                f"Failed to get context IDs from Vision index for document {doc_id}")
            return ""

        # Retrieve vision chunks from vector store
        logger.info(
            f"Retrieving vision chunks from vector store for document {doc_id}, "
            f"context IDs: {ctx_ids}")
        try:
            from aperag.config import settings
            from aperag.vectorstore.connector import VectorStoreConnectorAdaptor

            collection_name = generate_vector_db_collection_name(
                collection_id=collection.id)
            ctx = json.loads(settings.vector_db_context)
            ctx["collection"] = collection_name
            vector_store_adaptor = VectorStoreConnectorAdaptor(
                settings.vector_db_type, ctx=ctx
            )
            qdrant_client = vector_store_adaptor.connector.client

            logger.debug(
                f"Querying vector store collection '{collection_name}' for {len(ctx_ids)} points")
            points = qdrant_client.retrieve(
                collection_name=collection_name,
                ids=ctx_ids,
                with_payload=True,
            )
            logger.info(
                f"Retrieved {len(points)} points from vector store for document {doc_id}")

            # Extract vision-to-text descriptions
            logger.info(
                f"Extracting vision-to-text content from {len(points)} points for document {doc_id}")
            for idx, point in enumerate(points, 1):
                if not point.payload:
                    logger.debug(
                        f"Point {point.id} ({(idx)}/{len(points)}) has no payload, skipping")
                    continue

                text = None
                metadata = {}
                asset_id = None
                page_idx = None

                # Try to get data from _node_content first (llama-index-0.10.13 format)
                node_content = point.payload.get("_node_content")
                if node_content and isinstance(node_content, str):
                    try:
                        payload_data = json.loads(node_content)
                        metadata = payload_data.get("metadata", {})
                        if metadata.get("index_method") == "vision_to_text":
                            text = payload_data.get("text", "")
                            asset_id = metadata.get("asset_id", "")
                            page_idx = metadata.get("page_idx")
                            logger.debug(
                                f"Point {point.id} ({(idx)}/{len(points)}): extracted from _node_content, "
                                f"text length: {len(text) if text else 0}, asset_id: {asset_id}")
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Could not parse _node_content for point {point.id}: {e}")

                # Fallback: try direct payload structure
                if not text or not text.strip():
                    direct_metadata = point.payload.get("metadata", {})
                    if direct_metadata.get("index_method") == "vision_to_text":
                        text = point.payload.get("text", "")
                        if not text:
                            # Try getting text from _node_content even if metadata check failed
                            if node_content and isinstance(node_content, str):
                                try:
                                    payload_data = json.loads(node_content)
                                    text = payload_data.get("text", "")
                                    metadata = payload_data.get("metadata", {})
                                except Exception as e:
                                    logger.debug(
                                        f"Failed to parse _node_content as fallback for point {point.id}: {e}")
                        asset_id = direct_metadata.get(
                            "asset_id") or metadata.get("asset_id")
                        page_idx = direct_metadata.get(
                            "page_idx") if "page_idx" in direct_metadata else metadata.get("page_idx")
                        logger.debug(
                            f"Point {point.id} ({(idx)}/{len(points)}): extracted from direct payload, "
                            f"text length: {len(text) if text else 0}, asset_id: {asset_id}")

                # If we found text, format and add it
                if text and text.strip():
                    # Format the vision analysis text
                    section_header = f"\n\n------ Vision Analysis"
                    if asset_id:
                        section_header += f" (Asset: {asset_id})"
                    if page_idx is not None:
                        section_header += f" (Page: {int(page_idx) + 1})"
                    section_header += " ------\n"

                    vision_chunks_text.append(
                        section_header + text.strip())
                    logger.info(
                        f"Extracted vision-to-text from point {point.id} ({(idx)}/{len(points)}), "
                        f"text length: {len(text)}, asset_id: {asset_id}, page_idx: {page_idx}")
                else:
                    logger.warning(
                        f"Point {point.id} ({(idx)}/{len(points)}) has no vision-to-text content")

        except Exception as e:
            logger.warning(
                f"Failed to retrieve vision chunks for document {doc_id}: {e}")
            return ""

        if vision_chunks_text:
            enriched_content = "\n".join(vision_chunks_text)
            total_length = len(enriched_content)
            logger.info(
                f"Successfully enriched content for document {doc_id} with {len(vision_chunks_text)} "
                f"vision analysis sections, total content length: {total_length} characters")
            return enriched_content
        else:
            logger.warning(
                f"No vision-to-text analysis found for document {doc_id} after processing {len(points)} points")
            return ""

    except Exception as e:
        logger.warning(
            f"Failed to enrich content with vision analysis for document {doc_id}: {e}")
        return ""


async def _process_document_async(
    collection: Collection,
    content: str,
    doc_id: str,
    file_path: str,
) -> Dict[str, Any]:
    """Process document using LightRAG's stateless interfaces"""
    rag = await create_lightrag_instance(collection)

    try:
        logger.info(
            f"Processing document {doc_id} for graph indexing, "
            f"initial content length: {len(content) if content else 0} characters")

        # Try to enrich content with vision analysis
        # This works for both:
        # 1. Image files (PNG, JPG, etc.) - content may contain OCR text, merge with vision analysis
        # 2. PDF files (especially image-based PDFs) - content may be empty or partial, merge vision analysis
        # Note: This function will wait for Vision index to complete if it's still in progress,
        # ensuring vision-to-text content is available for knowledge graph construction
        logger.info(
            f"Attempting to enrich content with vision analysis for document {doc_id}...")
        vision_content = await _enrich_content_with_vision_analysis(collection, doc_id)

        if vision_content:
            vision_length = len(vision_content)
            if not content:
                # Content is empty, use vision analysis as the main content
                content = vision_content
                logger.info(
                    f"Using vision analysis content for document {doc_id} (content was empty), "
                    f"vision content length: {vision_length} characters")
            else:
                # Content exists, append vision analysis to enhance it
                # This is useful for PDFs that have both text and images
                original_length = len(content)
                content = content + "\n\n" + vision_content
                logger.info(
                    f"Enriched existing content for document {doc_id} with vision analysis: "
                    f"original length: {original_length} chars, vision content: {vision_length} chars, "
                    f"total length: {len(content)} chars")
        elif not content:
            # No vision content available and content is empty, return empty result
            logger.warning(
                f"No content available for document {doc_id} (neither text nor vision content), "
                f"skipping graph indexing")
            return {
                "status": "success",
                "doc_id": doc_id,
                "chunks_created": 0,
                "entities_extracted": 0,
                "relations_extracted": 0,
            }
        else:
            logger.info(
                f"No vision content available for document {doc_id}, using text content only "
                f"(length: {len(content)} characters)")

        # Insert and chunk document
        logger.info(
            f"Inserting and chunking document {doc_id} for graph indexing, "
            f"content length: {len(content)} characters")
        chunk_result = await rag.ainsert_and_chunk_document(
            documents=[content], doc_ids=[doc_id], file_paths=[file_path]
        )

        results = chunk_result.get("results", [])
        if not results:
            logger.warning(
                f"No processing results returned for document {doc_id}")
            return {
                "status": "warning",
                "doc_id": doc_id,
                "message": "No processing results returned",
                "chunks_created": 0,
                "entities_extracted": 0,
                "relations_extracted": 0,
            }

        logger.info(
            f"Document {doc_id} chunking completed, got {len(results)} result(s)")

        # Process results
        total_stats = {"chunks_created": 0, "entities_extracted": 0,
                       "relations_extracted": 0, "documents": []}

        for idx, doc_result in enumerate(results, 1):
            doc_result_id = doc_result.get("doc_id")
            chunks_data = doc_result.get("chunks_data", {})
            chunk_count = doc_result.get("chunk_count", 0)

            logger.info(
                f"Processing result {idx}/{len(results)} for document {doc_result_id}: "
                f"{chunk_count} chunks, {len(chunks_data)} chunks_data entries")

            if chunks_data:
                # Build graph index
                logger.info(
                    f"Starting graph indexing for document {doc_result_id} with {len(chunks_data)} chunks...")
                graph_result = await rag.aprocess_graph_indexing(
                    chunks=chunks_data, collection_id=str(collection.id))

                entities_count = graph_result.get("entities_extracted", 0)
                relations_count = graph_result.get("relations_extracted", 0)

                logger.info(
                    f"Graph indexing completed for document {doc_result_id}: "
                    f"{entities_count} entities extracted, {relations_count} relations extracted")

                total_stats["chunks_created"] += chunk_count
                total_stats["entities_extracted"] += entities_count
                total_stats["relations_extracted"] += relations_count

                total_stats["documents"].append(
                    {
                        "doc_id": doc_result_id,
                        "chunks_created": chunk_count,
                        "entities_extracted": entities_count,
                        "relations_extracted": relations_count,
                    }
                )
            else:
                logger.warning(
                    f"No chunks_data in result {idx}/{len(results)} for document {doc_result_id}")

        logger.info(
            f"Graph indexing completed for document {doc_id}: "
            f"total chunks: {total_stats['chunks_created']}, "
            f"total entities: {total_stats['entities_extracted']}, "
            f"total relations: {total_stats['relations_extracted']}")

        return {"status": "success", "doc_id": doc_id, **total_stats}

    finally:
        await rag.finalize_storages()


async def _delete_document_async(collection: Collection, doc_id: str) -> Dict[str, Any]:
    """Delete a document from LightRAG"""
    rag = await create_lightrag_instance(collection)

    try:
        await rag.adelete_by_doc_id(str(doc_id))
        logger.info(f"Deleted document {doc_id} from LightRAG")
        return {"status": "success", "doc_id": doc_id, "message": "Document deleted successfully"}
    finally:
        await rag.finalize_storages()


def _run_in_new_loop(coro: Awaitable) -> Any:
    """Run an async function in a new event loop (for Celery compatibility)"""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            pending = [task for task in asyncio.all_tasks(
                loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
        except Exception:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)


# --- Internal Helper Functions ---


async def _gen_embed_func(
    collection: Collection,
) -> Tuple[Callable[[list[str]], Awaitable[numpy.ndarray]], int]:
    """Generate embedding function for LightRAG"""
    try:
        embedding_svc, dim = get_collection_embedding_service_sync(collection)

        async def embed_func(texts: list[str]) -> numpy.ndarray:
            embeddings = await embedding_svc.aembed_documents(texts)
            return numpy.array(embeddings)

        return embed_func, dim
    except (ProviderNotFoundError, EmbeddingError) as e:
        # Configuration or embedding-specific errors
        logger.error(
            f"Failed to create embedding function - configuration error: {str(e)}")
        raise LightRAGError(f"Embedding configuration error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Failed to create embedding function: {str(e)}")
        raise LightRAGError(
            f"Failed to create embedding function: {str(e)}") from e


async def _gen_llm_func(collection: Collection) -> Callable[..., Awaitable[str]]:
    """Generate LLM function for LightRAG"""
    try:
        config = parseCollectionConfig(collection.config)
        llm_provider_name = config.completion.model_service_provider
        api_key = db_ops.query_provider_api_key(
            llm_provider_name, collection.user)
        if not api_key:
            raise Exception(
                f"API KEY not found for LLM Provider:{llm_provider_name}")

        # Get base_url from LLMProvider
        llm_provider = db_ops.query_llm_provider_by_name(llm_provider_name)
        base_url = llm_provider.base_url

        async def llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: List = [],
            max_tokens: Optional[int] = None,
            **kwargs,
        ) -> str:
            from aperag.llm.completion.completion_service import CompletionService

            completion_service = CompletionService(
                provider=config.completion.custom_llm_provider,
                model=config.completion.model,
                base_url=base_url,
                api_key=api_key,
                temperature=config.completion.temperature,
                max_tokens=max_tokens,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history_messages:
                messages.extend(history_messages)

            full_response = await completion_service.agenerate(
                history=messages, prompt=prompt, images=[
                ], memory=bool(messages)
            )

            return full_response

        return llm_func

    except Exception as e:
        logger.error(f"Failed to create LLM function: {str(e)}")
        raise LightRAGError(f"Failed to create LLM function: {str(e)}") from e


async def _configure_storage_backends(kv_storage, vector_storage, graph_storage):
    """Configure storage backends based on environment variables"""

    # Configure PostgreSQL if needed
    using_pg = any(
        [
            kv_storage in ["PGKVStorage",
                           "PGSyncKVStorage", "PGOpsSyncKVStorage"],
            vector_storage in ["PGVectorStorage",
                               "PGSyncVectorStorage", "PGOpsSyncVectorStorage"],
            graph_storage == "PGGraphStorage",
        ]
    )

    if using_pg:
        _configure_postgresql()


def _configure_postgresql():
    """Configure PostgreSQL environment variables"""
    required_vars = ["POSTGRES_HOST", "POSTGRES_USER",
                     "POSTGRES_PASSWORD", "POSTGRES_DB"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        raise LightRAGError(
            f"PostgreSQL storage requires: {', '.join(missing_vars)}")
