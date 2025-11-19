# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pyright: reportMissingImports=false

import logging
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

try:
    from aperag.agent.core.models import AgentRole, AgentState, AgentThinkingStep
    from aperag.agent.orchestrator import MasterOrchestrator
    from aperag.agent.registry import agent_registry
    from aperag.agent.specialists.archivist import ArchivistAgent
except ImportError:  # pragma: no cover
    from ..agent.core.models import AgentRole, AgentState, AgentThinkingStep
    from ..agent.orchestrator import MasterOrchestrator
    from ..agent.registry import agent_registry
    from ..agent.specialists.archivist import ArchivistAgent

logger = logging.getLogger(__name__)


class AgentChatService:
    """
    智能体对话服务
    负责初始化智能体环境，并协调 Agent 完成用户请求。
    """

    def __init__(self, llm_service: Any = None, retrieve_service: Any = None):
        self.llm_service = llm_service
        self.retrieve_service = retrieve_service
        self._initialize_registry()

    def _initialize_registry(self):
        """
        初始化并注册专家智能体
        生产环境可在应用启动时统一注册，这里简化为在 Service 初始化时完成。
        """
        agent_registry.initialize_default_agents(
            llm_service=self.llm_service, retrieve_service=self.retrieve_service
        )

    async def chat(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        agent_id: str = "supervisor",
    ) -> Dict[str, Any]:
        """
        处理用户一次性对话请求
        :param agent_id: 指定要调用的智能体 ID (默认为 supervisor).
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        state = AgentState(session_id=session_id)
        agent_id = agent_id or AgentRole.SUPERVISOR.value
        target_agent = None
        resolved_role: Optional[AgentRole] = None

        try:
            logger.info("Starting agent execution for session %s", session_id)

            if agent_id == AgentRole.SUPERVISOR.value:
                target_agent = MasterOrchestrator(llm_service=self.llm_service)
                resolved_role = AgentRole.SUPERVISOR
            else:
                resolved_role = next(
                    (role for role in AgentRole if role.value == agent_id), None)
                if resolved_role:
                    target_agent = agent_registry.get_agent(resolved_role)

            if not target_agent:
                logger.warning(
                    "Agent '%s' not found or not registered. Falling back to Supervisor.",
                    agent_id,
                )
                target_agent = MasterOrchestrator(llm_service=self.llm_service)
                resolved_role = AgentRole.SUPERVISOR
                state.add_thought(
                    AgentThinkingStep(
                        role=AgentRole.SYSTEM,
                        step_type="correction",
                        description=f"未找到指定的专家 [{agent_id}]，已自动切换为值长 (Supervisor) 接管。",
                        detail={"requested": agent_id,
                                "fallback": AgentRole.SUPERVISOR.value},
                    )
                )
            elif resolved_role and resolved_role != AgentRole.SUPERVISOR:
                state.add_thought(
                    AgentThinkingStep(
                        role=resolved_role,
                        step_type="plan",
                        description=f"用户直接唤起了 [{target_agent.name}]，正在准备执行...",
                        detail={"mode": "direct_invocation"},
                    )
                )

            input_data = {
                "query": query,
                "task": query,
                "user_id": user_id,
                "original_query": query,
            }
            result = await target_agent.run(state, input_data)

            response = {
                "answer": result.get("answer")
                or result.get("content")
                or "No response generated.",
                "thoughts": [step.model_dump() for step in state.thinking_stream],
                "plan": result.get("plan"),
                "session_id": session_id,
                "agent_id": resolved_role.value if resolved_role else agent_id,
            }
            return response

        except Exception as exc:
            logger.error(f"Agent execution failed: {exc}", exc_info=True)
            return {
                "answer": "系统运行遇到错误，请稍后再试。",
                "error": str(exc),
                "thoughts": [step.model_dump() for step in state.thinking_stream],
            }

    async def stream_chat(self, query: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        流式输出接口 (占位)
        未来可以将 BaseAgent 改造为支持 yield，从而在此处实时推送 Reasoning Bubble。
        """
        response = await self.chat(query, "user", session_id)
        yield response["answer"]
