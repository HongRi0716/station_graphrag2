from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from aperag.agent.core.models import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentThinkingStep,
    ToolCallInfo,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    所有智能体（专家/值长）的基类
    实现了标准的思维链记录和状态管理功能
    """

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        tools: Optional[List[Any]] = None,
    ):
        self.role = role
        self.name = name
        self.description = description
        self.tools = tools or []

    async def run(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能体执行的主入口。
        使用 Template Method 模式，封装了通用的日志和思维链记录逻辑。
        """
        try:
            # 1. 记录开始思考
            self._log_thought(state, "thought",
                              f"{self.name} 开始接收任务", input_data)

            # 2. 执行具体的业务逻辑 (由子类实现)
            result = await self._execute(state, input_data)

            # 3. 记录执行完成
            self._log_thought(state, "final_answer",
                              f"{self.name} 任务完成", result)

            return result

        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}", exc_info=True)
            self._log_thought(state, "correction", f"发生错误: {str(e)}")
            raise e

    @abstractmethod
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑，必须由子类实现。
        例如：图纸侦探在此处调用 VLM，安监卫士在此处查询规则库。
        """
        ...

    def _log_thought(
        self,
        state: AgentState,
        step_type: str,
        description: str,
        detail: Optional[Dict[str, Any]] = None,
        citations: Optional[List[str]] = None,
    ):
        """
        辅助方法：向共享状态中添加思考步骤，用于前端展示“气泡”
        """
        step = AgentThinkingStep(
            role=self.role,
            step_type=step_type,
            description=description,
            detail=detail,
            citations=citations or [],
        )
        state.add_thought(step)
        # 也可以在此处通过 WebSocket 实时推送到前端

    def _log_tool_use(self, state: AgentState, tool_info: ToolCallInfo):
        """
        记录工具调用
        """
        self._log_thought(
            state,
            "action",
            f"调用工具: {tool_info.tool_name}",
            detail=tool_info.model_dump(),
        )

    async def reflect(self, state: AgentState, result: Any) -> bool:
        """
        (可选) 反思机制：检查结果是否符合预期，是否需要重试
        """
        return True
