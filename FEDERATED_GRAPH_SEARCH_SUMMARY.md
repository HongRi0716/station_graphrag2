# 联邦图谱搜索功能实现总结

## 📋 功能概述

本文档总结了**全局联邦图谱搜索**功能的完整实现。该功能实现了在**不构建物理全局大图**的前提下，通过**动态聚合**的方式实现跨 Collection 的知识图谱搜索和可视化。

## 🎯 核心设计理念

### 联邦搜索模式 (Federated Search)

```
用户查询
  ↓
┌─────────────────────────────────────┐
│  1. Scatter (分发)                   │
│  - 获取所有启用 KG 的 Collections    │
│  - 并发初始化 LightRAG 实例          │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  2. Gather (查询)                    │
│  - 向量搜索实体 (entities_vdb)       │
│  - 获取实体关系 (graph.get_node_edges)│
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  3. Merge (聚合)                     │
│  - 合并节点 (按 entity_name)         │
│  - 合并边 (去重)                     │
│  - 标记来源 (source_collections)     │
└─────────────────────────────────────┘
  ↓
返回统一的 Graph 数据结构
```

## 🏗️ 架构实现

### 1. 后端服务层

#### `aperag/service/global_graph_service.py`

**核心方法**: `federated_graph_search(user, query, top_k)`

**实现要点**:
- ✅ 并发查询所有活跃的知识图谱 Collections
- ✅ 使用 `asyncio.Semaphore(10)` 限制并发数，防止数据库过载
- ✅ 每个 Collection 独立执行:
  - 向量搜索: `rag.entities_vdb.query(query, top_k=top_k)`
  - 关系获取: `rag.chunk_entity_relation_graph.get_node_edges(entity_name)`
- ✅ 智能节点合并:
  - 使用 `entity_name` 作为全局唯一 ID
  - 跨库同名实体自动合并（视觉上）
  - 保留 `source_collections` 数组追踪所有来源

**代码片段**:
```python
async def federated_graph_search(self, user, query: str, top_k: int = 20) -> Dict[str, Any]:
    # 1. 获取所有启用 KG 的 Collections
    collections = await async_db_ops.query_collections([str(user.id)])
    active_collections = [col for col in collections if is_kg_enabled(col)]
    
    # 2. 并发搜索
    semaphore = asyncio.Semaphore(10)
    async def _search_single_graph(collection):
        async with semaphore:
            rag = await lightrag_manager.create_lightrag_instance(collection)
            entities = await rag.entities_vdb.query(query, top_k=top_k)
            # ... 获取边和构建节点
            return {"nodes": nodes, "edges": edges}
    
    results = await asyncio.gather(*[_search_single_graph(col) for col in active_collections])
    
    # 3. 聚合结果
    aggregated_nodes = {}
    for res in results:
        for node in res['nodes']:
            if node['id'] not in aggregated_nodes:
                aggregated_nodes[node['id']] = node
                aggregated_nodes[node['id']]['source_collections'] = [node['metadata']['workspace']]
            else:
                # 合并来源
                aggregated_nodes[node['id']]['source_collections'].append(node['metadata']['workspace'])
    
    return {"nodes": list(aggregated_nodes.values()), "edges": aggregated_edges}
```

### 2. API 视图层

#### `aperag/views/graph.py`

**端点**: `POST /api/v1/graphs/search/global`

**实现要点**:
- ✅ 依赖注入 `GlobalGraphService`
- ✅ 调用 `federated_graph_search` 方法
- ✅ 完善的错误处理和日志记录

**代码片段**:
```python
@router.post("/graphs/search/global", tags=["graph"])
async def global_graph_search_view(
    request: Request,
    query: str = Body(..., embed=True),
    top_k: int = Body(100, embed=True),
    user: User = Depends(required_user),
) -> Dict[str, Any]:
    """Search for entities across all collections (Global Graph)"""
    from aperag.service.global_graph_service import GlobalGraphService
    
    global_service = GlobalGraphService(
        collection_service=collection_service,
        search_service=search_service
    )
    
    graph_data = await global_service.federated_graph_search(
        user=user,
        query=query,
        top_k=top_k
    )
    
    return graph_data
```

### 3. 前端组件

#### `web/src/app/workspace/collections/all/graph/global-graph-explorer.tsx`

**核心功能**:
- ✅ 调用 `/api/v1/graphs/search/global` 获取图谱数据
- ✅ 使用 `react-force-graph-2d` 进行可视化
- ✅ 显示实体来源信息:
  - 悬停或放大时显示 `source_collections`
  - 多来源显示数量 (e.g., "3 sources")
  - 单来源显示工作区名称
- ✅ 集成右键菜单和源文档查看器

**关键渲染逻辑**:
```typescript
nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
  // ... 绘制节点 ...
  
  // 显示来源信息
  if (nodeType === 'entity' && (isHovered || globalScale > 1.5)) {
    const sourceCollections = node.source_collections as string[] | undefined;
    let sourceLabel = '';
    
    if (sourceCollections && sourceCollections.length > 0) {
      sourceLabel = sourceCollections.length > 1
        ? `${sourceCollections.length} sources`
        : sourceCollections[0];
    }
    
    if (sourceLabel) {
      // 绘制来源标签
      ctx.fillText(sourceLabel, x, sourceY);
    }
  }
}}
```

## 📊 数据结构

### 节点 (Node) 结构

```typescript
interface GraphNode {
  id: string;                    // 实体名称 (全局唯一)
  label: string;                 // 显示标签
  type: 'entity';                // 节点类型
  value: number;                 // 可视化大小
  metadata: {
    workspace: string;           // 来源工作区
    collection_id: string;       // 来源 Collection ID
    description: string;         // 实体描述
    source_id: string;           // 源文档 ID
  };
  source_collections: string[];  // 所有来源 Collections (聚合后)
}
```

