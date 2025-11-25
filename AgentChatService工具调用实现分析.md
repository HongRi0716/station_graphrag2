# AgentChatService工具调用能力实现分析

## 📋 概述

`AgentChatService` 通过 **MCP (Model Context Protocol)** 实现了强大的工具调用能力，包括RAG检索、网络搜索等功能。本文档详细分析其实现机制。

## 🏗️ 核心架构

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   AgentChatService                       │
│  - 处理WebSocket消息                                      │
│  - 管理会话和历史                                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              AgentSessionManager                         │
│  - 管理MCP会话生命周期                                    │
│  - 缓存会话避免重复创建                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  MCP Session                             │
│  - 连接到MCP服务器                                        │
│  - 提供LLM实例                                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              AugmentedLLM (mcp_agent库)                  │
│  - 自动调用MCP工具                                        │
│  - 管理工具调用历史                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  MCP Tools                               │
│  - search_collection (RAG检索)                           │
│  - web_search (网络搜索)                                 │
│  - upload_file (文件上传)                                │
│  - ... 其他工具                                          │
└─────────────────────────────────────────────────────────┘
```

## 🔑 关键组件

### 1. AgentConfig - 配置对象

```python
# aperag/agent/agent_config.py

@dataclass
class AgentConfig:
    """智能体会话配置"""
    user_id: str
    chat_id: str
    provider_name: str          # 模型提供商 (如 "siliconflow")
    api_key: str                # LLM API密钥
    base_url: str               # LLM API地址
    default_model: str          # 默认模型名称
    language: str               # 语言
    instruction: str            # 系统提示词
    server_names: List[str]     # MCP服务器列表 (如 ["aperag"])
    aperag_api_key: str         # ApeRAG API密钥
    aperag_mcp_url: str         # MCP服务器地址
    temperature: float = 0.7
    max_tokens: int = 60000
```

**作用**: 
- 封装所有会话所需的配置参数
- 传递给 `AgentSessionManager` 创建会话

### 2. AgentSessionManager - 会话管理器

```python
# aperag/agent/agent_session_manager.py

class AgentSessionManager:
    """管理MCP会话的生命周期"""
    
    async def get_or_create_session(self, config: AgentConfig):
        """获取或创建会话（带缓存）"""
        session_key = self._generate_session_key(config)
        
        if session_key in self._sessions:
            # 复用现有会话
            return self._sessions[session_key]
        
        # 创建新会话
        session = await self._create_mcp_session(config)
        self._sessions[session_key] = session
        return session
    
    async def _create_mcp_session(self, config: AgentConfig):
        """创建MCP会话"""
        from mcp_agent import MCPSession
        
        # 创建MCP会话，连接到MCP服务器
        session = MCPSession(
            server_names=config.server_names,
            mcp_url=config.aperag_mcp_url,
            api_key=config.aperag_api_key,
            llm_provider=config.provider_name,
            llm_api_key=config.api_key,
            llm_base_url=config.base_url,
            system_prompt=config.instruction
        )
        
        await session.initialize()
        return session
```

**作用**:
- 管理MCP会话的创建和缓存
- 避免重复创建会话，提高性能
- 处理会话的清理和资源释放

### 3. MCP Session - MCP会话

MCP会话是 `mcp_agent` 库提供的核心对象：

```python
# 来自 mcp_agent 库

class MCPSession:
    """MCP会话对象"""
    
    async def initialize(self):
        """初始化会话，连接到MCP服务器"""
        # 1. 连接到MCP服务器
        # 2. 获取可用工具列表
        # 3. 注册工具到LLM
        pass
    
    async def get_llm(self, model_name: str):
        """获取LLM实例"""
        # 返回 AugmentedLLM 实例
        # 该LLM实例已经注册了所有MCP工具
        return AugmentedLLM(...)
```

### 4. AugmentedLLM - 增强的LLM

```python
# 来自 mcp_agent.workflows.llm.augmented_llm

class AugmentedLLM:
    """增强的LLM，支持自动工具调用"""
    
    async def generate_str(self, prompt: str, params: RequestParams) -> str:
        """
        生成响应，自动调用工具
        
        工作流程:
        1. 发送提示词到LLM
        2. LLM决定是否需要调用工具
        3. 如果需要，自动调用MCP工具
        4. 将工具结果返回给LLM
        5. LLM基于工具结果生成最终响应
        6. 重复2-5直到LLM不再需要工具或达到最大迭代次数
        """
        pass
    
    @property
    def history(self) -> List[Dict]:
        """
        获取对话历史，包含所有工具调用记录
        
        格式:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "...", "tool_calls": [...]},
            {"role": "tool", "tool_call_id": "...", "content": "..."},
            ...
        ]
        """
        pass
