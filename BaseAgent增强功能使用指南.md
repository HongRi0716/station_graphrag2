# BaseAgent增强功能使用指南

## 📋 概述

`BaseAgent` 已经被全面增强，现在具备以下能力：

1. ✅ **MCP工具调用** - RAG检索、网络搜索
2. ✅ **LLM生成** - 使用大模型生成专业内容
3. ✅ **参考文档学习** - 上传参考文档，学习其格式
4. ✅ **模板提取** - 从参考文档自动提取Jinja2模板
5. ✅ **模板渲染** - 使用模板生成标准化文档

## 🚀 新增功能

### 1. MCP工具调用

#### 1.1 知识库检索

```python
from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState

# 获取智能体
agent = agent_registry.get_agent(AgentRole.OPERATION_TICKET)

# 设置用户信息
agent.user_id = "user123"
agent.chat_id = "chat456"

# 创建状态
state = AgentState(session_id="test-session")

# 检索知识库
results = await agent._search_knowledge(
    state=state,
    query="主变压器转冷备用操作步骤",
    collection_ids=["operation_tickets_db", "regulations_db"],
    top_k=5
)

# 结果包含检索到的文档
for result in results:
    print(f"文档: {result.get('title')}")
    print(f"内容: {result.get('content')}")
```

#### 1.2 网络搜索

```python
# 网络搜索最新信息
results = await agent._web_search(
    state=state,
    query="2024年电力安全工作规程最新修订",
    num_results=5
)

for result in results:
    print(f"标题: {result.get('title')}")
    print(f"链接: {result.get('url')}")
    print(f"摘要: {result.get('snippet')}")
```

#### 1.3 LLM生成

```python
# 使用LLM生成内容
generated_text = await agent._generate_with_llm(
    state=state,
    prompt="""
请根据以下信息生成一份操作票：
- 设备: #1主变压器
- 操作类型: 转冷备用
- 电压等级: 110kV/10kV
""",
    temperature=0.7
)

print(generated_text)
```

### 2. 参考文档功能

#### 2.1 添加参考文档

```python
# 上传参考文档
reference_doc = """
# 操作票示例

**票号**: OT-2024-001
**操作任务**: #1主变转冷备用
**设备名称**: #1主变压器

## 操作步骤

1. 核对运行方式
2. 断开#1主变110kV侧断路器
3. 断开#1主变10kV侧断路器
...
"""

await agent.add_reference_document(
    state=state,
    document_content=reference_doc,
    document_name="操作票示例1"
)

# 可以添加多个参考文档
await agent.add_reference_document(
    state=state,
    document_content=another_doc,
    document_name="操作票示例2"
)
```

#### 2.2 提取模板

```python
# 从参考文档中自动提取Jinja2模板
template = await agent.extract_template_from_reference(
    state=state,
    model_provider="siliconflow",
    model_name="Qwen/Qwen2.5-7B-Instruct"
)

print("提取的模板:")
print(template)

# 输出示例:
# # 操作票
# 
# **票号**: {{ ticket_no }}
# **操作任务**: {{ title }}
# **设备名称**: {{ equipment }}
# 
# ## 操作步骤
# 
# {% for step in steps %}
# {{ step.seq }}. {{ step.action }}
# {% endfor %}
```

#### 2.3 保存模板

```python
# 保存提取的模板到文件
success = await agent.save_extracted_template(
    state=state,
    template_path="aperag/templates/my_operation_ticket.md"
)

if success:
    print("模板已保存")
```

#### 2.4 使用模板渲染

```python
# 使用提取的模板渲染内容
rendered = await agent.render_with_template(
    state=state,
    template_name=None,  # 使用提取的模板
    context={
        "ticket_no": "OT-2024-1125-001",
        "title": "#1主变转冷备用",
        "equipment": "#1主变压器",
        "steps": [
            {"seq": 1, "action": "核对运行方式"},
            {"seq": 2, "action": "断开110kV侧断路器"},
            {"seq": 3, "action": "断开10kV侧断路器"},
        ]
    }
)

print(rendered)

# 或者使用已有的模板文件
rendered = await agent.render_with_template(
    state=state,
    template_name="operation_ticket.md",
    context={...}
)
```

## 💡 完整使用示例

### 示例1: 操作票专家生成操作票

```python
from aperag.agent.specialists.operation_ticket_agent import OperationTicketAgent
from aperag.agent.core.models import AgentState

# 创建智能体
agent = OperationTicketAgent()
agent.user_id = "user123"
agent.chat_id = "chat456"

# 创建状态
state = AgentState(session_id="test-session")

# 执行任务
result = await agent.run(state, {
    "task": "生成#1主变转冷备用操作票"
})

# 在_execute方法中，智能体可以：
# 1. 检索历史操作票案例
# 2. 检索操作规程
# 3. 使用LLM生成操作步骤
# 4. 使用模板渲染最终输出

print(result["answer"])  # 格式化的操作票
```

### 示例2: 从参考文档学习并生成

