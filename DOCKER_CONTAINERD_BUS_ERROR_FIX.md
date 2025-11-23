# Docker Containerd Bus Error 修复指南

## 🚨 问题描述

Docker 服务报错：

```
docker service containerd failed: signal: bus error (core dumped)
```

**Bus Error (SIGBUS)** 是一个系统级错误，通常表示：

- 内存访问错误（访问未对齐的内存地址）
- 硬件问题（内存损坏、CPU 问题）
- 损坏的 Docker/containerd 安装
- 不兼容的系统库
- 磁盘 I/O 问题
- 资源耗尽

## 🔍 快速诊断步骤

### 1. 检查系统资源

```powershell
# 检查内存使用情况
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory

# 检查磁盘空间
Get-PSDrive C | Select-Object Used, Free

# 检查 CPU 使用率
Get-Counter '\Processor(_Total)\% Processor Time'
```

### 2. 检查 Docker 状态

```powershell
# 检查 Docker 进程
Get-Process | Where-Object { $_.ProcessName -like "*docker*" -or $_.ProcessName -like "*containerd*" }

# 检查 WSL2 状态
wsl --list --verbose

# 检查 Docker 日志
Get-Content "$env:LOCALAPPDATA\Docker\log.txt" -Tail 50
```

### 3. 检查系统事件日志

```powershell
# 查看系统错误日志
Get-EventLog -LogName System -EntryType Error -Newest 20 | Where-Object { $_.Source -like "*docker*" -or $_.Source -like "*containerd*" }
```

## 🛠️ 解决方案

### 方案一：重启 Docker 服务（最简单）

```powershell
# 1. 完全关闭 Docker Desktop
# 通过任务管理器结束所有 Docker 相关进程：
# - Docker Desktop
# - com.docker.backend
# - com.docker.proxy
# - com.docker.service
# - containerd

# 或使用脚本强制关闭
.\scripts\fix-docker-startup.ps1 -Force

# 2. 关闭 WSL2
wsl --shutdown

# 3. 等待 10 秒
Start-Sleep -Seconds 10

# 4. 重新启动 Docker Desktop
```

### 方案二：清理并重置 Docker（推荐）

```powershell
# 1. 停止所有 Docker 容器和服务
docker-compose down

# 2. 强制关闭 Docker
.\scripts\fix-docker-startup.ps1 -Force

# 3. 清理 Docker 系统
docker system prune -a --volumes -f

# 4. 清理构建缓存
docker builder prune -a -f

# 5. 重启 Docker Desktop
```

### 方案三：重置 WSL2（如果问题持续）

```powershell
# ⚠️ 警告：这会删除 WSL2 中的所有数据！

# 1. 以管理员身份运行 PowerShell

# 2. 关闭所有 WSL 实例
wsl --shutdown

# 3. 列出所有 WSL 分发版
wsl --list --verbose

# 4. 注销 Docker 相关的 WSL 分发版（如果需要）
# wsl --unregister docker-desktop
# wsl --unregister docker-desktop-data

# 5. 重新启动 Docker Desktop（会自动重新创建 WSL 分发版）
```

### 方案四：修复 containerd 配置

```powershell
# 1. 关闭 Docker Desktop

# 2. 备份并检查 containerd 配置
$containerdConfig = "$env:LOCALAPPDATA\Docker\wsl\distro\data\etc\containerd\config.toml"
if (Test-Path $containerdConfig) {
    Copy-Item $containerdConfig "$containerdConfig.backup"
    Get-Content $containerdConfig
}

# 3. 如果配置文件损坏，删除它（Docker 会重新创建）
# Remove-Item $containerdConfig -Force

# 4. 重新启动 Docker Desktop
```

### 方案五：检查并修复磁盘错误

```powershell
# 1. 以管理员身份运行 PowerShell

# 2. 检查 C 盘错误（需要重启）
chkdsk C: /f

# 3. 如果 Docker 数据在 E 盘，检查 E 盘
chkdsk E: /f

# 4. 重启系统后，重新启动 Docker Desktop
```

### 方案六：更新或重新安装 Docker Desktop

如果以上方法都无效，可能需要重新安装：

