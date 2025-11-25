import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

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


@dataclass
class AgentMetadata:
    """智能体元数据配置"""
    role: AgentRole
    name: str
    description: str
    
    # 专属知识库配置
    default_collections: List[str] = field(default_factory=list)  # 知识库ID列表
    
    # 提示词配置
    system_prompt_template: Optional[str] = None
    query_prompt_template: Optional[str] = None
    
    # 文件模板配置
    file_templates: Dict[str, str] = field(default_factory=dict)  # {模板名: 模板路径}
    
    # 工具配置
    required_tools: List[str] = field(default_factory=list)  # 必需工具列表
    optional_tools: List[str] = field(default_factory=list)  # 可选工具列表
    
    # 能力标签
    capabilities: Set[str] = field(default_factory=set)  # {"rag", "vision", "calculation", "generation"}
    
    # 优先级
    priority: int = 0  # 用于多智能体协作时的调度


class AgentRegistry:
    """
    智能体注册中心 (IoC Container)
    负责管理所有可用专家的实例及其元数据。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents: Dict[AgentRole, BaseAgent] = {}
            cls._instance._metadata: Dict[AgentRole, AgentMetadata] = {}
            cls._instance._capability_index: Dict[str, List[AgentRole]] = {}
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

        # 从配置加载元数据
        self._load_agent_metadata()

        self._initialized = True
        logger.info(
            f"Successfully initialized {len(self._agents)} specialist agents")

    def register(self, agent: BaseAgent, metadata: Optional[AgentMetadata] = None):
        """
        注册一个智能体实例及其元数据
        
        Args:
            agent: 智能体实例
            metadata: 智能体元数据(可选,会自动从agent提取基础信息)
        """
        if agent.role in self._agents:
            logger.warning(
                f"Agent role {agent.role} is already registered. Overwriting.")

        self._agents[agent.role] = agent
        
        # 如果没有提供元数据，创建基础元数据
        if metadata is None:
            metadata = AgentMetadata(
                role=agent.role,
                name=agent.name,
                description=agent.description
            )
        
        self._metadata[agent.role] = metadata
        
        # 建立能力索引
        if metadata.capabilities:
            for capability in metadata.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = []
                if agent.role not in self._capability_index[capability]:
                    self._capability_index[capability].append(agent.role)
        
        logger.info(f"Registered agent: {agent.name} ({agent.role})")

    def get_agent(self, role: AgentRole) -> Optional[BaseAgent]:
        """根据角色获取智能体实例"""
        return self._agents.get(role)

    def get_metadata(self, role: AgentRole) -> Optional[AgentMetadata]:
        """获取智能体元数据"""
        return self._metadata.get(role)

    def list_agents(self) -> List[BaseAgent]:
        """获取所有已注册的智能体"""
        return list(self._agents.values())

    def find_by_capability(self, capability: str) -> List[BaseAgent]:
        """根据能力查找智能体"""
        roles = self._capability_index.get(capability, [])
        return [self._agents[role] for role in roles if role in self._agents]

    def get_default_collections(self, role: AgentRole) -> List[str]:
        """获取智能体的默认知识库"""
        metadata = self._metadata.get(role)
        return metadata.default_collections if metadata else []

    def get_system_prompt(self, role: AgentRole, language: str = "zh-CN") -> Optional[str]:
        """获取智能体的系统提示词"""
        metadata = self._metadata.get(role)
        if metadata and metadata.system_prompt_template:
            return metadata.system_prompt_template
        return None

    def get_query_prompt_template(self, role: AgentRole, language: str = "zh-CN") -> Optional[str]:
        """获取智能体的查询提示词模板"""
        metadata = self._metadata.get(role)
        if metadata and metadata.query_prompt_template:
            return metadata.query_prompt_template
        return None

    def get_file_template(self, role: AgentRole, template_name: str) -> Optional[str]:
        """获取智能体的文件模板"""
        metadata = self._metadata.get(role)
        if metadata and metadata.file_templates:
            return metadata.file_templates.get(template_name)
        return None

    def get_agent_descriptions(self) -> str:
        """为总控生成专家花名册（用于 Prompt）"""
        descriptions = []
        for agent in self._agents.values():
            if agent.role == AgentRole.SUPERVISOR:
                continue
            descriptions.append(f"- {agent.role.value}: {agent.description}")
        return "\n".join(descriptions)

    def _load_agent_metadata(self):
        """从配置加载智能体元数据"""
        try:
            from aperag.agent.agent_configs import AGENT_CONFIGS
            
            for role, config in AGENT_CONFIGS.items():
                if role in self._agents:
                    # 更新已注册智能体的元数据
                    self._metadata[role] = config
                    
                    # 更新能力索引
                    if config.capabilities:
                        for capability in config.capabilities:
                            if capability not in self._capability_index:
                                self._capability_index[capability] = []
                            if role not in self._capability_index[capability]:
                                self._capability_index[capability].append(role)
                    
                    logger.info(f"Loaded metadata for {config.name}")
        except ImportError:
            logger.warning("Agent configs not found, using default metadata")


agent_registry = AgentRegistry()
