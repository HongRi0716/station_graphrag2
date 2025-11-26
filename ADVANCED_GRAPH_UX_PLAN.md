# 全局知识图谱 - 高级交互体验优化方案

## 📋 优化目标概览

基于专业 GraphRAG 系统的最佳实践，我们将实现以下核心优化：

### 1. 🔍 图文联动 (Source Grounding)
- 三栏布局：目录树 + 图谱 + 原文预览
- 点击节点/边 → 右侧显示原文并高亮相关句子
- 溯源能力：验证关系的来源

### 2. 🤖 AI Agent 能力 (Chat-to-Graph)
- 右键菜单增强：以实体为中心提问、生成摘要
- 动态子图加载：自然语言查询子图
- 上下文感知对话

### 3. 🕸️ 语义聚合节点 (Combo/Cluster Nodes)
- 社区节点聚类
- 双击展开/折叠
- 降低视觉复杂度

### 4. 🛤️ 路径发现 (Pathfinding Mode)
- 两点间最短路径
- 关系探寻模式
- 路径高亮显示

### 5. 🔦 聚光灯模式 (Spotlight Effect)
- 搜索时保留上下文
- 非匹配节点降低透明度
- 高亮一跳邻居

---

## 🎯 Phase 1: 图文联动 (Source Grounding)

### 设计方案

#### 布局结构
```
┌────────────────────────────────────────────────────────────┐
│  顶部控制栏 (搜索、过滤、视图切换)                          │
├──────────┬─────────────────────────┬────────────────────────┤
│          │                         │                        │
│  目录树  │      图谱画布           │   原文预览面板         │
│  (20%)   │      (50%)              │   (30%)                │
│          │                         │                        │
│  - 知识库│  [节点和边的可视化]     │  📄 文档标题           │
│  - 文档  │                         │  ━━━━━━━━━━━━━━━━━━━━  │
│  - 实体  │  [交互式图谱]           │  原文内容...           │
│          │                         │  **高亮句子**          │
│          │                         │  更多内容...           │
│          │                         │                        │
└──────────┴─────────────────────────┴────────────────────────┘
```

#### 核心功能

**1. 点击节点 → 显示原文**
```typescript
const handleNodeClick = (node: GraphNode) => {
  if (node.type === 'entity') {
    // 获取该实体的原文位置
    const sourceInfo = {
      collectionId: node.metadata?.collection_id,
      documentId: node.metadata?.document_id,
      chunkId: node.metadata?.chunk_id,
      entityName: node.name,
    };
    
    // 打开右侧原文面板
    setSourceViewer({
      open: true,
      ...sourceInfo,
      highlightText: node.name,
    });
  }
};
```

**2. 点击边 → 显示关系原文**
```typescript
const handleLinkClick = (link: GraphEdge) => {
  // 获取生成该关系的原始句子
  const relationshipSource = {
    collectionId: link.metadata?.collection_id,
    documentId: link.metadata?.document_id,
    chunkId: link.metadata?.chunk_id,
    relationshipText: link.label,
  };
  
  setSourceViewer({
    open: true,
    ...relationshipSource,
    highlightText: `${link.source} -> ${link.target}`,
  });
};
```

**3. 原文面板组件**
```typescript
<ResizablePanel defaultSize={30} minSize={20} maxSize={40}>
  <SourceViewer
    collectionId={sourceViewer.collectionId}
    documentId={sourceViewer.documentId}
    chunkId={sourceViewer.chunkId}
    highlightText={sourceViewer.highlightText}
    onClose={() => setSourceViewer({ ...sourceViewer, open: false })}
  />
</ResizablePanel>
```

### 实现步骤

#### Step 1.1: 修改布局为三栏
- [ ] 调整 `ResizablePanelGroup` 为三个面板
- [ ] 左侧：目录树 (20%)
- [ ] 中间：图谱 (50%)
- [ ] 右侧：原文预览 (30%, 可关闭)

#### Step 1.2: 实现 SourceViewer 组件
- [ ] 创建 `SourceViewer` 组件
- [ ] 支持按 chunkId 加载原文
- [ ] 实现文本高亮功能
- [ ] 添加滚动到高亮位置

#### Step 1.3: 后端支持
- [ ] 添加 API: `/api/v1/documents/{doc_id}/chunks/{chunk_id}`
- [ ] 返回原文内容和元数据
- [ ] 支持关系溯源查询

---

## 🤖 Phase 2: AI Agent 能力 (Chat-to-Graph)

### 设计方案

#### 增强右键菜单
```typescript
<ContextMenu>
  <ContextMenuItem onClick={() => handleAIAction('explain')}>
    <Brain className="h-4 w-4" />
    解释该实体
  </ContextMenuItem>
  <ContextMenuItem onClick={() => handleAIAction('summarize')}>
    <FileText className="h-4 w-4" />
    生成摘要报告
  </ContextMenuItem>
  <ContextMenuItem onClick={() => handleAIAction('related')}>
    <Network className="h-4 w-4" />
    查找相关实体
  </ContextMenuItem>
  <ContextMenuSeparator />
  <ContextMenuItem onClick={() => handleAIAction('expand')}>
    <Expand className="h-4 w-4" />
    动态扩展子图
  </ContextMenuItem>
</ContextMenu>
```

