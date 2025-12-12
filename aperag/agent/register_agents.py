# Copyright 2025 ApeCloud, Inc.

"""
智能体注册初始化
在应用启动时注册所有智能体
"""

import logging
from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole
from aperag.agent.agent_configs import AGENT_CONFIGS

logger = logging.getLogger(__name__)


def register_all_agents():
    """注册所有智能体到agent_registry"""
    
    logger.info("Starting agent registration...")
    
    # 导入所有智能体
    from aperag.agent.specialists.supervisor_agent import SupervisorAgent
    from aperag.agent.specialists.archivist import ArchivistAgent
    from aperag.agent.specialists.accident_deduction_agent import AccidentDeductionAgent
    from aperag.agent.specialists.operation_ticket_agent import OperationTicketAgent
    from aperag.agent.specialists.work_permit_agent import WorkPermitAgent
    from aperag.agent.specialists.power_guarantee_agent import PowerGuaranteeAgent
    
    # 注册 Supervisor
    try:
        supervisor = SupervisorAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.SUPERVISOR)
        agent_registry.register(supervisor, metadata)
        logger.info(f"✓ Registered {supervisor.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register Supervisor: {e}")
    
    # 注册 Archivist
    try:
        archivist = ArchivistAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.ARCHIVIST)
        agent_registry.register(archivist, metadata)
        logger.info(f"✓ Registered {archivist.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register Archivist: {e}")
    
    # 注册 AccidentDeduction
    try:
        accident_deduction = AccidentDeductionAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.ACCIDENT_DEDUCTION)
        agent_registry.register(accident_deduction, metadata)
        logger.info(f"✓ Registered {accident_deduction.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register AccidentDeduction: {e}")
    
    # 注册 OperationTicket
    try:
        operation_ticket = OperationTicketAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.OPERATION_TICKET)
        agent_registry.register(operation_ticket, metadata)
        logger.info(f"✓ Registered {operation_ticket.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register OperationTicket: {e}")
    
    # 注册 WorkPermit
    try:
        work_permit = WorkPermitAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.WORK_PERMIT)
        agent_registry.register(work_permit, metadata)
        logger.info(f"✓ Registered {work_permit.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register WorkPermit: {e}")
    
    # 注册 PowerGuarantee
    try:
        power_guarantee = PowerGuaranteeAgent()
        metadata = AGENT_CONFIGS.get(AgentRole.POWER_GUARANTEE)
        agent_registry.register(power_guarantee, metadata)
        logger.info(f"✓ Registered {power_guarantee.name}")
    except Exception as e:
        logger.error(f"✗ Failed to register PowerGuarantee: {e}")
    
    # 统计注册结果
    registered_count = len(agent_registry.list_agents())
    logger.info(f"Agent registration complete: {registered_count} agents registered")
    
    return registered_count

