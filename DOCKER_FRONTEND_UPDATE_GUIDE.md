# Docker 前端界面更新指南

## 问题：Docker 重建后界面不是最新的

如果 Docker 重建后前端界面没有更新，通常是因为以下原因：

1. **Docker 构建缓存**：使用了旧的缓存层
2. **浏览器缓存**：浏览器缓存了旧的静态资源
3. **镜像未更新**：使用了旧的 Docker 镜像
4. **构建顺序问题**：前端代码在构建时没有正确复制

## 快速解决方案

### 方案 1：使用重建脚本（推荐）

```powershell
# 完全重建前端（不使用缓存）
.\scripts\rebuild-frontend.ps1 -NoCache

# 或者清理后重建
.\scripts\rebuild-frontend.ps1 -Clean -NoCache
```

### 方案 2：手动重建

```powershell
# 1. 停止并删除前端容器
docker-compose stop frontend
docker-compose rm -f frontend

# 2. 删除旧的前端镜像
docker rmi docker.io/apecloud/aperag-frontend:v0.0.0-nightly

# 3. 不使用缓存重建前端
docker-compose build --no-cache frontend

# 4. 启动前端
docker-compose up -d frontend
```

### 方案 3：完全重建所有服务

```powershell
# 停止所有服务
docker-compose down

# 不使用缓存重建所有服务
docker-compose build --no-cache

# 启动所有服务
docker-compose up -d
```

## 清除浏览器缓存

即使 Docker 镜像更新了，浏览器可能仍缓存旧资源：

### Chrome/Edge

- **硬刷新**：`Ctrl + F5` 或 `Ctrl + Shift + R`
- **清除缓存**：`Ctrl + Shift + Delete` → 选择"缓存的图片和文件"

### Firefox

- **硬刷新**：`Ctrl + F5` 或 `Ctrl + Shift + R`
- **清除缓存**：`Ctrl + Shift + Delete` → 选择"缓存"

### Safari

- **硬刷新**：`Cmd + Option + R`
- **清除缓存**：`Cmd + Option + E`

## 验证更新是否成功

### 1. 检查镜像构建时间

```powershell
# 查看前端镜像的创建时间
docker images docker.io/apecloud/aperag-frontend:v0.0.0-nightly

# 应该显示最近的时间
```

### 2. 检查容器日志

```powershell
# 查看前端容器日志
docker logs aperag-frontend --tail 50
```

### 3. 检查前端文件

```powershell
# 进入前端容器检查文件
docker exec -it aperag-frontend ls -la /app

# 检查构建时间戳
docker exec -it aperag-frontend stat /app/server.js
```

### 4. 检查浏览器网络请求

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 勾选 "Disable cache"
4. 刷新页面（F5）
5. 查看请求的响应时间，应该是新的

## 常见问题排查

### Q1: 重建后仍然看到旧界面

**可能原因**：

- 浏览器缓存未清除
- Docker 镜像缓存未清除
- 构建时使用了旧代码

**解决方法**：

```powershell
# 1. 完全清理并重建
.\scripts\rebuild-frontend.ps1 -Clean -NoCache

# 2. 清除浏览器缓存并硬刷新（Ctrl+F5）

# 3. 如果还不行，检查代码是否已提交
git status
git log --oneline -5
```

### Q2: 构建很慢

**原因**：使用 `--no-cache` 会重新构建所有层

**解决方法**：

- 开发时可以使用缓存：`docker-compose build frontend`
- 发布前使用无缓存：`docker-compose build --no-cache frontend`

### Q3: 前端代码修改后没有反映

**检查清单**：

- [ ] 代码是否已保存
- [ ] 是否在正确的分支
- [ ] 是否使用了 `--no-cache` 重建
- [ ] 浏览器缓存是否已清除
- [ ] 容器是否已重启

### Q4: 构建失败

**常见错误**：

- `yarn install` 失败 → 检查网络和 `yarn.lock`
- `yarn build` 失败 → 检查前端代码错误
- 镜像拉取失败 → 检查网络连接

**解决方法**：

```powershell
# 查看详细错误
docker-compose build --no-cache frontend 2>&1 | Tee-Object build.log

# 检查构建日志
Get-Content build.log | Select-String -Pattern "error|Error|ERROR" -Context 5
```

## 最佳实践

### 开发环境

```powershell
# 快速重建（使用缓存）
docker-compose build frontend
docker-compose up -d frontend
```

### 生产环境

```powershell
# 完全重建（不使用缓存）
.\scripts\rebuild-frontend.ps1 -Clean -NoCache

# 或者
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### 自动化脚本

在 `package.json` 或 `Makefile` 中添加：

```makefile
rebuild-frontend:
	docker-compose stop frontend
	docker-compose rm -f frontend
	docker-compose build --no-cache frontend
	docker-compose up -d frontend
```

## 相关文件

- `web/Dockerfile` - 前端 Dockerfile
- `docker-compose.yml` - Docker Compose 配置
- `scripts/rebuild-frontend.ps1` - 前端重建脚本
- `Makefile` - 构建命令

## 技术细节

### 前端构建流程

1. **构建阶段**（builder）：

   - 复制 `package.json` 和 `yarn.lock`
   - 安装依赖：`yarn install --frozen-lockfile`
   - 复制源代码：`COPY . .`
   - 构建应用：`yarn build`

2. **生产阶段**：
   - 从构建阶段复制构建产物：`COPY --from=builder /app/build ./`
   - 安装 pm2
   - 启动服务：`pm2-runtime start server.js`

### 为什么需要 --no-cache

Docker 使用层缓存来加速构建。如果源代码层（`COPY . .`）被缓存，即使代码已更新，Docker 也会使用旧的缓存层。使用 `--no-cache` 强制重新构建所有层，确保使用最新代码。

### Next.js 缓存

Next.js 在构建时会生成静态资源，这些资源会被浏览器缓存。即使 Docker 镜像更新了，浏览器仍可能使用缓存的旧资源。因此需要清除浏览器缓存。
