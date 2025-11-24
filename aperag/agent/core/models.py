from datetime import datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentRole(str, Enum):
    """
    定义智能体角色 (Persona)
    """

    USER = "user"
    SYSTEM = "system"
    SUPERVISOR = "supervisor"  # 值长：总控大脑
    DETECTIVE = "detective"  # 图纸侦探：视觉/拓扑
    GATEKEEPER = "gatekeeper"  # 安监卫士：规则/五防
    ARCHIVIST = "archivist"  # 图谱专家：检索/数据
    PROPHET = "prophet"  # 趋势预言家：预测
    AUDITOR = "auditor"  # 合规审计师：文档校验
    DIAGNOSTICIAN = "diagnostician"  # 故障诊断师：录波分析/事故推演
    INSTRUCTOR = "instructor"  # 培训教官：仿真/考核
    CALCULATOR = "calculator"  # 整定计算师：参数核算
    SCRIBE = "scribe"  # 文书专员：自动填报/语音转录
    SENTINEL = "sentinel"  # 巡视哨兵：视频监控/实时安防
    OPERATION_TICKET = "operation_ticket"  # 操作票专家：操作票编制审核
    WORK_PERMIT = "work_permit"  # 工作票专家：工作票编制审核
    ACCIDENT_DEDUCTION = "accident_deduction"  # 事故预想专家：事故推演
    POWER_GUARANTEE = "power_guarantee"  # 保电方案专家：保电方案编制


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCallInfo(BaseModel):
    """记录工具调用的详细信息"""

    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    execution_time_ms: float = 0.0
    success: bool = True


class AgentThinkingStep(BaseModel):
    """
    核心数据结构：用于前端“思考气泡”的可视化展示 (Reasoning Bubble)
    记录智能体在单次交互中的思维碎片
    """

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: AgentRole
    step_type: Literal[
        "plan", "thought", "action", "observation", "correction", "final_answer"
    ]

    # 思考的具体内容（例如："正在分析主接线图 B5391S..."）
    description: str

    # 具体的详情（例如：检索到的文档片段、生成的中间 JSON、工具调用参数）
    detail: Optional[Dict[str, Any]] = None

    # 引用来源（支持证据溯源）
    citations: List[str] = Field(default_factory=list)

    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(populate_by_name=True)


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SubTask(BaseModel):
    """
    值长拆解出的子任务
    """

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    assigned_to: AgentRole
    dependencies: List[str] = Field(default_factory=list)  # 依赖的 task_id
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskPlan(BaseModel):
    """
    任务编排计划 (SOP)
    """

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str
    goal: str
    tasks: List[SubTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentMessage(BaseModel):
    """
    智能体之间传递的消息对象
    """

    sender: AgentRole
    receiver: AgentRole
    content: str
    message_type: Literal["instruction", "report",
                          "query", "error"] = "instruction"

    # 携带上下文数据（例如：解析后的 PDF 文本、图谱子图）
    context_data: Optional[Dict[str, Any]] = None

    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """
    智能体运行时的上下文状态
    """

    session_id: str
    current_plan: Optional[TaskPlan] = None
    memory: List[AgentMessage] = Field(default_factory=list)
    thinking_stream: List[AgentThinkingStep] = Field(default_factory=list)

    # 共享黑板 (Blackboard Pattern)：存放各个专家的产出物
    shared_context: Dict[str, Any] = Field(default_factory=dict)

    def add_thought(self, step: AgentThinkingStep):
        self.thinking_stream.append(step)

    def add_message(self, msg: AgentMessage):
        self.memory.append(msg)
