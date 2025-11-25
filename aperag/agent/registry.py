import logging
from typing import Dict, List, Optional

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.generic import PromptDrivenAgent
from aperag.agent.core.models import AgentRole
from aperag.agent.prompts import get_agent_prompt
from aperag.agent.specialists.archivist import ArchivistAgent
from aperag.agent.specialists.calculator import CalculatorAgent
from aperag.agent.specialists.scribe import ScribeAgent
from aperag.agent.specialists.detective import DetectiveAgent
from aperag.agent.specialists.gatekeeper import GatekeeperAgent
from aperag.agent.specialists.prophet import ProphetAgent
from aperag.agent.specialists.auditor import AuditorAgent
from aperag.agent.specialists.operation_ticket_agent import OperationTicketAgent
from aperag.agent.specialists.work_permit_agent import WorkPermitAgent
from aperag.agent.specialists.accident_deduction_agent import AccidentDeductionAgent
from aperag.agent.specialists.power_guarantee_agent import PowerGuaranteeAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    智能体注册中心 (IoC Container)
    负责管理所有可用专家的实例。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents: Dict[AgentRole, BaseAgent] = {}
            cls._instance._initialized = False
        return cls._instance

    def initialize_default_agents(self, llm_service=None, retrieve_service=None, vision_service=None):
        """
        系统启动时初始化默认的专家团队
        """
        if getattr(self, "_initialized", False):
            return

        logger.info("Initializing default specialist agents...")

        # 核心检索和通用 Agent
        self.register(ArchivistAgent(retrieve_service=retrieve_service))
        self.register(CalculatorAgent(llm_service=llm_service))
        self.register(ScribeAgent(llm_service=llm_service))

        generic_roles = [
            (AgentRole.DIAGNOSTICIAN, "故障诊断专家", "负责分析故障现象和日志"),
            (AgentRole.INSTRUCTOR, "技能培训导师", "负责解释技术原理和培训"),
            (AgentRole.SENTINEL, "安监卫士", "负责审核操作票和安全风险"),
        ]

        for role, name, description in generic_roles:
            try:
                system_prompt = get_agent_prompt(role)
                agent = PromptDrivenAgent(
                    role=role,
                    name=name,
                    description=description,
                    llm_service=llm_service,
                    system_prompt=system_prompt,
                )
                self.register(agent)
            except Exception as exc:
                logger.error(
                    "Failed to register generic agent %s: %s", name, exc)

        # 新增的4个核心Agent
        self.register(DetectiveAgent(llm_service=llm_service,
                      vision_service=vision_service))
        self.register(GatekeeperAgent(llm_service=llm_service))
        self.register(ProphetAgent(llm_service=llm_service))
        self.register(AuditorAgent(llm_service=llm_service))

        # 新增的4个变电站专用Agent
        self.register(OperationTicketAgent(llm_service=llm_service))
        self.register(WorkPermitAgent(llm_service=llm_service))
        self.register(AccidentDeductionAgent(llm_service=llm_service))
        self.register(PowerGuaranteeAgent(llm_service=llm_service))

        self._initialized = True
        logger.info(
            f"Successfully initialized {len(self._agents)} specialist agents")

    def register(self, agent: BaseAgent):
        """
        注册一个智能体实例
        """
        if agent.role in self._agents:
            logger.warning(
                f"Agent role {agent.role} is already registered. Overwriting.")

        self._agents[agent.role] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.role})")

    def get_agent(self, role: AgentRole) -> Optional[BaseAgent]:
        """
        根据角色获取智能体实例
        """
        return self._agents.get(role)

    def list_agents(self) -> List[BaseAgent]:
        """
        获取所有已注册的智能体
        """
        return list(self._agents.values())

    def get_agent_descriptions(self) -> str:
        """
        为总控生成专家花名册（用于 Prompt）
        """
        descriptions = []
        for agent in self._agents.values():
            if agent.role == AgentRole.SUPERVISOR:
                continue
            descriptions.append(f"- {agent.role.value}: {agent.description}")
        return "\n".join(descriptions)


agent_registry = AgentRegistry()
