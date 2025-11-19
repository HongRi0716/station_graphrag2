import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class DiagnosticianAgent(BaseAgent):
    """
    故障诊断师 (The Diagnostician)
    职责：分析故障录波、SOE记录，推断事故原因，生成分析报告。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.DIAGNOSTICIAN,
            name="故障诊断师 (Diagnostician)",
            description="深度分析故障录波与SOE日志，推演事故起因，判断保护动作行为是否正确。",
            tools=["analyze_soe", "parse_comtrade", "causal_inference"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        task = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到诊断请求: {task}")
        if "log" not in task.lower() and "录波" not in task:
            self._log_thought(state, "thought", "未检测到具体的日志文件，将基于通用知识进行假设性分析。")

        soe_events = self._mock_soe_extraction()
        self._log_thought(
            state,
            "action",
            "解析 SOE (Sequence of Events) 记录",
            detail={"extracted_events": soe_events},
        )

        diagnosis = self._perform_diagnosis(soe_events)
        self._log_thought(
            state,
            "thought",
            "正在构建故障因果链...",
            detail={"causal_chain": diagnosis["chain"]},
        )

        report = (
            "### 故障诊断报告\n\n"
            f"**1. 事故概况**: {diagnosis['summary']}\n"
            f"**2. 保护动作分析**: \n{diagnosis['protection_analysis']}\n"
            f"**3. 结论与建议**: \n{diagnosis['conclusion']}"
        )

        return {"answer": report, "diagnosis_data": diagnosis}

    def _mock_soe_extraction(self) -> List[str]:
        return [
            "T0+0ms: 10kV II段母线 A相电压突降至 45V",
            "T0+20ms: 10kV #2出线 51P (过流一段) 保护启动",
            "T0+35ms: 10kV #2出线 51P 保护出口跳闸",
            "T0+80ms: 10kV #2出线 断路器 DL 分位",
            "T0+90ms: 10kV II段母线 电压恢复正常",
        ]

    def _perform_diagnosis(self, events: List[str]) -> Dict[str, Any]:
        return {
            "summary": "10kV #2出线发生 A相短路故障，导致 II段母线电压跌落。",
            "chain": [
                "故障发生 (A相短路)",
                "电流激增/电压跌落",
                "保护装置检测到过流",
                "保护指令跳闸",
                "故障切除",
            ],
            "protection_analysis": (
                "- **保护行为**: 51P (速断保护) 正确动作。\n"
                "- **动作时间**: 从启动到出口耗时 15ms，符合整定值要求 (<20ms)。\n"
                "- **断路器**: 开关分闸时间 45ms，机构动作正常。"
            ),
            "conclusion": "本次事故为 10kV #2出线区内故障，保护装置与断路器动作正确，属于永久性故障切除。建议巡视 #2出线电缆沟及终端头。",
        }
