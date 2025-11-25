# Frontend Setup Guide

## 安装依赖

在运行前端应用之前，需要安装必要的依赖包：

```bash
cd frontend

# 使用 npm
npm install
npm install --save-dev @types/react @types/react-dom @types/node

# 或使用 yarn
yarn install
yarn add -D @types/react @types/react-dom @types/node
```

## 配置说明

### API URL 配置

前端默认连接到 `http://localhost:8000` 的后端 API。

如果需要修改 API URL，可以通过以下方式：

1. **在代码中修改**：编辑 `src/lib/api/agents.ts`，修改 `API_BASE_URL` 常量
2. **通过环境变量**：在 `window.ENV.API_URL` 中设置（需要在 HTML 中注入）

### WebSocket URL 配置

WebSocket 连接默认使用 `ws://localhost:8000`。如果需要修改，请编辑 `src/lib/api/agents.ts` 中的 `createSupervisorWebSocket` 方法。

## 运行开发服务器

```bash
npm run dev
# 或
yarn dev
```

## 构建生产版本

```bash
npm run build
# 或
yarn build
```

## 智能体组件说明

### SupervisorDashboard
- 路径: `src/components/agents/SupervisorDashboard.tsx`
- 功能: 值班长总控台，支持任务分发、态势展示、实时思维链
- 使用: `<SupervisorDashboard userId="user123" />`

### ArchivistSearch
- 路径: `src/components/agents/ArchivistSearch.tsx`
- 功能: 图谱专家知识检索，支持知识检索、图谱遍历、历史查询
- 使用: `<ArchivistSearch userId="user123" />`

## 故障排查

### TypeScript 错误

如果遇到 "Cannot find module 'react'" 等错误，请确保已安装类型定义包：

```bash
npm install --save-dev @types/react @types/react-dom @types/node
```

### API 连接失败

1. 确保后端服务已启动（`uvicorn aperag.app:app --reload`）
2. 检查 API URL 配置是否正确
3. 查看浏览器控制台的网络请求错误信息
