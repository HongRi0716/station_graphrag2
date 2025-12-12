# Copyright 2025 ApeCloud, Inc.

"""
保电方案专家API接口
提供保电方案编制、巡检计划、应急资源配置等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent.core.models import AgentRole
from aperag.agent.specialists.power_guarantee_agent import PowerGuaranteeAgent
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

router = APIRouter(prefix="/api/v1/agents/power-guarantee", tags=["power-guarantee"])


# ========== 请求/响应模型 ==========

class PowerGuaranteeRequest(BaseAgentRequest):
    """保电方案请求"""
    event_name: Optional[str] = Field(None, description="活动名称")
    event_level: Optional[str] = Field(None, description="保电级别")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class PowerGuaranteeResponse(BaseAgentResponse):
    """保电方案响应"""
    plan: Optional[Dict[str, Any]] = Field(None, description="保电方案详情")


# ========== API端点 ==========

@router.post("/plan", response_model=PowerGuaranteeResponse)
async def generate_power_guarantee_plan(
    request: PowerGuaranteeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """生成保电方案"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.POWER_GUARANTEE, PowerGuaranteeAgent)
        setup_agent(agent, request.user_id, request.chat_id, "power-guarantee")
        
        # 创建状态
        state = create_agent_state("power-guarantee", request.user_id)
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task,
            "event_name": request.event_name,
            "event_level": request.event_level,
            "start_date": request.start_date,
            "end_date": request.end_date
        })

        return PowerGuaranteeResponse(
            success=True,
            message="保电方案生成成功",
            plan=result.get("plan"),
            answer=result.get("answer") or result.get("report"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Power guarantee plan generation", e, logger)


@router.post("/inspection", response_model=PowerGuaranteeResponse)
async def generate_inspection_plan(
    request: PowerGuaranteeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """生成巡检计划"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.POWER_GUARANTEE, PowerGuaranteeAgent)
        setup_agent(agent, request.user_id, request.chat_id, "inspection")
        
        # 创建状态
        state = create_agent_state("inspection", request.user_id)
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task
        })
        
        return PowerGuaranteeResponse(
            success=True,
            message="巡检计划生成成功",
            plan=result.get("plan"),
            answer=result.get("answer") or result.get("report"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Inspection plan generation", e, logger)


@router.post("/resources", response_model=PowerGuaranteeResponse)
async def prepare_resources(
    request: PowerGuaranteeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """准备应急资源"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.POWER_GUARANTEE, PowerGuaranteeAgent)
        setup_agent(agent, request.user_id, request.chat_id, "resources")
        
        # 创建状态
        state = create_agent_state("resources", request.user_id)
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task
        })
        
        return PowerGuaranteeResponse(
            success=True,
            message="资源清单生成成功",
            plan=result.get("resources"),
            answer=result.get("answer") or result.get("report"),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Resource preparation", e, logger)


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        agent = get_agent_or_raise(AgentRole.POWER_GUARANTEE, PowerGuaranteeAgent)
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.POWER_GUARANTEE.value
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