```python
# 1. 上传参考文档
await agent.add_reference_document(
    state=state,
    document_content=reference_doc1,
    document_name="标准操作票1"
)

await agent.add_reference_document(
    state=state,
    document_content=reference_doc2,
    document_name="标准操作票2"
)

# 2. 提取模板
template = await agent.extract_template_from_reference(state=state)

# 3. 保存模板（可选）
await agent.save_extracted_template(
    state=state,
    template_path="aperag/templates/learned_template.md"
)

# 4. 使用学到的模板生成新文档
# 4.1 先检索相关信息
knowledge = await agent._search_knowledge(
    state=state,
    query="#2主变转热备用操作步骤"
)

# 4.2 使用LLM生成数据
prompt = f"""
根据以下知识库内容，生成#2主变转热备用操作票的数据：

{knowledge}

请以JSON格式输出，包含：
- ticket_no
- title
- equipment
- steps (列表)
"""

data_json = await agent._generate_with_llm(
    state=state,
    prompt=prompt,
    temperature=0.3
)

# 4.3 解析JSON并渲染模板
import json
data = json.loads(data_json)

rendered = await agent.render_with_template(
    state=state,
    template_name=None,  # 使用提取的模板
    context=data
)

print(rendered)
```

### 示例3: 在专家智能体中使用

修改 `OperationTicketAgent` 的 `_execute` 方法：

```python
async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行操作票编制任务"""
    query = input_data.get("task", "")
    
    # 1. 解析操作类型
    operation_type = self._parse_operation_type(query)
    
    # 2. 检索知识库
    historical_tickets = await self._search_knowledge(
        state=state,
        query=f"{operation_type} 操作票案例",
        collection_ids=["operation_tickets_db"],
        top_k=3
    )
    
    regulations = await self._search_knowledge(
        state=state,
        query=f"{operation_type} 操作规程",
        collection_ids=["regulations_db"],
        top_k=3
    )
    
    # 3. 构建上下文
    context = self._build_context(historical_tickets, regulations)
    
    # 4. 使用LLM生成操作步骤
    prompt = f"""
根据以下信息生成操作票：

操作任务: {query}
操作类型: {operation_type}

参考资料:
{context}

请生成详细的操作步骤，包括安全注意事项。
以JSON格式输出。
"""
    
    generated_json = await self._generate_with_llm(
        state=state,
        prompt=prompt,
        temperature=0.5
    )
    
    # 5. 解析生成的数据
    import json
    ticket_data = json.loads(generated_json)
    
    # 6. 执行安全校验
    safety_check = self._perform_safety_check(ticket_data)
    
    # 7. 使用模板渲染
    rendered = await self.render_with_template(
        state=state,
        template_name="operation_ticket.md",
        context={
            **ticket_data,
            "safety_check": safety_check
        }
    )
    
    return {
        "answer": rendered,
        "ticket": ticket_data,
        "safety_check": safety_check
    }
```

## 🔧 配置说明

### 必需配置

在使用MCP功能前，需要设置：

```python
agent.user_id = "user_id"  # 用户ID
agent.chat_id = "chat_id"  # 聊天ID（可选，会自动生成）
```

### 默认参数

所有MCP方法都支持以下参数：

- `model_provider`: 模型提供商（默认: "siliconflow"）
- `model_name`: 模型名称（默认: "Qwen/Qwen2.5-7B-Instruct"）
- `language`: 语言（默认: "zh-CN"）

可以根据需要修改：

```python
results = await agent._search_knowledge(
    state=state,
    query="查询内容",
    model_provider="openai",
    model_name="gpt-4",
    language="en-US"
)
```

## 📊 思维链记录

所有操作都会自动记录到思维链中：

```python
# 查看思维链
for thought in state.thinking_stream:
    print(f"[{thought.step_type}] {thought.description}")
    if thought.detail:
        print(f"  详情: {thought.detail}")

# 输出示例:
# [action] 初始化MCP会话成功: siliconflow/Qwen/Qwen2.5-7B-Instruct
# [action] 正在检索知识库: operation_tickets_db, regulations_db
#   详情: {'query': '主变转冷备用', 'collections': [...], 'top_k': 5}
# [observation] 检索完成，找到 3 个工具调用
# [action] 正在使用LLM生成内容
#   详情: {'prompt_length': 1234, 'temperature': 0.7}
# [observation] 生成完成，长度: 2500 字符
# [action] 使用模板渲染: operation_ticket.md
# [observation] 模板渲染完成，长度: 3200 字符
```

## ⚠️ 注意事项

1. **MCP会话初始化**
   - 第一次调用MCP方法时会自动初始化会话
   - 会话会被缓存，后续调用复用
   - 需要有效的API key和数据库配置

2. **知识库ID**
   - 如果不指定`collection_ids`，会使用智能体的默认知识库
   - 默认知识库在`agent_configs.py`中配置

3. **模板提取**
   - 需要先添加参考文档
   - 提取质量取决于参考文档的质量和数量
   - 建议提供2-3个格式一致的参考文档

4. **错误处理**
   - 所有方法都有异常处理
   - 错误会记录到思维链中
   - 失败时返回空结果而不是抛出异常

## 🎯 最佳实践

1. **组合使用功能**
   - 先检索知识库获取参考资料
   - 使用LLM基于参考资料生成内容
   - 使用模板确保输出格式标准化

2. **参考文档学习**
   - 上传高质量的参考文档
   - 提取模板后保存以便复用
   - 定期更新模板以适应新需求

3. **思维链可视化**
   - 记录详细的思维过程
   - 便于调试和优化
   - 提高用户信任度

## 📚 相关文档

- `智能体系统使用指南.md` - 整体系统使用说明
- `Agent智能体工具调用实现方案.md` - 详细的实现方案
- `aperag/agent/core/base.py` - BaseAgent源代码

---

**状态**: ✅ **BaseAgent已全面增强，可以投入使用！**
