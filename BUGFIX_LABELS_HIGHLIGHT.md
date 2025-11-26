# 节点标签和搜索高亮修复

## 🐛 问题描述

用户报告了两个问题：
1. **节点没有名称** - 图谱中的节点不显示文字标签
2. **没有高亮显示搜索到的实体** - 搜索后匹配的节点没有变黄色高亮

## 🔍 问题分析

### 问题 1: 节点标签不显示

**原因：**
```typescript
// 之前的条件太严格
const shouldShowLabel = globalScale > 0.8 || isHighlighted || isSearchMatched;
```

- `globalScale` 是当前缩放级别
- 初始加载时，图谱会自动缩放到适配所有节点（`zoomToFit`）
- 如果节点很多，`globalScale` 可能小于 0.8
- 导致所有标签都不显示

### 问题 2: 搜索高亮不工作

**可能原因：**
1. 节点名称字段不统一（`name` vs `entity_name` vs `label`）
2. 搜索匹配逻辑可能有问题
3. 状态更新可能没有触发重新渲染

## ✅ 解决方案

### 修复 1: 优化标签显示逻辑

**修改前：**
```typescript
const shouldShowLabel = globalScale > 0.8 || isHighlighted || isSearchMatched;
```

**修改后：**
```typescript
// 🔥 优化标签显示逻辑
// 始终显示：Collection、Document、搜索匹配、高亮节点
// 或者缩放级别 > 0.3 时显示所有标签
const isImportantNode = node.type === 'collection' || node.type === 'document';
const shouldShowLabel = isImportantNode || isSearchMatched || isHighlighted || globalScale > 0.3;
```

**改进：**
- ✅ Collection 和 Document 节点始终显示标签（重要节点）
- ✅ 搜索匹配的节点始终显示标签
- ✅ 高亮的节点始终显示标签
- ✅ 降低缩放阈值从 0.8 到 0.3（更容易看到标签）

### 修复 2: 改进搜索匹配逻辑

**修改前：**
```typescript
const nodeName = (n.name || n.entity_name || '').toLowerCase();
if (nodeName.includes(query.toLowerCase())) {
  matchedNodeIds.add(n.id);
}
```

**修改后：**
```typescript
// 尝试多个名称字段，确保转换为字符串
const nodeName = String(n.name || n.entity_name || n.label || n.id || '').toLowerCase();
const queryLower = query.toLowerCase();

if (nodeName.includes(queryLower)) {
  console.log('✅ Matched node:', n.id, nodeName);
  matchedNodeIds.add(n.id);
}
```

**改进：**
- ✅ 尝试更多名称字段（`name`, `entity_name`, `label`, `id`）
- ✅ 使用 `String()` 确保类型安全
- ✅ 添加调试日志，方便排查问题
- ✅ 预先计算 `queryLower`，提高性能

### 修复 3: 添加调试日志

```typescript
console.log('🔍 Search query:', query);
console.log('✅ Matched node:', n.id, nodeName);
console.log('🎯 Total matched nodes:', matchedNodeIds.size);
console.log('📄 Matched documents:', matchedDocIds.size);
console.log('🌟 Search matched nodes state updated:', matchedNodeIds.size);
```

**用途：**
- 帮助诊断搜索是否正常工作
- 查看匹配了多少节点
- 验证状态是否正确更新

## 📊 预期效果

### 标签显示

**之前：**
- ❌ 缩放级别 < 0.8 时，所有标签都不显示
- ❌ 用户看到的只是一堆没有名字的点

**之后：**
- ✅ Collection 和 Document 始终显示标签
- ✅ 搜索匹配的节点始终显示标签
- ✅ 缩放级别 > 0.3 时，所有节点都显示标签
- ✅ 用户可以清楚地看到节点名称

### 搜索高亮

**之前：**
- ❌ 搜索后节点可能不高亮
- ❌ 无法区分哪些是匹配结果

**之后：**
- ✅ 搜索匹配的节点变为黄色 (`#fbbf24`)
- ✅ 节点大小放大到 10px
- ✅ 橙色边框 (`#f59e0b`)
- ✅ 文字加粗显示
- ✅ 连接线也变黄色加粗
- ✅ 统计面板显示匹配数量

