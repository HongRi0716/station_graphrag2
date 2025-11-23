# Docker Containerd Bus Error 修复脚本
# 用于修复 "containerd failed: signal: bus error (core dumped)" 错误

param(
    [switch]$Help,
    [switch]$Force,
    [switch]$Diagnose,
    [switch]$ResetWSL2,
    [switch]$Reinstall
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
Docker Containerd Bus Error 修复脚本

用法: .\scripts\fix-containerd-bus-error.ps1 [选项]

选项:
    -Help              显示此帮助信息
    -Diagnose          只诊断问题，不执行修复
    -Force             强制执行，不询问确认
    -ResetWSL2         重置 WSL2（会删除数据，谨慎使用）
    -Reinstall         完全重新安装 Docker（最后手段）

示例:
    .\scripts\fix-containerd-bus-error.ps1 -Diagnose    # 诊断问题
    .\scripts\fix-containerd-bus-error.ps1              # 标准修复
    .\scripts\fix-containerd-bus-error.ps1 -Force       # 强制修复
    .\scripts\fix-containerd-bus-error.ps1 -ResetWSL2   # 重置 WSL2

"@
}

# 检查是否为管理员
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 诊断问题
function Diagnose-BusError {
    Write-Info "开始诊断 Containerd Bus Error..."
    Write-Host ""
    
    $issues = @()
    
    # 1. 检查 Docker 进程
    Write-Info "1. 检查 Docker/Containerd 进程..."
    $dockerProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*docker*" -or 
        $_.ProcessName -like "*containerd*" -or
        $_.ProcessName -like "*com.docker*"
    }
    if ($dockerProcesses) {
        Write-Warning "发现 Docker 相关进程正在运行:"
        $dockerProcesses | ForEach-Object { 
            Write-Host "  - $($_.ProcessName) (PID: $($_.Id))" 
        }
        $issues += "Docker 进程未完全关闭"
    } else {
        Write-Success "No Docker processes found"
    }
    Write-Host ""
    
    # 2. 检查内存
    Write-Info "2. 检查系统内存..."
    $os = Get-CimInstance Win32_OperatingSystem
    $totalMemory = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeMemory = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $usedMemory = $totalMemory - $freeMemory
    $memoryPercent = [math]::Round(($usedMemory / $totalMemory) * 100, 2)
    
    Write-Host "  总内存: $totalMemory GB"
    Write-Host "  已使用: $usedMemory GB ($memoryPercent%)"
    Write-Host "  可用: $freeMemory GB"
    
    if ($freeMemory -lt 2) {
        Write-Error "可用内存不足！少于 2GB"
        $issues += "内存不足 (Available: $freeMemory GB)"
    } elseif ($freeMemory -lt 4) {
        Write-Warning "可用内存较低 (Available: $freeMemory GB)"
    } else {
        Write-Success "内存充足"
    }
    Write-Host ""
    
    # 3. 检查磁盘空间
    Write-Info "3. 检查磁盘空间..."
    $drives = Get-PSDrive -PSProvider FileSystem
    foreach ($drive in $drives) {
        $freeGB = [math]::Round($drive.Free / 1GB, 2)
        $usedGB = [math]::Round($drive.Used / 1GB, 2)
        $totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
        
        Write-Host "  $($drive.Name): 可用 $freeGB GB / 总计 $totalGB GB"
        
        if ($freeGB -lt 5) {
            Write-Error "  $($drive.Name) 盘空间不足！少于 5GB"
            $issues += "$($drive.Name) 盘空间不足 (Available: $freeGB GB)"
        } elseif ($freeGB -lt 10) {
            Write-Warning "  $($drive.Name) 盘空间较低 (Available: $freeGB GB)"
        }
    }
    Write-Host ""
    
    # 4. 检查 WSL2 状态
    Write-Info "4. 检查 WSL2 状态..."
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
    
    # 5. 检查 Docker 日志
    Write-Info "5. 检查 Docker 日志..."
    $logPath = "$env:LOCALAPPDATA\Docker\log.txt"
    if (Test-Path $logPath) {
        $logContent = Get-Content $logPath -Tail 20 -ErrorAction SilentlyContinue
        if ($logContent) {
            Write-Host "  最近的错误日志:"
            $logContent | Select-String -Pattern "error|bus|containerd|failed" -CaseSensitive:$false | 
                ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        }
    } else {
        Write-Info "  未找到日志文件"
    }
    Write-Host ""
    
    # 6. 检查系统事件日志
    Write-Info "6. 检查系统事件日志..."
    try {
        $events = Get-EventLog -LogName System -EntryType Error -Newest 10 -ErrorAction SilentlyContinue | 
            Where-Object { $_.Source -like "*docker*" -or $_.Source -like "*containerd*" }
        if ($events) {
            Write-Warning "发现 Docker 相关系统错误:"
            $events | ForEach-Object { 
                Write-Host "  [$($_.TimeGenerated)] $($_.Source): $($_.Message.Substring(0, [Math]::Min(100, $_.Message.Length)))..." 
            }
            $issues += "系统事件日志中发现 Docker 错误"
        } else {
            Write-Success "未发现相关系统错误"
        }
    } catch {
        Write-Info "无法访问系统事件日志（可能需要管理员权限）"
    }
    Write-Host ""
    
    # 总结
    Write-Host "=== 诊断总结 ===" -ForegroundColor Cyan
    if ($issues.Count -eq 0) {
        Write-Success "未发现明显问题，可能是临时性错误"
        Write-Info "建议：尝试重启 Docker Desktop"
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
        "containerd",
        "dockerd",
        "docker",
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

# 关闭 WSL2
function Stop-WSL2 {
    Write-Info "关闭 WSL2..."
    try {
        wsl --shutdown 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Success "WSL2 已关闭"
    } catch {
        Write-Warning "关闭 WSL2 时出错: $_"
    }
}

# 清理 Docker 系统
function Clean-DockerSystem {
    Write-Info "清理 Docker 系统..."
    
    try {
        # 检查 Docker 是否可用
        $dockerAvailable = $false
        try {
            docker ps 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $dockerAvailable = $true
            }
        } catch {
            $dockerAvailable = $false
        }
        
        if ($dockerAvailable) {
            Write-Info "  清理未使用的容器、网络、镜像..."
            docker system prune -a --volumes -f 2>&1 | Out-Null
            Write-Success "Docker 系统清理完成"
        } else {
            Write-Info "  Docker 不可用，跳过系统清理"
        }
    } catch {
        Write-Warning "清理 Docker 系统时出错: $_"
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
                Write-Host "  已清理: $path ($count 个文件)"
                $cleaned += $count
            } catch {
                Write-Warning "  无法清理: $path"
            }
        }
    }
    
    if ($cleaned -eq 0) {
        Write-Info "未找到临时文件"
    } else {
        Write-Success "已清理 $cleaned 个临时文件"
    }
}

