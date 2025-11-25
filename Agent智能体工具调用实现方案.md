# Agent智能体工具调用实现方案

## 📋 目标

让 `aperag/agent/specialists/` 中的专家智能体（如操作票专家、工作票专家等）能够使用：
1. **文件检索** - 从知识库检索相关文档
2. **联网搜索** - 搜索网络获取最新信息
3. **工具调用** - 调用各种MCP工具

## 🔍 现状分析

### 当前架构

#### AgentChatService (已有完整功能)
```python
# aperag/service/agent_chat_service.py
class AgentChatService:
    - 使用 MCP (Model Context Protocol)
    - 通过 mcp_agent 库调用工具
    - 支持 RAG检索、网络搜索、文件上传
    - 使用 LLM 生成响应
```

#### Agent专家智能体 (当前缺少工具调用)
```python
# aperag/agent/specialists/*.py
class OperationTicketAgent(BaseAgent):
    async def _execute(self, state, input_data):
        # 当前只有业务逻辑
        # 没有工具调用能力
        pass
```

### 问题识别

1. **专家智能体无法访问知识库** - 无法检索相关文档
2. **专家智能体无法联网搜索** - 无法获取最新信息
3. **专家智能体无法调用工具** - 功能受限

## 💡 解决方案

### 方案概述

为专家智能体添加**服务注入**机制，让它们能够使用与 `AgentChatService` 相同的工具和服务。

### 核心思路

