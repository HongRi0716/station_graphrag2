import logging
from typing import Any, Dict

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class CalculatorAgent(BaseAgent):
    """
    整定计算师 (The Calculator)
    职责：进行继电保护定值计算、CT/PT 变比核算、负荷率计算。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.CALCULATOR,
            name="整定计算师 (Calculator)",
            description="提供精确的电气参数计算服务，如继电保护定值、短路电流估算。",
            tools=["python_repl", "formula_retriever"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"分析计算需求: {query}")

        params = {
            "ct_ratio_primary": 600,
            "ct_ratio_secondary": 5,
            "k_rel": 1.3,
            "k_ret": 0.85,
            "i_load_max": 400,
        }
        self._log_thought(state, "plan", "提取计算参数", detail=params)

        calculation_code = """
i_primary_op = (k_rel * i_load_max) / k_ret
i_secondary_op = i_primary_op * (ct_ratio_secondary / ct_ratio_primary)
result = {
    "primary_op": round(i_primary_op, 2),
    "secondary_op": round(i_secondary_op, 2)
}
"""

        try:
            local_scope = params.copy()
            exec(calculation_code, {}, local_scope)
            result = local_scope["result"]
            self._log_thought(
                state,
                "action",
                "执行计算公式",
                detail={"code": calculation_code.strip(), "result": result},
            )

            return {
                "answer": (
                    "根据计算：\n\n"
                    f"- **一次侧动作电流**: {result['primary_op']} A\n"
                    f"- **二次侧整定值**: {result['secondary_op']} A\n\n"
                    "(注：公式采用 I_op = (K_rel * I_load_max) / K_ret)"
                ),
                "result": result,
            }

        except Exception as exc:
            error_msg = f"计算过程出错: {exc}"
            self._log_thought(state, "correction", error_msg)
            return {
                "answer": "抱歉，无法完成计算，请检查参数是否完整。",
                "error": error_msg,
            }
