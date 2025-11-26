import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.agent_orchestrator import agent_orchestrator, TaskType, CollaborationMode

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """
    值班长智能体 (Supervisor Agent)
    
    职责：
    - 统筹协调所有专家智能体
    - 任务分发和优先级管理
    - 综合决策和应急指挥
    - 全局态势感知
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SUPERVISOR,
            name="值班长 (Supervisor)",
            description="变电站总控智能体，负责统筹协调和综合决策",
            tools=["task_dispatcher", "priority_manager", "decision_maker"]
        )
    
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行总控任务"""
        query = input_data.get("task", "")
        
        self._log_thought(state, "thought", f"值班长接收任务: {query}")
        
        # 分析任务类型
        task_analysis = await self._analyze_task(state, query)
        
        self._log_thought(
            state,
            "action",
            f"任务分析: {task_analysis['task_type']}",
            detail=task_analysis
        )
        
        # 判断是否需要协作
        if task_analysis['requires_collaboration']:
            return await self._coordinate_collaboration(state, query, task_analysis)
        else:
            return await self._handle_single_task(state, query, task_analysis)
    
    async def _analyze_task(self, state: AgentState, query: str) -> Dict[str, Any]:
        """
        分析任务类型和复杂度
        策略: 优先使用 LLM 进行精准意图识别，如果失败则回退到关键词匹配
        """
        # 1. 尝试使用 LLM 进行分析
        try:
            prompt = f"""
你是一个变电站值班长智能体。请分析以下用户指令，并提取任务关键信息。

用户指令: "{query}"

请分析并返回如下 JSON 格式 (不要包含 Markdown 代码块标记):
{{
    "task_type": "任务类型(emergency_response/operation_planning/safety_check/information_retrieval/power_guarantee/unknown)",
    "complexity": "复杂度(high/medium/low)",
    "priority": "优先级(urgent/high/normal)",
    "requires_collaboration": true/false,
    "involved_agents": ["涉及的智能体角色ID(accident_deduction/operation_ticket/work_permit/archivist/power_guarantee/diagnosis)"],
    "reasoning": "简短的分析理由"
}}

任务类型定义:
- emergency_response: 事故、故障、跳闸、异常告警处置
- operation_planning: 倒闸操作、投运、停运、转备用
- safety_check: 检修、维护、工作票、安全检查
- information_retrieval: 查询、检索、查找历史记录或规程
- power_guarantee: 保电、重要活动供电保障
"""
            self._log_thought(state, "thought", "正在使用 LLM 分析任务意图...")
            
            response = await self._generate_with_llm(
                state=state,
                prompt=prompt,
                temperature=0.1, # 低温度以保证输出格式稳定
                max_tokens=500
            )
            
            import json
            import re
            
            # 清理可能的 Markdown 标记
            cleaned_response = re.sub(r"```json|```", "", response).strip()
            analysis = json.loads(cleaned_response)
            
            # 简单的校验
            if "task_type" in analysis:
                self._log_thought(state, "observation", f"LLM 意图识别成功: {analysis['task_type']}")
                return analysis
                
        except Exception as e:
            logger.warning(f"LLM task analysis failed: {e}, falling back to keyword matching.")
            self._log_thought(state, "correction", f"LLM 分析失败，回退到规则匹配: {str(e)}")

        # 2. 回退到关键词匹配 (原有逻辑)
        analysis = {
            "task_type": "unknown",
            "complexity": "low",
            "requires_collaboration": False,
            "priority": "normal",
            "involved_agents": [],
            "reasoning": "基于关键词规则匹配"
        }
        
        # 事故相关
        if any(keyword in query for keyword in ["事故", "故障", "跳闸", "异常", "告警"]):
            analysis["task_type"] = "emergency_response"
            analysis["complexity"] = "high"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "urgent"
            analysis["involved_agents"] = ["accident_deduction", "diagnosis", "operation_ticket"]
        
        # 操作相关
        elif any(keyword in query for keyword in ["操作", "倒闸", "投运", "停运", "转冷备用", "转热备用"]):
            analysis["task_type"] = "operation_planning"
            analysis["complexity"] = "medium"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "high"
            analysis["involved_agents"] = ["operation_ticket", "accident_deduction", "work_permit"]
        
        # 检修相关
        elif any(keyword in query for keyword in ["检修", "维护", "试验", "工作票"]):
            analysis["task_type"] = "safety_check"
            analysis["complexity"] = "medium"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "normal"
            analysis["involved_agents"] = ["work_permit", "accident_deduction"]
        
        # 查询相关
        elif any(keyword in query for keyword in ["查询", "检索", "查找", "历史", "搜索"]):
            analysis["task_type"] = "information_retrieval"
            analysis["complexity"] = "low"
            analysis["requires_collaboration"] = False
            analysis["priority"] = "normal"
            analysis["involved_agents"] = ["archivist"]
        
        # 保电相关
        elif any(keyword in query for keyword in ["保电", "重要活动", "供电保障"]):
            analysis["task_type"] = "power_guarantee"
            analysis["complexity"] = "high"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "high"
            analysis["involved_agents"] = ["power_guarantee", "accident_deduction", "operation_ticket"]
        
        return analysis
    
    async def _coordinate_collaboration(
        self,
        state: AgentState,
        query: str,
        task_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """协调多智能体协作"""
        self._log_thought(
            state,
            "plan",
            f"启动智能体协作，涉及 {len(task_analysis['involved_agents'])} 个智能体"
        )
        
        # 确定任务类型
        task_type_map = {
            "emergency_response": TaskType.EMERGENCY_RESPONSE,
            "operation_planning": TaskType.OPERATION_PLANNING,
            "safety_check": TaskType.SAFETY_CHECK,
            "accident_analysis": TaskType.ACCIDENT_ANALYSIS,
            "power_guarantee": TaskType.OPERATION_PLANNING  # 使用操作规划类型
        }
        
        task_type = task_type_map.get(
            task_analysis["task_type"],
            TaskType.ACCIDENT_ANALYSIS
        )
        
        # 确定协作模式
        if task_analysis["priority"] == "urgent":
            mode = CollaborationMode.PARALLEL  # 紧急任务并行执行
        else:
            mode = CollaborationMode.SEQUENTIAL  # 常规任务顺序执行
        
        self._log_thought(
            state,
            "action",
            f"协作模式: {mode.value}, 优先级: {task_analysis['priority']}"
        )
        
        # 执行协作
        if self.user_id:
            try:
                result = await agent_orchestrator.execute_collaboration(
                    task=query,
                    task_type=task_type,
                    user_id=self.user_id,
                    chat_id=self.chat_id or f"supervisor-{self.user_id}",
                    mode=mode
                )
                
                self._log_thought(
                    state,
                    "observation",
                    f"协作完成: {result['summary']['successful']}/{result['summary']['total_subtasks']} 成功"
                )
                
                return {
                    "answer": result["integrated_report"],
                    "collaboration_result": result,
                    "task_analysis": task_analysis
                }
                
            except Exception as e:
                logger.error(f"Collaboration failed: {e}", exc_info=True)
                self._log_thought(
                    state,
                    "correction",
                    f"协作失败: {str(e)}，回退到单任务处理"
                )
                return await self._handle_single_task(state, query, task_analysis)
        else:
            # 没有user_id，回退到单任务处理
            self._log_thought(
                state,
                "observation",
                "未设置user_id，回退到单任务处理"
            )
            return await self._handle_single_task(state, query, task_analysis)
    
    async def _handle_single_task(
        self,
        state: AgentState,
        query: str,
        task_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理单个任务"""
        self._log_thought(state, "action", "分发任务到专家智能体")
        
        # 选择合适的智能体
        if task_analysis["involved_agents"]:
            target_agent_capability = task_analysis["involved_agents"][0]
        else:
            target_agent_capability = "rag"
        
        # 查找智能体
        from aperag.agent import agent_registry
        agents = agent_registry.find_by_capability(target_agent_capability)
        
        if agents and self.user_id:
            agent = agents[0]
            agent.user_id = self.user_id
            agent.chat_id = self.chat_id
            
            self._log_thought(
                state,
                "action",
                f"分发任务到: {agent.name}"
            )
            
            # 执行任务
            agent_state = AgentState(session_id=f"supervisor-delegate-{self.user_id}")
            result = await agent.run(agent_state, {"task": query})
            
            return {
                "answer": result.get("answer", ""),
                "delegated_to": agent.name,
                "task_analysis": task_analysis
            }
        else:
            # 回退到通用响应
            return {
                "answer": self._generate_general_guidance(query, task_analysis),
                "task_analysis": task_analysis
            }
    
    async def get_station_status(self, state: AgentState) -> Dict[str, Any]:
        """获取变电站整体态势"""
        self._log_thought(state, "action", "获取变电站态势")
        
        # 检索实时数据（如果有MCP会话）
        equipment_status = []
        alarms = []
        
        if self.user_id:
            try:
                # 检索设备状态
                self._log_thought(state, "action", "检索设备运行状态")
                status_results = await self._search_knowledge(
                    state=state,
                    query="变电站设备运行状态 实时数据",
                    top_k=10
                )
                equipment_status = self._extract_documents_from_tool_results(status_results)
                
                # 检索告警信息
                self._log_thought(state, "action", "检索告警信息")
                alarm_results = await self._search_knowledge(
                    state=state,
                    query="变电站告警 异常信息",
                    top_k=5
                )
                alarms = self._extract_documents_from_tool_results(alarm_results)
                
            except Exception as e:
                logger.warning(f"Status retrieval failed: {e}")
                self._log_thought(state, "observation", f"态势检索失败: {str(e)}")
        
        # 构建态势报告
        status_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "正常" if len(alarms) == 0 else "异常",
            "equipment_count": len(equipment_status),
            "alarm_count": len(alarms),
            "equipment_status": equipment_status[:5],
            "recent_alarms": alarms[:3]
        }
        
        self._log_thought(
            state,
            "observation",
            f"态势获取完成: {status_report['equipment_count']}个设备, {status_report['alarm_count']}个告警"
        )
        
        return status_report
    
    def _generate_general_guidance(self, query: str, task_analysis: Dict) -> str:
        """生成通用指导"""
        guidance = f"## 值班长分析\n\n"
        guidance += f"**任务**: {query}\n"
        guidance += f"**任务类型**: {task_analysis['task_type']}\n"
        guidance += f"**复杂度**: {task_analysis['complexity']}\n"
        guidance += f"**优先级**: {task_analysis['priority']}\n\n"
        
        guidance += "### 建议处理流程\n\n"
        
        if task_analysis["task_type"] == "emergency_response":
            guidance += "1. **立即汇报调度** - 向地区调度汇报故障情况\n"
            guidance += "2. **启动应急预案** - 按照应急预案执行\n"
            guidance += "3. **组织现场检查** - 派员检查设备状态\n"
            guidance += "4. **分析故障原因** - 查看保护动作报告\n"
            guidance += "5. **制定恢复方案** - 制定供电恢复计划\n"
        elif task_analysis["task_type"] == "operation_planning":
            guidance += "1. **编制操作票** - 生成详细操作步骤\n"
            guidance += "2. **进行事故预想** - 分析可能的风险\n"
            guidance += "3. **制定安全措施** - 确定安全措施\n"
            guidance += "4. **审批操作票** - 完成审批流程\n"
            guidance += "5. **执行操作** - 按票执行操作\n"
        elif task_analysis["task_type"] == "safety_check":
            guidance += "1. **编制工作票** - 填写工作票信息\n"
            guidance += "2. **识别危险点** - 分析作业危险点\n"
            guidance += "3. **制定安全措施** - 制定针对性措施\n"
            guidance += "4. **审批工作票** - 完成审批流程\n"
            guidance += "5. **现场安全检查** - 检查措施落实\n"
        elif task_analysis["task_type"] == "information_retrieval":
            guidance += "1. **明确查询需求** - 确定查询范围\n"
            guidance += "2. **执行知识检索** - 在知识库中检索\n"
            guidance += "3. **整理检索结果** - 筛选相关信息\n"
            guidance += "4. **提供查询结果** - 返回检索结果\n"
        
        guidance += "\n### 涉及的专家智能体\n\n"
        for agent in task_analysis["involved_agents"]:
            guidance += f"- {agent}\n"
        
        return guidance
    
    def _extract_documents_from_tool_results(self, tool_results: List[Dict]) -> List[Dict]:
        """从工具调用结果中提取文档"""
        documents = []
        for result in tool_results:
            if isinstance(result, dict) and "result" in result:
                result_data = result["result"]
                if isinstance(result_data, dict) and "documents" in result_data:
                    documents.extend(result_data["documents"])
        return documents
