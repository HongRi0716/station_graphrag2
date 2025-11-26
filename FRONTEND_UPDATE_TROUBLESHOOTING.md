# 前端更新未生效 - 诊断和解决方案

## 🔍 问题诊断

### 现象
重新构建前端后，浏览器中看不到新功能（节点标签、搜索高亮、聚光灯模式等）

### 可能原因
1. **浏览器缓存** - 浏览器加载了旧版本的 JavaScript
2. **Service Worker** - Next.js 的 Service Worker 缓存了旧版本
3. **构建问题** - 代码没有正确编译

---

## ✅ 解决方案

### 方案 1: 强制刷新浏览器缓存 (推荐)

#### Windows/Linux
```
Ctrl + Shift + R
或
Ctrl + F5
```

#### macOS
```
Cmd + Shift + R
或
Cmd + Option + R
```

### 方案 2: 清除浏览器缓存

#### Chrome/Edge
1. 按 `F12` 打开开发者工具
2. 右键点击刷新按钮
3. 选择 "清空缓存并硬性重新加载"

#### 或者
1. 按 `Ctrl + Shift + Delete`
2. 选择 "缓存的图片和文件"
3. 点击 "清除数据"

### 方案 3: 禁用缓存（开发模式）

#### 开发者工具设置
1. 按 `F12` 打开开发者工具
2. 按 `F1` 打开设置
3. 勾选 "Disable cache (while DevTools is open)"
4. 保持开发者工具打开状态
5. 刷新页面

### 方案 4: 无痕模式测试

```
Ctrl + Shift + N (Chrome/Edge)
Ctrl + Shift + P (Firefox)
```

在无痕模式下打开页面，验证新功能是否生效

### 方案 5: 检查 Service Worker

#### 清除 Service Worker
1. 打开开发者工具 (`F12`)
2. 切换到 "Application" 标签
3. 左侧选择 "Service Workers"
4. 点击 "Unregister" 注销所有 Service Worker
5. 刷新页面

---

## 🔬 验证新功能

### 1. 检查节点标签

**测试步骤：**
1. 打开全局知识图谱页面
2. 观察图谱中的节点

**预期结果：**
- ✅ Collection 和 Document 节点显示名称
- ✅ 缩放时标签可见
- ✅ 实体节点在缩放 > 0.3 时显示标签

**如果看不到标签：**
- 打开控制台 (`F12`)
- 查看是否有 JavaScript 错误
- 检查网络请求是否成功

### 2. 检查搜索高亮

**测试步骤：**
1. 在搜索框输入关键词（如 "主变"）
2. 按回车搜索

**预期结果：**
- ✅ 匹配的节点变黄色
- ✅ 节点有橙色边框
- ✅ 文字加粗显示
- ✅ 统计面板显示 "匹配: N"

**控制台日志：**
```
🔍 Search query: 主变
✅ Matched node: entity_123 主变压器
🎯 Total matched nodes: 2
```

### 3. 检查聚光灯模式

**测试步骤：**
1. 搜索任意关键词
2. 观察节点透明度变化

**预期结果：**
- ✅ 匹配节点完全不透明
- ✅ 邻居节点半透明
- ✅ 其他节点几乎透明
- ✅ 统计面板显示 "🔦 聚光灯: N"

**控制台日志：**
```
🔦 Spotlight mode activated. Spotlight nodes: 8
```

---

## 🛠️ 高级诊断

### 检查构建版本

#### 1. 查看页面源代码
```
右键 → 查看网页源代码
或
Ctrl + U
```

查找 `<script>` 标签，检查 JavaScript 文件的哈希值是否改变

#### 2. 检查网络请求
1. 打开开发者工具 (`F12`)
2. 切换到 "Network" 标签
3. 勾选 "Disable cache"
4. 刷新页面
5. 查看 JavaScript 文件是否重新加载

**预期：**
- 状态码应该是 `200` 或 `304`
- 文件大小应该有变化
- 时间戳应该是最新的

#### 3. 检查控制台错误
```
F12 → Console 标签
```

查找红色错误信息，特别是：
- `SyntaxError` - 语法错误
- `TypeError` - 类型错误
- `ReferenceError` - 引用错误

### 检查 Docker 构建

#### 1. 确认构建成功
```bash
docker-compose logs frontend --tail 100
```

查找构建日志中的错误

#### 2. 检查容器状态
```bash
docker ps | Select-String "frontend"
```

