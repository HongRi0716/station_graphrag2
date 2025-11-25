# Copyright 2025 ApeCloud, Inc.

"""
智能体协作编排器 (Agent Orchestrator)
支持多智能体协同工作，任务分解和结果整合
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState, AgentMessage

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型"""
    ACCIDENT_ANALYSIS = "accident_analysis"  # 事故分析
    EMERGENCY_RESPONSE = "emergency_response"  # 应急响应
    SAFETY_CHECK = "safety_check"  # 安全检查
    OPERATION_PLANNING = "operation_planning"  # 操作规划


class CollaborationMode(str, Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HIERARCHICAL = "hierarchical"  # 层次执行


class AgentOrchestrator:
    """
    智能体协作编排器
    
    功能：
    - 任务分解
    - 智能体选择
    - 执行调度
    - 结果整合
    """
    
    def __init__(self):
        self.registry = agent_registry
    
    async def execute_collaboration(
        self,
        task: str,
        task_type: TaskType,
        user_id: str,
        chat_id: str,
        mode: CollaborationMode = CollaborationMode.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        执行智能体协作任务
        
        Args:
            task: 任务描述
            task_type: 任务类型
            user_id: 用户ID
            chat_id: 聊天ID
            mode: 协作模式
            
        Returns:
            协作结果
        """
        logger.info(f"Starting collaboration: {task_type} - {mode}")
        
        # 1. 任务分解
        subtasks = self._decompose_task(task, task_type)
        
        # 2. 智能体选择
        agent_assignments = self._assign_agents(subtasks, task_type)
        
        # 3. 执行调度
        if mode == CollaborationMode.SEQUENTIAL:
            results = await self._execute_sequential(agent_assignments, user_id, chat_id)
        elif mode == CollaborationMode.PARALLEL:
            results = await self._execute_parallel(agent_assignments, user_id, chat_id)
        else:
            results = await self._execute_hierarchical(agent_assignments, user_id, chat_id)
        
        # 4. 结果整合
        final_result = self._integrate_results(results, task, task_type)
        
        return final_result
    
    def _decompose_task(self, task: str, task_type: TaskType) -> List[Dict[str, Any]]:
        """
        任务分解
        
        根据任务类型将复杂任务分解为子任务
        """
        subtasks = []
        
        if task_type == TaskType.ACCIDENT_ANALYSIS:
            # 事故分析任务分解
            subtasks = [
                {
                    "id": "1",
                    "name": "事故推演",
                    "description": f"对'{task}'进行事故推演分析",
                    "required_capability": "accident_deduction"
                },
                {
                    "id": "2",
                    "name": "历史案例检索",
                    "description": f"检索与'{task}'相关的历史事故案例",
                    "required_capability": "rag"
                },
                {
                    "id": "3",
                    "name": "应急预案生成",
                    "description": f"基于推演结果生成应急预案",
                    "required_capability": "accident_deduction"
                }
            ]
        
        elif task_type == TaskType.EMERGENCY_RESPONSE:
            # 应急响应任务分解
            subtasks = [
                {
                    "id": "1",
                    "name": "事故定位",
                    "description": f"定位'{task}'的故障点和影响范围",
                    "required_capability": "diagnosis"
                },
                {
                    "id": "2",
                    "name": "隔离操作",
                    "description": "生成故障隔离操作票",
                    "required_capability": "operation_ticket"
                },
                {
                    "id": "3",
                    "name": "恢复计划",
                    "description": "制定供电恢复计划",
                    "required_capability": "power_guarantee"
                }
            ]
        
        elif task_type == TaskType.SAFETY_CHECK:
            # 安全检查任务分解
            subtasks = [
                {
                    "id": "1",
                    "name": "工作票审核",
                    "description": f"审核'{task}'相关工作票",
                    "required_capability": "work_permit"
                },
                {
                    "id": "2",
                    "name": "安全措施检查",
                    "description": "检查安全措施完整性",
                    "required_capability": "work_permit"
                },
                {
                    "id": "3",
                    "name": "危险点识别",
                    "description": "识别作业危险点",
                    "required_capability": "accident_deduction"
                }
            ]
        
        elif task_type == TaskType.OPERATION_PLANNING:
            # 操作规划任务分解
            subtasks = [
                {
                    "id": "1",
                    "name": "操作票生成",
                    "description": f"生成'{task}'操作票",
                    "required_capability": "operation_ticket"
                },
                {
                    "id": "2",
                    "name": "事故预想",
                    "description": "进行操作过程事故预想",
                    "required_capability": "accident_deduction"
                },
                {
                    "id": "3",
                    "name": "安全措施",
                    "description": "制定安全措施",
                    "required_capability": "work_permit"
                }
            ]
        
        return subtasks
    
    def _assign_agents(
        self,
        subtasks: List[Dict[str, Any]],
        task_type: TaskType
    ) -> List[Tuple[Dict[str, Any], AgentRole]]:
        """
        智能体选择
        
        为每个子任务分配最合适的智能体
        """
        assignments = []
        
        for subtask in subtasks:
            capability = subtask.get("required_capability")
            
            # 根据能力查找智能体
            agents = self.registry.find_by_capability(capability)
            
            if agents:
                # 选择优先级最高的智能体
                selected_agent = max(agents, key=lambda a: self.registry.get_metadata(a.role).priority)
                assignments.append((subtask, selected_agent.role))
                logger.info(f"Assigned {subtask['name']} to {selected_agent.name}")
            else:
                logger.warning(f"No agent found for capability: {capability}")
        
        return assignments
    
    async def _execute_sequential(
        self,
        assignments: List[Tuple[Dict[str, Any], AgentRole]],
        user_id: str,
        chat_id: str
    ) -> List[Dict[str, Any]]:
        """
        顺序执行
        
        按顺序执行每个子任务，后续任务可以使用前面任务的结果
        """
        results = []
        context = {}  # 共享上下文
        
        for subtask, agent_role in assignments:
            logger.info(f"Executing subtask: {subtask['name']}")
            
            # 获取智能体
            agent = self.registry.get_agent(agent_role)
            agent.user_id = user_id
            agent.chat_id = f"{chat_id}-{subtask['id']}"
            
            # 创建状态
            state = AgentState(session_id=f"{chat_id}-{subtask['id']}")
            
            # 执行任务（传入上下文）
            try:
                result = await agent.run(state, {
                    "task": subtask["description"],
                    "context": context  # 传递前面任务的结果
                })
                
                # 保存结果
                result_data = {
                    "subtask_id": subtask["id"],
                    "subtask_name": subtask["name"],
                    "agent": agent.name,
                    "result": result,
                    "thinking_stream": [
                        {
                            "step_type": step.step_type,
                            "description": step.description
                        }
                        for step in state.thinking_stream
                    ]
                }
                results.append(result_data)
                
                # 更新共享上下文
                context[subtask["id"]] = result
                
                logger.info(f"Completed subtask: {subtask['name']}")
                
            except Exception as e:
                logger.error(f"Subtask failed: {subtask['name']} - {e}")
                results.append({
                    "subtask_id": subtask["id"],
                    "subtask_name": subtask["name"],
                    "agent": agent.name,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_parallel(
        self,
        assignments: List[Tuple[Dict[str, Any], AgentRole]],
        user_id: str,
        chat_id: str
    ) -> List[Dict[str, Any]]:
        """
        并行执行
        
        同时执行所有子任务，适用于独立的子任务
        """
        tasks = []
        
        for subtask, agent_role in assignments:
            task = self._execute_single_task(subtask, agent_role, user_id, chat_id)
            tasks.append(task)
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "subtask_id": assignments[i][0]["id"],
                    "subtask_name": assignments[i][0]["name"],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_single_task(
        self,
        subtask: Dict[str, Any],
        agent_role: AgentRole,
        user_id: str,
        chat_id: str
    ) -> Dict[str, Any]:
        """执行单个任务"""
        agent = self.registry.get_agent(agent_role)
        agent.user_id = user_id
        agent.chat_id = f"{chat_id}-{subtask['id']}"
        
        state = AgentState(session_id=f"{chat_id}-{subtask['id']}")
        
        result = await agent.run(state, {
            "task": subtask["description"]
        })
        
        return {
            "subtask_id": subtask["id"],
            "subtask_name": subtask["name"],
            "agent": agent.name,
            "result": result
        }
    
    async def _execute_hierarchical(
        self,
        assignments: List[Tuple[Dict[str, Any], AgentRole]],
        user_id: str,
        chat_id: str
    ) -> List[Dict[str, Any]]:
        """
        层次执行
        
        先执行高优先级任务，再执行低优先级任务
        """
        # 按优先级排序
        sorted_assignments = sorted(
            assignments,
            key=lambda x: self.registry.get_metadata(x[1]).priority,
            reverse=True
        )
        
        # 顺序执行
        return await self._execute_sequential(sorted_assignments, user_id, chat_id)
    
    def _integrate_results(
        self,
        results: List[Dict[str, Any]],
        original_task: str,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """
        结果整合
        
        将多个子任务的结果整合为最终结果
        """
        # 提取所有成功的结果
        successful_results = [r for r in results if "error" not in r]
        failed_results = [r for r in results if "error" in r]
        
        # 构建整合报告
        integrated_report = f"# {original_task} - 协作分析报告\n\n"
        integrated_report += f"**任务类型**: {task_type.value}\n"
        integrated_report += f"**完成子任务**: {len(successful_results)}/{len(results)}\n\n"
        
        # 添加每个子任务的结果
        integrated_report += "## 子任务执行结果\n\n"
        for result in successful_results:
            integrated_report += f"### {result['subtask_name']}\n"
            integrated_report += f"**执行智能体**: {result['agent']}\n\n"
            
            # 添加子任务的答案
            if "result" in result and "answer" in result["result"]:
                integrated_report += result["result"]["answer"] + "\n\n"
        
        # 添加失败的任务
        if failed_results:
            integrated_report += "## 失败的子任务\n\n"
            for result in failed_results:
                integrated_report += f"- {result['subtask_name']}: {result['error']}\n"
        
        # 生成总结
        integrated_report += "\n## 协作总结\n\n"
        integrated_report += f"本次协作共执行 {len(results)} 个子任务，"
        integrated_report += f"成功 {len(successful_results)} 个，失败 {len(failed_results)} 个。\n"
        
        return {
            "success": len(failed_results) == 0,
            "task": original_task,
            "task_type": task_type.value,
            "subtask_results": results,
            "integrated_report": integrated_report,
            "summary": {
                "total_subtasks": len(results),
                "successful": len(successful_results),
                "failed": len(failed_results)
            }
        }


# 全局编排器实例
agent_orchestrator = AgentOrchestrator()
