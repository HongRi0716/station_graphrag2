# Copyright 2025 ApeCloud, Inc.

"""
通用智能体API路由工厂
用于快速生成智能体API路由的模板
"""

import logging
from typing import Any, Dict, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent import agent_registry
from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole

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


def create_generic_agent_router(
    prefix: str,
    tag: str,
    role: AgentRole,
    agent_class: Type[BaseAgent],
    agent_name: str,
    description: str = ""
) -> APIRouter:
    """
    创建通用智能体路由
    
    Args:
        prefix: 路由前缀，如 "detective"
        tag: API 标签
        role: 智能体角色
        agent_class: 智能体类
        agent_name: 智能体名称（用于日志和消息）
        description: 智能体描述
        
    Returns:
        配置好的 APIRouter
    """
    
    router = APIRouter(prefix=f"/api/v1/agents/{prefix}", tags=[tag])
    
    @router.post("/execute", response_model=BaseAgentResponse)
    async def execute_task(
        request: BaseAgentRequest,
        session = Depends(get_async_session)
    ):
        """执行智能体任务"""
        try:
            agent = get_agent_or_raise(role, agent_class)
            setup_agent(agent, request.user_id, request.chat_id, prefix)
            state = create_agent_state(prefix, request.user_id)
            
            result = await agent.run(state, {"task": request.task})
            
            return BaseAgentResponse(
                success=True,
                message=f"{agent_name}任务执行成功",
                answer=result.get("answer"),
                thinking_stream=extract_thinking_stream(state)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            handle_agent_error(f"{agent_name} task execution", e, logger)
    
    @router.get("/health")
    async def health_check():
        """健康检查"""
        try:
            agent = get_agent_or_raise(role, agent_class)
            return {
                "status": "healthy",
                "agent": agent.name if agent else "not found",
                "role": role.value
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
    
    return router


# 工具函数：获取数据库会话
def get_async_session():
    """获取异步数据库会话的依赖"""
    from aperag.db.database import get_async_session as _get_async_session
    return _get_async_session
