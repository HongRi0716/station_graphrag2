import logging
import random
from typing import Any, Dict

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class InstructorAgent(BaseAgent):
    """
    培训教官 (The Instructor)
    职责：进行安全规程考核、倒闸操作模拟演练。
    特点：主动提问，评估用户回答。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.INSTRUCTOR,
            name="培训教官 (Instructor)",
            description="负责变电站运维人员的技能培训与考核，模拟故障处置场景。",
            tools=["scenario_generator", "evaluator"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_input = input_data.get("task", "")

        is_start = any(keyword in user_input for keyword in ["模拟", "培训", "考核"])

        if is_start:
            scenario = self._generate_scenario()
            self._log_thought(state, "plan", f"生成演练场景: {scenario['title']}")
            return {
                "answer": f"👨‍🏫 **{scenario['title']}**\n\n{scenario['description']}\n\n请回答：**{scenario['question']}**",
                "context": {"scenario_id": scenario["id"], "step": 1},
            }

        self._log_thought(state, "thought", "评估用户回答的正确性...")
        evaluation = self._evaluate_response(user_input)

        return {"answer": evaluation["feedback"], "score": evaluation["score"]}

    def _generate_scenario(self) -> Dict[str, str]:
        scenarios = [
            {
                "id": "S001",
                "title": "110kV 母线倒闸操作",
                "description": "当前运行方式：110kV I母、II母并列运行，所有元件均在I母运行。现需将 #1主变 110kV侧 101开关 由 I母倒至 II母运行。",
                "question": "请口述第一步操作是什么？（提示：考虑母差保护）",
            },
            {
                "id": "S002",
                "title": "主变瓦斯保护动作处置",
                "description": "警报响起，#1主变重瓦斯保护动作跳闸。",
                "question": "作为值班员，你到达现场后首先应检查什么内容？",
            },
        ]
        return random.choice(scenarios)

    def _evaluate_response(self, user_response: str) -> Dict[str, Any]:
        keywords = ["互联板", "压板", "检查", "油色", "气体"]
        if any(keyword in user_response for keyword in keywords):
            score = 90
            feedback = f"✅ 回答正确！(得分: {score})\n关键点已涵盖。继续下一步操作..."
        else:
            score = 40
            feedback = f"❌ 回答不完整或有误。(得分: {score})\n建议参考《安规》第 5.3 章节。请重新作答。"
        return {"score": score, "feedback": feedback}
