# Docker Desktop 启动问题修复脚本
# 用于解决 Docker Desktop 卡在启动界面的问题

param(
    [switch]$Help,
    [switch]$Force,
    [switch]$Diagnose
)

# 颜色函数
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

# 显示帮助
function Show-Help {
    Write-Host @"
Docker Desktop 启动问题修复脚本

用法: .\scripts\fix-docker-startup.ps1 [选项]

选项:
    -Help              显示此帮助信息
    -Diagnose          只诊断问题，不执行修复
    -Force             强制执行，不询问确认

示例:
    .\scripts\fix-docker-startup.ps1 -Diagnose    # 诊断问题
    .\scripts\fix-docker-startup.ps1              # 修复启动问题
    .\scripts\fix-docker-startup.ps1 -Force       # 强制修复

"@
}

# 检查是否为管理员
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 诊断问题
function Diagnose-StartupIssue {
    Write-Info "开始诊断 Docker Desktop 启动问题..."
    Write-Host ""
    
    $issues = @()
    
    # 1. 检查 Docker 进程
    Write-Info "1. 检查 Docker 进程..."
    $dockerProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" -or $_.ProcessName -like "*com.docker*" }
    if ($dockerProcesses) {
        Write-Warning "发现 Docker 相关进程正在运行:"
        $dockerProcesses | ForEach-Object { Write-Host "  - $($_.ProcessName) (PID: $($_.Id))" }
        $issues += "Docker 进程未完全关闭"
    } else {
        Write-Success "No Docker processes found"
    }
    Write-Host ""
    
    # 2. 检查磁盘空间
    Write-Info "2. 检查磁盘空间..."
    $drive = Get-PSDrive C
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    $usedGB = [math]::Round($drive.Used / 1GB, 2)
    
    Write-Host "  C: Drive usage: $usedGB GB / $([math]::Round(($drive.Used + $drive.Free) / 1GB, 2)) GB"
    Write-Host "  Free space: $freeGB GB"
    
    if ($freeGB -lt 5) {
        Write-Error "Insufficient disk space! Less than 5GB available"
        $issues += "Insufficient disk space (Available: $freeGB GB)"
    } elseif ($freeGB -lt 10) {
        Write-Warning "Low disk space (Available: $freeGB GB), cleanup recommended"
    } else {
        Write-Success "Sufficient disk space"
    }
    Write-Host ""
    
    # 3. 检查 WSL2 状态
    Write-Info "3. 检查 WSL2 状态..."
    try {
        $wslStatus = wsl --list --verbose 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "WSL2 可用"
            Write-Host $wslStatus
        } else {
            Write-Warning "无法获取 WSL2 状态"
            $issues += "WSL2 可能有问题"
        }
    } catch {
        Write-Warning "WSL2 检查失败: $_"
        $issues += "WSL2 检查失败"
    }
    Write-Host ""
    
    # 4. 检查 Docker 数据目录
    Write-Info "4. 检查 Docker 数据目录..."
    $dockerDataPath = "$env:LOCALAPPDATA\Docker"
    if (Test-Path $dockerDataPath) {
        $size = (Get-ChildItem $dockerDataPath -Recurse -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Host "  Docker 数据目录大小: $([math]::Round($size, 2)) GB"
        
        if ($size -gt 50) {
            Write-Warning "Docker 数据目录占用空间较大（$([math]::Round($size, 2)) GB）"
            $issues += "Docker 数据目录占用空间大"
        }
    } else {
        Write-Info "Docker 数据目录不存在（可能是首次安装）"
    }
    Write-Host ""
    
    # 5. 检查 Docker 日志
    Write-Info "5. 检查 Docker 日志位置..."
    $logPaths = @(
        "$env:LOCALAPPDATA\Docker\log.txt",
        "$env:APPDATA\Docker\log.txt",
        "$env:PROGRAMDATA\Docker\log.txt"
    )
    
    $foundLogs = $false
    foreach ($logPath in $logPaths) {
        if (Test-Path $logPath) {
            Write-Host "  找到日志: $logPath"
            $foundLogs = $true
        }
    }
    
    if (-not $foundLogs) {
        Write-Info "  未找到日志文件（可能 Docker 从未成功启动）"
    }
    Write-Host ""
    
    # 总结
    Write-Host "=== 诊断总结 ===" -ForegroundColor Cyan
    if ($issues.Count -eq 0) {
        Write-Success "未发现明显问题"
    } else {
        Write-Warning "发现以下问题:"
        foreach ($issue in $issues) {
            Write-Host "  - $issue" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    
    return $issues
}

# 强制关闭 Docker
function Stop-DockerForcibly {
    Write-Info "强制关闭所有 Docker 相关进程..."
    
    $processNames = @(
        "Docker Desktop",
        "com.docker.backend",
        "com.docker.proxy",
        "com.docker.service",
        "vpnkit",
        "dockerd",
        "docker"
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
    
    # 等待进程完全关闭
    Start-Sleep -Seconds 3
}

# 关闭 WSL2
function Stop-WSL2 {
    Write-Info "关闭 WSL2..."
    try {
        wsl --shutdown 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        Write-Success "WSL2 已关闭"
    } catch {
        Write-Warning "关闭 WSL2 时出错: $_"
    }
}

# 清理 Docker 临时文件
function Clear-DockerTempFiles {
    Write-Info "清理 Docker 临时文件..."
    
    $tempPaths = @(
        "$env:LOCALAPPDATA\Docker\tmp",
        "$env:TEMP\Docker*",
        "$env:LOCALAPPDATA\Temp\Docker*"
    )
    
    $cleaned = 0
    foreach ($path in $tempPaths) {
        if (Test-Path $path) {
            try {
                $items = Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue
                $count = $items.Count
                Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  Cleaned: $path ($count files)"
                $cleaned += $count
            } catch {
                Write-Warning "  无法清理: $path"
            }
        }
    }
    
    if ($cleaned -eq 0) {
        Write-Info "No temporary files found to clean"
    } else {
        Write-Success "Cleaned $cleaned temporary files"
    }
}

# 压缩 WSL2 磁盘
function Compact-WSL2Disk {
    if (-not (Test-Administrator)) {
        Write-Warning "压缩 WSL2 磁盘需要管理员权限，跳过此步骤"
        Write-Info "如需压缩，请以管理员身份运行此脚本"
        return $false
    }
    
    Write-Info "压缩 WSL2 磁盘（这可能需要几分钟）..."
    
    $vhdxPath = "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx"
    
    if (-not (Test-Path $vhdxPath)) {
        Write-Info "未找到 WSL2 磁盘文件: $vhdxPath"
        return $false
    }
    
    Write-Host "  找到磁盘文件: $vhdxPath"
    
    # 获取文件大小
    $fileSize = (Get-Item $vhdxPath).Length / 1GB
    Write-Host "  当前大小: $([math]::Round($fileSize, 2)) GB"
    
    # 关闭 WSL2
    Stop-WSL2
    
    # 压缩磁盘
    try {
        $diskpartScript = @"
select vdisk file="$vhdxPath"
compact vdisk
exit
"@
        
        Write-Host "  Compacting, please wait..."
        $diskpartScript | diskpart | Out-Null
        
        # 获取压缩后的大小
        $newSize = (Get-Item $vhdxPath).Length / 1GB
        $saved = $fileSize - $newSize
        
        Write-Success "Compaction completed!"
        Write-Host "  New size: $([math]::Round($newSize, 2)) GB"
        Write-Host "  Space freed: $([math]::Round($saved, 2)) GB"
        
        return $true
    } catch {
        Write-Error "压缩失败: $_"
        return $false
    }
}

# 重置 Docker 网络
function Reset-DockerNetwork {
    Write-Info "重置 Docker 网络配置..."
    
    $networkConfigPath = "$env:LOCALAPPDATA\Docker\settings.json"
    if (Test-Path $networkConfigPath) {
        try {
            $settings = Get-Content $networkConfigPath -Raw | ConvertFrom-Json
            if ($settings.network) {
                Write-Host "  备份网络配置..."
                Copy-Item $networkConfigPath "$networkConfigPath.backup" -ErrorAction SilentlyContinue
                Write-Success "网络配置已备份"
            }
        } catch {
            Write-Warning "无法读取网络配置: $_"
        }
    }
}

# 主修复函数
function Fix-DockerStartup {
    Write-Info "开始修复 Docker Desktop 启动问题..."
    Write-Host ""
    
    if (-not $Force) {
        $response = Read-Host "This will close all Docker processes and clean temporary files. Continue? [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "Operation cancelled"
            return
        }
    }
    
    Write-Host ""
    
    # 步骤 1: 强制关闭 Docker
    Stop-DockerForcibly
    Write-Host ""
    
    # 步骤 2: 关闭 WSL2
    Stop-WSL2
    Write-Host ""
    
    # 步骤 3: 清理临时文件
    Clear-DockerTempFiles
    Write-Host ""
    
    # 步骤 4: 压缩 WSL2 磁盘（可选，需要管理员权限）
    if (Test-Administrator) {
        $compact = Read-Host "Compact WSL2 disk to free space? [y/N]"
        if ($compact -match "^[Yy]$") {
            Compact-WSL2Disk
            Write-Host ""
        }
    }
    
    # 步骤 5: 重置网络配置（可选）
    Write-Info "修复完成！"
    Write-Host ""
    Write-Info "下一步操作:"
    Write-Host "  1. 重新启动 Docker Desktop"
    Write-Host "  2. 等待完全启动（可能需要几分钟）"
    Write-Host "  3. 如果仍然无法启动，请检查:"
    Write-Host "     - 磁盘空间是否充足（至少 10GB）"
    Write-Host "     - WSL2 是否正常工作: wsl --list --verbose"
    Write-Host "     - Docker Desktop 日志: 设置 → Troubleshoot → View logs"
    Write-Host ""
}

# 主函数
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    if ($Diagnose) {
        Diagnose-StartupIssue
        return
    }
    
    # 先诊断
    Write-Info "先进行问题诊断..."
    Write-Host ""
    $issues = Diagnose-StartupIssue
    
    Write-Host ""
    Write-Host "Press any key to continue fixing, or Ctrl+C to cancel..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Write-Host ""
    
    # 执行修复
    Fix-DockerStartup
}

# 运行主函数
Main

