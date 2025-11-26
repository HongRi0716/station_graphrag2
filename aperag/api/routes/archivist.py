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

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.specialists.archivist import ArchivistAgent
from aperag.db.database import get_async_session

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


class ArchivistResponse(BaseModel):
    """图谱专家响应"""
    success: bool
    message: str
    answer: Optional[str] = None
    documents: Optional[List[Dict]] = None
    count: int = 0
    thinking_stream: Optional[List[Dict]] = None


# ========== API端点 ==========

@router.post("/search", response_model=ArchivistResponse)
async def search_knowledge(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    知识库检索
    
    从知识库中检索相关文档
    
    Args:
        request: 检索请求
        session: 数据库会话
        
    Returns:
        检索结果
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
        
        if not isinstance(agent, ArchivistAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"archivist-{request.user_id}"
        
        # 创建状态
        state = AgentState(session_id=f"archivist-{request.user_id}")
        
        # 执行检索
        result = await agent.run(state, {
            "query": request.query,
            "search_type": request.search_type,
            "collection_ids": request.collection_ids
        })
        
        # 提取思维链
        thinking_stream = [
            {
                "step_type": step.step_type,
                "description": step.description,
                "detail": step.detail
            }
            for step in state.thinking_stream
        ]
        
        return ArchivistResponse(
            success=True,
            message="检索成功",
            answer=result.get("answer"),
            documents=result.get("documents", []),
            count=result.get("count", 0),
            thinking_stream=thinking_stream
        )
        
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph-traversal", response_model=ArchivistResponse)
async def graph_traversal(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    图谱关系遍历
    
    查询设备之间的关系和路径
    
    Args:
        request: 遍历请求
        session: 数据库会话
        
    Returns:
        遍历结果
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
        
        if not isinstance(agent, ArchivistAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"archivist-graph-{request.user_id}"
        
        # 创建状态
        state = AgentState(session_id=f"archivist-graph-{request.user_id}")
        
        # 执行图谱遍历
        result = await agent._graph_traversal(state, request.query)
        
        return ArchivistResponse(
            success=True,
            message="图谱遍历成功",
            answer=result.get("answer"),
            documents=[],
            count=0
        )
        
    except Exception as e:
        logger.error(f"Graph traversal failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical-search", response_model=ArchivistResponse)
async def historical_search(
    request: ArchivistRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    历史数据查询
    
    查询历史记录和案例
    
    Args:
        request: 查询请求
        session: 数据库会话
        
    Returns:
        历史记录
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
        
        if not isinstance(agent, ArchivistAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"archivist-history-{request.user_id}"
        
        # 创建状态
        state = AgentState(session_id=f"archivist-history-{request.user_id}")
        
        # 执行历史查询
        result = await agent._historical_search(state, request.query, request.collection_ids)
        
        return ArchivistResponse(
            success=True,
            message="历史查询成功",
            answer=result.get("answer"),
            documents=result.get("documents", []),
            count=result.get("count", 0)
        )
        
    except Exception as e:
        logger.error(f"Historical search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查智能体是否可用
        agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
        
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.ARCHIVIST.value
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