#### 动态子图加载
```typescript
const handleDynamicQuery = async (query: string) => {
  // 自然语言查询
  const response = await fetch('/api/v1/graphs/dynamic-query', {
    method: 'POST',
    body: JSON.stringify({
      query: "显示和变压器相关的所有故障",
      currentGraph: graphData,
      maxNodes: 50,
    }),
  });
  
  const newSubgraph = await response.json();
  
  // 合并到当前图谱
  mergeSubgraph(newSubgraph);
};
```

### 实现步骤

#### Step 2.1: 增强右键菜单
- [ ] 添加 AI 相关菜单项
- [ ] 实现 `handleAIAction` 处理函数
- [ ] 集成 AI 对话接口

#### Step 2.2: 动态子图加载
- [ ] 实现自然语言查询解析
- [ ] 后端支持子图检索
- [ ] 前端子图合并逻辑

#### Step 2.3: 上下文感知对话
- [ ] 将当前图谱作为对话上下文
- [ ] 支持基于图谱的问答
- [ ] 实现对话历史记录

---

## 🕸️ Phase 3: 语义聚合节点 (Combo/Cluster Nodes)

### 设计方案

#### 社区节点概念
```typescript
interface CommunityNode extends GraphNode {
  type: 'community';
  communityId: string;
  memberCount: number;
  members: string[];  // 成员实体 ID
  isExpanded: boolean;
}
```

#### 视觉设计
```
┌─────────────────┐
│  📦 主题社区     │  ← 社区节点（大圆形）
│  设备维护 (15)   │     显示主题和成员数量
└─────────────────┘
         ↓ 双击展开
    ┌────┴────┐
    │         │
   ⚙️        🔧        ← 展开后显示成员实体
  主变      断路器
```

#### 交互逻辑
```typescript
const handleCommunityClick = (node: CommunityNode) => {
  if (node.isExpanded) {
    // 折叠：隐藏成员，只显示社区节点
    collapseCommunity(node.communityId);
  } else {
    // 展开：显示所有成员实体
    expandCommunity(node.communityId);
  }
};
```

### 实现步骤

#### Step 3.1: 后端社区检测
- [ ] 实现社区检测算法 (Louvain/Label Propagation)
- [ ] API 返回社区信息
- [ ] 支持多层级社区

#### Step 3.2: 前端社区渲染
- [ ] 实现社区节点组件
- [ ] 展开/折叠动画
- [ ] 成员节点布局算法

#### Step 3.3: 交互优化
- [ ] 双击展开/折叠
- [ ] 平滑过渡动画
- [ ] 保持布局稳定性

---

## 🛤️ Phase 4: 路径发现 (Pathfinding Mode)

### 设计方案

#### 路径探寻界面
```
┌────────────────────────────────────────┐
│  路径探寻模式                           │
│  ┌──────────┐    ┌──────────┐          │
│  │ 起点实体  │ → │ 终点实体  │ [查找]  │
│  └──────────┘    └──────────┘          │
│                                        │
│  路径类型: ○ 最短路径  ○ 所有路径      │
└────────────────────────────────────────┘
```

#### 路径算法
```typescript
const findPath = (sourceId: string, targetId: string, type: 'shortest' | 'all') => {
  if (type === 'shortest') {
    // Dijkstra 或 BFS
    return dijkstra(graphData, sourceId, targetId);
  } else {
    // DFS 查找所有路径（限制深度）
    return findAllPaths(graphData, sourceId, targetId, maxDepth: 5);
  }
};
```

#### 路径高亮
```typescript
const highlightPath = (path: string[]) => {
  // 高亮路径上的节点
  setHighlightNodes(new Set(path));
  
  // 高亮路径上的边
  const pathEdges = new Set<string>();
  for (let i = 0; i < path.length - 1; i++) {
    pathEdges.add(`${path[i]}-${path[i+1]}`);
  }
  setHighlightLinks(pathEdges);
  
  // 其他节点降低透明度
  setSpotlightMode(true);
};
```

### 实现步骤

#### Step 4.1: 路径查找算法
- [ ] 实现 Dijkstra 最短路径
- [ ] 实现 DFS 所有路径查找
- [ ] 路径权重计算

#### Step 4.2: 路径探寻 UI
- [ ] 添加路径探寻模式切换
- [ ] 实体选择器组件
- [ ] 路径结果展示

#### Step 4.3: 路径可视化
- [ ] 路径高亮动画
- [ ] 路径流动效果
- [ ] 路径信息面板

---

## 🔦 Phase 5: 聚光灯模式 (Spotlight Effect)

### 设计方案

