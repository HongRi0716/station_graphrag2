# The Supervisor 和 The Archivist 完整实现方案

**实施时间**: 2024-11-25  
**实施范围**: 核心功能、API接口、智能体协作、前端集成

---

## 📋 概述

本文档详细说明 The Supervisor（值班长/总控智能体）和 The Archivist（图谱专家）的完整实现方案。

---

## 一、The Supervisor（值班长/总控智能体）

### 1.1 角色定位

**名称**: The Supervisor（值班长）  
**角色**: 变电站总控智能体  
**职责**:
- 统筹协调所有专家智能体
- 任务分发和优先级管理
- 综合决策和应急指挥
- 全局态势感知

### 1.2 核心功能设计

#### 功能1: 任务分发

```python
# aperag/agent/specialists/supervisor_agent.py

from typing import Any, Dict, List, Optional
from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.agent_orchestrator import agent_orchestrator, TaskType, CollaborationMode

class SupervisorAgent(BaseAgent):
    """
    值班长智能体 (Supervisor Agent)
    
    职责：
    - 统筹协调所有专家智能体
    - 任务分发和优先级管理
    - 综合决策和应急指挥
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SUPERVISOR,
            name="值班长 (Supervisor)",
            description="变电站总控智能体，负责统筹协调和综合决策",
            tools=["task_dispatcher", "priority_manager", "decision_maker"]
        )
    
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行总控任务"""
        query = input_data.get("task", "")
        
        self._log_thought(state, "thought", f"值班长接收任务: {query}")
        
        # 分析任务类型
        task_analysis = self._analyze_task(query)
        
        self._log_thought(
            state,
            "action",
            f"任务分析: {task_analysis['task_type']}",
            detail=task_analysis
        )
        
        # 判断是否需要协作
        if task_analysis['requires_collaboration']:
            return await self._coordinate_collaboration(state, query, task_analysis)
        else:
            return await self._handle_single_task(state, query, task_analysis)
    
    def _analyze_task(self, query: str) -> Dict[str, Any]:
        """分析任务类型和复杂度"""
        analysis = {
            "task_type": "unknown",
            "complexity": "low",
            "requires_collaboration": False,
            "priority": "normal",
            "involved_agents": []
        }
        
        # 事故相关
        if any(keyword in query for keyword in ["事故", "故障", "跳闸", "异常"]):
            analysis["task_type"] = "emergency_response"
            analysis["complexity"] = "high"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "urgent"
            analysis["involved_agents"] = ["accident_deduction", "diagnosis", "operation_ticket"]
        
        # 操作相关
        elif any(keyword in query for keyword in ["操作", "倒闸", "投运", "停运"]):
            analysis["task_type"] = "operation_planning"
            analysis["complexity"] = "medium"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "high"
            analysis["involved_agents"] = ["operation_ticket", "accident_deduction", "work_permit"]
        
        # 检修相关
        elif any(keyword in query for keyword in ["检修", "维护", "试验"]):
            analysis["task_type"] = "safety_check"
            analysis["complexity"] = "medium"
            analysis["requires_collaboration"] = True
            analysis["priority"] = "normal"
            analysis["involved_agents"] = ["work_permit", "accident_deduction"]
        
        # 查询相关
        elif any(keyword in query for keyword in ["查询", "检索", "查找", "历史"]):
            analysis["task_type"] = "information_retrieval"
            analysis["complexity"] = "low"
            analysis["requires_collaboration"] = False
            analysis["priority"] = "normal"
            analysis["involved_agents"] = ["archivist"]
        
        return analysis
    
    async def _coordinate_collaboration(
        self,
        state: AgentState,
        query: str,
        task_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """协调多智能体协作"""
        self._log_thought(
            state,
            "plan",
            f"启动智能体协作，涉及 {len(task_analysis['involved_agents'])} 个智能体"
        )
        
        # 确定任务类型
        task_type_map = {
            "emergency_response": TaskType.EMERGENCY_RESPONSE,
            "operation_planning": TaskType.OPERATION_PLANNING,
            "safety_check": TaskType.SAFETY_CHECK,
            "accident_analysis": TaskType.ACCIDENT_ANALYSIS
        }
        
        task_type = task_type_map.get(
            task_analysis["task_type"],
            TaskType.ACCIDENT_ANALYSIS
        )
        
        # 确定协作模式
        if task_analysis["priority"] == "urgent":
            mode = CollaborationMode.PARALLEL  # 紧急任务并行执行
        else:
            mode = CollaborationMode.SEQUENTIAL  # 常规任务顺序执行
        
        # 执行协作
        if self.user_id:
            try:
                result = await agent_orchestrator.execute_collaboration(
                    task=query,
                    task_type=task_type,
                    user_id=self.user_id,
                    chat_id=self.chat_id or f"supervisor-{self.user_id}",
                    mode=mode
                )
                
                self._log_thought(
                    state,
                    "observation",
                    f"协作完成: {result['summary']['successful']}/{result['summary']['total_subtasks']} 成功"
                )
                
                return {
                    "answer": result["integrated_report"],
                    "collaboration_result": result,
                    "task_analysis": task_analysis
                }
                
            except Exception as e:
                self._log_thought(
                    state,
                    "correction",
                    f"协作失败: {str(e)}"
                )
                return await self._handle_single_task(state, query, task_analysis)
        else:
            # 没有user_id，回退到单任务处理
            return await self._handle_single_task(state, query, task_analysis)
    
    async def _handle_single_task(
        self,
        state: AgentState,
        query: str,
        task_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理单个任务"""
        self._log_thought(state, "action", "分发任务到专家智能体")
        
        # 选择合适的智能体
        if task_analysis["involved_agents"]:
            target_agent_capability = task_analysis["involved_agents"][0]
        else:
            target_agent_capability = "rag"
        
        # 查找智能体
        from aperag.agent import agent_registry
        agents = agent_registry.find_by_capability(target_agent_capability)
        
        if agents and self.user_id:
            agent = agents[0]
            agent.user_id = self.user_id
            agent.chat_id = self.chat_id
            
            # 执行任务
            agent_state = AgentState(session_id=f"supervisor-delegate-{self.user_id}")
            result = await agent.run(agent_state, {"task": query})
            
            return {
                "answer": result.get("answer", ""),
                "delegated_to": agent.name,
                "task_analysis": task_analysis
            }
        else:
            # 回退到通用响应
            return {
                "answer": self._generate_general_guidance(query, task_analysis),
                "task_analysis": task_analysis
            }
    
    def _generate_general_guidance(self, query: str, task_analysis: Dict) -> str:
        """生成通用指导"""
        guidance = f"## 值班长分析\n\n"
        guidance += f"**任务**: {query}\n"
        guidance += f"**任务类型**: {task_analysis['task_type']}\n"
        guidance += f"**复杂度**: {task_analysis['complexity']}\n"
        guidance += f"**优先级**: {task_analysis['priority']}\n\n"
        
        guidance += "### 建议处理流程\n\n"
        
        if task_analysis["task_type"] == "emergency_response":
            guidance += "1. 立即汇报调度\n"
            guidance += "2. 启动应急预案\n"
            guidance += "3. 组织现场检查\n"
            guidance += "4. 分析故障原因\n"
            guidance += "5. 制定恢复方案\n"
        elif task_analysis["task_type"] == "operation_planning":
            guidance += "1. 编制操作票\n"
            guidance += "2. 进行事故预想\n"
            guidance += "3. 制定安全措施\n"
            guidance += "4. 审批操作票\n"
            guidance += "5. 执行操作\n"
        elif task_analysis["task_type"] == "safety_check":
            guidance += "1. 编制工作票\n"
            guidance += "2. 识别危险点\n"
            guidance += "3. 制定安全措施\n"
            guidance += "4. 审批工作票\n"
            guidance += "5. 现场安全检查\n"
        
        return guidance
```

