from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from aperag.db.models import AgentKnowledgeBinding, AgentKnowledgeBindingType
from aperag.utils.utils import utc_now
import logging

logger = logging.getLogger(__name__)

class AsyncAgentBindingRepositoryMixin:
    """Repository mixin for agent knowledge bindings"""

    async def query_agent_bindings(self, agent_role: str) -> List[AgentKnowledgeBinding]:
        """Query active bindings for an agent"""
        async with self.get_session() as session:
            stmt = select(AgentKnowledgeBinding).where(
                AgentKnowledgeBinding.agent_role == agent_role,
                AgentKnowledgeBinding.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def query_agent_bindings_map(self) -> Dict[str, List[AgentKnowledgeBinding]]:
        """Query all active bindings grouped by agent role"""
        async with self.get_session() as session:
            stmt = select(AgentKnowledgeBinding).where(
                AgentKnowledgeBinding.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            bindings = result.scalars().all()
            
            result_map = {}
            for b in bindings:
                if b.agent_role not in result_map:
                    result_map[b.agent_role] = []
                result_map[b.agent_role].append(b)
            return result_map

    async def update_agent_bindings(
        self, 
        agent_role: str, 
        collection_ids: List[str], 
        document_ids: List[str] = None
    ):
        """
        Update bindings for an agent.
        This will soft-delete existing bindings and create new ones.
        """
        document_ids = document_ids or []
        
        async with self.get_session() as session:
            try:
                # 1. Soft delete all existing active bindings for this agent
                stmt = update(AgentKnowledgeBinding).where(
                    and_(
                        AgentKnowledgeBinding.agent_role == agent_role,
                        AgentKnowledgeBinding.gmt_deleted.is_(None)
                    )
                ).values(gmt_deleted=utc_now())
                
                await session.execute(stmt)
                
                # 2. Insert new bindings
                # Collections
                for cid in collection_ids:
                    binding = AgentKnowledgeBinding(
                        agent_role=agent_role,
                        resource_id=cid,
                        binding_type=AgentKnowledgeBindingType.COLLECTION,
                        is_default=True
                    )
                    session.add(binding)
                
                # Documents
                for did in document_ids:
                    binding = AgentKnowledgeBinding(
                        agent_role=agent_role,
                        resource_id=did,
                        binding_type=AgentKnowledgeBindingType.DOCUMENT,
                        is_default=True
                    )
                    session.add(binding)
                
                await session.commit()
                logger.info(f"Updated bindings for {agent_role}: {len(collection_ids)} collections, {len(document_ids)} documents")
                return True
            except Exception as e:
                logger.error(f"Failed to update agent bindings: {e}")
                await session.rollback()
                raise e
