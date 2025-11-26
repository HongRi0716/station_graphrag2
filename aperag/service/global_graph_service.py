import asyncio
import logging
from collections import Counter
from typing import Any, Dict, List, Optional, TYPE_CHECKING



from aperag.schema.view_models import (
    GlobalEvidence,
    GraphData,
    GraphDirectoryCollection,
    GraphDirectoryDocument,
    GraphDirectoryResponse,
    GraphHierarchyEdge,
    GraphHierarchyNode,
)
from aperag.service.collection_service import CollectionService, collection_service
from aperag.service.document_service import DocumentService, document_service

# SearchService import not needed; using Any for type hint

logger = logging.getLogger(__name__)


def _status_value(raw_status: Any) -> str:
    if raw_status is None:
        return ""
    if isinstance(raw_status, str):
        return raw_status
    return getattr(raw_status, "value", str(raw_status))


class GlobalGraphService:
    """
    全局图谱服务：负责跨 Collection 的联邦搜索与聚合。
    实现 Scatter-Gather (分发-聚合) 模式。
    """


    def __init__(
        self,
        collection_service: CollectionService,
        search_service: Optional[Any] = None,
        document_service: Optional[DocumentService] = None,
    ):
        self.collection_service = collection_service
        self.search_service = search_service
        self.document_service = document_service or DocumentService()

    async def get_global_hierarchy(
        self,
        user_id: str,
        top_k: int = 50,
        docs_per_collection: int = 10,
        query: Optional[str] = None,
        include_entities: bool = True,
    ) -> GraphData:
        """
        获取全局层级结构数据 (Collection -> Document)。
        支持全局实体搜索：当搜索词匹配实体时，返回包含该实体的文档。
        """
        if not user_id:
            raise ValueError("user_id is required to build hierarchy data")

        logger.info("Fetching global hierarchy data for user %s with query: %s", user_id, query)

        collections = await self.collection_service.get_all_collections(user_id)
        if not collections:
            return GraphData()

        normalized_query = (query or "").strip().lower()

        active_collections = [
            col
            for col in collections
            if _status_value(getattr(col, "status", "")).upper() == "ACTIVE"
        ]

        # 如果有搜索词，尝试进行全局实体搜索（可选）
        entity_matched_doc_ids = set()
        if normalized_query and include_entities:
            entity_matched_doc_ids = await self._search_entities_globally(
                user_id=user_id,
                collections=active_collections,
                query=normalized_query,
            )
            logger.info(f"Entity search found {len(entity_matched_doc_ids)} matching documents")

        def _matches_collection(col) -> bool:
            if not normalized_query:
                return True
            search_blob = " ".join(
                filter(
                    None,
                    [
                        getattr(col, "title", "") or "",
                        getattr(col, "description", "") or "",
                        getattr(col, "id", "") or "",
                    ],
                )
            ).lower()
            return normalized_query in search_blob

        # 如果实体搜索有结果，优先使用实体搜索结果
        if entity_matched_doc_ids:
            # 获取包含匹配实体的文档所属的 collections
            matched_collection_ids = set()
            for doc_id in entity_matched_doc_ids:
                # 从 doc_id 中提取 collection_id（假设格式为 collection_id/document_id）
                parts = doc_id.split("/")
                if len(parts) >= 2:
                    matched_collection_ids.add(parts[0])
            
            filtered_collections = [
                col for col in active_collections 
                if col.id in matched_collection_ids or _matches_collection(col)
            ]
        else:
            filtered_collections = [col for col in active_collections if _matches_collection(col)]
        
        if not filtered_collections and normalized_query:
            filtered_collections = active_collections

        max_collections = min(max(top_k, 0), len(filtered_collections)) if filtered_collections else 0
        if max_collections == 0:
            max_collections = len(filtered_collections)
        selected_collections = filtered_collections[:max_collections]

        nodes: List[GraphHierarchyNode] = []
        edges: List[GraphHierarchyEdge] = []

        async def _fetch_docs(col):
            return await self.document_service.get_recent_documents_by_collection(
                user_id=user_id,
                collection_id=col.id,
                limit=docs_per_collection,
            )

        document_results = await asyncio.gather(
            *[_fetch_docs(col) for col in selected_collections],
            return_exceptions=True,
        )

        for idx, col in enumerate(selected_collections):
            col_node_id = f"col_{col.id}"
            status_value = _status_value(getattr(col, "status", ""))
            nodes.append(
                GraphHierarchyNode(
                    id=col_node_id,
                    type="collection",
                    name=col.title or col.id,
                    description=col.description,
                    metadata={
                        "collection_id": col.id,
                        "status": status_value,
                        "document_count": getattr(col, "document_count", 0),
                        "owner_user_id": getattr(col, "user", None),
                    },
                    size=20,
                )
            )

            docs = document_results[idx]
            if isinstance(docs, Exception):
                logger.warning("Failed to load documents for collection %s: %s", col.id, docs)
                continue

            for doc in docs:
                doc_name = getattr(doc, "name", "") or getattr(doc, "title", "")
                doc_id_full = f"{col.id}/{doc.id}"
                
                # 如果有实体搜索结果，只显示匹配的文档
                if entity_matched_doc_ids:
                    if doc_id_full not in entity_matched_doc_ids and doc.id not in entity_matched_doc_ids:
                        # 同时检查文档名称是否匹配
                        if normalized_query not in (doc_name or "").lower():
                            continue
                elif normalized_query and normalized_query not in (doc_name or "").lower():
                    continue

                doc_node_id = f"doc_{doc.id}"
                nodes.append(
                    GraphHierarchyNode(
                        id=doc_node_id,
                        type="document",
                        name=doc_name or "Untitled Document",
                        metadata={
                            "document_id": doc.id,
                            "collection_id": doc.collection_id,
                            "status": str(getattr(doc, "status", "")),
                            "size": getattr(doc, "size", None),
                            "updated_at": getattr(doc, "gmt_updated", None),
                        },
                        size=10,
                    )
                )
                edges.append(
                    GraphHierarchyEdge(
                        id=f"{col_node_id}_{doc_node_id}",
                        source=col_node_id,
                        target=doc_node_id,
                        type="CONTAINS",
                        label="contains",
                    )
                )

        node_type_counter = Counter(node.type for node in nodes)
        edge_type_counter = Counter(edge.type for edge in edges)

        logger.info(
            "Hierarchy built for user %s with %s nodes and %s edges (entity search enabled=%s, matches=%s)",
            user_id,
            len(nodes),
            len(edges),
            include_entities and bool(normalized_query),
            len(entity_matched_doc_ids),
        )

        return GraphData(
            nodes=nodes,
            edges=edges,
            statistics={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": dict(node_type_counter),
                "edge_types": dict(edge_type_counter),
                "entity_matches": len(entity_matched_doc_ids),
            },
        )

    async def get_directory_tree(
        self,
        user_id: str,
        query: Optional[str] = None,
        include_empty: bool = True,
    ) -> GraphDirectoryResponse:
        """
        Return a lightweight Collection -> Document directory for the Global Graph Explorer sidebar.
        """
        if not user_id:
            raise ValueError("user_id is required to fetch directory data")

        collections = await self.collection_service.get_all_collections(user_id)
        if not collections:
            return GraphDirectoryResponse()

        normalized_query = (query or "").strip().lower()
        active_collections = [
            col for col in collections if _status_value(getattr(col, "status", "")).upper() != "DELETED"
        ]

        collection_ids = [str(col.id) for col in active_collections if col.id]
        documents_by_collection = await self.document_service.get_documents_by_collection_ids(
            user_id=user_id,
            collection_ids=collection_ids,
        )

        directory_collections: List[GraphDirectoryCollection] = []
        total_documents = 0

        def _doc_sort_key(doc: Any) -> float:
            dt = getattr(doc, "gmt_updated", None) or getattr(doc, "gmt_created", None)
            if hasattr(dt, "timestamp"):
                try:
                    return float(dt.timestamp())
                except Exception:
                    return 0.0
            return 0.0

        for col in active_collections:
            col_id = str(col.id)
            docs = documents_by_collection.get(col_id, [])
            collection_matches = False
            if normalized_query:
                search_blob = " ".join(
                    filter(
                        None,
                        [
                            getattr(col, "title", "") or "",
                            getattr(col, "description", "") or "",
                            col_id,
                        ],
                    )
                ).lower()
                collection_matches = normalized_query in search_blob

            if normalized_query:
                if collection_matches:
                    filtered_docs = docs
                else:
                    filtered_docs = [
                        doc for doc in docs if normalized_query in (getattr(doc, "name", "") or "").lower()
                    ]
                if not collection_matches and not filtered_docs:
                    continue
            else:
                filtered_docs = docs

            if not include_empty and not docs:
                continue

            sorted_docs = sorted(filtered_docs, key=_doc_sort_key, reverse=True)

            documents_payload = [
                GraphDirectoryDocument(
                    id=str(doc.id),
                    name=getattr(doc, "name", "") or getattr(doc, "title", "") or "Untitled Document",
                    collection_id=col_id,
                    status=_status_value(getattr(doc, "status", "")),
                    size=getattr(doc, "size", None),
                    created_at=getattr(doc, "gmt_created", None),
                    updated_at=getattr(doc, "gmt_updated", None),
                    metadata={
                        "graph_index_status": getattr(doc, "graph_index_status", None),
                        "vector_index_status": getattr(doc, "vector_index_status", None),
                    },
                )
                for doc in sorted_docs
            ]

            total_documents += len(documents_payload)

            directory_collections.append(
                GraphDirectoryCollection(
                    id=col_id,
                    title=getattr(col, "title", None) or col_id,
                    description=getattr(col, "description", None),
                    status=_status_value(getattr(col, "status", "")),
                    document_count=len(docs),
                    documents=documents_payload,
                )
            )

        return GraphDirectoryResponse(
            collections=directory_collections,
            total_collections=len(directory_collections),
            total_documents=total_documents,
        )

    async def _search_entities_globally(
        self,
        user_id: str,
        collections: List[Any],
        query: str,
    ) -> set:
        """
        在所有开启知识图谱的 Collection 中搜索实体。
        返回包含匹配实体的文档ID集合。
        """
        from aperag.graph import lightrag_manager
        from aperag.schema.utils import parseCollectionConfig

        # 筛选开启了知识图谱的 collections
        kg_collections = []
        for col in collections:
            try:
                config = parseCollectionConfig(col.config)
                if getattr(config, "enable_knowledge_graph", False):
                    kg_collections.append(col)
            except Exception as exc:
                logger.debug("Failed to parse collection config for %s: %s", col.id, exc)

        if not kg_collections:
            return set()

        matched_doc_ids = set()

        async def _search_entities_in_collection(collection):
            """在单个 collection 中搜索实体"""
            try:
                rag = await lightrag_manager.create_lightrag_instance(collection)
                try:
                    # 使用 LightRAG 的全局图谱搜索功能
                    graph_data = await rag.get_global_graph_data(query=query, top_k=50)
                    
                    # 从返回的节点中提取文档ID
                    doc_ids = set()
                    if graph_data and "nodes" in graph_data:
                        for node in graph_data.get("nodes", []):
                            # 检查节点的 source_id 或 metadata 中的文档信息
                            source_id = node.get("source_id")
                            if source_id:
                                doc_ids.add(source_id)
                            
                            # 也检查 metadata
                            metadata = node.get("metadata", {})
                            if isinstance(metadata, dict):
                                doc_id = metadata.get("document_id") or metadata.get("source_id")
                                if doc_id:
                                    doc_ids.add(f"{collection.id}/{doc_id}")
                    
                    return doc_ids
                finally:
                    await rag.finalize_storages()
            except Exception as exc:
                logger.warning(
                    "Failed to search entities in collection %s: %s",
                    collection.id,
                    exc,
                )
                return set()

        # 并发搜索所有 collections
        tasks = [_search_entities_in_collection(col) for col in kg_collections]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        for result in results:
            if isinstance(result, set):
                matched_doc_ids.update(result)

        return matched_doc_ids

    async def get_global_graph_search(
        self,
        user_id: str,
        query: str,
        top_k: int = 100,
    ) -> Dict[str, Any]:
        """
        执行全局图谱搜索：并发查询所有开启知识图谱的 Collection，并合并结果。
        """
        if not user_id:
            raise ValueError("user_id is required for global graph search")
        if not query:
            raise ValueError("query is required for global graph search")

        from aperag.graph import lightrag_manager
        from aperag.schema.utils import parseCollectionConfig

        logger.info("Starting global graph search for user %s query: %s", user_id, query)
        collections = await self.collection_service.get_all_collections(user_id)
        if not collections:
            return {"nodes": [], "edges": []}

        kg_collections = []
        for col in collections:
            status = getattr(col, "status", "")
            if (isinstance(status, str) and status.upper() != "ACTIVE") or (
                hasattr(status, "value") and status.value != "ACTIVE"
            ):
                continue
            try:
                config = parseCollectionConfig(col.config)
                if getattr(config, "enable_knowledge_graph", False):
                    kg_collections.append(col)
            except Exception as exc:
                logger.debug("Failed to parse collection config for %s: %s", col.id, exc)

        if not kg_collections:
            logger.info("No knowledge graph enabled collections for user %s", user_id)
            return {"nodes": [], "edges": []}

        async def _search_single_collection(collection):
            try:
                rag = await lightrag_manager.create_lightrag_instance(collection)
                try:
                    graph_data = await rag.get_global_graph_data(query=query, top_k=top_k)
                    return graph_data or {"nodes": [], "edges": []}
                finally:
                    await rag.finalize_storages()
            except Exception as exc:
                logger.warning(
                    "Failed to search knowledge graph for collection %s: %s",
                    collection.id,
                    exc,
                )
                return {"nodes": [], "edges": []}

        tasks = [_search_single_collection(col) for col in kg_collections]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged_graph = self._merge_graph_results(results)
        logger.info(
            "Global graph search finished for user %s: %s nodes, %s edges",
            user_id,
            len(merged_graph["nodes"]),
            len(merged_graph["edges"]),
        )
        return merged_graph

    def _merge_graph_results(self, graph_results: List[Any]) -> Dict[str, Any]:
        """
        Merge nodes and edges from multiple graph search results, deduplicating by ID.
        """
        merged_nodes: Dict[str, Dict[str, Any]] = {}
        merged_edges: Dict[str, Dict[str, Any]] = {}

        for res in graph_results:
            if isinstance(res, Exception) or not isinstance(res, dict):
                continue

            for node in res.get("nodes", []) or []:
                node_id = node.get("id")
                if not node_id:
                    continue
                if node_id not in merged_nodes:
                    merged_nodes[node_id] = node

            for edge in res.get("edges", []) or []:
                edge_id = edge.get("id")
                if not edge_id:
                    source = edge.get("source")
                    target = edge.get("target")
                    edge_type = edge.get("type", "")
                    edge_id = f"{source}_{target}_{edge_type}"
                if edge_id and edge_id not in merged_edges:
                    merged_edges[edge_id] = edge

        return {
            "nodes": list(merged_nodes.values()),
            "edges": list(merged_edges.values()),
        }

    async def global_search(
        self,
        user_id: str,
        query: str,
        entity_names: Optional[List[str]] = None,
    ) -> List[GlobalEvidence]:
        """
        执行全局联邦搜索。
        1. 获取所有活跃的 Collections。
        2. 并发向每个 Collection 发起混合检索。
        3. 聚合结果并进行重排序 (Rerank)。
        """
        if not self.search_service:
            raise RuntimeError("Search service is not configured")

        logger.info(
            "Starting global federated search for user %s query: %s",
            user_id,
            query,
        )

        collections = await self.collection_service.get_all_collections(user_id)

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
        if not self.search_service:
            raise RuntimeError("Search service is not configured")

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


    async def federated_graph_search(
        self, user, query: str, top_k: int = 20
    ) -> Dict[str, Any]:
        """
        执行全局联邦图谱搜索（结构化数据）。
        用于前端 Global Graph Explorer 的可视化展示。
        """
        from aperag.graph import lightrag_manager
        from aperag.schema.utils import parseCollectionConfig
        from aperag.db.ops import async_db_ops

        logger.info(f"Starting federated graph structure search for query: {query}")

        user_id = str(getattr(user, "id", user))
        normalized_query = (query or "").strip().lower()

        # 1. 获取所有 Collection
        collections = await async_db_ops.query_collections([user_id])

        active_collections = []
        for col in collections:
            # Check status
            status_value = getattr(col, "status", "")
            if hasattr(status_value, "value"):
                status_value = status_value.value
            
            if str(status_value).upper() != "ACTIVE":
                continue

            try:
                config = parseCollectionConfig(col.config)
                if getattr(config, "enable_knowledge_graph", False):
                    active_collections.append(col)
            except Exception as e:
                logger.debug(f"Skipping collection {col.id} due to config error: {e}")

        if not active_collections:
            return {"nodes": [], "edges": [], "matches": {"collections": [], "documents": [], "entities": []}}

        collection_lookup = {str(col.id): col for col in active_collections}

        def _normalize_document_id(raw_value: Any) -> Optional[str]:
            if not raw_value:
                return None
            if isinstance(raw_value, str):
                parts = raw_value.split("/")
                return parts[-1] if parts else raw_value
            return str(raw_value)

        # 2. 并发执行子图查询
        # 限制并发数防止数据库过载
        semaphore = asyncio.Semaphore(10)

        async def _search_single_graph(collection):
            async with semaphore:
                try:
                    logger.info(f"DEBUG: Processing collection {collection.id} ({collection.title})")
                    rag = await lightrag_manager.create_lightrag_instance(collection)
                    logger.info(f"DEBUG: Created RAG instance for {collection.id}")
                    
                    try:
                        # A. 语义搜索实体 (Vector Search)
                        # rag.entities_vdb.query 接受文本 query，内部会自动 embed
                        logger.info(f"DEBUG: Querying entities for {collection.id}")
                        similar_entities = await rag.entities_vdb.query(query, top_k=top_k)
                        logger.info(f"DEBUG: Found {len(similar_entities)} entities for {collection.id}")
                        
                        if not similar_entities:
                            return {"nodes": [], "edges": []}

                        # B. 获取这些实体的子图 (Ego-Graph)
                        nodes_map = {}
                        edges_list = []
                        
                        # 优化：批量获取或并行获取
                        for entity_data in similar_entities:
                            e_name = entity_data['entity_name']
                            doc_ref = _normalize_document_id(
                                entity_data.get('document_id') or entity_data.get('source_id')
                            )
                            
                            # 添加中心节点
                            # 使用 entity_name 作为 ID，允许前端自动合并
                            
                            nodes_map[e_name] = {
                                "id": e_name, # Shared ID for visual merging
                                "label": e_name,
                                "type": "entity",
                                "value": entity_data.get('distance', 1.0) * 10, # Visualization size
                                "metadata": {
                                    "workspace": collection.title, # Show collection name
                                    "collection_id": str(collection.id),
                                    "collection_name": collection.title,
                                    "description": entity_data.get('content', '')[:100] + "...",
                                    "source_id": entity_data.get('source_id'),
                                    "document_id": doc_ref,
                                    "match_score": entity_data.get('distance'),
                                    "match_type": "entity",
                                }
                            }

                            # 获取邻边
                            # 注意：lightrag graph storage 接口可能不同
                            if hasattr(rag.chunk_entity_relation_graph, 'get_node_edges'):
                                node_edges = await rag.chunk_entity_relation_graph.get_node_edges(e_name)
                                if node_edges:
                                    for src, tgt in node_edges:
                                        edge_id = f"{src}_{tgt}"
                                        edges_list.append({
                                            "source": src,
                                            "target": tgt,
                                            "id": edge_id,
                                            "label": "related", # 简化，实际需查询边属性
                                            "workspace": collection.title
                                        })
                                        
                                        # 确保 source/target 都在 nodes_map 中 (作为占位符)
                                        if src not in nodes_map:
                                            nodes_map[src] = {"id": src, "label": src, "type": "entity", "metadata": {"workspace": collection.title}}
                                        if tgt not in nodes_map:
                                            nodes_map[tgt] = {
                                                "id": tgt,
                                                "label": tgt,
                                                "type": "entity",
                                                "metadata": {"workspace": collection.title, "collection_id": str(collection.id)},
                                            }

                            if doc_ref:
                                doc_edge_id = f"doc_{doc_ref}_{e_name}_match"
                                edges_list.append(
                                    {
                                        "source": f"doc_{doc_ref}",
                                        "target": e_name,
                                        "id": doc_edge_id,
                                        "label": "extracted",
                                        "type": "EXTRACTED_FROM",
                                        "workspace": collection.title,
                                    }
                                )

                        return {"nodes": list(nodes_map.values()), "edges": edges_list}
                    finally:
                        await rag.finalize_storages()

                except Exception as e:
                    logger.warning(f"Graph search failed for {collection.title}: {e}")
                    return {"nodes": [], "edges": []}

        tasks = [_search_single_graph(col) for col in active_collections]
        results = await asyncio.gather(*tasks)

        # 3. 聚合结果
        aggregated_nodes = {}
        aggregated_edges = []

        for res in results:
            # 合并节点
            for node in res['nodes']:
                nid = node['id']
                if nid not in aggregated_nodes:
                    aggregated_nodes[nid] = node
                    # Initialize source_collections
                    aggregated_nodes[nid]['source_collections'] = [node['metadata']['workspace']]
                else:
                    # 节点已存在（跨库共现实体），合并信息
                    if node['metadata']['workspace'] not in aggregated_nodes[nid]['source_collections']:
                        aggregated_nodes[nid]['source_collections'].append(node['metadata']['workspace'])
                    # 可以合并描述等

            # 合并边
            aggregated_edges.extend(res['edges'])

        # 转换回列表
        final_nodes = list(aggregated_nodes.values())
        
        # 简单去重边
        unique_edges = {f"{e['source']}_{e['target']}_{e.get('type', '')}": e for e in aggregated_edges}.values()
        unique_edges_list = list(unique_edges)

        entity_matches: List[Dict[str, Any]] = []
        for node in final_nodes:
            if node.get("type") != "entity":
                continue
            metadata = node.get("metadata", {}) or {}
            entity_matches.append(
                {
                    "id": node.get("id"),
                    "name": node.get("label") or node.get("name") or node.get("id"),
                    "collection_id": metadata.get("collection_id"),
                    "collection_name": metadata.get("collection_name"),
                    "document_id": metadata.get("document_id"),
                    "score": metadata.get("match_score"),
                }
            )

        matched_collections: List[Dict[str, Any]] = []
        matched_documents: List[Dict[str, Any]] = []
        if normalized_query:
            for col in active_collections:
                blob = " ".join(
                    filter(
                        None,
                        [
                            getattr(col, "title", "") or "",
                            getattr(col, "description", "") or "",
                            str(col.id),
                        ],
                    )
                ).lower()
                if normalized_query in blob:
                    matched_collections.append(
                        {
                            "id": str(col.id),
                            "title": getattr(col, "title", None) or str(col.id),
                            "description": getattr(col, "description", None),
                            "status": _status_value(getattr(col, "status", "")),
                        }
                    )

            document_hits = await self.document_service.search_documents_by_name(
                user_id=user_id,
                query=normalized_query,
                limit=200,
                collection_ids=list(collection_lookup.keys()),
            )
            for doc in document_hits:
                col_id = str(getattr(doc, "collection_id", ""))
                parent_collection = collection_lookup.get(col_id)
                matched_documents.append(
                    {
                        "id": str(doc.id),
                        "name": getattr(doc, "name", "") or getattr(doc, "title", "") or "Untitled Document",
                        "collection_id": col_id,
                        "collection_name": getattr(parent_collection, "title", None) or col_id,
                        "status": _status_value(getattr(doc, "status", "")),
                        "updated_at": getattr(doc, "gmt_updated", None),
                    }
                )

        logger.info(
            "Federated graph search completed: %s nodes, %s edges (matches: %s collections, %s documents, %s entities)",
            len(final_nodes),
            len(unique_edges_list),
            len(matched_collections),
            len(matched_documents),
            len(entity_matches),
        )
        
        return {
            "nodes": final_nodes,
            "edges": unique_edges_list,
            "matches": {
                "collections": matched_collections,
                "documents": matched_documents,
                "entities": entity_matches,
            },
        }


global_graph_service = GlobalGraphService(
    collection_service=collection_service,
    document_service=document_service,
)
