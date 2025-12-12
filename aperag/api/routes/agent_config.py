# Copyright 2025 ApeCloud, Inc.

"""
智能体配置管理 API
管理智能体与知识库的绑定关系
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.db.database import get_async_session
from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-config", tags=["Agent Config"])


# ========== Pydantic 模型 ==========

class CollectionBinding(BaseModel):
    """知识库绑定"""
    collection_id: str = Field(..., description="知识库ID")
    collection_name: str = Field(default="", description="知识库名称")
    is_default: bool = Field(default=False, description="是否为默认知识库")


class AgentConfig(BaseModel):
    """智能体配置"""
    role: str = Field(..., description="智能体角色标识")
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    collections: List[CollectionBinding] = Field(default_factory=list, description="绑定的知识库")
    capabilities: List[str] = Field(default_factory=list, description="能力标签")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    priority: int = Field(default=5, description="优先级")


class UpdateCollectionsRequest(BaseModel):
    """更新知识库绑定请求"""
    collection_ids: List[str] = Field(..., description="知识库ID列表")


class AgentConfigResponse(BaseModel):
    """智能体配置响应"""
    success: bool = True
    data: Optional[AgentConfig] = None
    message: str = ""


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    success: bool = True
    agents: List[AgentConfig] = Field(default_factory=list)


# ========== API 端点 ==========

@router.get("/list", response_model=AgentListResponse)
async def list_agent_configs():
    """
    获取所有智能体配置
    """
    agents = []
    
    for agent in agent_registry.list_agents():
        metadata = agent_registry.get_metadata(agent.role)
        
        config = AgentConfig(
            role=agent.role.value,
            name=agent.name,
            description=agent.description,
            collections=[
                CollectionBinding(collection_id=cid, is_default=True)
                for cid in (metadata.default_collections if metadata else [])
            ],
            capabilities=list(metadata.capabilities) if metadata else [],
            system_prompt=metadata.system_prompt_template if metadata else None,
            priority=metadata.priority if metadata else 5
        )
        agents.append(config)
    
    return AgentListResponse(agents=agents)


@router.get("/{role}", response_model=AgentConfigResponse)
async def get_agent_config(role: str):
    """
    获取单个智能体配置
    """
    try:
        agent_role = AgentRole(role)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent role '{role}' not found")
    
    agent = agent_registry.get_agent(agent_role)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{role}' not registered")
    
    metadata = agent_registry.get_metadata(agent_role)
    
    config = AgentConfig(
        role=agent.role.value,
        name=agent.name,
        description=agent.description,
        collections=[
            CollectionBinding(collection_id=cid, is_default=True)
            for cid in (metadata.default_collections if metadata else [])
        ],
        capabilities=list(metadata.capabilities) if metadata else [],
        system_prompt=metadata.system_prompt_template if metadata else None,
        priority=metadata.priority if metadata else 5
    )
    
    return AgentConfigResponse(data=config)


@router.put("/{role}/collections", response_model=AgentConfigResponse)
async def update_agent_collections(
    role: str,
    request: UpdateCollectionsRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    更新智能体的知识库绑定
    """
    try:
        agent_role = AgentRole(role)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent role '{role}' not found")
    
    metadata = agent_registry.get_metadata(agent_role)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Agent metadata not found for '{role}'")
    
    # 更新配置（内存中）
    metadata.default_collections = request.collection_ids
    
    # TODO: 持久化到数据库
    # 可以创建一个 agent_collections 表来存储绑定关系
    
    logger.info(f"Updated collections for {role}: {request.collection_ids}")
    
    agent = agent_registry.get_agent(agent_role)
    config = AgentConfig(
        role=agent.role.value,
        name=agent.name,
        description=agent.description,
        collections=[
            CollectionBinding(collection_id=cid, is_default=True)
            for cid in metadata.default_collections
        ],
        capabilities=list(metadata.capabilities),
        system_prompt=metadata.system_prompt_template,
        priority=metadata.priority
    )
    
    return AgentConfigResponse(
        data=config,
        message=f"Successfully updated {len(request.collection_ids)} collections"
    )


@router.get("/{role}/recommended-collections")
async def get_recommended_collections(
    role: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取推荐的知识库（基于智能体角色）
    """
    # 根据智能体角色推荐相关的知识库
    RECOMMENDED_COLLECTIONS = {
        "operation_ticket": [
            {"category": "规程类", "keywords": ["倒闸操作", "操作规程", "五防"]},
            {"category": "设备类", "keywords": ["设备台账", "设备拓扑", "一次设备"]},
            {"category": "案例类", "keywords": ["操作票范本", "历史操作票"]}
        ],
        "work_permit": [
            {"category": "规程类", "keywords": ["工作票", "安全规程", "检修规程"]},
            {"category": "安全类", "keywords": ["安全措施", "危险点", "安全工器具"]},
            {"category": "案例类", "keywords": ["工作票范本", "典型票据"]}
        ],
        "accident_deduction": [
            {"category": "事故类", "keywords": ["事故案例", "故障分析", "保护动作"]},
            {"category": "应急类", "keywords": ["应急预案", "处置方案", "事故处理"]},
            {"category": "设备类", "keywords": ["设备故障", "缺陷记录"]}
        ],
        "power_guarantee": [
            {"category": "保电类", "keywords": ["保电方案", "重保活动", "供电保障"]},
            {"category": "运行类", "keywords": ["运行方式", "负荷预测", "电网运行"]},
            {"category": "应急类", "keywords": ["应急预案", "备用电源"]}
        ],
        "archivist": [
            {"category": "全局", "keywords": ["所有知识库"]}
        ]
    }
    
    recommendations = RECOMMENDED_COLLECTIONS.get(role, [])
    
    return {
        "success": True,
        "role": role,
        "recommendations": recommendations
    }


class CollectionItem(BaseModel):
    """知识库项"""
    id: str = Field(..., description="知识库ID")
    title: str = Field(..., description="知识库标题")
    description: Optional[str] = Field(None, description="知识库描述")
    type: Optional[str] = Field(None, description="知识库类型")
    doc_count: int = Field(default=0, description="文档数量")


class CollectionListResponse(BaseModel):
    """知识库列表响应"""
    success: bool = True
    collections: List[CollectionItem] = Field(default_factory=list)
    total: int = 0


@router.get("/collections/available", response_model=CollectionListResponse)
async def get_available_collections(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取所有可用的知识库列表（从数据库读取）
    """
    from aperag.db.ops import async_db_ops
    
    try:
        logger.info("Starting to fetch available collections...")
        # 获取所有用户的知识库
        collections_data = await async_db_ops.query_all_collections()
        logger.info(f"Found {len(collections_data) if collections_data else 0} collections from database")
        
        collections = []
        for col in collections_data:
            try:
                # type 可能是枚举或字符串
                col_type = None
                if hasattr(col, 'type') and col.type:
                    if hasattr(col.type, 'value'):
                        col_type = str(col.type.value)
                    else:
                        col_type = str(col.type)
                
                collections.append(CollectionItem(
                    id=str(col.id),
                    title=col.title or str(col.id),
                    description=col.description,
                    type=col_type,
                    doc_count=0
                ))
            except Exception as item_error:
                logger.warning(f"Failed to process collection {col.id}: {item_error}")
                continue
        
        logger.info(f"Returning {len(collections)} collections")
        return CollectionListResponse(
            success=True,
            collections=collections,
            total=len(collections)
        )
    except Exception as e:
        import traceback
        logger.error(f"Failed to fetch collections: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return CollectionListResponse(
            success=False,
            collections=[],
            total=0
        )