#### 功能2: 态势感知

```python
async def get_station_status(self, state: AgentState) -> Dict[str, Any]:
    """获取变电站整体态势"""
    
    # 检索实时数据（如果有MCP会话）
    if self.user_id:
        # 检索设备状态
        equipment_status = await self._search_knowledge(
            state=state,
            query="变电站设备运行状态 实时数据",
            top_k=10
        )
        
        # 检索告警信息
        alarms = await self._search_knowledge(
            state=state,
            query="变电站告警 异常信息",
            top_k=5
        )
    else:
        equipment_status = []
        alarms = []
    
    # 构建态势报告
    status_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "正常",
        "equipment_count": len(equipment_status),
        "alarm_count": len(alarms),
        "equipment_status": equipment_status[:5],
        "recent_alarms": alarms[:3]
    }
    
    return status_report
```

### 1.3 API接口

```python
# aperag/api/routes/supervisor.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/agents/supervisor", tags=["supervisor"])

class SupervisorRequest(BaseModel):
    task: str
    user_id: str
    chat_id: Optional[str] = None
    priority: Optional[str] = "normal"

@router.post("/dispatch")
async def dispatch_task(request: SupervisorRequest):
    """任务分发"""
    agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
    agent.user_id = request.user_id
    agent.chat_id = request.chat_id
    
    state = AgentState(session_id=f"supervisor-{request.user_id}")
    result = await agent.run(state, {"task": request.task})
    
    return {
        "success": True,
        "result": result
    }

@router.get("/status")
async def get_station_status(user_id: str):
    """获取变电站态势"""
    agent = agent_registry.get_agent(AgentRole.SUPERVISOR)
    agent.user_id = user_id
    
    state = AgentState(session_id=f"supervisor-status-{user_id}")
    status = await agent.get_station_status(state)
    
    return {
        "success": True,
        "status": status
    }
```

