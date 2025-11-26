import logging
from typing import Any, Dict, List, Optional

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class ArchivistAgent(BaseAgent):
    """
    图谱专家 (The Archivist)
    
    职责：
    - 知识库检索
    - 图谱关系遍历
    - 历史数据查询
    - 知识整合
    """

    def __init__(self, retrieve_service: Any = None):
        super().__init__(
            role=AgentRole.ARCHIVIST,
            name="图谱专家 (Archivist)",
            description="拥有全局知识库的访问权限，擅长查找设备台账、历史缺陷记录、检修规程和技术文档。",
            tools=["global_search", "graph_traversal", "rag"],
        )
        self.retrieve_service = retrieve_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行检索任务"""
        query = input_data.get("query", input_data.get("task", ""))
        search_type = input_data.get("search_type", "hybrid")  # vector, graph, hybrid
        
        collection_ids = input_data.get("collection_ids")
        
        self._log_thought(state, "thought", f"图谱专家接收查询: {query}")
        
        # 判断查询类型
        if any(keyword in query for keyword in ["关系", "连接", "路径", "关联"]):
            return await self._graph_traversal(state, query)
        elif any(keyword in query for keyword in ["历史", "案例", "记录"]):
            return await self._historical_search(state, query, collection_ids)
        else:
            return await self._knowledge_search(state, query, search_type, collection_ids)
    
    async def _knowledge_search(
        self,
        state: AgentState,
        query: str,
        search_type: str,
        collection_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """知识库检索"""
        self._log_thought(state, "action", f"执行{search_type}检索")
        
        if self.user_id:
            try:
                # 如果未指定知识库，则获取用户的所有知识库（图谱专家默认搜索全局）
                if not collection_ids:
                    from aperag.service.collection_service import collection_service
                    collections = await collection_service.get_all_collections(self.user_id)
                    collection_ids = [str(c.id) for c in collections]
                    
                    if not collection_ids:
                        self._log_thought(state, "observation", "用户没有知识库，跳过检索")
                        return self._fallback_response(query)

                # 使用BaseAgent的检索能力
                results = await self._search_knowledge(
                    state=state,
                    query=query,
                    collection_ids=collection_ids,
                    top_k=10
                )
                
                # 提取文档
                documents = self._extract_documents_from_tool_results(results)
                
                self._log_thought(
                    state,
                    "observation",
                    f"检索到 {len(documents)} 条相关文档"
                )
                
                # 构建结果报告
                report = self._format_search_results(query, documents)
                
                return {
                    "answer": report,
                    "content": report,
                    "documents": documents,
                    "source_documents": documents,
                    "count": len(documents)
                }
                
            except Exception as e:
                logger.warning(f"Knowledge search failed: {e}")
                self._log_thought(state, "correction", f"检索失败: {str(e)}")
                return self._fallback_response(query)
        else:
            # 没有user_id，使用Mock数据
            return self._fallback_response(query)
    
    async def _graph_traversal(
        self,
        state: AgentState,
        query: str
    ) -> Dict[str, Any]:
        """图谱关系遍历"""
        self._log_thought(state, "action", "执行图谱遍历")
        
        if self.user_id:
            try:
                # 使用LLM分析查询意图
                intent_prompt = f"""
分析以下查询的图谱遍历需求：
查询: {query}

请提取：
1. 起始节点（设备名称）
2. 目标节点（如果有）
3. 关系类型（如：连接、供电、保护等）
4. 遍历深度（1-3）

以JSON格式输出：
{{
    "start_node": "起始节点",
    "target_node": "目标节点或null",
    "relation_type": "关系类型",
    "depth": 2
}}

只输出JSON，不要其他说明。
"""
                
                self._log_thought(state, "action", "使用LLM分析查询意图")
                
                intent_json = await self._generate_with_llm(
                    state=state,
                    prompt=intent_prompt,
                    temperature=0.3,
                    max_tokens=500
                )
                
                import json
                import re
                
                cleaned_intent = re.sub(r"```json|```", "", intent_json).strip()
                intent = json.loads(cleaned_intent)
                
                self._log_thought(
                    state,
                    "observation",
                    f"识别意图: {intent}"
                )
                
                # 执行图谱遍历（调用图谱工具）
                # 这里我们模拟一个图谱查询，并要求LLM返回结构化数据
                traversal_prompt = f"""
请查询知识图谱中的关系：
起始节点: {intent.get('start_node')}
目标节点: {intent.get('target_node', '所有相关节点')}
关系类型: {intent.get('relation_type', '所有关系')}
遍历深度: {intent.get('depth', 2)}

请返回两部分内容：
1. 自然语言描述：描述找到的关系和路径。
2. 结构化数据：以JSON格式列出涉及的节点和边。

格式要求：
[DESCRIPTION]
...自然语言描述...