### 边 (Edge) 结构

```typescript
interface GraphEdge {
  id: string;                    // 边 ID (src_tgt)
  source: string;                // 源节点 ID
  target: string;                // 目标节点 ID
  label: string;                 // 关系标签
  workspace: string;             // 来源工作区
}
```

## ✅ 实现验证清单

### 后端
- [x] `GlobalGraphService.federated_graph_search` 方法实现
- [x] 并发控制 (Semaphore)
- [x] 节点合并逻辑
- [x] 边去重逻辑
- [x] 来源追踪 (`source_collections`)
- [x] 错误处理和日志记录

### API
- [x] `/api/v1/graphs/search/global` 端点
- [x] 请求参数验证
- [x] 响应格式标准化
- [x] 异常处理

### 前端
- [x] `GlobalGraphExplorer` 组件
- [x] 图谱可视化 (Force Graph)
- [x] 来源信息显示
- [x] 右键菜单集成
- [x] 源文档查看器集成

## 🔍 数据流示例

### 请求
```json
POST /api/v1/graphs/search/global
{
  "query": "变压器",
  "top_k": 20
}
```

### 响应
```json
{
  "nodes": [
    {
      "id": "变压器",
      "label": "变压器",
      "type": "entity",
      "value": 50,
      "metadata": {
        "workspace": "电力设备知识库",
        "collection_id": "col_123",
        "description": "电力变压器是一种静止的电气设备...",
        "source_id": "doc_456"
      },
      "source_collections": ["电力设备知识库", "运维手册库"]
    }
  ],
  "edges": [
    {
      "id": "变压器_绝缘油",
      "source": "变压器",
      "target": "绝缘油",
      "label": "related",
      "workspace": "电力设备知识库"
    }
  ]
}
```

## 🎨 前端可视化特性

### 1. 节点颜色编码
- 🔵 Collection: 蓝色 (`#3b82f6`)
- 🟢 Document: 绿色 (`#10b981`)
- 🟠 Entity: 橙色 (`#f59e0b`)

### 2. 交互功能
- **单击**: 展开/折叠节点，显示详情
- **双击**: 导航到 Collection/Document 图谱
- **右键**: 打开上下文菜单 (聚焦、对话、查看源)
- **悬停**: 高亮连接节点，显示来源信息

### 3. 来源显示策略
- **多来源**: 显示 "N sources" (e.g., "3 sources")
- **单来源**: 显示工作区名称 (e.g., "电力设备知识库")
- **触发条件**: 悬停或缩放级别 > 1.5

## 🚀 性能优化

### 1. 并发控制
```python
semaphore = asyncio.Semaphore(10)  # 最多同时查询 10 个 Collections
```

### 2. 资源管理
```python
try:
    rag = await lightrag_manager.create_lightrag_instance(collection)
    # ... 执行查询 ...
finally:
    await rag.finalize_storages()  # 确保资源释放
```

### 3. 前端渲染优化
- 使用 Canvas 渲染 (react-force-graph-2d)
- 动态 LOD (Level of Detail): 根据缩放级别显示标签
- Spotlight 效果: 悬停时降低其他节点透明度

## 📝 使用示例

### 场景: 跨库搜索 "变压器"

1. **用户操作**: 在全局图谱页面搜索 "变压器"
2. **后端处理**:
   - 查询用户的 3 个 Collections: "电力设备", "运维手册", "培训资料"
   - 并发在 3 个库中搜索 "变压器" 实体
   - 发现 "电力设备" 和 "运维手册" 都包含该实体
3. **结果聚合**:
   - 创建单个 "变压器" 节点
   - `source_collections: ["电力设备", "运维手册"]`
   - 合并两个库中的关系边
4. **前端展示**:
   - 显示 "变压器" 节点
   - 悬停时显示 "2 sources"
   - 点击可查看详情和来源

## 🔧 故障排查

### 问题: 搜索返回空结果

**可能原因**:
1. 没有启用知识图谱的 Collections
2. 查询词与实体名称不匹配
3. Vector DB 未正确索引

**解决方案**:
```python
# 检查日志
logger.info(f"Active KG collections: {len(active_collections)}")
logger.info(f"Federated graph search completed: {len(final_nodes)} nodes")
```

### 问题: 前端不显示来源信息

**可能原因**:
1. 后端未设置 `source_collections`
2. 前端缩放级别不足

**解决方案**:
```typescript
// 检查节点数据
console.log('Node data:', node);
console.log('Source collections:', node.source_collections);

// 降低缩放阈值
if (nodeType === 'entity' && (isHovered || globalScale > 1.2)) {
  // 显示来源
}
```

## 📚 相关文档

- [LightRAG 文档](../aperag/graph/lightrag/README.md)
- [Vector Storage 接口](../aperag/graph/lightrag/base.py)
- [Graph Storage 接口](../aperag/graph/lightrag/base.py)
- [前端组件文档](../web/src/components/graph/README.md)

## 🎉 总结

联邦图谱搜索功能已**完整实现**并**可立即使用**。该实现:

✅ **保持数据隔离**: 不修改底层存储结构  
✅ **高性能**: 并发查询 + 资源管理  
✅ **用户友好**: 直观的可视化 + 来源追踪  
✅ **可扩展**: 易于添加新的聚合策略  

---

**实现日期**: 2025-11-26  
**版本**: v1.0  
**状态**: ✅ 生产就绪