**预期输出：**
```
STATUS: Up X minutes
```

#### 3. 进入容器检查文件
```bash
docker exec -it aperag-frontend sh
ls -la /app/.next
```

查看构建产物是否存在

---

## 🔧 强制重新构建

### 完全清理重建

```bash
# 1. 停止容器
docker-compose down

# 2. 删除镜像
docker rmi apecloud/aperag-frontend:v0.0.0-nightly

# 3. 清理构建缓存
docker builder prune -f

# 4. 重新构建（不使用缓存）
docker-compose build --no-cache frontend

# 5. 启动容器
docker-compose up -d frontend
```

### 验证新镜像

```bash
# 查看镜像创建时间
docker images | Select-String "aperag-frontend"
```

**预期：**
创建时间应该是刚才的时间

---

## 📊 问题排查清单

### 浏览器端
- [ ] 已强制刷新 (Ctrl + Shift + R)
- [ ] 已清除浏览器缓存
- [ ] 已清除 Service Worker
- [ ] 已在无痕模式测试
- [ ] 已禁用缓存（开发者工具）

### 服务器端
- [ ] 容器状态为 "Up"
- [ ] 构建日志无错误
- [ ] 文件时间戳最新
- [ ] 端口 3000 可访问

### 代码端
- [ ] TypeScript 无编译错误
- [ ] 控制台无 JavaScript 错误
- [ ] 网络请求成功 (200/304)
- [ ] 文件哈希值已更新

---

## 🎯 快速验证脚本

### 浏览器控制台运行

```javascript
// 检查组件是否加载
console.log('Checking GlobalGraphExplorer...');

// 检查状态
const checkFeatures = () => {
  console.log('✓ Page loaded');
  
  // 检查是否有搜索框
  const searchInput = document.querySelector('input[placeholder*="搜索"]');
  console.log('Search input:', searchInput ? '✓ Found' : '✗ Not found');
  
  // 检查是否有统计面板
  const statsPanel = document.querySelector('.text-xs.font-bold');
  console.log('Stats panel:', statsPanel ? '✓ Found' : '✗ Not found');
  
  // 检查是否有图谱
  const canvas = document.querySelector('canvas');
  console.log('Graph canvas:', canvas ? '✓ Found' : '✗ Not found');
};

setTimeout(checkFeatures, 2000);
```

---

## 💡 常见问题

### Q1: 强制刷新后还是看不到变化？
**A:** 尝试以下步骤：
1. 完全关闭浏览器
2. 重新打开浏览器
3. 访问页面

### Q2: 无痕模式可以看到，正常模式看不到？
**A:** 这是缓存问题，解决方案：
1. 清除浏览器所有缓存
2. 清除 Service Worker
3. 重启浏览器

### Q3: 控制台有错误？
**A:** 检查错误信息：
- 如果是 `404`：文件路径错误
- 如果是 `SyntaxError`：代码语法错误
- 如果是 `TypeError`：类型错误

### Q4: 网络请求返回旧文件？
**A:** 检查：
1. CDN 缓存（如果使用）
2. 反向代理缓存（如 Nginx）
3. Docker 容器是否真的重启了

---

## ✅ 验证成功标志

当您看到以下内容时，说明更新成功：

### 控制台日志
```
🔍 Search query: XXX
✅ Matched node: ...
🎯 Total matched nodes: N
🔦 Spotlight mode activated. Spotlight nodes: N
```

### 视觉效果
- ✅ 节点显示名称标签
- ✅ 搜索匹配节点变黄色
- ✅ 聚光灯模式：透明度变化
- ✅ 统计面板显示完整信息

### 统计面板
```
┌─────────────────┐
│ 图谱统计    ✕   │
├─────────────────┤
│ 节点:      156  │
│ 连接:      234  │
├─────────────────┤
│ 匹配:        2  │
│ 🔦 聚光灯:   8  │
└─────────────────┘
```

---

## 🚀 推荐操作流程

### 标准刷新流程
```
1. Ctrl + Shift + R (强制刷新)
   ↓
2. 检查控制台日志
   ↓
3. 测试搜索功能
   ↓
4. 验证视觉效果
```

### 如果还是不行
```
1. 清除浏览器缓存
   ↓
2. 清除 Service Worker
   ↓
3. 无痕模式测试
   ↓
4. 重新构建容器
```

---

**请先尝试 Ctrl + Shift + R 强制刷新，然后告诉我结果！**
