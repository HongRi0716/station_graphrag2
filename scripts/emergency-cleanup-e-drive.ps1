# Emergency cleanup for E drive when Docker fills it up
# This script will free up space on E drive by cleaning Docker resources

param(
    [switch]$Help,
    [switch]$Force,
    [switch]$CompactWSL2
)

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Host @"
E盘Docker紧急清理脚本

用法: .\scripts\emergency-cleanup-e-drive.ps1 [选项]

选项:
    -Help          显示此帮助信息
    -Force         强制执行，不询问确认
    -CompactWSL2   压缩WSL2虚拟磁盘（需要管理员权限）

示例:
    .\scripts\emergency-cleanup-e-drive.ps1              # 标准清理
    .\scripts\emergency-cleanup-e-drive.ps1 -Force       # 强制清理
    .\scripts\emergency-cleanup-e-drive.ps1 -CompactWSL2 # 包含WSL2压缩

"@
}

# 检查E盘空间
function Get-EDriveSpace {
    $drive = Get-PSDrive E -ErrorAction SilentlyContinue
    if (-not $drive) {
        Write-Error "E盘未找到！"
        return $null
    }
    
    $usedGB = [math]::Round($drive.Used / 1GB, 2)
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    $totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
    
    return @{
        Used = $usedGB
        Free = $freeGB
        Total = $totalGB
    }
}

# 停止Docker进程
function Stop-DockerProcesses {
    Write-Info "停止Docker进程..."
    
    $processNames = @(
        "Docker Desktop",
        "com.docker.backend",
        "com.docker.proxy",
        "com.docker.service",
        "com.docker.build",
        "containerd",
        "dockerd",
        "vpnkit"
    )
    
    $stopped = 0
    foreach ($procName in $processNames) {
        $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue
        if ($processes) {
            foreach ($proc in $processes) {
                try {
                    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                    Write-Host "  已停止: $($proc.ProcessName) (PID: $($proc.Id))"
                    $stopped++
                } catch {
                    Write-Warning "  无法停止: $($proc.ProcessName) (PID: $($proc.Id))"
                }
            }
        }
    }
    
    if ($stopped -eq 0) {
        Write-Info "没有发现需要停止的进程"
    } else {
        Write-Success "已停止 $stopped 个进程"
    }
    
    Start-Sleep -Seconds 3
}

# 关闭WSL2
function Stop-WSL2 {
    Write-Info "关闭WSL2..."
    try {
        wsl --shutdown 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Success "WSL2已关闭"
    } catch {
        Write-Warning "关闭WSL2时出错: $_"
    }
}

# 清理Docker系统资源
function Clean-DockerSystem {
    Write-Info "清理Docker系统资源..."
    
    try {
        # 检查Docker是否可用
        docker ps 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Docker不可用，跳过系统清理"
            return
        }
        
        Write-Info "  清理未使用的镜像..."
        docker image prune -a -f 2>&1 | Out-Null
        
        Write-Info "  清理停止的容器..."
        docker container prune -f 2>&1 | Out-Null
        
        Write-Info "  清理未使用的网络..."
        docker network prune -f 2>&1 | Out-Null
        
        Write-Info "  清理未使用的卷..."
        docker volume prune -f 2>&1 | Out-Null
        
        Write-Info "  清理构建缓存..."
        docker builder prune -a -f 2>&1 | Out-Null
        
        Write-Success "Docker系统清理完成"
    } catch {
        Write-Warning "清理Docker系统时出错: $_"
    }
}

