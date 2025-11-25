# Copyright 2025 ApeCloud, Inc.

"""
事故预想智能体API接口
提供事故推演、应急预案生成、演练设计等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.specialists.accident_deduction_agent import AccidentDeductionAgent
from aperag.db.database import get_async_session
from aperag.db.ops import AsyncDatabaseOps

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/accident-deduction", tags=["accident-deduction"])


# ========== 请求/响应模型 ==========

class AccidentDeductionRequest(BaseModel):
    """事故推演请求"""
    task: str = Field(..., description="任务描述，如：'#1主变重瓦斯保护动作事故预想'")
    equipment: Optional[str] = Field(None, description="设备名称")
    scenario: Optional[str] = Field(None, description="事故场景")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")
    model_provider: str = Field("siliconflow", description="模型提供商")
    model_name: str = Field("Qwen/Qwen2.5-7B-Instruct", description="模型名称")
    enable_rag: bool = Field(True, description="是否启用RAG检索")
    enable_llm: bool = Field(True, description="是否启用LLM生成")


class EmergencyPlanRequest(BaseModel):
    """应急预案请求"""
    task: str = Field(..., description="任务描述")
    plan_type: Optional[str] = Field(None, description="预案类型")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")


class DrillDesignRequest(BaseModel):
    """演练设计请求"""
    task: str = Field(..., description="任务描述")
    drill_type: Optional[str] = Field(None, description="演练类型")
    participants: Optional[List[str]] = Field(None, description="参演人员")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")


class AccidentDeductionResponse(BaseModel):
    """事故推演响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    thinking_stream: Optional[List[Dict]] = None


class ThinkingStep(BaseModel):
    """思维步骤"""
    step_type: str
    description: str
    detail: Optional[Dict] = None
    timestamp: str


# ========== API端点 ==========

@router.post("/deduction", response_model=AccidentDeductionResponse)
async def generate_accident_deduction(
    request: AccidentDeductionRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    生成事故推演报告
    
    Args:
        request: 事故推演请求
        session: 数据库会话
        
    Returns:
        事故推演响应
    """
    try:
        # 获取智能体
        agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
        
        if not isinstance(agent, AccidentDeductionAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        # 设置用户信息
        agent.user_id = request.user_id if request.enable_rag or request.enable_llm else None
        agent.chat_id = request.chat_id or f"accident-{request.user_id}"
        
        # 创建状态
        state = AgentState(session_id=f"deduction-{request.user_id}")
        
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
        
        return AccidentDeductionResponse(
            success=True,
            message="事故推演报告生成成功",
            data=result.get("deduction"),
            report=result.get("answer"),
            thinking_stream=thinking_stream
        )
        
    except Exception as e:
        logger.error(f"Accident deduction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-plan", response_model=AccidentDeductionResponse)
async def generate_emergency_plan(
    request: EmergencyPlanRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    生成应急预案
    
    Args:
        request: 应急预案请求
        session: 数据库会话
        
    Returns:
        应急预案响应
    """
    try:
        agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
        
        if not isinstance(agent, AccidentDeductionAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"plan-{request.user_id}"
        
        state = AgentState(session_id=f"plan-{request.user_id}")
        
        result = await agent.run(state, {
            "task": request.task
        })
        
        return AccidentDeductionResponse(
            success=True,
            message="应急预案生成成功",
            data=result.get("plan"),
            report=result.get("answer")
        )
        
    except Exception as e:
        logger.error(f"Emergency plan generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drill-design", response_model=AccidentDeductionResponse)
async def design_drill(
    request: DrillDesignRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    设计应急演练
    
    Args:
        request: 演练设计请求
        session: 数据库会话
        
    Returns:
        演练设计响应
    """
    try:
        agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
        
        if not isinstance(agent, AccidentDeductionAgent):
            raise HTTPException(status_code=500, detail="Agent type mismatch")
        
        agent.user_id = request.user_id
        agent.chat_id = request.chat_id or f"drill-{request.user_id}"
        
        state = AgentState(session_id=f"drill-{request.user_id}")
        
        result = await agent.run(state, {
            "task": request.task
        })
        
        return AccidentDeductionResponse(
            success=True,
            message="演练方案设计成功",
            data=result.get("drill"),
            report=result.get("answer")
        )
        
    except Exception as e:
        logger.error(f"Drill design failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_templates():
    """
    获取可用的事故场景模板
    
    Returns:
        模板列表
    """
    templates = [
        {
            "id": "transformer_gas",
            "name": "主变重瓦斯保护动作",
            "equipment": "主变压器",
            "scenario": "重瓦斯保护动作",
            "description": "主变压器重瓦斯保护动作跳闸事故预想"
        },
        {
            "id": "busbar_fault",
            "name": "母线故障",
            "equipment": "母线",
            "scenario": "母差保护动作",
            "description": "母线故障跳闸事故预想"
        },
        {
            "id": "line_fault",
            "name": "线路故障",
            "equipment": "输电线路",
            "scenario": "线路保护动作",
            "description": "输电线路故障事故预想"
        },
        {
            "id": "fire",
            "name": "设备火灾",
            "equipment": "变电站设备",
            "scenario": "火灾事故",
            "description": "变电站火灾事故预想"
        }
    ]
    
    return {
        "success": True,
        "templates": templates
    }


@router.websocket("/ws/deduction")
async def websocket_deduction(websocket: WebSocket):
    """
    WebSocket接口 - 实时事故推演
    
    支持流式返回思维链和推演过程
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
            agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
            agent.user_id = user_id
            agent.chat_id = f"ws-{user_id}"
            
            # 创建状态
            state = AgentState(session_id=f"ws-{user_id}")
            
            # 发送开始消息
            await websocket.send_json({
                "type": "start",
                "message": "开始事故推演..."
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
                    "data": result.get("deduction"),
                    "report": result.get("answer")
                })
                
                # 发送完成消息
                await websocket.send_json({
                    "type": "complete",
                    "message": "事故推演完成"
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
        agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
        
        return {
            "status": "healthy",
            "agent": agent.name if agent else "not found",
            "role": AgentRole.ACCIDENT_DEDUCTION.value
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
