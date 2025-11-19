import asyncio
import logging
from typing import Any, List, Optional

from inject import autoparams

from aperag.schema.view_models import GlobalEvidence
from aperag.service.collection_service import CollectionService
from aperag.service.search_service import SearchService

logger = logging.getLogger(__name__)


class GlobalGraphService:
    """
    全局图谱服务：负责跨 Collection 的联邦搜索与聚合。
    实现 Scatter-Gather (分发-聚合) 模式。
    """

    @autoparams()
    def __init__(
        self,
        collection_service: CollectionService,
        search_service: SearchService,
    ):
        self.collection_service = collection_service
        self.search_service = search_service

    async def global_search(
        self, query: str, entity_names: Optional[List[str]] = None
    ) -> List[GlobalEvidence]:
        """
        执行全局联邦搜索。
        1. 获取所有活跃的 Collections。
        2. 并发向每个 Collection 发起混合检索。
        3. 聚合结果并进行重排序 (Rerank)。
        """
        logger.info(f"Starting global federated search for query: {query}")

        collections = await self.collection_service.get_all_collections()

        active_collections = [
            col
            for col in collections
            if getattr(col, "document_count", 0) and getattr(col, "status", "") == "ACTIVE"
        ]

        if not active_collections:
            logger.warning("No active collections found for global search.")
            return []

        tasks = [
            self._search_single_collection(col.id, col.title or col.id, query)
            for col in active_collections
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        all_evidence: List[GlobalEvidence] = []
        for res in results_list:
            if isinstance(res, list):
                all_evidence.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Error in federated search task: {res}")

        all_evidence.sort(key=lambda item: item.relevance_score, reverse=True)

        logger.info(
            "Global search finished. Found %s evidences from %s collections.",
            len(all_evidence),
            len(active_collections),
        )

        return all_evidence[:20]

    async def _search_single_collection(
        self, collection_id: str, collection_name: str, query: str
    ) -> List[GlobalEvidence]:
        """
        在单个知识库中执行搜索，并标准化输出格式。
        """
        try:
            results = await self.search_service.search(
                collection_id=collection_id,
                query=query,
                limit=5,
                search_type="hybrid",
            )

            evidence_list: List[GlobalEvidence] = []
            for item in results or []:
                evidence_list.append(
                    GlobalEvidence(
                        source_collection_id=collection_id,
                        source_collection_name=collection_name,
                        document_id=getattr(item, "document_id", "unknown"),
                        document_name=getattr(
                            item, "document_name", "unknown"),
                        chunk_text=getattr(item, "content", ""),
                        relevance_score=getattr(item, "score", 0.0),
                        entity_names=getattr(item, "entities", []) or [],
                        graph_context=getattr(item, "graph_context", None),
                    )
                )
            return evidence_list

        except Exception as exc:
            logger.warning(
                "Search failed for collection %s (%s): %s",
                collection_name,
                collection_id,
                exc,
            )
            return []
