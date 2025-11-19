# Docker 容器清理指南

本文档说明如何清理 ApeRAG 项目的 Docker 容器、镜像、卷和网络。

## 快速清理命令

### 1. 停止并删除所有容器（保留数据卷）

```bash
# 停止所有容器
docker-compose down

# 或者使用Makefile
make compose-down
```

### 2. 停止并删除所有容器和数据卷（⚠️ 会删除所有数据）

```bash
# 停止并删除容器和数据卷
docker-compose down -v

# 或者使用Makefile
make compose-down REMOVE_VOLUMES=1
```

### 3. 清理未使用的 Docker 资源

```bash
# 清理所有未使用的容器、网络、镜像（悬空镜像）
docker system prune

# 清理所有未使用的资源，包括未使用的卷（⚠️ 谨慎使用）
docker system prune -a --volumes
```

## 详细清理步骤

### 步骤 1: 查看当前运行的容器

```bash
# 查看所有容器（包括停止的）
docker ps -a

# 查看ApeRAG相关的容器
docker ps -a | grep aperag
```

### 步骤 2: 停止容器

```bash
# 停止所有ApeRAG容器
docker-compose stop

# 或者停止特定容器
docker stop aperag-api
docker stop aperag-celeryworker
docker stop aperag-frontend
```

### 步骤 3: 删除容器

```bash
# 删除所有ApeRAG容器（必须先停止）
docker-compose rm -f

# 或者删除特定容器
docker rm aperag-api
docker rm aperag-celeryworker
docker rm aperag-frontend
```

### 步骤 4: 清理数据卷（可选，⚠️ 会删除所有数据）

```bash
# 查看所有卷
docker volume ls

# 查看ApeRAG相关的卷
docker volume ls | grep aperag

# 删除特定卷
docker volume rm aperag-postgres-data
docker volume rm aperag-qdrant-data
docker volume rm aperag-redis-data
docker volume rm aperag-es-data
docker volume rm aperag-neo4j-data
docker volume rm aperag-shared-data

# 或者删除所有未使用的卷
docker volume prune
```

### 步骤 5: 清理镜像（可选）

```bash
# 查看所有镜像
docker images

# 查看ApeRAG相关的镜像
docker images | grep aperag

# 删除特定镜像
docker rmi aperag-api:latest
docker rmi aperag-frontend:latest

# 删除所有未使用的镜像
docker image prune -a
```

### 步骤 6: 清理网络（可选）

```bash
# 查看所有网络
docker network ls

# 删除未使用的网络
docker network prune
```

## 完整清理脚本

### 方案 A: 保留数据卷（推荐用于开发环境）

```bash
# 停止并删除容器，但保留数据卷
docker-compose down

# 清理未使用的镜像和网络
docker system prune -f
```

### 方案 B: 完全清理（⚠️ 会删除所有数据，包括数据库）

```bash
# 停止并删除容器和数据卷
docker-compose down -v

# 清理所有未使用的资源
docker system prune -a --volumes -f
```

## 针对特定问题的清理

### 问题 1: 磁盘空间不足

#### 方案 A: Docker 可以运行时的清理（推荐）

```bash
# 使用清理脚本（推荐）
.\scripts\cleanup-docker.ps1 -DiskSpace

# 或者手动执行：
# 1. 停止所有容器
docker-compose down

# 2. 清理构建缓存（通常占用最多空间）
docker builder prune -a -f

# 3. 清理未使用的镜像、容器、网络
docker system prune -a -f

# 4. 查看磁盘使用情况
docker system df
```

#### 方案 B: Docker 无法启动时的清理（紧急情况）

如果 Docker 因为磁盘空间不足无法启动，需要手动清理：

**Windows (Docker Desktop with WSL2):**

