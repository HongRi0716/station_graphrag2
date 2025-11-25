# 智能体API快速启动指南

## 🚀 前端调用准备工作

### 1. 注册API路由

需要在主应用中注册新创建的API路由。

**文件**: `aperag/main.py` 或 `aperag/api/app.py`

```python
# 添加导入
from aperag.api.routes import supervisor, archivist, accident_deduction

# 注册路由
app.include_router(supervisor.router)
app.include_router(archivist.router)
app.include_router(accident_deduction.router)
```

### 2. 注册智能体

确保智能体已注册到 `agent_registry`。

**文件**: `aperag/agent/__init__.py`

```python
from aperag.agent.specialists.supervisor_agent import SupervisorAgent
from aperag.agent.specialists.archivist import ArchivistAgent
from aperag.agent.specialists.accident_deduction_agent import AccidentDeductionAgent

# 注册智能体
def register_all_agents():
    """注册所有智能体"""
    from aperag.agent import agent_registry
    from aperag.agent.agent_configs import AGENT_CONFIGS
    
    # 注册 Supervisor
    supervisor = SupervisorAgent()
    agent_registry.register(supervisor, AGENT_CONFIGS.get(AgentRole.SUPERVISOR))
    
    # 注册 Archivist
    archivist = ArchivistAgent()
    agent_registry.register(archivist, AGENT_CONFIGS.get(AgentRole.ARCHIVIST))
    
    # 注册 AccidentDeduction
    accident_deduction = AccidentDeductionAgent()
    agent_registry.register(accident_deduction, AGENT_CONFIGS.get(AgentRole.ACCIDENT_DEDUCTION))
    
    # ... 注册其他智能体

# 在应用启动时调用
register_all_agents()
```

### 3. 前端API调用示例

#### TypeScript/JavaScript 调用

```typescript
// api/agents.ts

// The Supervisor API
export async function dispatchTask(task: string, userId: string) {
  const response = await fetch('/api/v1/agents/supervisor/dispatch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      task,
      user_id: userId
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export async function getStationStatus(userId: string) {
  const response = await fetch(`/api/v1/agents/supervisor/status?user_id=${userId}`);
  return await response.json();
}

// The Archivist API
export async function searchKnowledge(query: string, userId: string, searchType = 'hybrid') {
  const response = await fetch('/api/v1/agents/archivist/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      user_id: userId,
      search_type: searchType
    })
  });
  
  return await response.json();
}

// Accident Deduction API
export async function generateAccidentDeduction(task: string, userId: string) {
  const response = await fetch('/api/v1/agents/accident-deduction/deduction', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      task,
      user_id: userId,
      enable_rag: true,
      enable_llm: true
    })
  });
  
  return await response.json();
}
```

#### React 组件示例

```typescript
// components/SupervisorPanel.tsx
import { useState } from 'react';
import { dispatchTask, getStationStatus } from '@/api/agents';

export function SupervisorPanel({ userId }: { userId: string }) {
  const [task, setTask] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleDispatch = async () => {
    setLoading(true);
    try {
      const response = await dispatchTask(task, userId);
      setResult(response);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="supervisor-panel">
      <h2>值班长总控台</h2>
      
      <div className="task-input">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="输入任务，如：#1主变跳闸，请组织应急处置"
          rows={3}
        />
        <button onClick={handleDispatch} disabled={loading}>
          {loading ? '处理中...' : '分发任务'}
        </button>
      </div>
      
      {result && (
        <div className="result">
          <h3>处理结果</h3>
          {result.task_analysis && (
            <div className="task-analysis">
              <p>任务类型: {result.task_analysis.task_type}</p>
              <p>优先级: {result.task_analysis.priority}</p>
            </div>
          )}
          <div className="answer">
            {result.data?.answer}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 4. 测试API是否可用

#### 方法1: 使用curl测试

```bash
# 测试 Supervisor
curl -X POST http://localhost:8000/api/v1/agents/supervisor/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "task": "查询主变操作规程",
    "user_id": "test-user"
  }'

# 测试 Archivist
curl -X POST http://localhost:8000/api/v1/agents/archivist/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询主变操作规程",
    "user_id": "test-user",
    "search_type": "hybrid"
  }'

# 测试健康检查
curl http://localhost:8000/api/v1/agents/supervisor/health
curl http://localhost:8000/api/v1/agents/archivist/health
```

#### 方法2: 使用Python测试

```python
import requests

# 测试 Supervisor
response = requests.post(
    'http://localhost:8000/api/v1/agents/supervisor/dispatch',
    json={
        'task': '#1主变跳闸，请组织应急处置',
        'user_id': 'test-user'
    }
)
print(response.json())

# 测试 Archivist
response = requests.post(
    'http://localhost:8000/api/v1/agents/archivist/search',
    json={
        'query': '查询主变操作规程',
        'user_id': 'test-user',
        'search_type': 'hybrid'
    }
)
print(response.json())
```

### 5. 启动服务

```bash
# 开发环境
uvicorn aperag.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn aperag.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## ✅ 检查清单

在前端调用之前，请确认：

- [ ] API路由已注册到主应用
- [ ] 智能体已注册到 `agent_registry`
- [ ] 后端服务已启动
- [ ] 健康检查接口返回正常
- [ ] 数据库连接正常
- [ ] 环境变量已配置（如 `APERAG_MCP_URL`）

---

## 🔧 常见问题

### Q1: 404 Not Found

**原因**: API路由未注册

**解决**: 在 `main.py` 中添加路由注册

```python
app.include_router(supervisor.router)
app.include_router(archivist.router)
```

### Q2: 500 Internal Server Error - "Agent type mismatch"

**原因**: 智能体未注册或类型不匹配

**解决**: 确保智能体已正确注册

```python
supervisor = SupervisorAgent()
agent_registry.register(supervisor, metadata)
```

### Q3: CORS错误

**原因**: 跨域请求被阻止

**解决**: 在 `main.py` 中添加CORS中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 下一步

1. **注册路由和智能体** - 完成上述步骤1和2
2. **启动后端服务** - 运行 `uvicorn aperag.main:app --reload`
3. **测试API** - 使用curl或Postman测试
4. **前端集成** - 使用提供的TypeScript示例
5. **部署上线** - 配置生产环境

---

## 🎯 快速验证

运行以下命令快速验证API是否可用：

```bash
# 1. 启动服务
uvicorn aperag.main:app --reload &

# 2. 等待服务启动
sleep 3

# 3. 测试健康检查
curl http://localhost:8000/api/v1/agents/supervisor/health

# 4. 测试任务分发
curl -X POST http://localhost:8000/api/v1/agents/supervisor/dispatch \
  -H "Content-Type: application/json" \
  -d '{"task": "查询主变操作规程", "user_id": "test"}'
```

如果返回正常的JSON响应，说明API已可用！
