# Docker 清理脚本使用指南

## 脚本文件

- `cleanup-docker.sh` - Linux/macOS 版本（Bash）
- `cleanup-docker.ps1` - Windows 版本（PowerShell）

## 快速开始

### Windows (PowerShell)

```powershell
# 查看帮助
.\scripts\cleanup-docker.ps1 -Help

# 查看当前状态
.\scripts\cleanup-docker.ps1 -Status

# 只清理容器（保留数据）
.\scripts\cleanup-docker.ps1 -Containers

# 清理容器和数据卷（⚠️ 会删除所有数据）
.\scripts\cleanup-docker.ps1 -Volumes

# 完全清理（容器、卷、镜像、网络）
.\scripts\cleanup-docker.ps1 -All

# 清理后重启服务
.\scripts\cleanup-docker.ps1 -Containers -Restart
```

### Linux/macOS (Bash)

```bash
# 添加执行权限
chmod +x scripts/cleanup-docker.sh

# 查看帮助
./scripts/cleanup-docker.sh -h

# 查看当前状态
./scripts/cleanup-docker.sh --status

# 只清理容器（保留数据）
./scripts/cleanup-docker.sh -c

# 清理容器和数据卷（⚠️ 会删除所有数据）
./scripts/cleanup-docker.sh -v

# 完全清理（容器、卷、镜像、网络）
./scripts/cleanup-docker.sh -a

# 清理后重启服务
./scripts/cleanup-docker.sh -c --restart
```

## 常用场景

### 场景 1: 解决 I/O 错误或容器无法启动

```powershell
# Windows
.\scripts\cleanup-docker.ps1 -Containers -Restart

# Linux/macOS
./scripts/cleanup-docker.sh -c --restart
```

### 场景 2: 清理磁盘空间

```powershell
# Windows
.\scripts\cleanup-docker.ps1 -System

# Linux/macOS
./scripts/cleanup-docker.sh -s
```

### 场景 3: 完全重置（⚠️ 会删除所有数据）

```powershell
# Windows
.\scripts\cleanup-docker.ps1 -All -Restart

# Linux/macOS
./scripts/cleanup-docker.sh -a --restart
```

### 场景 4: 强制清理（不询问确认）

```powershell
# Windows
.\scripts\cleanup-docker.ps1 -Containers -Force

# Linux/macOS
./scripts/cleanup-docker.sh -c -f
```

## 选项说明

| 选项               | 说明                     | 危险级别 |
| ------------------ | ------------------------ | -------- |
| `-c, --containers` | 只清理容器（保留数据卷） | ⚠️ 低    |
| `-v, --volumes`    | 清理容器和数据卷         | 🔴 高    |
| `-i, --images`     | 清理未使用的镜像         | ⚠️ 中    |
| `-s, --system`     | 清理系统资源（不包括卷） | ⚠️ 中    |
| `-a, --all`        | 完全清理（所有资源）     | 🔴 极高  |
| `-f, --force`      | 强制执行，不询问确认     | -        |
| `--status`         | 显示当前资源状态         | ✅ 安全  |
| `--restart`        | 清理后重新启动服务       | ⚠️ 低    |

## 注意事项

1. **数据备份**: 使用 `-v` 或 `-a` 选项前，请确保已备份重要数据
2. **生产环境**: 在生产环境中使用时要格外小心
3. **卷数据**: 数据卷包含数据库、向量数据库等重要数据
4. **确认提示**: 默认会询问确认，使用 `-f` 可跳过确认

## 故障排除

### 问题 1: 脚本无法执行

**Windows PowerShell:**

```powershell
# 如果遇到执行策略限制
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/macOS:**

```bash
# 确保有执行权限
chmod +x scripts/cleanup-docker.sh
```

### 问题 2: Docker 命令失败

```powershell
# 检查Docker是否运行
docker ps

# 如果Docker Desktop未运行，先启动它
```

### 问题 3: 权限不足

```powershell
# Windows: 以管理员身份运行PowerShell
# Linux/macOS: 使用sudo（如果需要）
sudo ./scripts/cleanup-docker.sh -c
```

## 示例输出

```
[INFO] 当前Docker资源状态:

=== 容器 ===
NAMES              STATUS    SIZE
aperag-api         Up 2 days 0B
aperag-celeryworker Up 2 days 0B

=== 卷 ===
DRIVER    VOLUME NAME
local     aperag-postgres-data
local     aperag-qdrant-data

[INFO] 清理容器...
[SUCCESS] 容器已停止并删除
[INFO] 清理完成！
```
