# 智能体前后端 API 连接完成报告

## 📋 概述

本文档记录了将智能体前端页面连接到实际后端 API 的工作。

---

## ✅ 已完成的工作

### 1. **值班长 (Supervisor) API 连接**

#### 前端页面
- **文件**: `web/src/app/workspace/agents/specific/supervisor/page.tsx`
- **路由**: `/workspace/agents/specific/supervisor`

#### API 端点
- **URL**: `POST /api/v1/agents/supervisor/dispatch`
- **后端文件**: `aperag/api/routes/supervisor.py`

#### 请求格式
```typescript
{
  task: string,          // 任务描述
  user_id: string,       // 用户ID
  priority?: string      // 优先级 (normal/high/urgent)
}
```

#### 响应格式
```typescript
{
  success: boolean,
  message: string,
  data: {
    assigned_agent?: string,
    task_id?: string,
    estimated_time?: string
  },
  task_analysis?: {
    task_type?: string,
    complexity?: string,
    required_agents?: string[]
  }
}
```

#### 功能特性
- ✅ 实时 API 调用
- ✅ 加载状态显示
- ✅ 错误处理和用户友好的错误提示
- ✅ 格式化的结果展示
- ✅ 任务分析信息展示
- ✅ 表单验证

---

### 2. **图谱专家 (Archivist) 页面**

#### 前端页面
- **文件**: `web/src/app/workspace/agents/specific/archivist/page.tsx`
- **路由**: `/workspace/agents/specific/archivist`
- **状态**: 页面已完整实现，包含搜索界面和统计展示

#### API 端点（待连接）
- **URL**: `POST /api/v1/agents/archivist/search`
- **后端文件**: `aperag/api/routes/archivist.py`

#### 建议的下一步
需要在 `handleStartTask` 函数中添加实际的 API 调用，类似于 Supervisor 的实现。

---

## 🔧 技术实现细节

### API 调用模式

```typescript
const response = await fetch('/api/v1/agents/[agent]/[action]', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // 包含认证 cookies
  body: JSON.stringify(requestData)
});

if (!response.ok) {
  const errorData = await response.json().catch(() => ({ message: '请求失败' }));
  throw new Error(errorData.message || `HTTP ${response.status}`);
}

const data = await response.json();
```

### 错误处理策略

1. **网络错误**: 捕获 fetch 异常
2. **HTTP 错误**: 检查 `response.ok`
3. **JSON 解析错误**: 使用 `.catch()` 提供默认错误消息
4. **用户友好提示**: 显示具体的错误信息和排查建议

### 状态管理

```typescript
const [loading, setLoading] = useState(false);    // 加载状态
const [result, setResult] = useState<string | null>(null);  // 结果
const [task, setTask] = useState('');             // 用户输入
```

---

## 📊 后端 API 路由总览

### 已实现的智能体 API

| 智能体 | 端点 | 方法 | 状态 |
|--------|------|------|------|
| Supervisor | `/api/v1/agents/supervisor/dispatch` | POST | ✅ 已连接 |
| Archivist | `/api/v1/agents/archivist/search` | POST | ⏳ 待连接 |
| Archivist | `/api/v1/agents/archivist/graph-traversal` | POST | ⏳ 待连接 |
| Archivist | `/api/v1/agents/archivist/historical-search` | POST | ⏳ 待连接 |
| Accident Deduction | `/api/v1/agents/accident-deduction/deduction` | POST | ⏳ 待连接 |
| Accident Deduction | `/api/v1/agents/accident-deduction/emergency-plan` | POST | ⏳ 待连接 |
| Accident Deduction | `/api/v1/agents/accident-deduction/drill-design` | POST | ⏳ 待连接 |

---

## 🚀 使用方法

### 1. 启动后端服务

```bash
# 确保所有 Docker 容器正在运行
docker-compose up -d

# 检查 API 健康状态
curl http://localhost:8000/health
```

### 2. 启动前端服务

```bash
cd web
npm run dev
```

### 3. 访问智能体页面

- **值班长**: http://localhost:3000/workspace/agents/specific/supervisor
- **图谱专家**: http://localhost:3000/workspace/agents/specific/archivist

### 4. 测试 API 调用

在值班长页面：
1. 输入任务，例如："请查询110kV主变的运行状态"
2. 点击"发送指令"
3. 查看返回的结果

---

## 🐛 故障排查

### 问题 1: API 调用返回 404

**原因**: 后端路由未正确注册或 URL 路径错误

**解决**:
```bash
# 检查 API 文档
curl http://localhost:8000/docs

# 确认路由是否存在
grep -r "router.post" aperag/api/routes/
```

### 问题 2: CORS 错误

**原因**: 跨域请求被阻止

**解决**: 确保后端已配置 CORS 中间件，允许前端域名

### 问题 3: 401 Unauthorized

**原因**: 用户未登录或 token 过期

**解决**:
1. 确保用户已登录
2. 检查 `credentials: 'include'` 是否设置
3. 验证后端的认证中间件

### 问题 4: 500 Internal Server Error

**原因**: 后端代码错误

**解决**:
```bash
# 查看后端日志
docker logs aperag-api

# 检查智能体是否正确注册
# 查看 aperag/agent/register_agents.py
```

---

## 📝 代码示例

### 完整的 API 调用示例

```typescript
const handleStartTask = async () => {
  if (!task.trim()) {
    alert('请输入任务指令');
    return;
  }

  setLoading(true);
  setResult(null);

  try {
    const response = await fetch('/api/v1/agents/supervisor/dispatch', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ 
        task: task.trim(),
        user_id: 'current_user',
        priority: 'normal'
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: '请求失败' 
      }));
      throw new Error(errorData.message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    
    // 格式化结果
    let resultText = `✅ 任务已成功提交\n\n`;
    resultText += `📋 任务: ${task}\n\n`;
    
    if (data.task_analysis) {
      resultText += `📊 分析结果:\n`;
      resultText += `- 任务类型: ${data.task_analysis.task_type || '未识别'}\n`;
    }
    
    setResult(resultText);
  } catch (error) {
    console.error('任务提交失败:', error);
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    setResult(`❌ 任务提交失败\n\n错误信息: ${errorMessage}`);
  } finally {
    setLoading(false);
  }
};
```

---

## 🎯 下一步计划

### 短期目标

1. ✅ ~~连接 Supervisor API~~
2. ⏳ 连接 Archivist API
3. ⏳ 添加 WebSocket 支持（实时思维流）
4. ⏳ 实现用户认证集成

### 中期目标

1. 为其他智能体创建专属页面
2. 实现任务历史记录功能
3. 添加结果导出功能
4. 优化错误处理和用户体验

### 长期目标

1. 实现智能体间的协作可视化
2. 添加性能监控和分析
3. 支持自定义智能体配置
4. 实现批量任务处理

---

## 📚 相关文档

- [智能体使用指南](./智能体使用指南.md)
- [API 文档](http://localhost:8000/docs)
- [后端路由代码](./aperag/api/routes/)
- [前端组件代码](./web/src/app/workspace/agents/)

---

**最后更新**: 2025-11-25  
**状态**: Supervisor API 已连接 ✅ | Archivist 待连接 ⏳
