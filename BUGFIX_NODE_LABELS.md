# 节点标签显示问题 - 最终修复

## 🐛 问题描述

用户报告：**看不到节点的名称**

即使在强制刷新浏览器后，图谱中的节点仍然没有显示名称标签。

---

## 🔍 根本原因分析

### 可能的原因

1. **字段名不匹配**
   - 后端返回的节点数据中，名称字段可能不是 `name` 或 `entity_name`
   - 可能是 `label`, `title`, `description` 等其他字段

2. **标签显示条件太严格**
   - 之前的逻辑要求 `globalScale > 0.3`
   - 如果初始缩放级别很小，标签不会显示

3. **数据为空**
   - 节点数据中可能根本没有名称字段
   - 或者名称字段为空字符串

---

## ✅ 解决方案

### 修复 1: 扩展字段名检测

**修改前：**
```typescript
const label = node.name || node.entity_name || '';
```

**修改后：**
```typescript
const label = node.name || 
              node.entity_name || 
              node.label || 
              node.title ||
              node.description ||
              node.id || 
              'Unknown';
```

**改进：**
- ✅ 尝试 6 个可能的字段名
- ✅ 最后使用节点 ID 作为后备
- ✅ 避免空标签

### 修复 2: 添加调试日志

```typescript
// 调试：第一次渲染时打印节点结构
if (!(window as any)._nodeLogged && node.id) {
  console.log('📊 Sample node structure:', {
    id: node.id,
    type: node.type,
    name: node.name,
    entity_name: node.entity_name,
    label: node.label,
    title: node.title,
    allKeys: Object.keys(node),
  });
  (window as any)._nodeLogged = true;
}
```

**用途：**
- 🔍 帮助诊断节点数据结构
- 📊 查看所有可用的字段
- 🐛 快速定位问题

### 修复 3: 默认显示所有标签

**添加状态：**
```typescript
const [showAllLabels, setShowAllLabels] = useState(true); // 默认显示所有标签
```

**更新显示逻辑：**
```typescript
const shouldShowLabel = showAllLabels ||  // 🔥 强制显示
                       isImportantNode || 
                       isSearchMatched || 
                       isHighlighted || 
                       globalScale > 0.3;

if (shouldShowLabel && label && label !== 'Unknown') {
  // 渲染标签...
}
```

**改进：**
- ✅ 默认显示所有标签（`showAllLabels = true`）
- ✅ 不显示 "Unknown" 标签（避免混乱）
- ✅ 可以通过状态控制是否显示

---

## 🔬 调试步骤

### 1. 重新构建前端

```bash
docker-compose up -d --build frontend
```

### 2. 强制刷新浏览器

```
Ctrl + Shift + R
```

### 3. 打开浏览器控制台

```
F12 → Console 标签
```

### 4. 查看节点结构日志

刷新页面后，应该看到类似的日志：

```javascript
📊 Sample node structure: {
  id: "col_123",
  type: "collection",
  name: "设备台账库",
  entity_name: undefined,
  label: undefined,
  title: undefined,
  allKeys: ["id", "type", "name", "metadata", "x", "y", "vx", "vy"]
}
```

**分析日志：**
- 查看 `name`, `entity_name`, `label`, `title` 哪个有值
- 查看 `allKeys` 列表，找到实际的名称字段
- 如果所有字段都是 `undefined`，说明后端数据有问题

### 5. 验证标签显示

**预期效果：**
- ✅ 所有节点都显示标签（因为 `showAllLabels = true`）
- ✅ 标签内容是节点名称或 ID
- ✅ 不显示 "Unknown" 标签

---

## 📊 可能的场景

### 场景 1: 字段名正确

**日志：**
```javascript
📊 Sample node structure: {
  name: "设备台账库",  // ✅ 有值
  ...
}
```

**结果：**
- ✅ 标签正常显示
- ✅ 显示 "设备台账库"

### 场景 2: 使用其他字段

**日志：**
```javascript
📊 Sample node structure: {
  name: undefined,
  label: "设备台账库",  // ✅ 使用 label 字段
  ...
}
```

**结果：**
- ✅ 标签正常显示
- ✅ 显示 "设备台账库"

### 场景 3: 所有字段都为空

**日志：**
```javascript
📊 Sample node structure: {
  name: undefined,
  entity_name: undefined,
  label: undefined,
  title: undefined,
  id: "col_123",  // ✅ 使用 ID 作为后备
  ...
}
```

**结果：**
- ✅ 标签显示节点 ID
- ✅ 显示 "col_123"

### 场景 4: 完全没有数据

**日志：**
```javascript
📊 Sample node structure: {
  id: undefined,  // ❌ 连 ID 都没有
  ...
}
```

**结果：**
- ❌ 不显示标签（因为 `label === 'Unknown'`）
- 🐛 **这是后端数据问题，需要修复后端**

---

## 🛠️ 后端数据检查

如果前端修复后还是看不到标签，需要检查后端：

### 1. 检查 API 响应

```bash
curl -X POST http://localhost:3000/api/v1/graphs/hierarchy/global \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 10, "include_entities": true}'
```

### 2. 查看返回的节点数据

```json
{
  "nodes": [
    {
      "id": "col_123",
      "type": "collection",
      "name": "设备台账库",  // ← 检查这个字段
      "metadata": {...}
    }
  ]
}
```

### 3. 确认字段存在

- ✅ `name` 字段存在且有值
- ✅ 或者 `label`, `title` 等字段有值
- ❌ 如果所有字段都没有，需要修复后端

---

## 📝 修改文件

### 前端文件
- `web/src/app/workspace/collections/all/graph/global-graph-explorer.tsx`
  - 行 221: 添加 `showAllLabels` 状态
  - 行 774-797: 扩展字段名检测 + 调试日志
  - 行 844-854: 更新标签显示逻辑

---

## ✅ 验证清单

### 前端验证
- [ ] 重新构建前端容器
- [ ] 强制刷新浏览器 (Ctrl + Shift + R)
- [ ] 打开控制台查看节点结构日志
- [ ] 确认节点显示标签

### 调试信息
- [ ] 控制台显示 "📊 Sample node structure"
- [ ] 日志中有节点的字段信息
- [ ] 可以看到哪个字段包含名称

### 视觉效果
- [ ] 图谱中的节点显示名称
- [ ] Collection 节点显示知识库名称
- [ ] Document 节点显示文档名称
- [ ] Entity 节点显示实体名称或 ID

---

## 🎯 预期结果

### 成功标志

1. **控制台日志**
```
📊 Sample node structure: {
  id: "col_123",
  type: "collection",
  name: "设备台账库",
  allKeys: [...]
}
```

2. **视觉效果**
- ✅ 所有节点都有标签
- ✅ 标签内容清晰可读
- ✅ 不同类型节点的标签颜色不同

3. **交互效果**
- ✅ 缩放时标签始终可见
- ✅ 搜索时匹配节点标签加粗
- ✅ 高亮节点标签突出显示

---

## 🚀 下一步

如果标签仍然不显示：

### 1. 检查控制台日志
- 查看 "📊 Sample node structure" 日志
- 确认哪个字段有值
- 如果所有字段都是 `undefined`，问题在后端

### 2. 检查后端数据
- 使用 `curl` 或 Postman 测试 API
- 查看返回的 JSON 数据
- 确认节点数据包含名称字段

### 3. 临时解决方案
- 如果后端数据没有名称，会显示节点 ID
- 这样至少可以区分不同的节点
- 然后修复后端数据

---

**现在请重新构建并测试，然后查看控制台日志告诉我节点结构！** 🔍
