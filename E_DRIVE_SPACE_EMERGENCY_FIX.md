# E 盘空间紧急修复指南

## 🚨 当前状况

- **E 盘可用空间**: 仅 0.11 GB（严重不足！）
- **主要问题**: `E:\docker\DockerDesktopWSL\disk\docker_data.vhdx` 占用了 **163.16 GB**
- **Docker 状态**: 已停止（无法启动，空间不足）

## ⚡ 快速解决方案

### 方案一：压缩 WSL2 虚拟磁盘（推荐，可释放大量空间）

这是最有效的方法，可以释放大量空间。

#### 步骤 1: 以管理员身份打开 PowerShell

1. 按 `Win + X`
2. 选择 "Windows PowerShell (管理员)" 或 "终端 (管理员)"
3. 导航到项目目录：
   ```powershell
   cd "E:\我的口袋\科创\python\创意一_基于视觉语言大模型基座和模型蒸馏演化的全时空巡检天眼系统\model_zoo\ApeRAGv2"
   ```

#### 步骤 2: 确保 Docker 和 WSL2 已关闭

```powershell
# 关闭所有Docker进程
Get-Process | Where-Object { $_.ProcessName -like "*docker*" -or $_.ProcessName -like "*com.docker*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 关闭WSL2
wsl --shutdown
Start-Sleep -Seconds 5
```

#### 步骤 3: 压缩虚拟磁盘

**方法 A: 使用脚本（推荐）**

```powershell
.\scripts\compact-docker-vhdx.ps1
```

**方法 B: 手动使用 diskpart**

```powershell
# 打开diskpart
diskpart

# 在diskpart中执行：
select vdisk file="E:\docker\DockerDesktopWSL\disk\docker_data.vhdx"
compact vdisk
exit
```

**注意**: 压缩过程可能需要 **10-30 分钟**，请耐心等待。

#### 步骤 4: 验证空间释放

```powershell
Get-PSDrive E | Select-Object @{Name='FreeGB';Expression={[math]::Round($_.Free/1GB,2)}}
```

### 方案二：清理 Docker 数据（如果压缩不够）

如果压缩后空间仍然不足，可以清理 Docker 数据：

```powershell
# 1. 确保Docker已停止
wsl --shutdown

# 2. 清理Docker系统（如果Docker可用）
docker system prune -a --volumes -f

# 3. 清理构建缓存
docker builder prune -a -f

# 4. 手动删除E盘Docker临时文件（谨慎操作）
# 删除构建缓存
Remove-Item "E:\docker\DockerDesktopWSL\data\buildkit" -Recurse -Force -ErrorAction SilentlyContinue

# 删除临时文件
Remove-Item "E:\docker\DockerDesktopWSL\data\tmp" -Recurse -Force -ErrorAction SilentlyContinue
```

### 方案三：移动 Docker 数据到其他盘（长期解决方案）

如果 E 盘空间持续不足，考虑将 Docker 数据移动到其他有更多空间的盘：

1. **在 Docker Desktop 设置中更改数据目录**:

   - 打开 Docker Desktop
   - Settings → Resources → Advanced
   - 更改 "Disk image location" 到其他盘（如 C 盘或 D 盘）

2. **或者使用符号链接**:

   ```powershell
   # 1. 停止Docker和WSL2
   wsl --shutdown

   # 2. 移动数据到其他盘（例如D盘）
   Move-Item "E:\docker" "D:\docker" -Force

   # 3. 创建符号链接
   New-Item -ItemType SymbolicLink -Path "E:\docker" -Target "D:\docker"
   ```

## 📋 完整清理步骤（按顺序执行）

### 1. 停止所有服务

```powershell
# 停止Docker容器
docker-compose down

# 停止Docker进程
Get-Process | Where-Object { $_.ProcessName -like "*docker*" -or $_.ProcessName -like "*com.docker*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 关闭WSL2
wsl --shutdown
Start-Sleep -Seconds 5
```

### 2. 清理 Docker 系统资源

```powershell
# 清理所有未使用的资源
docker system prune -a --volumes -f

# 清理构建缓存
docker builder prune -a -f
```

### 3. 压缩 WSL2 虚拟磁盘（需要管理员权限）

```powershell
# 以管理员身份运行
.\scripts\compact-docker-vhdx.ps1
```

### 4. 清理 E 盘临时文件

```powershell
# 清理Docker临时目录
$tempDirs = @(
    "E:\docker\DockerDesktopWSL\data\buildkit",
    "E:\docker\DockerDesktopWSL\data\tmp",
    "E:\docker\DockerDesktopWSL\data\containers"
)

foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned: $dir"
    }
}
```

### 5. 验证空间释放

```powershell
Get-PSDrive E | Select-Object @{Name='FreeGB';Expression={[math]::Round($_.Free/1GB,2)}}, @{Name='UsedGB';Expression={[math]::Round($_.Used/1GB,2)}}
```

### 6. 重新启动 Docker

```powershell
# 启动Docker Desktop（通过开始菜单或快捷方式）
# 等待Docker完全启动后，验证：
docker ps
```

## ⚠️ 重要提示

1. **备份重要数据**: 在执行任何清理操作前，确保重要数据已备份
2. **管理员权限**: 压缩虚拟磁盘需要管理员权限
3. **时间**: 压缩过程可能需要 10-30 分钟，请耐心等待
4. **最小空间**: 建议至少保留 10GB 可用空间供 Docker 使用
5. **数据卷**: 清理数据卷会删除所有容器数据，请谨慎操作

## 🔍 检查空间使用情况

```powershell
# 检查E盘总空间
Get-PSDrive E | Select-Object Used, Free

# 检查Docker目录大小
Get-ChildItem -Path "E:\docker" -Recurse -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum |
    Select-Object @{Name='SizeGB';Expression={[math]::Round($_.Sum/1GB,2)}}

# 检查虚拟磁盘文件大小
Get-Item "E:\docker\DockerDesktopWSL\disk\docker_data.vhdx" |
    Select-Object @{Name='SizeGB';Expression={[math]::Round($_.Length/1GB,2)}}
```

## 🆘 如果仍然无法启动

如果清理后 Docker 仍然无法启动：

1. **检查空间**: 确保 E 盘至少有 10GB 可用空间
2. **检查 WSL2**: 运行 `wsl --list --verbose` 检查 WSL2 状态
3. **重置 Docker**: 考虑重置 Docker Desktop 到默认设置
4. **重新安装**: 作为最后手段，可以完全卸载并重新安装 Docker Desktop

## 📝 预防措施

1. **定期清理**: 每周运行一次 `docker system prune -a --volumes -f`
2. **监控空间**: 定期检查 E 盘可用空间
3. **限制资源**: 在 Docker Desktop 设置中限制磁盘使用
4. **自动清理**: 启用 Docker Desktop 的自动清理功能

## 🔗 相关脚本

- `scripts/compact-docker-vhdx.ps1` - 压缩 WSL2 虚拟磁盘
- `scripts/emergency-cleanup-e-drive.ps1` - 紧急清理脚本
- `scripts/cleanup-docker-e-drive.ps1` - E 盘 Docker 清理脚本