[GRAPH_DATA]
{{
    "nodes": [
        {{"id": "节点ID", "label": "节点名称", "type": "设备类型"}}
    ],
    "edges": [
        {{"source": "源节点ID", "target": "目标节点ID", "label": "关系类型"}}
    ]
}}
"""
                
                traversal_result_raw = await self._generate_with_llm(
                    state=state,
                    prompt=traversal_prompt,
                    temperature=0.5
                )
                
                # 解析结果
                description = traversal_result_raw
                graph_data = {"nodes": [], "edges": []}
                
                if "[GRAPH_DATA]" in traversal_result_raw:
                    parts = traversal_result_raw.split("[GRAPH_DATA]")
                    description = parts[0].replace("[DESCRIPTION]", "").strip()
                    try:
                        graph_json_str = parts[1].strip()
                        graph_json_str = re.sub(r"```json|```", "", graph_json_str).strip()
                        graph_data = json.loads(graph_json_str)
                    except Exception as e:
                        logger.warning(f"Failed to parse graph data: {e}")
                
                return {
                    "answer": description,
                    "content": description,
                    "intent": intent,
                    "graph_data": graph_data
                }
                
            except Exception as e:
                logger.warning(f"Graph traversal failed: {e}")
                self._log_thought(state, "correction", f"图谱遍历失败: {str(e)}")
                return self._fallback_response(query)
        else:
            return self._fallback_response(query)
    
    async def _historical_search(
        self,
        state: AgentState,
        query: str,
        collection_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """历史数据查询"""
        self._log_thought(state, "action", "检索历史数据")
        
        # 检索历史记录
        if self.user_id:
            try:
                # 如果未指定知识库，则获取用户的所有知识库
                if not collection_ids:
                    from aperag.service.collection_service import collection_service
                    collections = await collection_service.get_all_collections(self.user_id)
                    collection_ids = [str(c.id) for c in collections]

                results = await self._search_knowledge(
                    state=state,
                    query=query,
                    collection_ids=collection_ids,
                    top_k=20  # 历史查询返回更多结果
                )
                
                documents = self._extract_documents_from_tool_results(results)
                
                # 按时间排序（如果有时间戳）
                sorted_docs = sorted(
                    documents,
                    key=lambda x: x.get('timestamp', x.get('date', '')),
                    reverse=True
                )
                
                self._log_thought(
                    state,
                    "observation",
                    f"检索到 {len(sorted_docs)} 条历史记录"
                )
                
                report = self._format_historical_results(query, sorted_docs)
                
                return {
                    "answer": report,
                    "content": report,
                    "documents": sorted_docs,
                    "source_documents": sorted_docs,
                    "count": len(sorted_docs)
                }
            except Exception as e:
                logger.warning(f"Historical search failed: {e}")
                self._log_thought(state, "correction", f"历史查询失败: {str(e)}")
                return self._fallback_response(query)
        else:
            return self._fallback_response(query)
    
    def _format_search_results(self, query: str, documents: List[Dict]) -> str:
        """格式化检索结果"""
        report = f"## 检索结果\n\n"
        report += f"**查询**: {query}\n"
        report += f"**找到**: {len(documents)} 条相关文档\n\n"
        
        for i, doc in enumerate(documents[:10]):
            report += f"### {i+1}. {doc.get('title', '未知')}\n"
            report += f"**来源**: {doc.get('source', '知识库')}\n"
            
            # 显示内容摘要
            content = doc.get('content', '')
            if len(content) > 300:
                content = content[:300] + "..."
            report += f"{content}\n\n"
        
        if len(documents) > 10:
            report += f"*还有 {len(documents) - 10} 条结果未显示*\n"
        
        return report
    
    def _format_historical_results(self, query: str, documents: List[Dict]) -> str:
        """格式化历史结果"""
        report = f"## 历史记录\n\n"
        report += f"**查询**: {query}\n"
        report += f"**找到**: {len(documents)} 条历史记录\n\n"
        
        for i, doc in enumerate(documents[:15]):
            report += f"### {i+1}. {doc.get('title', '未知')}\n"
            
            # 显示时间信息
            timestamp = doc.get('timestamp', doc.get('date', '未知时间'))
            report += f"**时间**: {timestamp}\n"
            
            # 显示类型
            doc_type = doc.get('type', doc.get('category', '未知类型'))
            report += f"**类型**: {doc_type}\n"
            
            # 显示内容摘要
            content = doc.get('content', '')
            if len(content) > 200:
                content = content[:200] + "..."
            report += f"{content}\n\n"
        
        if len(documents) > 15:
            report += f"*还有 {len(documents) - 15} 条记录未显示*\n"
        
        return report
    
    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """回退响应（使用Mock数据）"""
        # Mock数据库
        mock_db = [
            {
                "id": "doc_001",
                "title": "1号主变检修记录_202405",
                "content": "2024年5月12日，对1号主变进行了例行检修。发现高压侧套管油位略低，已补油处理。本体油色谱分析正常。",
                "source": "检修记录库",
                "timestamp": "2024-05-12"
            },
            {
                "id": "kb_node_102",
                "title": "设备台账: #1 主变压器",
                "content": "型号: SFZ11-110000/110; 厂家: 特变电工; 投运日期: 2015-06-01; 当前状态: 运行中。",
                "source": "设备台账",
                "type": "设备信息"
            },
            {
                "id": "rule_205",
                "title": "变电安规-变压器作业",
                "content": "在变压器上作业时，必须断开电源，并挂好接地线。攀登变压器时应佩戴安全带。",
                "source": "安全规程",
                "type": "规程文档"
            },
        ]
        
        # 简单的关键词匹配
        results = []
        query_lower = query.lower()
        for item in mock_db:
            if any(keyword in query_lower for keyword in ["主变", "变压器", "检修", "台账", "规程"]):
                results.append(item)
        
        if not results:
            results = mock_db  # 返回所有Mock数据
        
        report = self._format_search_results(query, results)
        
        return {
            "answer": report,
            "content": report,
            "documents": results,
            "source_documents": results,
            "count": len(results),
            "note": "使用Mock数据，实际部署时将连接真实知识库"
        }
    
    def _extract_documents_from_tool_results(self, tool_results: List[Dict]) -> List[Dict]:
        """从工具调用结果中提取文档"""
        documents = []
        for result in tool_results:
            if isinstance(result, dict) and "result" in result:
                result_data = result["result"]
                if isinstance(result_data, dict) and "documents" in result_data:
                    documents.extend(result_data["documents"])
        return documents