```

**关键特性**:
- **自动工具调用**: LLM自主决定何时调用哪个工具
- **多轮对话**: 支持多次工具调用直到获得最终答案
- **历史记录**: 完整记录所有工具调用过程

## 🔄 工具调用流程

### 完整流程图

```
用户查询
    ↓
1. AgentChatService.process_agent_message()
    ↓
2. 获取或创建MCP会话
    session = await agent_session_manager.get_or_create_session(config)
    ↓
3. 获取LLM实例
    llm = await session.get_llm(model_name)
    ↓
4. 构建查询提示词
    query_prompt = build_agent_query_prompt(...)
    ↓
5. 调用LLM生成
    response = await llm.generate_str(query_prompt, request_params)
    ↓
    ┌─────────────────────────────────────┐
    │  LLM内部自动工具调用循环             │
    │                                     │
    │  while 需要工具 and 未达到最大迭代:  │
    │    1. LLM决定调用哪个工具            │
    │    2. 执行工具调用                   │
    │    3. 获取工具结果                   │
    │    4. 将结果返回给LLM                │
    │    5. LLM基于结果继续生成            │
    └─────────────────────────────────────┘
    ↓
6. 提取工具调用记录
    tool_references = extract_tool_call_references(llm.history)
    ↓
7. 返回响应和工具调用记录
```

### 代码实现

#### 步骤1: 创建会话配置

```python
# agent_chat_service.py: _get_agent_session()

async def _get_agent_session(
    self, agent_message, user, chat_id, custom_system_prompt=None
):
    """获取或创建MCP会话"""
    
    # 1. 查询模型提供商信息
    provider_info = await self.db_ops.query_llm_provider_by_name(
        agent_message.completion.model_service_provider
    )
    
    # 2. 查询API密钥
    api_key = await self.db_ops.query_provider_api_key(
        agent_message.completion.model_service_provider,
        user_id=user,
        need_public=True
    )
    
    # 3. 获取或创建ApeRAG API密钥
    aperag_api_keys = await self.db_ops.query_api_keys(user, is_system=True)
    aperag_api_key = aperag_api_keys[0].key if aperag_api_keys else None
    
    if not aperag_api_key:
        # 自动创建
        api_key_result = await self.db_ops.create_api_key(
            user=user,
            description="aperag",
            is_system=True
        )
        aperag_api_key = api_key_result.key
    
    # 4. 确定系统提示词
    system_prompt = (
        custom_system_prompt if custom_system_prompt 
        else get_agent_system_prompt(language=agent_message.language)
    )
    
    # 5. 创建AgentConfig
    config = AgentConfig(
        user_id=user,
        chat_id=chat_id,
        provider_name=agent_message.completion.model_service_provider,
        api_key=api_key,
        base_url=provider_info.base_url,
        default_model=agent_message.completion.model,
        language=agent_message.language,
        instruction=system_prompt,
        server_names=["aperag"],  # MCP服务器名称
        aperag_api_key=aperag_api_key,
        aperag_mcp_url=os.getenv("APERAG_MCP_URL", "http://localhost:8000/mcp/"),
        temperature=0.7,
        max_tokens=60000,
    )
    
    # 6. 获取或创建会话
    session = await agent_session_manager.get_or_create_session(config)
    
    return session
```

#### 步骤2: 调用LLM生成

```python
# agent_chat_service.py: process_agent_message()

async def process_agent_message(
    self,
    agent_message,
    user,
    bot,
    chat_id,
    message_id,
    message_queue,
    **kwargs
):
    """处理智能体消息"""
    
    try:
        # 1. 获取MCP会话
        session = await self._get_agent_session(
            agent_message, user, chat_id, custom_system_prompt
        )
        
        # 2. 获取LLM实例
        llm = await session.get_llm(agent_message.completion.model)
        
        # 3. 构建查询提示词
        query_prompt = build_agent_query_prompt(
            query=agent_message.query,
            collections=agent_message.collections,
            language=agent_message.language,
            chat_id=chat_id,
            enable_web_search=agent_message.enable_web_search,
            custom_template=custom_query_prompt
        )
        
        # 4. 配置请求参数
        request_params = RequestParams(
            maxTokens=60000,
            model=agent_message.completion.model,
            use_history=True,           # 使用对话历史
            max_iterations=10,           # 最大工具调用迭代次数
            parallel_tool_calls=True,    # 支持并行工具调用
            temperature=0.7,
            user=user,
        )
        
        # 5. 调用LLM生成（自动工具调用）
        response = await llm.generate_str(query_prompt, request_params)
        
        # 6. 提取工具调用记录
        tool_references = extract_tool_call_references(llm.history)
        
        # 7. 返回结果
        return {
            "query": agent_message.query,
            "content": response,
            "references": tool_references,
        }
        
    finally:
        await message_queue.close()