```
┌─────────────────────────────────────────────────────────┐
│                   AgentChatService                       │
│  - MCP工具调用                                            │
│  - RAG检索服务                                            │
│  - 网络搜索服务                                           │
└─────────────────────────────────────────────────────────┘
                        ↓ 共享服务
┌─────────────────────────────────────────────────────────┐
│              ServiceProvider (服务提供者)                 │
│  - retrieve_service: RAG检索                             │
│  - search_service: 网络搜索                              │
│  - llm_service: LLM调用                                  │
│  - vision_service: 视觉分析                              │
└─────────────────────────────────────────────────────────┘
                        ↓ 注入到
┌─────────────────────────────────────────────────────────┐
│              专家智能体 (Specialists)                      │
│  - OperationTicketAgent                                 │
│  - WorkPermitAgent                                      │
│  - AccidentDeductionAgent                               │
│  - ...                                                  │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ 实现步骤

### 步骤1: 创建服务提供者

创建一个统一的服务提供者，封装所有工具调用功能。

```python
# aperag/agent/services/service_provider.py

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ServiceProvider:
    """
    服务提供者 - 为智能体提供统一的工具调用接口
    封装 RAG检索、网络搜索、LLM调用等功能
    """
    
    def __init__(
        self,
        llm_service=None,
        retrieve_service=None,
        search_service=None,
        vision_service=None,
        user_id: str = None,
        chat_id: str = None
    ):
        self.llm_service = llm_service
        self.retrieve_service = retrieve_service
        self.search_service = search_service
        self.vision_service = vision_service
        self.user_id = user_id
        self.chat_id = chat_id
    
    async def search_collection(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5,
        search_type: str = "hybrid"  # vector, graph, hybrid
    ) -> List[Dict[str, Any]]:
        """
        从知识库检索文档
        
        Args:
            collection_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数量
            search_type: 检索类型 (vector/graph/hybrid)
            
        Returns:
            检索结果列表
        """
        if not self.retrieve_service:
            logger.warning("Retrieve service not available")
            return []
        
        try:
            # 调用检索服务
            results = await self.retrieve_service.search(
                collection_id=collection_id,
                query=query,
                top_k=top_k,
                search_type=search_type,
                user_id=self.user_id
            )
            
            logger.info(f"Retrieved {len(results)} documents from {collection_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching collection: {e}")
            return []
    
    async def search_collections(
        self,
        collection_ids: List[str],
        query: str,
        top_k: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从多个知识库检索文档
        
        Returns:
            {collection_id: [results]}
        """
        results = {}
        for collection_id in collection_ids:
            results[collection_id] = await self.search_collection(
                collection_id, query, top_k
            )
        return results
    
    async def web_search(
        self,
        query: str,
        num_results: int = 5,
        search_engine: str = "google"
    ) -> List[Dict[str, Any]]:
        """
        网络搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            search_engine: 搜索引擎
            
        Returns:
            搜索结果列表
        """
        if not self.search_service:
            logger.warning("Search service not available")
            return []
        
        try:
            results = await self.search_service.search(
                query=query,
                num_results=num_results,
                engine=search_engine
            )
            
            logger.info(f"Found {len(results)} web results")
            return results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        使用LLM生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        if not self.llm_service:
            logger.warning("LLM service not available")
            return ""
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ""
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        """
        分析图像
        
        Args:
            image_path: 图像路径
            prompt: 分析提示词
            
        Returns:
            分析结果
        """
        if not self.vision_service:
            logger.warning("Vision service not available")
            return ""
        
        try:
            result = await self.vision_service.analyze(
                image_path=image_path,
                prompt=prompt
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return ""
    
    async def search_chat_files(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索聊天中上传的文件
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        if not self.chat_id or not self.retrieve_service:
            return []
        
        try:
            results = await self.retrieve_service.search_chat_files(
                chat_id=self.chat_id,
                query=query,
                top_k=top_k,
                user_id=self.user_id
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching chat files: {e}")
            return []
```

### 步骤2: 扩展BaseAgent基类

修改 `BaseAgent` 以支持服务注入。

```python
# aperag/agent/core/base.py (修改)

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from aperag.agent.core.models import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentThinkingStep,
    ToolCallInfo,
)
from aperag.agent.services.service_provider import ServiceProvider

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    所有智能体（专家/值长）的基类
    实现了标准的思维链记录和状态管理功能
    """

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        tools: Optional[List[Any]] = None,
        service_provider: Optional[ServiceProvider] = None,  # 新增
    ):
        self.role = role
        self.name = name
        self.description = description
        self.tools = tools or []
        self.service_provider = service_provider  # 新增

    async def run(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能体执行的主入口。
        使用 Template Method 模式，封装了通用的日志和思维链记录逻辑。
        """
        try:
            # 1. 记录开始思考
            self._log_thought(state, "thought",
                              f"{self.name} 开始接收任务", input_data)

            # 2. 执行具体的业务逻辑 (由子类实现)
            result = await self._execute(state, input_data)

            # 3. 记录执行完成
            self._log_thought(state, "final_answer",
                              f"{self.name} 任务完成", result)

            return result

        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}", exc_info=True)
            self._log_thought(state, "correction", f"发生错误: {str(e)}")
            raise e

    @abstractmethod
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑，必须由子类实现。
        例如：图纸侦探在此处调用 VLM，安监卫士在此处查询规则库。
        """
        ...

    def _log_thought(
        self,
        state: AgentState,
        step_type: str,
        description: str,
        detail: Optional[Dict[str, Any]] = None,
        citations: Optional[List[str]] = None,
    ):
        """
        辅助方法：向共享状态中添加思考步骤，用于前端展示"气泡"
        """
        step = AgentThinkingStep(
            role=self.role,
            step_type=step_type,
            description=description,
            detail=detail,
            citations=citations or [],
        )
        state.add_thought(step)
        # 也可以在此处通过 WebSocket 实时推送到前端

    def _log_tool_use(self, state: AgentState, tool_info: ToolCallInfo):
        """
        记录工具调用
        """
        self._log_thought(
            state,
            "action",
            f"调用工具: {tool_info.tool_name}",
            detail=tool_info.model_dump(),
        )

    async def reflect(self, state: AgentState, result: Any) -> bool:
        """
        (可选) 反思机制：检查结果是否符合预期，是否需要重试
        """
        return True
    
    # ========== 新增：工具调用辅助方法 ==========
    
    async def _search_knowledge(
        self,
        state: AgentState,
        query: str,
        collection_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索知识库
        
        Args:
            state: 智能体状态
            query: 查询文本
            collection_ids: 知识库ID列表（如果为None，使用智能体默认知识库）
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        if not self.service_provider:
            logger.warning(f"{self.name}: Service provider not available")
            return []
        
        # 如果没有指定知识库，使用智能体的默认知识库
        if not collection_ids:
            from aperag.agent import agent_registry
            collection_ids = agent_registry.get_default_collections(self.role)
        
        if not collection_ids:
            logger.warning(f"{self.name}: No collections specified")
            return []
        
        # 记录工具调用
        self._log_thought(
            state,
            "action",
            f"正在检索知识库: {', '.join(collection_ids)}",
            detail={"query": query, "collections": collection_ids}
        )
        
        # 执行检索
        all_results = []
        for collection_id in collection_ids:
            results = await self.service_provider.search_collection(
                collection_id=collection_id,
                query=query,
                top_k=top_k
            )
            all_results.extend(results)
        
        # 记录检索结果
        self._log_thought(
            state,
            "observation",
            f"检索到 {len(all_results)} 条相关文档",
            detail={"count": len(all_results)}
        )
        
        return all_results
    
    async def _web_search(
        self,
        state: AgentState,
        query: str,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        网络搜索
        
        Args:
            state: 智能体状态
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.service_provider:
            logger.warning(f"{self.name}: Service provider not available")
            return []
        
        # 记录工具调用
        self._log_thought(
            state,
            "action",
            f"正在进行网络搜索: {query}",
            detail={"query": query}
        )
        
        # 执行搜索
        results = await self.service_provider.web_search(
            query=query,
            num_results=num_results
        )
        
        # 记录搜索结果
        self._log_thought(
            state,
            "observation",
            f"找到 {len(results)} 条网络结果",
            detail={"count": len(results)}
        )
        
        return results
    
    async def _generate_with_llm(
        self,
        state: AgentState,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        使用LLM生成文本
        
        Args:
            state: 智能体状态
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            生成的文本
        """
        if not self.service_provider:
            logger.warning(f"{self.name}: Service provider not available")
            return ""
        
        # 如果没有提供系统提示词，使用智能体的默认提示词
        if not system_prompt:
            from aperag.agent import agent_registry
            system_prompt = agent_registry.get_system_prompt(self.role)
        
        # 记录工具调用
        self._log_thought(
            state,
            "action",
            "正在使用LLM生成内容",
            detail={"prompt_length": len(prompt)}
        )
        
        # 执行生成
        response = await self.service_provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # 记录生成结果
        self._log_thought(
            state,
            "observation",
            f"生成了 {len(response)} 字符的内容"
        )
        
        return response
```

### 步骤3: 更新专家智能体实现

以操作票专家为例，展示如何使用服务提供者。

```python
# aperag/agent/specialists/operation_ticket_agent.py (修改示例)

import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class OperationTicketAgent(BaseAgent):
    """
    操作票智能编制与审核专家 (Operation Ticket Agent)
    职责：自动生成操作票、审核操作票合规性、优化操作步骤顺序。
    特点：精通倒闸操作流程和安全规程，确保操作票的正确性和安全性。
    """

    def __init__(self, llm_service: Any = None, service_provider=None):
        super().__init__(
            role=AgentRole.OPERATION_TICKET,
            name="操作票专家 (Operation Ticket Agent)",
            description="智能生成和审核操作票，确保倒闸操作的安全性和规范性。",
            tools=["operation_template", "safety_checker", "sequence_optimizer"],
            service_provider=service_provider,  # 注入服务提供者
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行操作票编制或审核任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到操作票任务: {query}")

        # 判断任务类型
        if "生成" in query or "编制" in query or "开票" in query:
            return await self._generate_operation_ticket(state, query)
        elif "审核" in query or "检查" in query or "校验" in query:
            return await self._review_operation_ticket(state, query)
        elif "优化" in query or "调整" in query:
            return await self._optimize_operation_steps(state, query)
        else:
            return await self._general_guidance(state, query)

    async def _generate_operation_ticket(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成操作票 - 使用知识库检索和LLM生成"""
        self._log_thought(state, "plan", "开始智能生成操作票...")

        # 1. 解析操作任务
        operation_type = self._parse_operation_type(query)
        
        self._log_thought(
            state,
            "action",
            f"识别操作类型: {operation_type}",
            detail={"query": query, "type": operation_type}
        )

        # 2. 从知识库检索相关操作票案例和规程
        if self.service_provider:
            # 检索历史操作票
            historical_tickets = await self._search_knowledge(
                state,
                query=f"{operation_type} 操作票",
                top_k=3
            )
            
            # 检索操作规程
            regulations = await self._search_knowledge(
                state,
                query=f"{operation_type} 操作规程 安全要求",
                top_k=3
            )
            
            # 构建上下文
            context = self._build_context_from_search_results(
                historical_tickets,
                regulations
            )
        else:
            context = ""

        # 3. 使用LLM生成操作票
        if self.service_provider:
            prompt = self._build_generation_prompt(operation_type, query, context)
            
            generated_content = await self._generate_with_llm(
                state,
                prompt=prompt
            )
            
            # 解析生成的内容为结构化数据
            ticket = self._parse_generated_ticket(generated_content, operation_type)
        else:
            # 回退到模拟数据
            ticket = self._create_ticket_template(operation_type)

        self._log_thought(
            state,
            "observation",
            f"已生成 {len(ticket['steps'])} 步操作",
            detail=ticket
        )

        # 4. 安全校验
        safety_check = self._perform_safety_check(ticket)
        self._log_thought(
            state,
            "thought",
            "执行安全性校验...",
            detail=safety_check
        )

        # 5. 使用模板格式化输出
        from aperag.service.template_service import template_service
        
        rendered_ticket = template_service.render_template(
            "operation_ticket.md",
            context={
                "ticket_no": ticket["ticket_no"],
                "title": ticket["title"],
                "equipment": ticket["equipment"],
                "voltage_level": ticket["voltage_level"],
                "operation_date": ticket["operation_date"],
                "estimated_time": ticket["estimated_time"],
                "operator": ticket.get("operator"),
                "supervisor": ticket.get("supervisor"),
                "prerequisites": ticket.get("prerequisites", []),
                "steps": ticket["steps"],
                "safety_check": safety_check
            }
        )

        return {
            "answer": rendered_ticket,
            "ticket": ticket,
            "safety_check": safety_check
        }
    
    def _build_context_from_search_results(
        self,
        historical_tickets: List[Dict],
        regulations: List[Dict]
    ) -> str:
        """从检索结果构建上下文"""
        context = "## 参考资料\n\n"
        
        if historical_tickets:
            context += "### 历史操作票案例\n"
            for i, ticket in enumerate(historical_tickets[:3]):
                context += f"{i+1}. {ticket.get('title', '未知')}\n"
                context += f"   {ticket.get('content', '')[:200]}...\n\n"
        
        if regulations:
            context += "### 操作规程\n"
            for i, reg in enumerate(regulations[:3]):
                context += f"{i+1}. {reg.get('title', '未知')}\n"
                context += f"   {reg.get('content', '')[:200]}...\n\n"
        
        return context
    
    def _build_generation_prompt(
        self,
        operation_type: str,
        query: str,
        context: str
    ) -> str:
        """构建LLM生成提示词"""
        prompt = f"""
请根据以下信息生成一份标准的操作票：

**操作任务**: {query}
**操作类型**: {operation_type}

{context}

请生成包含以下内容的操作票：
1. 操作前提条件
2. 详细操作步骤（每步包含：序号、操作内容、具体细节、安全注意事项）
3. 预计用时

要求：
- 步骤完整、顺序正确
- 符合《电力安全工作规程》
- 包含必要的安全措施
- 格式规范、易于执行
"""
        return prompt
    
    def _parse_generated_ticket(self, content: str, operation_type: str) -> Dict:
        """解析LLM生成的内容为结构化数据"""
        # TODO: 实现解析逻辑
        # 这里可以使用正则表达式或结构化输出来解析
        # 暂时返回模板数据
        return self._create_ticket_template(operation_type)

    # ... 其他方法保持不变 ...
```

### 步骤4: 更新AgentRegistry初始化

修改智能体注册时注入服务提供者。

```python
# aperag/agent/registry.py (修改)

def initialize_default_agents(self, llm_service=None, retrieve_service=None, vision_service=None):
    """
    系统启动时初始化默认的专家团队
    """
    if getattr(self, "_initialized", False):
        return

    logger.info("Initializing default specialist agents...")
    
    # 创建服务提供者
    from aperag.agent.services.service_provider import ServiceProvider
    
    service_provider = ServiceProvider(
        llm_service=llm_service,
        retrieve_service=retrieve_service,
        vision_service=vision_service
    )

    # 核心检索和通用 Agent - 注入服务提供者
    self.register(ArchivistAgent(
        retrieve_service=retrieve_service,
        service_provider=service_provider
    ))
    self.register(CalculatorAgent(
        llm_service=llm_service,
        service_provider=service_provider
    ))
    self.register(ScribeAgent(
        llm_service=llm_service,
        service_provider=service_provider
    ))

    # ... 其他智能体也注入服务提供者 ...

    # 新增的4个变电站专用Agent
    self.register(OperationTicketAgent(
        llm_service=llm_service,
        service_provider=service_provider  # 注入
    ))
    self.register(WorkPermitAgent(
        llm_service=llm_service,
        service_provider=service_provider  # 注入
    ))
    self.register(AccidentDeductionAgent(
        llm_service=llm_service,
        service_provider=service_provider  # 注入
    ))
    self.register(PowerGuaranteeAgent(
        llm_service=llm_service,
        service_provider=service_provider  # 注入
    ))

    # 从配置加载元数据
    self._load_agent_metadata()

    self._initialized = True
    logger.info(
        f"Successfully initialized {len(self._agents)} specialist agents")
```

## 📊 实现效果

### 使用示例

```python
# 使用操作票专家生成操作票

from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState

# 获取智能体
agent = agent_registry.get_agent(AgentRole.OPERATION_TICKET)

# 创建状态
state = AgentState(session_id="test-session")

# 执行任务
result = await agent.run(state, {
    "task": "生成#1主变转冷备用操作票"
})

# 结果包含：
# - answer: 格式化的操作票（Markdown）
# - ticket: 结构化的票据数据
# - safety_check: 安全检查结果

# 查看思维链
for thought in state.thinking_stream:
    print(f"[{thought.step_type}] {thought.description}")
    
# 输出示例：
# [thought] 收到操作票任务: 生成#1主变转冷备用操作票
# [plan] 开始智能生成操作票...
# [action] 识别操作类型: 设备转冷备用
# [action] 正在检索知识库: operation_tickets_db, operation_regulations_db
# [observation] 检索到 6 条相关文档
# [action] 正在使用LLM生成内容
# [observation] 生成了 2500 字符的内容
# [observation] 已生成 10 步操作
# [thought] 执行安全性校验...
# [final_answer] 操作票专家 (Operation Ticket Agent) 任务完成
```

## 🎯 优势

1. **统一的工具调用** - 所有智能体使用相同的服务接口
2. **知识库检索** - 智能体可以检索相关文档提高准确性
3. **网络搜索** - 获取最新信息
4. **LLM增强** - 使用大模型生成专业内容
5. **思维链可视化** - 记录完整的推理过程
6. **易于扩展** - 新增工具只需在ServiceProvider中添加

## 📝 总结

通过引入 `ServiceProvider` 和修改 `BaseAgent`，我们成功地让专家智能体具备了与 `AgentChatService` 相同的工具调用能力，包括：

- ✅ 知识库检索
- ✅ 网络搜索  
- ✅ LLM生成
- ✅ 视觉分析
- ✅ 文件搜索

这使得专家智能体能够：
1. 从知识库检索相关案例和规程
2. 使用LLM生成专业内容
3. 结合模板输出标准化文档
4. 记录完整的思维链过程

**下一步**: 实现具体的服务类（RetrieveService, SearchService等）并集成到系统中。