# 重置 WSL2
function Reset-WSL2Distributions {
    if (-not (Test-Administrator)) {
        Write-Error "重置 WSL2 需要管理员权限！"
        return $false
    }
    
    Write-Warning "⚠️  警告：这将删除 WSL2 中的所有 Docker 数据！"
    
    if (-not $Force) {
        $response = Read-Host "确定要继续吗？这将删除所有 Docker 容器和数据卷 [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "操作已取消"
            return $false
        }
    }
    
    Write-Info "重置 WSL2 Docker 分发版..."
    
    try {
        Stop-WSL2
        
        $distributions = @("docker-desktop", "docker-desktop-data")
        foreach ($dist in $distributions) {
            Write-Info "  注销分发版: $dist"
            wsl --unregister $dist 2>&1 | Out-Null
        }
        
        Write-Success "WSL2 分发版已重置"
        Write-Info "重新启动 Docker Desktop 时会自动重新创建"
        return $true
    } catch {
        Write-Error "重置 WSL2 失败: $_"
        return $false
    }
}

# 标准修复流程
function Fix-BusError {
    Write-Info "开始修复 Containerd Bus Error..."
    Write-Host ""
    
    if (-not $Force) {
        $response = Read-Host "这将关闭所有 Docker 进程并清理临时文件。继续吗？ [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "操作已取消"
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
    
    # 步骤 4: 清理 Docker 系统（如果可用）
    Clean-DockerSystem
    Write-Host ""
    
    # 步骤 5: 如果指定了 ResetWSL2，执行重置
    if ($ResetWSL2) {
        Reset-WSL2Distributions
        Write-Host ""
    }
    
    Write-Success "修复完成！"
    Write-Host ""
    Write-Info "下一步操作:"
    Write-Host "  1. 重新启动 Docker Desktop"
    Write-Host "  2. 等待完全启动（可能需要几分钟）"
    Write-Host "  3. 如果仍然失败，请尝试:"
    Write-Host "     - 运行诊断: .\scripts\fix-containerd-bus-error.ps1 -Diagnose"
    Write-Host "     - 重置 WSL2: .\scripts\fix-containerd-bus-error.ps1 -ResetWSL2"
    Write-Host "     - 查看详细指南: DOCKER_CONTAINERD_BUS_ERROR_FIX.md"
    Write-Host ""
}

# 主函数
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    if ($Diagnose) {
        Diagnose-BusError
        return
    }
    
    # 先诊断
    Write-Info "先进行问题诊断..."
    Write-Host ""
    $issues = Diagnose-BusError
    
    if (-not $Force) {
        Write-Host ""
        Write-Host "按任意键继续修复，或 Ctrl+C 取消..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Write-Host ""
    }
    
    # 执行修复
    Fix-BusError
}

# 运行主函数
Main