```

#### 步骤3: 提取工具调用记录

```python
# aperag/agent/tool_reference_extractor.py

def extract_tool_call_references(history: List[Dict]) -> List[Dict]:
    """
    从LLM历史记录中提取工具调用引用
    
    Args:
        history: LLM对话历史
        
    Returns:
        工具调用记录列表
        
    示例:
    [
        {
            "tool_name": "search_collection",
            "tool_call_id": "call_123",
            "arguments": {
                "collection_id": "kb_001",
                "query": "主变操作步骤",
                "top_k": 5
            },
            "result": {
                "documents": [
                    {"title": "...", "content": "..."},
                    ...
                ]
            }
        },
        {
            "tool_name": "web_search",
            "tool_call_id": "call_124",
            "arguments": {
                "query": "2024年电力安全规程",
                "num_results": 5
            },
            "result": {
                "results": [
                    {"title": "...", "url": "...", "snippet": "..."},
                    ...
                ]
            }
        }
    ]
    """
    tool_references = []
    
    for message in history:
        # 查找工具调用消息
        if message.get("role") == "assistant" and "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                tool_ref = {
                    "tool_name": tool_call["function"]["name"],
                    "tool_call_id": tool_call["id"],
                    "arguments": json.loads(tool_call["function"]["arguments"])
                }
                tool_references.append(tool_ref)
        
        # 查找工具结果消息
        elif message.get("role") == "tool":
            # 匹配对应的工具调用
            for tool_ref in tool_references:
                if tool_ref["tool_call_id"] == message.get("tool_call_id"):
                    tool_ref["result"] = json.loads(message["content"])
    
    return tool_references
```

## 🛠️ MCP工具详解

### 1. search_collection - RAG检索

**功能**: 从知识库检索相关文档

**参数**:
```json
{
    "collection_id": "kb_001",      // 知识库ID
    "query": "主变操作步骤",         // 查询文本
    "top_k": 5,                     // 返回结果数量
    "search_type": "hybrid"         // 检索类型: vector/graph/hybrid
}
```

**返回**:
```json
{
    "documents": [
        {
            "id": "doc_001",
            "title": "主变压器操作规程",
            "content": "...",
            "score": 0.95,
            "metadata": {...}
        },
        ...
    ]
}
```

**LLM如何使用**:
```
用户: 如何进行主变转冷备用操作？

LLM思考: 我需要查询操作规程知识库

LLM调用工具:
search_collection(
    collection_id="operation_regulations_db",
    query="主变转冷备用操作步骤",
    top_k=3
)

工具返回: [文档1, 文档2, 文档3]

LLM基于文档生成回答:
根据操作规程，主变转冷备用操作步骤如下：
1. 核对运行方式...
2. 断开110kV侧断路器...
...
```

### 2. web_search - 网络搜索

**功能**: 搜索网络获取最新信息

**参数**:
```json
{
    "query": "2024年电力安全规程修订",
    "num_results": 5,
    "search_engine": "google"
}
```

**返回**:
```json
{
    "results": [
        {
            "title": "...",
            "url": "...",
            "snippet": "...",
            "published_date": "..."
        },
        ...
    ]
}
```

### 3. upload_file - 文件上传

**功能**: 上传文件到聊天会话

**参数**:
```json
{
    "chat_id": "chat_123",
    "file_path": "/path/to/file.pdf",
    "file_name": "document.pdf"
}
```

## 📊 提示词构建

### build_agent_query_prompt

```python
# aperag/service/prompt_template_service.py

def build_agent_query_prompt(
    query: str,
    collections: List[Collection],
    language: str,
    chat_id: str,
    enable_web_search: bool = False,
    custom_template: str = None
) -> str:
    """
    构建智能体查询提示词
    
    使用Jinja2模板，动态注入:
    - 用户查询
    - 可用知识库列表
    - 是否启用网络搜索
    - 聊天ID（用于文件检索）
    """
    
    if custom_template:
        template = Template(custom_template)
    else:
        template = Template(DEFAULT_QUERY_TEMPLATE)
    
    return template.render(
        query=query,
        collections=collections,
        enable_web_search=enable_web_search,
        chat_id=chat_id,
        language=language
    )