# 清理E盘Docker目录
function Clean-EDockerDirectory {
    Write-Info "清理E盘Docker目录..."
    
    $dockerPath = "E:\docker"
    if (-not (Test-Path $dockerPath)) {
        Write-Info "未找到E:\docker目录"
        return
    }
    
    # 检查各个子目录
    $subDirs = @("buildkit", "containers", "image", "network", "overlay2", "tmp", "volumes")
    
    foreach ($subDir in $subDirs) {
        $fullPath = Join-Path $dockerPath $subDir
        if (Test-Path $fullPath) {
            $size = (Get-ChildItem $fullPath -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
            $sizeGB = [math]::Round($size, 2)
            
            if ($sizeGB -gt 0.1) {
                Write-Info "  清理: $subDir ($sizeGB GB)"
                try {
                    Remove-Item $fullPath -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Success "  已清理: $subDir"
                } catch {
                    Write-Warning "  无法清理: $subDir - $_"
                }
            }
        }
    }
}

# 压缩WSL2虚拟磁盘
function Compact-WSL2Disk {
    if (-not (Test-Administrator)) {
        Write-Warning "压缩WSL2磁盘需要管理员权限！"
        Write-Info "请以管理员身份运行此脚本"
        return $false
    }
    
    Write-Info "查找WSL2虚拟磁盘文件..."
    
    # 可能的WSL2磁盘文件位置
    $vhdxPaths = @(
        "E:\docker\DockerDesktopWSL\data\ext4.vhdx",
        "E:\docker\DockerDesktopWSL\ext4.vhdx",
        "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx"
    )
    
    $vhdxPath = $null
    foreach ($path in $vhdxPaths) {
        if (Test-Path $path) {
            $vhdxPath = $path
            break
        }
    }
    
    if (-not $vhdxPath) {
        Write-Warning "未找到WSL2虚拟磁盘文件"
        return $false
    }
    
    Write-Info "找到WSL2磁盘文件: $vhdxPath"
    
    $fileSize = (Get-Item $vhdxPath).Length / 1GB
    Write-Host "  当前大小: $([math]::Round($fileSize, 2)) GB" -ForegroundColor Yellow
    
    Write-Warning "压缩WSL2磁盘可能需要较长时间（10-30分钟）"
    
    if (-not $Force) {
        $response = Read-Host "是否继续压缩？[y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "跳过WSL2压缩"
            return $false
        }
    }
    
    # 确保WSL2已关闭
    Stop-WSL2
    
    Write-Info "开始压缩WSL2磁盘..."
    
    try {
        $diskpartScript = @"
select vdisk file="$vhdxPath"
compact vdisk
exit
"@
        
        Write-Host "  正在压缩，请耐心等待..." -ForegroundColor Yellow
        $diskpartScript | diskpart | Out-Null
        
        $newSize = (Get-Item $vhdxPath).Length / 1GB
        $saved = $fileSize - $newSize
        
        Write-Success "压缩完成！"
        Write-Host "  新大小: $([math]::Round($newSize, 2)) GB" -ForegroundColor Green
        Write-Host "  释放空间: $([math]::Round($saved, 2)) GB" -ForegroundColor Green
        
        return $true
    } catch {
        Write-Error "压缩失败: $_"
        return $false
    }
}

# 检查是否为管理员
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 主清理函数
function Start-EmergencyCleanup {
    Write-Host "=== E盘Docker紧急清理 ===" -ForegroundColor Cyan
    Write-Host ""
    
    # 检查E盘空间
    $space = Get-EDriveSpace
    if (-not $space) {
        return
    }
    
    Write-Info "E盘空间状态:"
    Write-Host "  总容量: $($space.Total) GB"
    Write-Host "  已使用: $($space.Used) GB"
    Write-Host "  可用: $($space.Free) GB" -ForegroundColor $(if ($space.Free -lt 5) { "Red" } else { "Green" })
    Write-Host ""
    
    if ($space.Free -lt 1) {
        Write-Error "E盘空间严重不足！必须立即清理！"
    } elseif ($space.Free -lt 5) {
        Write-Warning "E盘空间不足，建议清理"
    }
    
    if (-not $Force) {
        $response = Read-Host "这将清理Docker资源以释放E盘空间。继续吗？[y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "操作已取消"
            return
        }
        Write-Host ""
    }
    
    # 步骤1: 停止Docker
    Stop-DockerProcesses
    Write-Host ""
    
    # 步骤2: 关闭WSL2
    Stop-WSL2
    Write-Host ""
    
    # 步骤3: 清理Docker系统（如果Docker可用）
    Clean-DockerSystem
    Write-Host ""
    
    # 步骤4: 清理E盘Docker目录
    Clean-EDockerDirectory
    Write-Host ""
    
    # 步骤5: 压缩WSL2磁盘（如果指定）
    if ($CompactWSL2) {
        Compact-WSL2Disk
        Write-Host ""
    }
    
    # 检查清理后的空间
    Start-Sleep -Seconds 2
    $newSpace = Get-EDriveSpace
    if ($newSpace) {
        $freed = $newSpace.Free - $space.Free
        Write-Host "=== 清理完成 ===" -ForegroundColor Cyan
        Write-Host "释放空间: $([math]::Round($freed, 2)) GB" -ForegroundColor Green
        Write-Host "当前可用: $($newSpace.Free) GB" -ForegroundColor Green
        Write-Host ""
        
        if ($newSpace.Free -lt 10) {
            Write-Warning "建议至少保留10GB可用空间"
            if (-not $CompactWSL2) {
                Write-Info "可以运行 -CompactWSL2 选项来压缩WSL2磁盘释放更多空间"
            }
        }
    }
    
    Write-Host "下一步操作:" -ForegroundColor Cyan
    Write-Host "  1. 重新启动Docker Desktop"
    Write-Host "  2. 如果仍然空间不足，考虑:"
    Write-Host "     - 移动Docker数据到其他盘"
    Write-Host "     - 删除不需要的容器和数据卷"
    Write-Host "     - 运行: .\scripts\emergency-cleanup-e-drive.ps1 -CompactWSL2"
    Write-Host ""
}

# 主函数
if ($Help) {
    Show-Help
    exit 0
}

Start-EmergencyCleanup