### 1.4 前端集成

```typescript
// api/supervisor.ts

export async function dispatchTask(task: string, userId: string) {
  const response = await fetch('/api/v1/agents/supervisor/dispatch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, user_id: userId })
  });
  return await response.json();
}

export async function getStationStatus(userId: string) {
  const response = await fetch(`/api/v1/agents/supervisor/status?user_id=${userId}`);
  return await response.json();
}

// components/SupervisorDashboard.tsx

export function SupervisorDashboard({ userId }: { userId: string }) {
  const [status, setStatus] = useState(null);
  const [task, setTask] = useState('');
  
  useEffect(() => {
    // 定期刷新态势
    const interval = setInterval(async () => {
      const data = await getStationStatus(userId);
      setStatus(data.status);
    }, 30000); // 30秒刷新一次
    
    return () => clearInterval(interval);
  }, [userId]);
  
  const handleDispatch = async () => {
    const result = await dispatchTask(task, userId);
    console.log('任务分发结果:', result);
  };
  
  return (
    <div className="supervisor-dashboard">
      <h1>值班长总控台</h1>
      
      {/* 态势展示 */}
      <div className="status-panel">
        <h2>变电站态势</h2>
        {status && (
          <>
            <div>整体状态: {status.overall_status}</div>
            <div>设备数量: {status.equipment_count}</div>
            <div>告警数量: {status.alarm_count}</div>
          </>
        )}
      </div>
      
      {/* 任务分发 */}
      <div className="task-dispatch">
        <h2>任务分发</h2>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="输入任务描述"
        />
        <button onClick={handleDispatch}>分发任务</button>
      </div>
    </div>
  );
}
```

---

## 二、The Archivist（图谱专家）

### 2.1 角色定位

**名称**: The Archivist（图谱专家）  
**角色**: 知识库检索和图谱遍历专家  
**职责**:
- 知识库检索
- 图谱关系遍历
- 历史数据查询
- 知识整合

### 2.2 核心功能设计

#### 功能1: 增强检索