```

**默认模板示例**:
```jinja2
你是一个智能助手。

## 可用资源

{% if collections %}
### 知识库
你可以使用 search_collection 工具从以下知识库检索信息：
{% for collection in collections %}
- {{ collection.title }} (ID: {{ collection.id }})
  描述: {{ collection.description }}
{% endfor %}
{% endif %}

{% if enable_web_search %}
### 网络搜索
你可以使用 web_search 工具搜索网络获取最新信息。
{% endif %}

{% if chat_id %}
### 聊天文件
你可以使用 search_chat_files 工具搜索用户上传的文件。
{% endif %}

## 用户查询

{{ query }}

## 指令

请基于可用资源回答用户查询。如果需要，主动调用工具获取信息。
```

## 🎯 关键设计模式

### 1. 会话缓存模式

```python
class AgentSessionManager:
    def __init__(self):
        self._sessions = {}  # 会话缓存
    
    async def get_or_create_session(self, config):
        key = self._generate_session_key(config)
        
        if key in self._sessions:
            return self._sessions[key]  # 复用
        
        session = await self._create_session(config)
        self._sessions[key] = session  # 缓存
        return session
```

**优势**:
- 避免重复创建MCP连接
- 提高响应速度
- 减少资源消耗

### 2. 自动工具调用模式

```python
# LLM自主决定工具调用
response = await llm.generate_str(prompt, params)

# 内部流程:
# 1. LLM: "我需要查询知识库"
# 2. 自动调用: search_collection(...)
# 3. 获取结果
# 4. LLM: "基于检索结果，答案是..."
```

**优势**:
- 无需手动编写工具调用逻辑
- LLM自主决策，更智能
- 支持多轮工具调用

### 3. 消息队列模式

```python
# 生产者: 生成消息
async def process_agent_message(..., message_queue):
    await message_queue.put(format_stream_start(...))
    response = await llm.generate_str(...)
    await message_queue.put(format_stream_content(...))
    await message_queue.put(format_stream_end(...))

# 消费者: 消费消息并发送到WebSocket
async def _consume_messages_from_queue(message_queue, websocket):
    while True:
        message = await message_queue.get()
        if message is None:
            break
        await websocket.send_text(json.dumps(message))
```

**优势**:
- 解耦生产和消费
- 支持流式响应
- 便于错误处理

## 💡 最佳实践

### 1. 配置管理

```python
# 集中管理配置
config = AgentConfig(
    user_id=user,
    chat_id=chat_id,
    provider_name="siliconflow",
    api_key=api_key,
    # ... 其他配置
    server_names=["aperag"],  # 关键: MCP服务器
    aperag_mcp_url=os.getenv("APERAG_MCP_URL"),  # 从环境变量读取
)
```

### 2. 错误处理

```python
try:
    session = await agent_session_manager.get_or_create_session(config)
    llm = await session.get_llm(model_name)
    response = await llm.generate_str(prompt, params)
except MCPConnectionError:
    # MCP连接失败
    return format_mcp_connection_error(language)
except AgentConfigurationError as e:
    # 配置错误
    return format_agent_setup_error(str(e), language)
except Exception as e:
    # 其他错误
    return format_processing_error(str(e), language)
```

### 3. 资源清理

```python
# 使用上下文管理器
async with message_queue:
    # 处理消息
    pass
# 自动关闭队列

# 或手动清理
try:
    # 处理
    pass
finally:
    await message_queue.close()
```

## 📚 总结

`AgentChatService` 的工具调用能力基于以下核心机制：

1. **MCP协议** - 标准化的工具调用协议
2. **AgentSessionManager** - 高效的会话管理
3. **AugmentedLLM** - 自动工具调用的LLM
4. **消息队列** - 解耦的消息处理
5. **提示词工程** - 动态构建的查询提示词

这些机制共同实现了：
- ✅ RAG检索
- ✅ 网络搜索
- ✅ 文件上传
- ✅ 多轮对话
- ✅ 流式响应
- ✅ 完整的工具调用记录

**关键优势**:
- **自动化** - LLM自主决定工具调用
- **高效** - 会话缓存和复用
- **可扩展** - 易于添加新工具
- **可追溯** - 完整的调用历史

这就是 `BaseAgent` 中实现的工具调用能力的原理！