1. **清理 WSL2 磁盘镜像**（通常占用最多空间）:

   ```powershell
   # 查看 WSL2 磁盘使用情况
   wsl --list --verbose

   # 压缩 WSL2 磁盘（需要先关闭 Docker Desktop）
   # 1. 关闭 Docker Desktop
   # 2. 在 PowerShell (管理员) 中运行：
   wsl --shutdown
   diskpart
   # 在 diskpart 中：
   # select vdisk file="C:\Users\<YourUser>\AppData\Local\Docker\wsl\data\ext4.vhdx"
   # compact vdisk
   # exit
   ```

2. **手动删除 Docker 构建缓存**:

   - 位置: `%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx`
   - 或者: `C:\Users\<YourUser>\AppData\Local\Docker\`
   - 注意: 删除前请确保 Docker Desktop 已完全关闭

3. **使用 Windows 磁盘清理工具**:

   - 运行 `cleanmgr` 或 "磁盘清理"
   - 选择系统盘（通常是 C:）
   - 勾选 "Docker Desktop" 相关选项（如果有）

4. **清理 WSL2 分发版**:

   ```powershell
   # 查看所有 WSL 分发版
   wsl --list --all

   # 如果不需要，可以卸载不用的分发版
   wsl --unregister <DistroName>
   ```

**Linux/Mac:**

```bash
# 1. 停止 Docker 服务
sudo systemctl stop docker  # Linux
# 或通过 Docker Desktop 界面停止  # Mac

# 2. 手动清理构建缓存目录
# Linux: /var/lib/docker/buildkit/
# Mac: ~/Library/Containers/com.docker.docker/Data/vms/0/

# 3. 清理 Docker 数据目录中的未使用文件
# 注意：需要谨慎操作，建议先备份
```

**清理后重启 Docker:**

```powershell
# Windows: 重新启动 Docker Desktop 应用
# 然后运行清理脚本
.\scripts\cleanup-docker.ps1 -DiskSpace -Restart
```

### 问题 2: 容器无法启动或 I/O 错误

```bash
# 1. 强制停止所有容器
docker-compose kill

# 2. 删除所有容器
docker-compose rm -f

# 3. 清理未使用的资源
docker system prune -f

# 4. 重新启动
docker-compose up -d
```

### 问题 3: 需要重置所有数据

```bash
# ⚠️ 警告：这会删除所有数据！

# 1. 停止并删除所有容器和数据卷
docker-compose down -v

# 2. 清理所有未使用的资源
docker system prune -a --volumes -f

# 3. 重新构建和启动
docker-compose build --no-cache
docker-compose up -d
```

## 使用 Makefile 清理

项目提供了 Makefile 命令来简化操作：

```bash
# 停止并删除容器（保留数据卷）
make compose-down

# 停止并删除容器和数据卷
make compose-down REMOVE_VOLUMES=1

# 查看日志
make compose-logs
```

## 检查清理结果

```bash
# 检查容器
docker ps -a | grep aperag

# 检查卷
docker volume ls | grep aperag

# 检查镜像
docker images | grep aperag

# 检查磁盘使用情况
docker system df
```

## 注意事项

1. **数据备份**: 在执行完全清理（`-v`选项）之前，确保已备份重要数据
2. **生产环境**: 在生产环境中清理时要格外小心
3. **卷数据**: 数据卷包含数据库、向量数据库等重要数据，删除前请确认
4. **网络**: 删除网络可能会影响容器间的通信

## 常见问题

### Q: 如何只清理特定服务的容器？

A:

```bash
# 只停止和删除特定服务
docker-compose stop api
docker-compose rm -f api
```

### Q: 如何保留数据但清理容器？

A:

```bash
# 使用docker-compose down（不带-v选项）
docker-compose down
```

### Q: 清理后如何重新启动？

A:

```bash
# 重新构建并启动
docker-compose up -d --build

# 或者使用Makefile
make compose-up
```

### Q: 如何查看哪些资源占用空间最大？

A:

```bash
# 查看详细磁盘使用情况
docker system df -v
```
