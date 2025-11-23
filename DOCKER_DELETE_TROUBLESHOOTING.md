# Docker 文件无法删除问题解决指南

## 🚨 常见无法删除的情况

### 情况 1: 虚拟磁盘文件无法删除（正常）

**问题**: `docker_data.vhdx` 文件无法删除

**原因**: 这是正常的！**不应该直接删除**这个文件，因为：

- 它包含所有 Docker 数据
- 删除会导致数据丢失
- 应该通过压缩来减小大小

**解决方案**: 压缩而不是删除

```powershell
# 以管理员身份运行
.\scripts\compact-docker-vhdx.ps1
```

### 情况 2: 文件被 Docker 进程占用

**问题**: 删除文件时提示"文件正在使用中"

**解决方案**:

```powershell
# 1. 强制停止所有Docker进程
Get-Process | Where-Object {
    $_.ProcessName -like "*docker*" -or
    $_.ProcessName -like "*com.docker*" -or
    $_.ProcessName -like "*containerd*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. 关闭WSL2
wsl --shutdown
Start-Sleep -Seconds 5

# 3. 再次尝试删除
```

### 情况 3: 权限不足

**问题**: 删除时提示"拒绝访问"或"需要管理员权限"

**解决方案**:

```powershell
# 1. 以管理员身份打开PowerShell
# 2. 使用管理员权限删除
Remove-Item "路径" -Recurse -Force -ErrorAction Stop
```

### 情况 4: 文件被其他程序占用

**问题**: 文件被其他程序（如杀毒软件、文件管理器）占用

**解决方案**:

```powershell
# 1. 关闭可能占用文件的程序
#    - 文件资源管理器
#    - 杀毒软件实时保护
#    - 其他可能访问该文件的程序

# 2. 使用PowerShell强制删除
Remove-Item "路径" -Recurse -Force
```

## 🛠️ 强制删除工具脚本

创建一个强制删除脚本：

```powershell
# 强制删除Docker相关文件
function Remove-DockerFilesForcibly {
    param(
        [string]$Path,
        [switch]$Confirm
    )

    # 1. 停止所有相关进程
    Write-Host "Stopping Docker processes..." -ForegroundColor Blue
    Get-Process | Where-Object {
        $_.ProcessName -like "*docker*" -or
        $_.ProcessName -like "*com.docker*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    # 2. 关闭WSL2
    Write-Host "Shutting down WSL2..." -ForegroundColor Blue
    wsl --shutdown 2>&1 | Out-Null
    Start-Sleep -Seconds 5

    # 3. 确认删除
    if (-not $Confirm) {
        $response = Read-Host "Are you sure you want to delete: $Path ? [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            return
        }
    }

    # 4. 尝试删除
    Write-Host "Attempting to delete: $Path" -ForegroundColor Blue
    try {
        if (Test-Path $Path) {
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
            Write-Host "Successfully deleted: $Path" -ForegroundColor Green
        } else {
            Write-Host "Path does not exist: $Path" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Failed to delete: $_" -ForegroundColor Red

        # 5. 如果仍然失败，尝试使用robocopy（空目录覆盖）
        Write-Host "Trying alternative method..." -ForegroundColor Yellow
        try {
            $emptyDir = New-TemporaryFile
            Remove-Item $emptyDir
            New-Item -ItemType Directory -Path $emptyDir | Out-Null

            robocopy $emptyDir $Path /MIR /R:0 /W:0 | Out-Null
            Remove-Item $Path -Force -ErrorAction SilentlyContinue
            Remove-Item $emptyDir -Force -ErrorAction SilentlyContinue

            Write-Host "Successfully deleted using alternative method" -ForegroundColor Green
        } catch {
            Write-Host "All deletion methods failed. File may be locked by system." -ForegroundColor Red
            Write-Host "Try:" -ForegroundColor Yellow
            Write-Host "  1. Restart your computer" -ForegroundColor White
            Write-Host "  2. Boot into Safe Mode and delete" -ForegroundColor White
            Write-Host "  3. Use Unlocker tool" -ForegroundColor White
        }
    }
}
```

## 🔧 具体删除场景

### 场景 1: 删除 Docker 镜像（Docker 未运行）

如果 Docker 未运行，无法使用`docker rmi`命令，需要手动删除：

```powershell
# ⚠️ 警告：这会删除所有Docker数据！
# 1. 确保Docker和WSL2已完全关闭
wsl --shutdown

# 2. 删除Docker数据目录（谨慎操作）
# 这会删除所有镜像、容器、数据卷
Remove-Item "E:\docker\DockerDesktopWSL" -Recurse -Force
```