#### 聚光灯效果
```typescript
// 搜索时不清空画布，而是降低非匹配节点的透明度
const applySpotlight = (matchedNodeIds: Set<string>) => {
  // 计算一跳邻居
  const spotlightNodes = new Set(matchedNodeIds);
  
  matchedNodeIds.forEach(nodeId => {
    const neighbors = getNeighbors(nodeId);
    neighbors.forEach(n => spotlightNodes.add(n));
  });
  
  setSpotlightNodes(spotlightNodes);
  setSpotlightMode(true);
};
```

#### 渲染逻辑
```typescript
nodeCanvasObject={(node: any, ctx, globalScale) => {
  const isInSpotlight = spotlightNodes.has(node.id);
  const isSearchMatched = searchMatchedNodes.has(node.id);
  
  // 透明度控制
  if (spotlightMode) {
    if (isSearchMatched) {
      ctx.globalAlpha = 1.0;  // 完全不透明
    } else if (isInSpotlight) {
      ctx.globalAlpha = 0.6;  // 半透明
    } else {
      ctx.globalAlpha = 0.1;  // 几乎透明
    }
  }
  
  // 绘制节点...
  
  // 恢复透明度
  ctx.globalAlpha = 1.0;
}}
```

### 实现步骤

#### Step 5.1: 聚光灯状态管理
- [ ] 添加 `spotlightMode` 状态
- [ ] 添加 `spotlightNodes` 状态
- [ ] 实现邻居计算函数

#### Step 5.2: 渲染优化
- [ ] 透明度渐变动画
- [ ] 聚光灯开关按钮
- [ ] 退出聚光灯模式

#### Step 5.3: 交互优化
- [ ] 点击非聚光灯节点时自动退出
- [ ] 支持多个聚光灯焦点
- [ ] 聚光灯强度调节

---

## 📊 实施优先级

### P0 (立即实现)
1. ✅ **聚光灯模式** - 最容易实现，效果显著
2. ✅ **图文联动基础** - 三栏布局 + 基础原文预览

### P1 (短期实现)
3. 🔄 **路径发现** - 核心功能，用户需求强烈
4. 🔄 **AI Agent 增强** - 提升交互体验

### P2 (中期实现)
5. 📅 **社区聚合** - 需要后端算法支持
6. 📅 **动态子图加载** - 需要完善的查询解析

---

## 🎯 Quick Win: 立即可实现的优化

### 1. 聚光灯模式 (30分钟)
```typescript
// 添加状态
const [spotlightMode, setSpotlightMode] = useState(false);
const [spotlightNodes, setSpotlightNodes] = useState(new Set<string>());

// 搜索时启用聚光灯
if (query && matchedNodeIds.size > 0) {
  const spotlight = new Set(matchedNodeIds);
  matchedNodeIds.forEach(id => {
    getNeighbors(id).forEach(n => spotlight.add(n));
  });
  setSpotlightNodes(spotlight);
  setSpotlightMode(true);
}

// 渲染时应用透明度
ctx.globalAlpha = spotlightMode 
  ? (spotlightNodes.has(node.id) ? 1.0 : 0.1)
  : 1.0;
```

### 2. 三栏布局 (1小时)
```typescript
<ResizablePanelGroup direction="horizontal">
  {/* 左侧：目录树 */}
  <ResizablePanel defaultSize={20}>
    <DirectoryTree />
  </ResizablePanel>
  
  <ResizableHandle />
  
  {/* 中间：图谱 */}
  <ResizablePanel defaultSize={50}>
    <ForceGraph2D />
  </ResizablePanel>
  
  <ResizableHandle />
  
  {/* 右侧：原文预览 */}
  {sourceViewer.open && (
    <ResizablePanel defaultSize={30}>
      <SourceViewer />
    </ResizablePanel>
  )}
</ResizablePanelGroup>
```

### 3. 点击边显示原文 (1小时)
```typescript
<ForceGraph2D
  onLinkClick={(link) => {
    setSourceViewer({
      open: true,
      documentId: link.metadata?.document_id,
      highlightText: link.label,
    });
  }}
/>
```

---

## 📝 技术债务和注意事项

### 性能考虑
- 大规模图谱 (>1000节点) 时，社区聚合是必须的
- 聚光灯模式需要优化渲染性能
- 路径查找需要限制深度和数量

### 用户体验
- 提供清晰的模式切换指示
- 避免突然的视觉变化
- 保持操作的可逆性

### 数据一致性
- 原文预览需要处理文档更新
- 动态子图需要去重
- 社区检测需要缓存

---

## 🚀 实施计划

### Week 1: 基础优化
- Day 1-2: 实现聚光灯模式
- Day 3-4: 实现三栏布局
- Day 5: 测试和优化

### Week 2: 核心功能
- Day 1-2: 实现原文预览
- Day 3-4: 实现路径发现
- Day 5: 集成测试

### Week 3: 高级功能
- Day 1-2: AI Agent 增强
- Day 3-4: 社区聚合
- Day 5: 性能优化

---

**让我们从 Quick Win 开始，立即实现聚光灯模式和三栏布局！**
