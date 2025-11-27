import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

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
        """格式化检索结果 - 优化版"""
        # 标题和概览
        report = f"# 📚 知识检索结果\n\n"
        report += f"**🔍 查询内容**: {query}\n"
        report += f"**📊 检索结果**: 共找到 **{len(documents)}** 条相关文档\n"
        report += f"**⏰ 检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "---\n\n"
        
        # 显示前10条结果
        display_count = min(10, len(documents))
        
        for i, doc in enumerate(documents[:display_count]):
            # 文档标题
            title = doc.get('title', '未命名文档')
            report += f"## 📄 {i+1}. {title}\n\n"
            
            # 元数据信息
            metadata_items = []
            
            # 来源
            source = doc.get('source', doc.get('collection_name', '知识库'))
            metadata_items.append(f"**📁 来源**: {source}")
            
            # 类型
            doc_type = doc.get('type', doc.get('category', ''))
            if doc_type:
                metadata_items.append(f"**🏷️ 类型**: {doc_type}")
            
            # 时间
            timestamp = doc.get('timestamp', doc.get('date', doc.get('created_at', '')))
            if timestamp:
                metadata_items.append(f"**📅 时间**: {timestamp}")
            
            # 相关度分数
            score = doc.get('score', doc.get('relevance_score', 0))
            if score > 0:
                score_percent = int(score * 100) if score <= 1 else int(score)
                score_bar = "🟢" if score_percent >= 80 else "🟡" if score_percent >= 60 else "🔴"
                metadata_items.append(f"**{score_bar} 相关度**: {score_percent}%")
            
            # 显示元数据
            report += " | ".join(metadata_items) + "\n\n"
            
            # 内容摘要
            content = doc.get('content', doc.get('text', ''))
            if content:
                # 智能截断
                if len(content) > 300:
                    # 尝试在句号处截断
                    truncated = content[:300]
                    last_period = truncated.rfind('。')
                    if last_period > 200:  # 如果句号位置合理
                        content = truncated[:last_period + 1]
                    else:
                        content = truncated + "..."
                
                report += f"**💡 内容摘要**:\n\n"
                report += f"> {content}\n\n"
            
            # 关键词/标签
            keywords = doc.get('keywords', doc.get('tags', []))
            if keywords:
                if isinstance(keywords, list):
                    keywords_str = " ".join([f"`{kw}`" for kw in keywords[:5]])
                else:
                    keywords_str = f"`{keywords}`"
                report += f"**🔖 关键词**: {keywords_str}\n\n"
            
            report += "---\n\n"
        
        # 显示更多提示
        if len(documents) > display_count:
            remaining = len(documents) - display_count
            report += f"📌 *还有 **{remaining}** 条相关结果未显示*\n\n"
        
        # 搜索建议
        if len(documents) == 0:
            report += "💡 **搜索建议**:\n"
            report += "- 尝试使用不同的关键词\n"
            report += "- 使用更具体的设备名称或编号\n"
            report += "- 检查拼写是否正确\n\n"
        elif len(documents) < 3:
            report += "💡 **提示**: 结果较少，可以尝试使用更宽泛的关键词\n\n"
        
        return report
    
    def _format_historical_results(self, query: str, documents: List[Dict]) -> str:
        """格式化历史结果 - 优化版"""
        # 标题和概览
        report = f"# 📜 历史记录查询结果\n\n"
        report += f"**🔍 查询内容**: {query}\n"
        report += f"**📊 查询结果**: 共找到 **{len(documents)}** 条历史记录\n"
        report += f"**⏰ 查询时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "---\n\n"
        
        # 按类型分组统计
        type_stats = {}
        for doc in documents:
            doc_type = doc.get('type', doc.get('category', '其他'))
            type_stats[doc_type] = type_stats.get(doc_type, 0) + 1
        
        if type_stats:
            report += "**📈 记录类型分布**:\n\n"
            for doc_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
                bar_length = min(20, int(count / len(documents) * 20))
                bar = "█" * bar_length + "░" * (20 - bar_length)
                report += f"- {doc_type}: {count} 条 {bar}\n"
            report += "\n---\n\n"
        
        # 显示前15条结果（时间线视图）
        display_count = min(15, len(documents))
        
        report += "## 📅 时间线视图\n\n"
        
        for i, doc in enumerate(documents[:display_count]):
            # 时间戳
            timestamp = doc.get('timestamp', doc.get('date', '未知时间'))
            
            # 文档标题和类型
            title = doc.get('title', '未命名记录')
            doc_type = doc.get('type', doc.get('category', '未分类'))
            
            # 类型图标
            type_icon = {
                '缺陷': '⚠️',
                '检修': '🔧',
                '巡视': '👁️',
                '操作': '⚡',
                '试验': '🧪',
                '事故': '🚨',
                '报告': '📋',
                '记录': '📝',
            }.get(doc_type, '📄')
            
            # 时间线节点
            report += f"### {type_icon} {timestamp}\n\n"
            report += f"**{i+1}. {title}**\n\n"
            
            # 元数据
            metadata_items = []
            metadata_items.append(f"**🏷️ 类型**: {doc_type}")
            
            # 设备信息
            equipment = doc.get('equipment', doc.get('device', ''))
            if equipment:
                metadata_items.append(f"**🔌 设备**: {equipment}")
            
            # 责任人
            responsible = doc.get('responsible', doc.get('operator', ''))
            if responsible:
                metadata_items.append(f"**👤 责任人**: {responsible}")
            
            # 状态
            status = doc.get('status', '')
            if status:
                status_icon = "✅" if status in ['已完成', '正常'] else "⏳" if status in ['进行中', '待处理'] else "❌"
                metadata_items.append(f"**{status_icon} 状态**: {status}")
            
            report += " | ".join(metadata_items) + "\n\n"
            
            # 内容摘要
            content = doc.get('content', doc.get('description', ''))
            if content:
                # 智能截断
                if len(content) > 200:
                    truncated = content[:200]
                    last_period = truncated.rfind('。')
                    if last_period > 150:
                        content = truncated[:last_period + 1]
                    else:
                        content = truncated + "..."
                
                report += f"> {content}\n\n"
            
            # 关键信息高亮
            severity = doc.get('severity', doc.get('level', ''))
            if severity:
                severity_color = {
                    '紧急': '🔴',
                    '重要': '🟠',
                    '一般': '🟡',
                    '轻微': '🟢',
                }.get(severity, '⚪')
                report += f"{severity_color} **严重程度**: {severity}\n\n"
            
            report += "---\n\n"
        
        # 显示更多提示
        if len(documents) > display_count:
            remaining = len(documents) - display_count
            report += f"📌 *还有 **{remaining}** 条历史记录未显示*\n\n"
        
        # 统计摘要
        if len(documents) > 0:
            report += "## 📊 统计摘要\n\n"
            
            # 时间范围
            timestamps = [doc.get('timestamp', doc.get('date', '')) for doc in documents if doc.get('timestamp') or doc.get('date')]
            if timestamps:
                timestamps_sorted = sorted([t for t in timestamps if t])
                if timestamps_sorted:
                    report += f"- **时间范围**: {timestamps_sorted[0]} 至 {timestamps_sorted[-1]}\n"
            
            # 记录总数
            report += f"- **记录总数**: {len(documents)} 条\n"
            
            # 最常见类型
            if type_stats:
                most_common_type = max(type_stats.items(), key=lambda x: x[1])
                report += f"- **最常见类型**: {most_common_type[0]} ({most_common_type[1]} 条)\n"
            
            report += "\n"
        
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