### 场景 2: 删除特定目录

```powershell
# 删除构建缓存
Remove-Item "E:\docker\DockerDesktopWSL\data\buildkit" -Recurse -Force -ErrorAction SilentlyContinue

# 删除临时文件
Remove-Item "E:\docker\DockerDesktopWSL\data\tmp" -Recurse -Force -ErrorAction SilentlyContinue

# 删除容器数据（谨慎！）
Remove-Item "E:\docker\DockerDesktopWSL\data\containers" -Recurse -Force -ErrorAction SilentlyContinue
```

### 场景 3: 删除虚拟磁盘文件（不推荐）

```powershell
# ⚠️ 警告：这会删除所有Docker数据！
# 只有在确定要完全重置Docker时才这样做

# 1. 确保Docker和WSL2完全关闭
wsl --shutdown
Start-Sleep -Seconds 10

# 2. 删除虚拟磁盘文件
Remove-Item "E:\docker\DockerDesktopWSL\disk\docker_data.vhdx" -Force

# 3. 重新启动Docker Desktop会创建新的虚拟磁盘
```

## 🔍 诊断无法删除的原因

### 检查文件是否被占用

```powershell
# 使用Handle工具（需要下载Sysinternals Suite）
# https://docs.microsoft.com/en-us/sysinternals/downloads/handle

# 或者使用PowerShell检查
function Get-FileLockingProcess {
    param([string]$FilePath)

    $processes = Get-Process | Where-Object {
        $_.Modules | Where-Object { $_.FileName -like "*$FilePath*" }
    }

    if ($processes) {
        Write-Host "File is locked by:" -ForegroundColor Red
        $processes | Select-Object ProcessName, Id, Path
    } else {
        Write-Host "File is not locked" -ForegroundColor Green
    }
}

# 使用
Get-FileLockingProcess "E:\docker\DockerDesktopWSL\disk\docker_data.vhdx"
```

### 检查文件权限

```powershell
# 检查文件权限
$file = Get-Item "E:\docker\DockerDesktopWSL\disk\docker_data.vhdx"
$acl = Get-Acl $file.FullName
$acl.Access | Format-Table IdentityReference, FileSystemRights, AccessControlType
```

### 检查磁盘空间

```powershell
# 如果目标盘空间不足，可能无法删除到回收站
Get-PSDrive E | Select-Object Free, Used
```

## 💡 推荐的安全删除方法

### 方法 1: 使用 Docker 命令删除（推荐）

```powershell
# 1. 启动Docker Desktop
# 2. 等待Docker完全启动
# 3. 使用Docker命令删除

docker system prune -a --volumes -f
docker builder prune -a -f
```

### 方法 2: 压缩虚拟磁盘（推荐用于释放空间）

```powershell
# 压缩而不是删除，可以释放空间但保留数据
.\scripts\compact-docker-vhdx.ps1
```

### 方法 3: 重置 Docker Desktop（最后手段）

如果所有方法都失败：

1. 打开 Docker Desktop
2. Settings → Troubleshoot → Reset to factory defaults
3. 这会删除所有 Docker 数据并重新开始

## 🆘 紧急情况处理

### 如果 E 盘空间完全满了，无法启动 Docker

```powershell
# 1. 以管理员身份运行PowerShell

# 2. 强制关闭所有Docker进程
Get-Process | Where-Object { $_.ProcessName -like "*docker*" } | Stop-Process -Force

# 3. 关闭WSL2
wsl --shutdown

# 4. 删除临时文件（不删除虚拟磁盘）
$tempDirs = @(
    "E:\docker\DockerDesktopWSL\data\buildkit",
    "E:\docker\DockerDesktopWSL\data\tmp"
)
foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 5. 压缩虚拟磁盘
.\scripts\compact-docker-vhdx.ps1
```

## 📋 删除前检查清单

在删除任何 Docker 文件前，请确认：

- [ ] Docker Desktop 已完全关闭
- [ ] WSL2 已关闭（`wsl --shutdown`）
- [ ] 没有 Docker 相关进程运行
- [ ] 已备份重要数据（如果需要）
- [ ] 有足够的空间（如果删除到回收站）
- [ ] 有管理员权限（如果需要）

## 🔗 相关文档

- [E 盘空间紧急修复指南](E_DRIVE_SPACE_EMERGENCY_FIX.md)
- [Docker 清理指南](DOCKER_CLEANUP_GUIDE.md)
- [为什么 Docker 占用这么大空间](WHY_DOCKER_USES_SO_MUCH_SPACE.md)
