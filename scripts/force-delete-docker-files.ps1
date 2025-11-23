# 强制删除Docker相关文件的脚本
# 用于解决文件被占用无法删除的问题

param(
    [string]$Path,
    [switch]$Help,
    [switch]$Force,
    [switch]$All
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
强制删除Docker相关文件

用法: .\scripts\force-delete-docker-files.ps1 [选项]

选项:
    -Path <路径>    要删除的文件或目录路径
    -All             删除所有Docker临时文件（谨慎使用）
    -Force           强制执行，不询问确认
    -Help            显示此帮助信息

示例:
    .\scripts\force-delete-docker-files.ps1 -Path "E:\docker\DockerDesktopWSL\data\buildkit"
    .\scripts\force-delete-docker-files.ps1 -All -Force
    .\scripts\force-delete-docker-files.ps1 -Help

"@
}

# 停止Docker相关进程
function Stop-DockerProcesses {
    Write-Info "Stopping Docker processes..."
    
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
                    Write-Host "  Stopped: $($proc.ProcessName) (PID: $($proc.Id))"
                    $stopped++
                } catch {
                    Write-Warning "  Failed to stop: $($proc.ProcessName)"
                }
            }
        }
    }
    
    if ($stopped -eq 0) {
        Write-Info "No Docker processes found"
    } else {
        Write-Success "Stopped $stopped processes"
    }
    
    Start-Sleep -Seconds 3
}

# 关闭WSL2
function Stop-WSL2 {
    Write-Info "Shutting down WSL2..."
    try {
        wsl --shutdown 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Success "WSL2 shutdown complete"
    } catch {
        Write-Warning "Failed to shutdown WSL2: $_"
    }
}

# 强制删除文件或目录
function Remove-ItemForcibly {
    param(
        [string]$ItemPath,
        [switch]$Confirm
    )
    
    if (-not (Test-Path $ItemPath)) {
        Write-Warning "Path does not exist: $ItemPath"
        return $false
    }
    
    $item = Get-Item $ItemPath -ErrorAction SilentlyContinue
    if (-not $item) {
        Write-Warning "Cannot access: $ItemPath"
        return $false
    }
    
    $itemType = if ($item.PSIsContainer) { "Directory" } else { "File" }
    $sizeGB = if ($item.PSIsContainer) {
        (Get-ChildItem $ItemPath -Recurse -ErrorAction SilentlyContinue | 
         Measure-Object -Property Length -Sum).Sum / 1GB
    } else {
        $item.Length / 1GB
    }
    
    Write-Info "Target: $ItemPath"
    Write-Info "Type: $itemType"
    if ($sizeGB -gt 0) {
        Write-Info "Size: $([math]::Round($sizeGB, 2)) GB"
    }
    Write-Host ""
    
    if (-not $Force -and -not $Confirm) {
        $response = Read-Host "Are you sure you want to delete this? [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "Operation cancelled"
            return $false
        }
    }
    
    # 方法1: 标准删除
    Write-Info "Attempting standard deletion..."
    try {
        Remove-Item $ItemPath -Recurse -Force -ErrorAction Stop
        Write-Success "Successfully deleted: $ItemPath"
        return $true
    } catch {
        Write-Warning "Standard deletion failed: $_"
    }
    
    # 方法2: 使用robocopy（空目录覆盖）
    Write-Info "Trying alternative method (robocopy)..."
    try {
        $emptyDir = New-TemporaryFile
        Remove-Item $emptyDir -Force
        New-Item -ItemType Directory -Path $emptyDir | Out-Null
        
        robocopy $emptyDir $ItemPath /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS | Out-Null
        Remove-Item $ItemPath -Force -ErrorAction SilentlyContinue
        Remove-Item $emptyDir -Force -ErrorAction SilentlyContinue
        
        if (-not (Test-Path $ItemPath)) {
            Write-Success "Successfully deleted using robocopy method"
            return $true
        }
    } catch {
        Write-Warning "Robocopy method failed: $_"
    }
    
    # 方法3: 使用takeown和icacls（需要管理员权限）
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdmin) {
        Write-Info "Trying administrator method (takeown + icacls)..."
        try {
            # 获取所有权
            takeown /F $ItemPath /R /D Y 2>&1 | Out-Null
            
            # 设置完全控制权限
            icacls $ItemPath /grant "${env:USERNAME}:F" /T 2>&1 | Out-Null
            
            # 再次尝试删除
            Remove-Item $ItemPath -Recurse -Force -ErrorAction Stop
            Write-Success "Successfully deleted using administrator method"
            return $true
        } catch {
            Write-Warning "Administrator method failed: $_"
        }
    }
    
    Write-Error "All deletion methods failed. File may be locked by system."
    Write-Host ""
    Write-Host "Suggestions:" -ForegroundColor Yellow
    Write-Host "  1. Restart your computer and try again" -ForegroundColor White
    Write-Host "  2. Boot into Safe Mode and delete" -ForegroundColor White
    Write-Host "  3. Check if file is locked by another process" -ForegroundColor White
    Write-Host "  4. Use Unlocker tool or Process Explorer" -ForegroundColor White
    
    return $false
}

# 删除所有Docker临时文件
function Remove-AllDockerTempFiles {
    Write-Warning "This will delete all Docker temporary files!"
    Write-Warning "This includes:"
    Write-Host "  - Build cache" -ForegroundColor Yellow
    Write-Host "  - Temporary files" -ForegroundColor Yellow
    Write-Host "  - Container data (stopped containers)" -ForegroundColor Yellow
    Write-Host ""
    Write-Warning "This will NOT delete:"
    Write-Host "  - Virtual disk file (docker_data.vhdx)" -ForegroundColor Green
    Write-Host "  - Data volumes (if accessible)" -ForegroundColor Green
    Write-Host ""
    
    if (-not $Force) {
        $response = Read-Host "Continue? [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "Operation cancelled"
            return
        }
    }
    
    $dockerBasePath = "E:\docker\DockerDesktopWSL\data"
    if (-not (Test-Path $dockerBasePath)) {
        Write-Warning "Docker data path not found: $dockerBasePath"
        return
    }
    
    $tempDirs = @(
        "buildkit",
        "tmp",
        "containers",
        "image",
        "network"
    )
    
    foreach ($dirName in $tempDirs) {
        $dirPath = Join-Path $dockerBasePath $dirName
        if (Test-Path $dirPath) {
            Write-Info "Deleting: $dirPath"
            Remove-ItemForcibly -ItemPath $dirPath -Confirm
            Write-Host ""
        }
    }
    
    Write-Success "Cleanup complete"
}

# 主函数
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    # 停止Docker和WSL2
    Stop-DockerProcesses
    Write-Host ""
    Stop-WSL2
    Write-Host ""
    
    if ($All) {
        Remove-AllDockerTempFiles
    } elseif ($Path) {
        Remove-ItemForcibly -ItemPath $Path
    } else {
        Write-Error "Please specify -Path or -All option"
        Write-Host ""
        Show-Help
    }
}

# 运行主函数
Main


