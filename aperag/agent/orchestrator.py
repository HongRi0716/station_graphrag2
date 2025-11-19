import logging
from typing import Any, Dict

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import (
    AgentRole,
    AgentState,
    SubTask,
    TaskPlan,
    TaskStatus,
)
from aperag.agent.registry import agent_registry

logger = logging.getLogger(__name__)


class MasterOrchestrator(BaseAgent):
    """
    变电站“值长” (Supervisor)
    职责：意图识别 -> SOP生成 -> 任务分发 -> 结果汇总
    """

    def __init__(self, llm_service: Any):
        super().__init__(
            role=AgentRole.SUPERVISOR,
            name="值长 (Supervisor)",
            description="负责理解用户意图，协调各专家智能体完成复杂的运维任务。",
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        总控执行流程：Plan -> Dispatch -> Synthesize
        """
        query = input_data.get("query", "")

        # 1. 规划 (Planning)
        self._log_thought(
            state, "plan", "正在分析用户意图并制定作业SOP...", {"query": query})
        plan = await self._create_plan(query, state)
        state.current_plan = plan

        # 2. 调度与执行 (Dispatch & Execution)
        results = {}
        for task in plan.tasks:
            # 检查依赖 (简化逻辑：按顺序执行)
            if task.status != TaskStatus.PENDING:
                continue

            # 记录调度动作
            self._log_thought(
                state,
                "action",
                f"指派任务给 [{task.assigned_to}]: {task.description}",
                {"task_id": task.task_id},
            )

            # 查找对应专家
            worker = agent_registry.get_agent(task.assigned_to)
            if not worker:
                error_msg = f"找不到指定的专家: {task.assigned_to}"
                logger.error(error_msg)
                task.status = TaskStatus.FAILED
                task.error = error_msg
                self._log_thought(state, "correction", error_msg)
                continue

            # 执行子任务
            task.status = TaskStatus.IN_PROGRESS
            try:
                # 构造专家的输入上下文
                worker_input = {
                    "task": task.description,
                    "context": state.shared_context,  # 共享之前的上下文
                    "original_query": query,
                }

                # 调用专家
                task_result = await worker.run(state, worker_input)

                # 更新任务状态
                task.result = task_result
                task.status = TaskStatus.COMPLETED

                # 更新共享黑板
                state.shared_context[task.task_id] = task_result
                results[task.task_id] = task_result

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                self._log_thought(state, "correction", f"专家执行失败: {str(e)}")

        # 3. 汇总 (Synthesis)
        self._log_thought(state, "thought", "正在汇总各专家报告并生成最终回复...")
        final_response = await self._synthesize_response(query, plan, results)

        return {
            "answer": final_response,
            "plan": plan.model_dump(),
            "debug_info": results,
        }

    async def _create_plan(self, query: str, state: AgentState) -> TaskPlan:
        """
        调用 LLM 生成任务计划 (JSON 模式)
        """
        # 获取可用专家列表
        agent_descriptions = agent_registry.get_agent_descriptions()

        # TODO: 接入 LLM，根据 agent_descriptions 生成结构化计划

        mock_plan = TaskPlan(
            original_query=query,
            goal="处理用户运维请求",
            tasks=[
                SubTask(
                    description=f"检索关于 '{query}' 的相关知识和文档",
                    assigned_to=AgentRole.ARCHIVIST,
                )
            ],
        )

        if "图" in query or "Drawing" in query:
            mock_plan.tasks.append(
                SubTask(
                    description="分析相关电气图纸内容",
                    assigned_to=AgentRole.DETECTIVE,
                )
            )

        self._log_thought(state, "plan", "已生成作业SOP", mock_plan.model_dump())
        return mock_plan

    async def _synthesize_response(self, query: str, plan: TaskPlan, results: Dict[str, Any]) -> str:
        """
        调用 LLM 将结构化结果汇总为自然语言
        """
        # TODO: 接入 LLM 进行最终回答汇总
        summary_parts = []
        for task in plan.tasks:
            if task.status == TaskStatus.COMPLETED and task.result:
                content = task.result.get("content", str(task.result))
                summary_parts.append(f"【{task.assigned_to} 汇报】: {content}")
            else:
                summary_parts.append(f"【{task.assigned_to}】: 任务失败或未执行")

        return "\n\n".join(summary_parts)
