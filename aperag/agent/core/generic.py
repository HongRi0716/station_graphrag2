import logging
from typing import Any, Dict, List, Optional

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class PromptDrivenAgent(BaseAgent):
    """
    通用提示词驱动智能体，依靠注入的 System Prompt 实现不同角色能力。
    """

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        llm_service: Any,
        system_prompt: str,
        tools: Optional[List[Any]] = None,
    ):
        super().__init__(role=role, name=name, description=description, tools=tools)
        self.llm_service = llm_service
        self.system_prompt = system_prompt

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        task = input_data.get("task", "")
        original_query = input_data.get("original_query", "")
        context = input_data.get("context", {})

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"【用户原始请求】：{original_query}\n"
                    f"【当前上下文信息】：{str(context)[:2000]}...\n"
                    f"【当前执行任务】：{task}\n\n"
                    "请根据你的角色设定，专业地完成上述任务。"
                ),
            },
        ]

        self._log_thought(
            state,
            "thought",
            f"{self.name} 正在根据设定分析任务...",
            detail={"prompt_preview": messages[-1]["content"][:200] + "..."},
        )

        try:
            response_content = ""
            if hasattr(self.llm_service, "chat"):
                response = await self.llm_service.chat(messages=messages)
                response_content = getattr(response, "content", str(response))
            elif hasattr(self.llm_service, "completion"):
                response = await self.llm_service.completion(messages)
                response_content = str(response)
            else:
                logger.warning("Agent %s has no valid LLM service.", self.name)
                response_content = f"[模拟回复] {self.name} 已收到任务: {task}。请配置真实的 LLM Service 以获得智能回复。"

            self._log_thought(
                state,
                "observation",
                f"{self.name} 完成了分析",
                detail={"content": response_content},
            )

            return {"answer": response_content, "content": response_content, "role": self.role.value}

        except Exception as exc:
            error_msg = f"模型调用失败: {exc}"
            logger.error("Error in PromptDrivenAgent %s: %s", self.name, exc, exc_info=True)
            self._log_thought(state, "correction", error_msg)
            raise

