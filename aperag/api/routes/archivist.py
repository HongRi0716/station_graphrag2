# Copyright 2025 ApeCloud, Inc.

"""
The Archivist（图谱专家）API接口
提供知识检索、图谱遍历、历史查询等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent.core.models import AgentRole
from aperag.agent.specialists.archivist import ArchivistAgent
from aperag.db.database import get_async_session

from .utils import (
    BaseAgentResponse,
    extract_thinking_stream,
    get_agent_or_raise,
    create_agent_state,
    setup_agent,
    handle_agent_error,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/archivist", tags=["archivist"])


# ========== 请求/响应模型 ==========

class ArchivistRequest(BaseModel):
    """图谱专家请求"""
    query: str = Field(..., description="查询内容")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")
    search_type: str = Field("hybrid", description="检索类型: vector/graph/hybrid")
    top_k: int = Field(10, description="返回结果数量")
    collection_ids: Optional[List[str]] = Field(None, description="指定检索的知识库ID列表")


class ArchivistResponse(BaseAgentResponse):
    """图谱专家响应"""
    documents: Optional[List[Dict]] = Field(None, description="检索到的文档")
    count: int = Field(0, description="文档数量")


# ========== API端点 ==========

@router.post("/search", response_model=ArchivistResponse)
async def search_knowledge(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """知识库检索"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.ARCHIVIST, ArchivistAgent)
        setup_agent(agent, request.user_id, request.chat_id, "archivist")
        
        # 创建状态
        state = create_agent_state("archivist", request.user_id)
        
        # 执行检索
        result = await agent.run(state, {
            "query": request.query,
            "search_type": request.search_type,
            "collection_ids": request.collection_ids
        })
        
        documents = result.get("documents", [])
        return ArchivistResponse(
            success=True,
            message="检索成功",
            answer=result.get("answer"),
            documents=documents,
            count=result.get("count", len(documents)),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Knowledge search", e, logger)


@router.post("/graph-traversal", response_model=ArchivistResponse)
async def graph_traversal(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """图谱关系遍历"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.ARCHIVIST, ArchivistAgent)
        setup_agent(agent, request.user_id, request.chat_id, "archivist-graph")
        
        # 创建状态
        state = create_agent_state("archivist-graph", request.user_id)
        
        # 执行图谱遍历
        result = await agent._graph_traversal(state, request.query)
        
        return ArchivistResponse(
            success=True,
            message="图谱遍历成功",
            answer=result.get("answer"),
            documents=[],
            count=0,
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Graph traversal", e, logger)


@router.post("/historical-search", response_model=ArchivistResponse)
async def historical_search(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """历史数据查询"""
    try:
        # 获取并配置智能体
        agent = get_agent_or_raise(AgentRole.ARCHIVIST, ArchivistAgent)
        setup_agent(agent, request.user_id, request.chat_id, "archivist-history")
        
        # 创建状态
        state = create_agent_state("archivist-history", request.user_id)
        
        # 执行历史查询
        result = await agent._historical_search(state, request.query, request.collection_ids)
        
        documents = result.get("documents", [])
        return ArchivistResponse(
            success=True,
            message="历史查询成功",
            answer=result.get("answer"),
            documents=documents,
            count=result.get("count", len(documents)),
            thinking_stream=extract_thinking_stream(state)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_agent_error("Historical search", e, logger)


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        agent = get_agent_or_raise(AgentRole.ARCHIVIST, ArchivistAgent)
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.ARCHIVIST.value
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