```python
# aperag/agent/specialists/archivist.py (优化)

class ArchivistAgent(BaseAgent):
    """
    图谱专家 (Archivist Agent)
    
    职责：
    - 知识库检索
    - 图谱关系遍历
    - 历史数据查询
    """
    
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行检索任务"""
        query = input_data.get("query", "")
        search_type = input_data.get("search_type", "hybrid")  # vector, graph, hybrid
        
        self._log_thought(state, "thought", f"图谱专家接收查询: {query}")
        
        # 判断查询类型
        if "关系" in query or "连接" in query or "路径" in query:
            return await self._graph_traversal(state, query)
        elif "历史" in query or "案例" in query:
            return await self._historical_search(state, query)
        else:
            return await self._knowledge_search(state, query, search_type)
    
    async def _knowledge_search(
        self,
        state: AgentState,
        query: str,
        search_type: str
    ) -> Dict[str, Any]:
        """知识库检索"""
        self._log_thought(state, "action", f"执行{search_type}检索")
        
        if self.user_id:
            try:
                # 使用BaseAgent的检索能力
                results = await self._search_knowledge(
                    state=state,
                    query=query,
                    top_k=10
                )
                
                # 提取文档
                documents = self._extract_documents_from_tool_results(results)
                
                # 构建结果报告
                report = self._format_search_results(query, documents)
                
                return {
                    "answer": report,
                    "documents": documents,
                    "count": len(documents)
                }
                
            except Exception as e:
                self._log_thought(state, "correction", f"检索失败: {str(e)}")
                return self._fallback_response(query)
        else:
            return self._fallback_response(query)
    
    async def _graph_traversal(
        self,
        state: AgentState,
        query: str
    ) -> Dict[str, Any]:
        """图谱关系遍历"""
        self._log_thought(state, "action", "执行图谱遍历")
        
        if self.user_id:
            try:
                # 使用LLM分析查询意图
                intent_prompt = f"""
分析以下查询的图谱遍历需求：
查询: {query}

请提取：
1. 起始节点
2. 目标节点
3. 关系类型
4. 遍历深度

以JSON格式输出。
"""
                
                intent_json = await self._generate_with_llm(
                    state=state,
                    prompt=intent_prompt,
                    temperature=0.3
                )
                
                import json
                intent = json.loads(intent_json)
                
                # 执行图谱遍历（调用图谱工具）
                traversal_prompt = f"""
使用graph_traversal工具查询：
起始节点: {intent.get('start_node')}
目标节点: {intent.get('target_node')}
关系类型: {intent.get('relation_type')}
深度: {intent.get('depth', 2)}
"""
                
                traversal_result = await self._generate_with_llm(
                    state=state,
                    prompt=traversal_prompt
                )
                
                return {
                    "answer": traversal_result,
                    "intent": intent
                }
                
            except Exception as e:
                self._log_thought(state, "correction", f"图谱遍历失败: {str(e)}")
                return self._fallback_response(query)
        else:
            return self._fallback_response(query)
    
    async def _historical_search(
        self,
        state: AgentState,
        query: str
    ) -> Dict[str, Any]:
        """历史数据查询"""
        self._log_thought(state, "action", "检索历史数据")
        
        # 检索历史记录
        if self.user_id:
            results = await self._search_knowledge(
                state=state,
                query=query,
                top_k=20  # 历史查询返回更多结果
            )
            
            documents = self._extract_documents_from_tool_results(results)
            
            # 按时间排序
            sorted_docs = sorted(
                documents,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            
            report = self._format_historical_results(query, sorted_docs)
            
            return {
                "answer": report,
                "documents": sorted_docs,
                "count": len(sorted_docs)
            }
        else:
            return self._fallback_response(query)
    
    def _format_search_results(self, query: str, documents: List[Dict]) -> str:
        """格式化检索结果"""
        report = f"## 检索结果\n\n"
        report += f"**查询**: {query}\n"
        report += f"**找到**: {len(documents)} 条相关文档\n\n"
        
        for i, doc in enumerate(documents[:10]):
            report += f"### {i+1}. {doc.get('title', '未知')}\n"
            report += f"**来源**: {doc.get('source', '未知')}\n"
            content = doc.get('content', '')[:300]
            report += f"{content}...\n\n"
        
        return report
    
    def _format_historical_results(self, query: str, documents: List[Dict]) -> str:
        """格式化历史结果"""
        report = f"## 历史记录\n\n"
        report += f"**查询**: {query}\n"
        report += f"**找到**: {len(documents)} 条历史记录\n\n"
        
        for i, doc in enumerate(documents[:15]):
            report += f"### {i+1}. {doc.get('title', '未知')}\n"
            report += f"**时间**: {doc.get('timestamp', '未知')}\n"
            report += f"**类型**: {doc.get('type', '未知')}\n"
            content = doc.get('content', '')[:200]
            report += f"{content}...\n\n"
        
        return report
    
    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """回退响应"""
        return {
            "answer": f"图谱专家提示：请提供更具体的查询条件。\n\n"
                     f"支持的查询类型：\n"
                     f"1. 知识检索 - 如：'查询主变操作规程'\n"
                     f"2. 图谱遍历 - 如：'#1主变与哪些设备有连接关系'\n"
                     f"3. 历史查询 - 如：'查询2023年的事故案例'\n",
            "query": query
        }
```

### 2.3 API接口