```powershell
# 1. 完全卸载 Docker Desktop
# - 通过 Windows 设置 → 应用 → Docker Desktop → 卸载
# - 或使用 PowerShell：
Get-AppxPackage *docker* | Remove-AppxPackage

# 2. 删除 Docker 数据目录（⚠️ 会删除所有数据）
Remove-Item "$env:LOCALAPPDATA\Docker" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:PROGRAMDATA\Docker" -Recurse -Force -ErrorAction SilentlyContinue

# 3. 清理 WSL2 Docker 分发版
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# 4. 重新下载并安装最新版本的 Docker Desktop
# 从 https://www.docker.com/products/docker-desktop 下载
```

## 🔧 高级诊断

### 检查硬件问题

```powershell
# 运行 Windows 内存诊断
# 1. 按 Win + R，输入 mdsched.exe
# 2. 选择"立即重新启动并检查问题"
# 3. 等待诊断完成

# 检查磁盘健康状态
Get-PhysicalDisk | Select-Object DeviceID, MediaType, HealthStatus, OperationalStatus
```

### 检查系统兼容性

```powershell
# 检查 Windows 版本
Get-ComputerInfo | Select-Object WindowsVersion, WindowsBuildLabEx

# 检查虚拟化支持
Get-ComputerInfo | Select-Object HyperV*

# 检查 WSL2 版本
wsl --version
```

### 查看详细错误信息

```powershell
# 查看 Docker Desktop 日志
Get-Content "$env:LOCALAPPDATA\Docker\log.txt" -Tail 100

# 查看 Windows 事件查看器中的 Docker 相关错误
# 1. 按 Win + X，选择"事件查看器"
# 2. Windows 日志 → 应用程序
# 3. 筛选包含 "docker" 或 "containerd" 的事件
```

## 📋 预防措施

### 1. 定期清理 Docker

```powershell
# 每周运行一次清理
.\scripts\cleanup-docker.ps1 -DiskSpace
```

### 2. 监控系统资源

- 确保至少有 10GB 可用磁盘空间
- 确保有足够的内存（建议 8GB+）
- 避免同时运行过多容器

### 3. 保持 Docker Desktop 更新

- 定期检查并更新到最新版本
- 关注 Docker Desktop 的发布说明

### 4. 配置 Docker 资源限制

在 Docker Desktop 设置中：

- Settings → Resources → Advanced
- 设置合理的 CPU 和内存限制
- 启用 "Automatically clean up unused data"

## 🆘 如果问题仍然存在

如果所有方法都无效，请收集以下信息：

1. **系统信息**：

   ```powershell
   Get-ComputerInfo | Select-Object WindowsVersion, WindowsBuildLabEx, TotalPhysicalMemory
   ```

2. **Docker 版本**：

   ```powershell
   docker --version
   docker-compose --version
   ```

3. **错误日志**：

   - Docker Desktop 日志：`%LOCALAPPDATA%\Docker\log.txt`
   - Windows 事件查看器中的相关错误

4. **硬件信息**：
   - CPU 型号
   - 内存大小和类型
   - 磁盘类型（SSD/HDD）

然后可以：

- 在 Docker Desktop 的 GitHub Issues 中搜索类似问题
- 联系 Docker 支持团队
- 考虑使用替代方案（如 Podman Desktop）

## 🔗 相关文档

- [Docker 磁盘空间修复指南](DOCKER_DISK_SPACE_FIX.md)
- [Docker 启动问题修复指南](scripts/fix-docker-startup.ps1)
- [Docker 清理指南](DOCKER_CLEANUP_GUIDE.md)

## 📝 常见问题

### Q: Bus Error 是硬件问题吗？

A: 不一定。虽然 Bus Error 可能由硬件问题引起，但更常见的原因是：

- 损坏的 Docker 安装
- 磁盘 I/O 错误
- 内存不足
- WSL2 配置问题

### Q: 需要更换硬件吗？

A: 通常不需要。先尝试软件层面的修复（重启、清理、重置），只有在确认硬件故障时才考虑更换。

### Q: 数据会丢失吗？

A: 如果只执行重启和清理操作，数据不会丢失。但如果执行"重置 WSL2"或"重新安装 Docker Desktop"，数据可能会丢失。**请务必先备份重要数据！**

### Q: 如何快速恢复服务？

A: 最快的恢复步骤：

1. 强制关闭 Docker：`.\scripts\fix-docker-startup.ps1 -Force`
2. 等待 10 秒
3. 重新启动 Docker Desktop
4. 如果仍然失败，执行清理：`docker system prune -a --volumes -f`