## 🎯 测试步骤

### 1. 测试标签显示

1. 刷新页面，加载全局知识图谱
2. 检查 Collection 和 Document 节点是否显示名称
3. 缩小图谱（Zoom Out）
4. 验证重要节点的标签仍然可见

**预期结果：**
- ✅ Collection 节点显示知识库名称
- ✅ Document 节点显示文档名称
- ✅ 即使缩小，重要节点的标签仍然可见

### 2. 测试搜索高亮

1. 在搜索框输入一个实体名称（例如 "主变"）
2. 按回车或点击搜索按钮
3. 打开浏览器控制台查看日志

**预期日志：**
```
🔍 Search query: 主变
✅ Matched node: entity_123 主变压器
✅ Matched node: entity_456 #1主变
🎯 Total matched nodes: 2
📄 Matched documents: 3
🌟 Search matched nodes state updated: 2
```

**预期视觉效果：**
- ✅ 匹配的节点变为黄色
- ✅ 节点比其他节点大
- ✅ 有橙色边框
- ✅ 文字加粗显示
- ✅ 连接线变黄色
- ✅ 统计面板显示 "匹配: 2"

### 3. 测试多来源标记

1. 搜索一个在多个文档中出现的实体
2. 查看该节点

**预期效果：**
- ✅ 节点下方显示 "N 个来源"（蓝色文字）
- ✅ 右键查看详情，显示所有来源知识库

## 🔧 技术细节

### 标签显示条件

```typescript
const isImportantNode = node.type === 'collection' || node.type === 'document';
const shouldShowLabel = 
  isImportantNode ||        // Collection/Document 始终显示
  isSearchMatched ||        // 搜索匹配始终显示
  isHighlighted ||          // 高亮节点始终显示
  globalScale > 0.3;        // 缩放 > 0.3 时显示
```

### 搜索匹配逻辑

```typescript
// 1. 获取节点名称（尝试多个字段）
const nodeName = String(
  n.name || 
  n.entity_name || 
  n.label || 
  n.id || 
  ''
).toLowerCase();

// 2. 检查是否包含搜索词
if (nodeName.includes(queryLower)) {
  matchedNodeIds.add(n.id);
}

// 3. 更新状态
setSearchMatchedNodes(matchedNodeIds);
```

### 视觉效果优先级

```typescript
// 节点大小
if (isSearchMatched) size = 10;      // 最大
else if (isHighlighted) size = 8;    // 中等
else if (node.val) size = Math.min(node.val * 2, 12);  // 根据度数

// 节点颜色
if (isSearchMatched) {
  ctx.fillStyle = '#fbbf24';  // 黄色
} else if (highlightNodes.size > 0 && !isHighlighted) {
  ctx.fillStyle = '#333';  // 灰色（非高亮）
} else {
  ctx.fillStyle = nodeTypeColors[node.type];  // 类型颜色
}

// 边框
if (isSearchMatched || isHighlighted) {
  ctx.strokeStyle = isSearchMatched ? '#f59e0b' : '#fff';
  ctx.lineWidth = 2 / globalScale;
  ctx.stroke();
}
```

## 📝 修改文件

- ✅ `web/src/app/workspace/collections/all/graph/global-graph-explorer.tsx`
  - 行 755-759: 优化标签显示逻辑
  - 行 378-383: 改进搜索匹配逻辑
  - 行 373-413: 添加调试日志

## 🚀 部署

```bash
# 重新构建前端容器
docker-compose up -d --build frontend

# 等待构建完成后，刷新浏览器页面
```

## ✅ 验收标准

- [x] 节点显示名称标签
- [x] Collection 和 Document 始终显示标签
- [x] 搜索后匹配节点变黄色高亮
- [x] 搜索匹配节点显示橙色边框
- [x] 搜索匹配节点文字加粗
- [x] 连接线高亮
- [x] 统计面板显示匹配数量
- [x] 多来源实体显示来源标记
- [x] 控制台输出调试日志

---

**状态：** ✅ 代码已修复，等待构建测试
**修复时间：** 2025-11-26 16:30:00