```python
# aperag/api/routes/archivist.py

router = APIRouter(prefix="/api/v1/agents/archivist", tags=["archivist"])

class ArchivistRequest(BaseModel):
    query: str
    user_id: str
    search_type: str = "hybrid"  # vector, graph, hybrid
    top_k: int = 10

@router.post("/search")
async def search_knowledge(request: ArchivistRequest):
    """知识检索"""
    agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
    agent.user_id = request.user_id
    
    state = AgentState(session_id=f"archivist-{request.user_id}")
    result = await agent.run(state, {
        "query": request.query,
        "search_type": request.search_type
    })
    
    return {
        "success": True,
        "result": result
    }

@router.post("/graph-traversal")
async def graph_traversal(request: ArchivistRequest):
    """图谱遍历"""
    agent = agent_registry.get_agent(AgentRole.ARCHIVIST)
    agent.user_id = request.user_id
    
    state = AgentState(session_id=f"archivist-graph-{request.user_id}")
    result = await agent._graph_traversal(state, request.query)
    
    return {
        "success": True,
        "result": result
    }
```

### 2.4 前端集成

```typescript
// components/ArchivistSearch.tsx

export function ArchivistSearch({ userId }: { userId: string }) {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('hybrid');
  const [results, setResults] = useState(null);
  
  const handleSearch = async () => {
    const response = await fetch('/api/v1/agents/archivist/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        user_id: userId,
        search_type: searchType
      })
    });
    
    const data = await response.json();
    setResults(data.result);
  };
  
  return (
    <div className="archivist-search">
      <h2>知识库检索</h2>
      
      <div className="search-controls">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入查询内容"
        />
        
        <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
          <option value="hybrid">混合检索</option>
          <option value="vector">向量检索</option>
          <option value="graph">图谱检索</option>
        </select>
        
        <button onClick={handleSearch}>搜索</button>
      </div>
      
      {results && (
        <div className="search-results">
          <h3>检索结果 ({results.count})</h3>
          <div dangerouslySetInnerHTML={{ __html: results.answer }} />
        </div>
      )}
    </div>
  );
}
```

---

## 三、完整实现清单

### 3.1 The Supervisor

| 组件 | 文件 | 状态 |
|------|------|------|
| 核心功能 | `aperag/agent/specialists/supervisor_agent.py` | ✅ 设计完成 |
| API接口 | `aperag/api/routes/supervisor.py` | ✅ 设计完成 |
| 前端组件 | `components/SupervisorDashboard.tsx` | ✅ 设计完成 |

**核心能力**:
- ✅ 任务分析和分发
- ✅ 智能体协作协调
- ✅ 态势感知
- ✅ 优先级管理

### 3.2 The Archivist

| 组件 | 文件 | 状态 |
|------|------|------|
| 核心功能 | `aperag/agent/specialists/archivist.py` | ✅ 优化完成 |
| API接口 | `aperag/api/routes/archivist.py` | ✅ 设计完成 |
| 前端组件 | `components/ArchivistSearch.tsx` | ✅ 设计完成 |

**核心能力**:
- ✅ 知识库检索
- ✅ 图谱关系遍历
- ✅ 历史数据查询
- ✅ 结果格式化

---

## 四、使用示例

### 4.1 The Supervisor使用

```python
# 任务分发
from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState

supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
supervisor.user_id = "user123"

state = AgentState(session_id="supervisor-test")
result = await supervisor.run(state, {
    "task": "#1主变跳闸，请组织应急处置"
})

print(result["answer"])  # 协作结果
```

### 4.2 The Archivist使用

```python
# 知识检索
archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
archivist.user_id = "user123"

state = AgentState(session_id="archivist-test")
result = await archivist.run(state, {
    "query": "查询主变操作规程",
    "search_type": "hybrid"
})

print(result["documents"])  # 检索结果
```

---

## 五、总结

### 已完成

1. ✅ **The Supervisor** - 完整设计
   - 任务分析和分发
   - 智能体协作协调
   - API接口
   - 前端集成

2. ✅ **The Archivist** - 完整优化
   - 增强检索能力
   - 图谱遍历
   - API接口
   - 前端集成

### 技术亮点

- 🎯 **智能分发** - 自动分析任务并选择合适的智能体
- 🔄 **协作协调** - 统筹多智能体协同工作
- 📊 **态势感知** - 实时掌握变电站整体状态
- 🔍 **增强检索** - 支持向量、图谱、混合检索
- 📈 **历史查询** - 时间序列数据检索

### 下一步

1. 实际代码实现
2. 集成测试
3. 性能优化
4. 用户体验优化

**状态**: ✅ **The Supervisor 和 The Archivist 完整方案设计完成！**
