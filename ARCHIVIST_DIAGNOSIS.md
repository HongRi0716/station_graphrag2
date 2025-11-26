# Archivist 查询问题诊断报告

## 📊 问题现象
- API 调用成功（HTTP 200）
- 返回 0 条文档
- `tool_calls: 0` - LLM 没有调用任何工具

## 🔍 根本原因分析

### 1. **核心问题：trace_id 丢失**
从 API 服务器日志中发现：
```
2025-11-26 02:30:05,305 - WARNING - Received event without a trace_id. Cannot dispatch.
```

**这意味着**：
- MCP 工具调用事件无法被正确分发
- 工具调用结果无法被记录到历史记录中
- `extract_tool_call_references` 无法从空的历史记录中提取结果

### 2. **trace_id 丢失的原因**

在 `base.py` 中，我们直接调用了 `_search_knowledge` 方法，但**没有设置 trace context**。

对比 `agent_chat_service.py`：
- ✅ 使用 `@trace_async_function` 装饰器创建新的 trace
- ✅ 通过 `register_message_queue` 注册 trace_id
- ✅ 工具调用事件可以正确分发到 message queue

而 `base.py` 中：
- ❌ 直接调用方法，没有 trace context
- ❌ 没有注册 message queue
- ❌ 工具调用事件无法被分发

## ✅ 已完成的修复

1. **初始化属性**：添加了 `_current_model_name` 和 `_current_model_provider`
2. **采用默认 LLM**：使用系统配置的 agent 对话 LLM
3. **对齐实现**：与 `agent_chat_service.py` 的参数和流程完全一致
4. **修复语法错误**：修复了函数签名问题

## 🔧 需要进一步修复的问题

### **方案 1：添加 trace context（推荐）**

在 `_search_knowledge` 方法中添加 trace 支持：

```python
from aperag.trace import trace_async_function

@trace_async_function("name=agent_search_knowledge", new_trace=True)
async def _search_knowledge(self, state, query, ...):
    # 获取 trace_id
    from aperag.trace.mcp_integration import get_current_trace_info
    trace_id, _ = get_current_trace_info()
    
    # 注册 event listener（如果需要实时事件）
    # ...
```

### **方案 2：直接调用 MCP 工具（最简单）**

绕过 LLM，直接调用 `search_collection_impl`：

```python
from aperag.mcp.tools.search_collection import search_collection_impl
from aperag.db.database import get_async_session

async with get_async_session() as session:
    results = await search_collection_impl(
        session=session,
        user_id=self.user_id,
        query=query,
        collection_ids=collection_ids,
        top_k=top_k,
        search_type="hybrid"
    )
```

### **方案 3：使用 agent_chat_service 的架构**

重构 `ArchivistAgent` 使用与 `agent_chat_service` 相同的架构：
- 使用 message queue
- 使用 event listener
- 使用 trace context

## 💡 推荐方案

**方案 2（直接调用 MCP 工具）** 是最简单、最可靠的方案：
- ✅ 不依赖 LLM 的工具调用能力
- ✅ 不需要复杂的 trace 管理
- ✅ 直接获取检索结果
- ✅ 性能更好（减少 LLM 调用）

## 📝 下一步行动

1. **实现方案 2**：修改 `_search_knowledge` 直接调用 MCP 工具
2. **测试验证**：确认可以正确检索到文档
3. **同步修复 `_web_search`**：使用相同的方式修复网络搜索功能
