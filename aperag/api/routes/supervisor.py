# Copyright 2025 ApeCloud, Inc.

"""
The Supervisor（值班长）API接口
提供任务分发、协作协调、态势感知等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.specialists.supervisor_agent import SupervisorAgent
from aperag.db.database import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/supervisor", tags=["supervisor"])


# ========== 请求/响应模型 ==========

class SupervisorRequest(BaseModel):
    """值班长任务请求"""
    task: str = Field(..., description="任务描述")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")
    priority: Optional[str] = Field("normal", description="优先级: urgent/high/normal")


class SupervisorResponse(BaseModel):
    """值班长响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    task_analysis: Optional[Dict] = None
    thinking_stream: Optional[List[Dict]] = None


class StationStatusResponse(BaseModel):
    """变电站态势响应"""
    success: bool
    status: Dict[str, Any]


# ========== API端点 ==========

@router.post("/dispatch", response_model=SupervisorResponse)
async def dispatch_task(
    request: SupervisorRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    任务分发
    
    值班长接收任务并智能分发给合适的专家智能体
    
    Args:
        request: 任务请求
        session: 数据库会话
        
    Returns:
        任务执行结果
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
        
        if not isinstance(agent, SupervisorAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"supervisor-{request.user_id}"
        
        # 创建状态
        state = AgentState(session_id=f"supervisor-{request.user_id}")
        
        # 执行任务
        result = await agent.run(state, {
            "task": request.task
        })
        
        # 提取思维链
        thinking_stream = [
            {
                "step_type": step.step_type,
                "description": step.description,
                "detail": step.detail,
                "timestamp": step.timestamp.isoformat() if step.timestamp else None
            }
            for step in state.thinking_stream
        ]
        
        return SupervisorResponse(
            success=True,
            message="任务分发成功",
            data=result,
            task_analysis=result.get("task_analysis"),
            thinking_stream=thinking_stream
        )
        
    except Exception as e:
        logger.error(f"Task dispatch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StationStatusResponse)
async def get_station_status(
    user_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取变电站态势
    
    实时获取变电站设备状态和告警信息
    
    Args:
        user_id: 用户ID
        session: 数据库会话
        
    Returns:
        变电站态势信息
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
        
        if not isinstance(agent, SupervisorAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = user_id
        
        # 创建状态
        state = AgentState(session_id=f"supervisor-status-{user_id}")
        
        # 获取态势
        status = await agent.get_station_status(state)
        
        return StationStatusResponse(
            success=True,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Get station status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/dispatch")
async def websocket_dispatch(websocket: WebSocket):
    """
    WebSocket接口 - 实时任务分发
    
    支持流式返回思维链和执行过程
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收请求
            data = await websocket.receive_json()
            
            task = data.get("task")
            user_id = data.get("user_id")
            
            if not task or not user_id:
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing required fields: task, user_id"
                })
                continue
            
            # 获取智能体
            agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
            agent.user_id = user_id
            agent.chat_id = f"ws-{user_id}"
            
            # 创建状态
            state = AgentState(session_id=f"ws-{user_id}")
            
            # 发送开始消息
            await websocket.send_json({
                "type": "start",
                "message": "值班长开始处理任务..."
            })
            
            # 执行任务
            try:
                result = await agent.run(state, {"task": task})
                
                # 发送思维链
                for step in state.thinking_stream:
                    await websocket.send_json({
                        "type": "thinking",
                        "step_type": step.step_type,
                        "description": step.description,
                        "detail": step.detail
                    })
                
                # 发送最终结果
                await websocket.send_json({
                    "type": "result",
                    "data": result,
                    "task_analysis": result.get("task_analysis")
                })
                
                # 发送完成消息
                await websocket.send_json({
                    "type": "complete",
                    "message": "任务处理完成"
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查智能体是否可用
        agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
        
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.SUPERVISOR.value
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
