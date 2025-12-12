# Copyright 2025 ApeCloud, Inc.

"""
智能体API共享工具类
提供通用的工具函数和基础类，减少代码重复
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, Field

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ========== 基础请求/响应模型 ==========

class BaseAgentRequest(BaseModel):
    """智能体请求基类"""
    task: str = Field(..., description="任务描述")
    user_id: str = Field(..., description="用户ID")
    chat_id: Optional[str] = Field(None, description="聊天ID")
    
    class Config:
        extra = "allow"  # 允许子类添加额外字段


class BaseAgentResponse(BaseModel):
    """智能体响应基类"""
    success: bool
    message: str
    answer: Optional[str] = Field(None, description="生成的回答/报告")
    thinking_stream: Optional[List[Dict[str, Any]]] = Field(None, description="思维链")
    
    class Config:
        extra = "allow"  # 允许子类添加额外字段


# ========== 工具函数 ==========

def extract_thinking_stream(state: AgentState) -> List[Dict[str, Any]]:
    """
    从AgentState中提取并序列化思维链
    
    Args:
        state: 智能体状态对象
        
    Returns:
        序列化后的思维链列表
    """
    result = []
    if not hasattr(state, 'thinking_stream'):
        return result
        
    for step in state.thinking_stream:
        try:
            result.append({
                "step_type": step.step_type,
                "description": step.description,
                "detail": step.detail,
                "timestamp": step.timestamp.isoformat() if step.timestamp else None
            })
        except Exception as e:
            logger.warning(f"Failed to serialize thinking step: {e}")
            
    return result


def get_agent_or_raise(role: AgentRole, expected_type: Type[T]) -> T:
    """
    从注册表获取智能体，如果不存在或类型不匹配则抛出HTTPException
    
    Args:
        role: 智能体角色
        expected_type: 期望的智能体类型
        
    Returns:
        智能体实例
        
    Raises:
        HTTPException: 如果智能体不存在或类型不匹配
    """
    agent = agent_registry.get_agent(role)
    
    if agent is None:
        raise HTTPException(
            status_code=500,
            detail=f"{expected_type.__name__} not found in registry. Please restart the API service."
        )
    
    if not isinstance(agent, expected_type):
        raise HTTPException(
            status_code=500,
            detail=f"Agent type mismatch. Expected {expected_type.__name__}, got {type(agent).__name__}"
        )
    
    return agent


def create_agent_state(prefix: str, user_id: str) -> AgentState:
    """
    创建智能体状态对象
    
    Args:
        prefix: 会话ID前缀
        user_id: 用户ID
        
    Returns:
        AgentState实例
    """
    return AgentState(session_id=f"{prefix}-{user_id}")


def setup_agent(agent, user_id: str, chat_id: Optional[str], prefix: str) -> None:
    """
    配置智能体的用户信息
    
    Args:
        agent: 智能体实例
        user_id: 用户ID
        chat_id: 可选的聊天ID
        prefix: 默认chat_id的前缀
    """
    agent.user_id = user_id
    agent.chat_id = chat_id or f"{prefix}-{user_id}"


def build_success_response(
    message: str,
    answer: Optional[str] = None,
    thinking_stream: Optional[List[Dict[str, Any]]] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    构建成功响应
    
    Args:
        message: 成功消息
        answer: 回答内容
        thinking_stream: 思维链
        **extra_fields: 额外的响应字段
        
    Returns:
        响应字典
    """
    response = {
        "success": True,
        "message": message,
        "answer": answer,
        "thinking_stream": thinking_stream
    }
    response.update(extra_fields)
    return response


def handle_agent_error(operation: str, error: Exception, logger: logging.Logger) -> None:
    """
    统一处理智能体错误
    
    Args:
        operation: 操作描述
        error: 异常对象
        logger: 日志记录器
        
    Raises:
        HTTPException: 包含错误信息的HTTP异常
    """
    import traceback
    error_msg = f"{operation} failed: {str(error)}"
    logger.error(f"{error_msg}\n{traceback.format_exc()}")
    raise HTTPException(status_code=500, detail=error_msg)
