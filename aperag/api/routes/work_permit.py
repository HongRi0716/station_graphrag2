# Copyright 2025 ApeCloud, Inc.

"""
工作票专家API接口
提供工作票生成、审核、危险点识别等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent.core.models import AgentRole
from aperag.agent.specialists.work_permit_agent import WorkPermitAgent
from aperag.db.database import get_async_session

from .utils import (
    BaseAgentRequest,
    BaseAgentResponse,
    extract_thinking_stream,
    get_agent_or_raise,
    create_agent_state,
    setup_agent,
    handle_agent_error,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/work-permit", tags=["work-permit"])


# ========== 请求/响应模型 ==========

class WorkPermitRequest(BaseAgentRequest):
    """工作票生成请求"""
    # task 和 user_id, chat_id 从 BaseAgentRequest 继承
    query: Optional[str] = Field(None, description="查询内容（向后兼容）")
    equipment: Optional[str] = Field(None, description="设备名称")
    work_content: Optional[str] = Field(None, description="工作内容")
    ticket_no: Optional[str] = Field(None, description="票号")
    ticket_content: Optional[str] = Field(None, description="票面内容")
    
    def get_task(self) -> str:
        """获取任务描述，优先使用task，向后兼容query"""
        return self.task if self.task else (self.query or "")


class WorkPermitResponse(BaseAgentResponse):
    """工作票响应"""
    # success, message, answer, thinking_stream 从 BaseAgentResponse 继承
    ticket: Optional[Dict[str, Any]] = Field(None, description="工作票详情")
    hazards: Optional[List[Dict[str, Any]]] = Field(None, description="识别的危险点")
    review_result: Optional[Dict[str, Any]] = Field(None, description="审核结果")


# ========== API端点 ==========

@router.post("/generate", response_model=WorkPermitResponse)
async def generate_work_permit(
    request: WorkPermitRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """生成工作票"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.WORK_PERMIT, WorkPermitAgent)
        setup_agent(agent, request.user_id, request.chat_id, "permit")
        
        # 创建状态
        state = create_agent_state("permit", request.user_id)
        
        # 构造任务描述，确保触发生成逻辑
        task = request.get_task()
        if "生成" not in task and "编制" not in task:
            task = f"生成工作票: {task}"
            
        # 执行任务
        result = await agent.run(state, {
            "task": task,
            "equipment": request.equipment,
            "work_content": request.work_content
        })
        
        # 构建响应
        return WorkPermitResponse(
            success=True,
            message="工作票生成成功",
            ticket=result.get("permit"),
            answer=result.get("answer"),
            hazards=result.get("hazards"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Work permit generation", e, logger)


@router.post("/hazards", response_model=WorkPermitResponse)
async def identify_hazards(
    request: WorkPermitRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """识别危险点"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.WORK_PERMIT, WorkPermitAgent)
        setup_agent(agent, request.user_id, request.chat_id, "hazards")
        
        # 创建状态
        state = create_agent_state("hazards", request.user_id)
        
        # 构造任务描述
        task = request.get_task()
        if "生成" not in task:
            task = f"生成工作票并识别危险点: {task}"
            
        # 执行任务
        result = await agent.run(state, {
            "task": task,
            "equipment": request.equipment,
            "work_content": request.work_content
        })
        
        return WorkPermitResponse(
            success=True,
            message="危险点识别完成",
            ticket=result.get("permit"),
            answer=result.get("answer"),
            hazards=result.get("hazards"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Hazard identification", e, logger)


@router.post("/review", response_model=WorkPermitResponse)
async def review_work_permit(
    request: WorkPermitRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """审核工作票"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.WORK_PERMIT, WorkPermitAgent)
        setup_agent(agent, request.user_id, request.chat_id, "review")
        
        # 创建状态
        state = create_agent_state("review", request.user_id)
        
        # 构造任务描述
        task = request.get_task()
        if "审核" not in task and "检查" not in task:
            task = f"审核工作票: {task}"
            
        # 执行任务
        result = await agent.run(state, {
            "task": task,
            "ticket_no": request.ticket_no,
            "ticket_content": request.ticket_content
        })
        
        return WorkPermitResponse(
            success=True,
            message="工作票审核完成",
            review_result=result.get("review_result"),
            answer=result.get("answer"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Work permit review", e, logger)


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        agent = get_agent_or_raise(AgentRole.WORK_PERMIT, WorkPermitAgent)
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.WORK_PERMIT.value
        }
    except HTTPException:
        return {
            "status": "unhealthy",
            "error": "Agent not available"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
