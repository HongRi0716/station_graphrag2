import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class ArchivistAgent(BaseAgent):
    """
    图谱专家 (The Archivist)
    职责：跨库检索、设备台账查询、缺陷溯源、规程查找。
    它是连接 LLM 与 向量数据库/知识图谱 的桥梁。
    """

    def __init__(self, retrieve_service: Any = None):
        super().__init__(
            role=AgentRole.ARCHIVIST,
            name="图谱专家 (Archivist)",
            description="拥有全局知识库的访问权限，擅长查找设备台账、历史缺陷记录、检修规程和技术文档。",
            tools=["global_search", "graph_traversal"],
        )
        self.retrieve_service = retrieve_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行检索任务
        """
        query = input_data.get("task", "")
        original_query = input_data.get("original_query", "")

        self._log_thought(state, "thought", f"收到检索请求: {query}")

        # 1. 关键词提取 (Keyword Extraction) - 模拟
        search_keywords = self._extract_keywords(query)
        self._log_thought(state, "plan", f"提取关键实体: {search_keywords}")

        # 2. 执行检索 (Execution)
        search_results = await self._perform_search(search_keywords)

        self._log_thought(
            state,
            "observation",
            f"检索到 {len(search_results)} 条相关记录",
            detail={"results": search_results},
        )

        # 3. 答案生成 (Answer Generation)
        summary = self._summarize_results(query, search_results)

        return {"content": summary, "source_documents": search_results}

    def _extract_keywords(self, query: str) -> List[str]:
        """简单的关键词提取逻辑"""
        ignore_words = ["查询", "查找", "一下", "帮我", "的", "记录", "什么", "有"]
        words = query.split()
        return [w for w in words if w not in ignore_words]

    async def _perform_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        模拟检索过程
        未来替换为: await vector_store.similarity_search(keywords)
        """
        mock_db = [
            {
                "id": "doc_001",
                "title": "1号主变检修记录_202405",
                "content": "2024年5月12日，对1号主变进行了例行检修。发现高压侧套管油位略低，已补油处理。本体油色谱分析正常。",
            },
            {
                "id": "kb_node_102",
                "title": "设备台账: #1 主变压器",
                "content": "型号: SFZ11-110000/110; 厂家: 特变电工; 投运日期: 2015-06-01; 当前状态: 运行中。",
            },
            {
                "id": "rule_205",
                "title": "变电安规-变压器作业",
                "content": "在变压器上作业时，必须断开电源，并挂好接地线。攀登变压器时应佩戴安全带。",
            },
        ]

        results = []
        for item in mock_db:
            results.append(item)

        return results[:3]

    def _summarize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        基于检索结果生成回答
        """
        if not results:
            return "未能在知识库中找到相关信息。"

        summary = "根据知识库检索结果：\n"
        for idx, res in enumerate(results):
            summary += f"{idx+1}. 来源于《{res['title']}》: {res['content']}\n"

        return summary
