# Copyright 2025 ApeCloud, Inc.

"""
操作票专家API接口
提供操作票生成、审核、模板查询等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent.core.models import AgentRole
from aperag.agent.specialists.operation_ticket_agent import OperationTicketAgent
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

router = APIRouter(prefix="/api/v1/agents/operation-ticket", tags=["operation-ticket"])


# ========== 请求/响应模型 ==========

class OperationTicketRequest(BaseAgentRequest):
    """操作票生成请求"""
    equipment: Optional[str] = Field(None, description="设备名称")
    operation_type: Optional[str] = Field(None, description="操作类型")
    target_state: Optional[str] = Field(None, description="目标状态")
    enable_rag: bool = Field(True, description="是否启用RAG检索")
    enable_llm: bool = Field(True, description="是否启用LLM生成")


class TicketReviewRequest(BaseAgentRequest):
    """操作票审核请求"""
    ticket_no: Optional[str] = Field(None, description="操作票编号")
    ticket_content: Optional[str] = Field(None, description="操作票内容")


class OperationTicketResponse(BaseAgentResponse):
    """操作票响应"""
    ticket: Optional[Dict[str, Any]] = Field(None, description="操作票详情")
    safety_check: Optional[Dict[str, Any]] = Field(None, description="安全检查结果")


# ========== API端点 ==========

@router.post("/generate", response_model=OperationTicketResponse)
async def generate_operation_ticket(
    request: OperationTicketRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """生成操作票"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.OPERATION_TICKET, OperationTicketAgent)
        
        # 根据 RAG/LLM 设置配置 user_id
        effective_user_id = request.user_id if (request.enable_rag or request.enable_llm) else None
        agent.user_id = effective_user_id
        agent.chat_id = request.chat_id or f"operation-{request.user_id}"
        
        # 创建状态
        state = create_agent_state("operation", request.user_id)
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task,
            "equipment": request.equipment,
            "operation_type": request.operation_type,
            "target_state": request.target_state
        })
        
        return OperationTicketResponse(
            success=True,
            message="操作票生成成功",
            ticket=result.get("ticket"),
            answer=result.get("answer") or result.get("report"),
            safety_check=result.get("safety_check"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Operation ticket generation", e, logger)


@router.post("/review", response_model=OperationTicketResponse)
async def review_operation_ticket(
    request: TicketReviewRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """审核操作票"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.OPERATION_TICKET, OperationTicketAgent)
        setup_agent(agent, request.user_id, request.chat_id, "review")
        
        # 创建状态
        state = create_agent_state("review", request.user_id)
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task,
            "ticket_no": request.ticket_no,
            "ticket_content": request.ticket_content
        })
        
        return OperationTicketResponse(
            success=True,
            message="操作票审核完成",
            ticket=result.get("review_result"),
            answer=result.get("answer") or result.get("report"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Operation ticket review", e, logger)


@router.get("/templates")
async def get_operation_templates():
    """获取可用的操作票模板"""
    templates = [
        {
            "id": "transformer_to_maintenance",
            "name": "主变转检修",
            "equipment_type": "主变压器",
            "operation_type": "运行转检修",
            "description": "主变压器由运行状态转为检修状态"
        },
        {
            "id": "transformer_to_operation",
            "name": "主变转运行",
            "equipment_type": "主变压器",
            "operation_type": "检修转运行",
            "description": "主变压器由检修状态转为运行状态"
        },
        {
            "id": "busbar_switching",
            "name": "母线倒闸",
            "equipment_type": "母线系统",
            "operation_type": "母线切换",
            "description": "母线间的负荷转移操作"
        },
        {
            "id": "line_commissioning",
            "name": "线路投运",
            "equipment_type": "输电线路",
            "operation_type": "设备投运",
            "description": "线路由停运状态转为运行状态"
        },
        {
            "id": "line_decommissioning",
            "name": "线路停运",
            "equipment_type": "输电线路",
            "operation_type": "设备停运",
            "description": "线路由运行状态转为停运状态"
        }
    ]
    
    return {
        "success": True,
        "templates": templates
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        agent = get_agent_or_raise(AgentRole.OPERATION_TICKET, OperationTicketAgent)
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.OPERATION_TICKET.value
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
