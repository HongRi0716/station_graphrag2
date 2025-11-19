import json
import logging
from datetime import datetime
from typing import Any, Dict

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class ScribeAgent(BaseAgent):
    """
    文书专员 (The Scribe)
    职责：自动生成巡视记录、缺陷单、操作票，将口语转化为标准格式。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.SCRIBE,
            name="文书专员 (Scribe)",
            description="负责将自然语言整理为标准化的运维记录、工作票或缺陷单。",
            tools=["form_filler", "grammar_check"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text_input = input_data.get("task", "")

        self._log_thought(state, "thought", "接收到记录请求，正在分析文本结构...")
        doc_type = "patrol_log"
        if "缺陷" in text_input:
            doc_type = "defect_report"
        elif "操作" in text_input:
            doc_type = "operation_ticket"

        self._log_thought(state, "plan", f"识别为 [{doc_type}] 类型，准备提取关键字段。")
        extracted_data = self._extract_fields(doc_type, text_input)

        self._log_thought(state, "action", "生成结构化数据", detail=extracted_data)

        formatted_output = json.dumps(
            extracted_data, indent=2, ensure_ascii=False)
        summary = (
            f"已为您生成{self._get_doc_name(doc_type)}，请核对：\n```json\n{formatted_output}\n```"
        )

        return {"answer": summary, "structured_data": extracted_data, "doc_type": doc_type}

    def _get_doc_name(self, doc_type: str) -> str:
        names = {
            "patrol_log": "巡视记录",
            "defect_report": "缺陷单",
            "operation_ticket": "操作票",
        }
        return names.get(doc_type, "文档")

    def _extract_fields(self, doc_type: str, text: str) -> Dict[str, Any]:
        base_info = {
            "created_at": datetime.now().isoformat(),
            "recorder": "当前用户",
        }

        if doc_type == "defect_report":
            return {
                **base_info,
                "equipment": "2号主变风冷系统" if "2号" in text else "未知设备",
                "component": "3号风机" if "3号" in text else "未知部件",
                "phenomenon": "异响" if "异响" in text else "待补充",
                "severity": "一般",
            }

        if doc_type == "patrol_log":
            return {
                **base_info,
                "task_name": "例行巡视",
                "status": "异常" if any(word in text for word in ["异响", "发热"]) else "正常",
                "content": text,
            }

        if doc_type == "operation_ticket":
            return {
                **base_info,
                "operation": "切换操作" if "切换" in text else "操作请求",
                "steps": ["核对票面", "确认设备", "执行操作"],
                "notes": text,
            }

        return {"raw_content": text}
