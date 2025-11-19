# Docker清理脚本 (PowerShell版本)
# 用于清理ApeRAG项目的Docker容器、镜像、卷等资源

param(
    [switch]$Help,
    [switch]$Containers,
    [switch]$Volumes,
    [switch]$Images,
    [switch]$All,
    [switch]$System,
    [switch]$Force,
    [switch]$Status,
    [switch]$Restart,
    [switch]$DiskSpace
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

# 显示帮助信息
function Show-Help {
    Write-Host @"
Docker清理脚本 - ApeRAG项目 (PowerShell版本)

用法: .\scripts\cleanup-docker.ps1 [选项]

选项:
    -Help              显示此帮助信息
    -Containers        只清理容器（保留数据卷）
    -Volumes           清理容器和数据卷（⚠️ 会删除所有数据）
    -Images            清理未使用的镜像
    -All               完全清理（容器、卷、镜像、网络）
    -System            清理系统（容器、网络、镜像，不包括卷）
    -DiskSpace         磁盘空间不足清理（清理构建缓存、未使用镜像等，不删除数据卷）
    -Force             强制执行，不询问确认
    -Status            显示当前Docker资源状态
    -Restart           清理后重新启动服务

示例:
    .\scripts\cleanup-docker.ps1 -Containers          # 只清理容器
    .\scripts\cleanup-docker.ps1 -Volumes             # 清理容器和数据卷
    .\scripts\cleanup-docker.ps1 -All                 # 完全清理
    .\scripts\cleanup-docker.ps1 -DiskSpace           # 磁盘空间不足清理（推荐）
    .\scripts\cleanup-docker.ps1 -Status              # 查看资源状态
    .\scripts\cleanup-docker.ps1 -Containers -Restart # 清理容器后重启

⚠️  警告: 使用 -Volumes 或 -All 选项会删除所有数据，包括数据库！

"@
}

# 显示当前状态
function Show-Status {
    Write-Info "Current Docker resource status:"
    Write-Host ""
    
    if (-not (Test-DockerRunning)) {
        Write-Warning "Docker is not running. Please start Docker Desktop first."
        Write-Host ""
        Write-Info "To start Docker Desktop:"
        Write-Host "  1. Open Docker Desktop application"
        Write-Host "  2. Wait for it to fully start"
        Write-Host "  3. Run this script again"
        return
    }
    
    Write-Host "=== Containers ===" -ForegroundColor Cyan
    $containers = docker ps -a --filter "name=aperag" --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" 2>$null
    if ($containers -and $LASTEXITCODE -eq 0) {
        Write-Host $containers
    } else {
        Write-Host "No containers found or unable to get container information"
    }
    Write-Host ""
    
    Write-Host "=== Volumes ===" -ForegroundColor Cyan
    $volumes = docker volume ls --filter "name=aperag" 2>$null
    if ($volumes -and $LASTEXITCODE -eq 0) {
        Write-Host $volumes
    } else {
        Write-Host "No volumes found or unable to get volume information"
    }
    Write-Host ""
    
    Write-Host "=== Images ===" -ForegroundColor Cyan
    $images = docker images --filter "reference=*aperag*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>$null
    if ($images -and $LASTEXITCODE -eq 0) {
        Write-Host $images
    } else {
        Write-Host "No images found or unable to get image information"
    }
    Write-Host ""
    
    Write-Host "=== Disk Usage ===" -ForegroundColor Cyan
    $df = docker system df 2>$null
    if ($df -and $LASTEXITCODE -eq 0) {
        Write-Host $df
    } else {
        Write-Host "Unable to get disk usage information"
    }
    Write-Host ""
}

# 确认操作
function Confirm-Action {
    param([string]$Message)
    
    if ($Force) {
        return $true
    }
    
    $response = Read-Host "$Message [y/N]"
    if ($response -match "^[Yy]$") {
        return $true
    }
    return $false
}

# 检查Docker是否运行
function Test-DockerRunning {
    try {
        $result = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            # 检查是否是Docker未运行的错误
            $errorText = $result -join " "
            if ($errorText -match "cannot find the file|docker daemon|connection refused|pipe.*not found") {
                return $false
            }
            return $false
        }
    } catch {
        return $false
    }
}

# 清理容器
function Cleanup-Containers {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Info "Cleaning up containers..."
    
    if (Test-Path "docker-compose.yml") {
        $result = docker-compose down 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Containers stopped and removed"
            return $true
        } else {
            Write-Error "Failed to stop containers: $result"
            return $false
        }
    } else {
        Write-Warning "docker-compose.yml not found, trying manual cleanup..."
        $containers = docker ps -aq --filter "name=aperag" 2>$null
        if ($containers) {
            docker stop $containers 2>$null
            docker rm $containers 2>$null
            Write-Success "Containers cleaned up"
            return $true
        } else {
            Write-Info "No containers found to clean"
            return $true
        }
    }
}

# 清理容器和卷
function Cleanup-ContainersAndVolumes {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Warning "WARNING: This will delete all data volumes, including database data!"
    
    if (-not (Confirm-Action "Are you sure you want to continue?")) {
        Write-Info "Operation cancelled"
        return $false
    }
    
    Write-Info "Cleaning up containers and volumes..."
    
    if (Test-Path "docker-compose.yml") {
        $result = docker-compose down -v 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Containers and volumes removed"
            return $true
        } else {
            Write-Error "Failed to remove containers and volumes: $result"
            return $false
        }
    } else {
        Write-Warning "docker-compose.yml not found, trying manual cleanup..."
        $containers = docker ps -aq --filter "name=aperag" 2>$null
        if ($containers) {
            docker stop $containers 2>$null
            docker rm $containers 2>$null
        }
        $volumes = docker volume ls -q --filter "name=aperag" 2>$null
        if ($volumes) {
            docker volume rm $volumes 2>$null
        }
        Write-Success "Containers and volumes cleaned up"
        return $true
    }
}

# 清理镜像
function Cleanup-Images {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Info "Cleaning up unused images..."
    $result = docker image prune -a -f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Unused images cleaned up"
        return $true
    } else {
        Write-Error "Failed to clean up images: $result"
        return $false
    }
}

# 清理系统
function Cleanup-System {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Info "Cleaning up system resources (containers, networks, images, excluding volumes)..."
    $result = docker system prune -a -f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "System resources cleaned up"
        return $true
    } else {
        Write-Error "Failed to clean up system: $result"
        return $false
    }
}

# 磁盘空间不足清理（不删除数据卷）
function Cleanup-DiskSpace {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        Write-Info "If Docker cannot start due to disk space, try:"
        Write-Host "  1. Manually delete Docker build cache folder"
        Write-Host "  2. Use Windows Disk Cleanup tool"
        Write-Host "  3. Free up space on the disk where Docker is installed"
        return $false
    }
    
    Write-Info "Starting disk space cleanup (this will NOT delete data volumes)..."
    Write-Host ""
    
    $overallSuccess = $true
    
    # 1. 清理构建缓存（通常占用最多空间）
    Write-Info "Step 1/4: Cleaning build cache..."
    $result = docker builder prune -a -f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build cache cleaned"
    } else {
        Write-Warning "Failed to clean build cache: $result"
        $overallSuccess = $false
    }
    Write-Host ""
    
    # 2. 停止并删除所有停止的容器
    Write-Info "Step 2/4: Cleaning stopped containers..."
    if (Test-Path "docker-compose.yml") {
        $result = docker-compose down 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Containers stopped and removed"
        } else {
            Write-Warning "Some containers may not have been removed: $result"
        }
    } else {
        $stoppedContainers = docker ps -aq --filter "status=exited" 2>$null
        if ($stoppedContainers) {
            docker rm $stoppedContainers 2>$null
            Write-Success "Stopped containers removed"
        } else {
            Write-Info "No stopped containers found"
        }
    }
    Write-Host ""
    
    # 3. 清理未使用的镜像
    Write-Info "Step 3/4: Cleaning unused images..."
    $result = docker image prune -a -f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Unused images cleaned"
    } else {
        Write-Warning "Failed to clean images: $result"
        $overallSuccess = $false
    }
    Write-Host ""
    
    # 4. 清理系统资源（容器、网络，不包括卷）
    Write-Info "Step 4/4: Cleaning system resources (excluding volumes)..."
    $result = docker system prune -a -f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "System resources cleaned"
    } else {
        Write-Warning "Failed to clean system: $result"
        $overallSuccess = $false
    }
    Write-Host ""
    
    # 显示清理后的磁盘使用情况
    Write-Info "Disk usage after cleanup:"
    docker system df 2>&1 | Out-Host
    
    if ($overallSuccess) {
        Write-Success "Disk space cleanup completed! Data volumes are preserved."
    } else {
        Write-Warning "Disk space cleanup completed with some warnings."
    }
    
    return $overallSuccess
}

# 完全清理
function Cleanup-All {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Warning "WARNING: This will delete all containers, volumes, images, and networks!"
    Write-Warning "WARNING: All data will be permanently deleted!"
    
    if (-not (Confirm-Action "Are you sure you want to continue?")) {
        Write-Info "Operation cancelled"
        return $false
    }
    
    Write-Info "Performing full cleanup..."
    
    # 清理容器和卷
    if (Test-Path "docker-compose.yml") {
        $result = docker-compose down -v 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to remove containers and volumes: $result"
            return $false
        }
    } else {
        $allContainers = docker ps -aq 2>$null
        if ($allContainers) {
            docker stop $allContainers 2>$null
            docker rm $allContainers 2>$null
        }
        docker volume prune -f
    }
    
    # 清理所有未使用的资源
    $result = docker system prune -a --volumes -f 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to prune system: $result"
        return $false
    }
    
    Write-Success "Full cleanup completed"
    return $true
}

# 重启服务
function Restart-Services {
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        return $false
    }
    
    Write-Info "Restarting services..."
    
    if (Test-Path "docker-compose.yml") {
        $result = docker-compose up -d 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Services started"
            return $true
        } else {
            Write-Error "Failed to start services: $result"
            return $false
        }
    } else {
        Write-Error "docker-compose.yml not found, cannot auto-start services"
        Write-Info "Please run manually: docker-compose up -d"
        return $false
    }
}

# 主函数
function Main {
    # 显示帮助
    if ($Help) {
        Show-Help
        return
    }
    
    # 显示状态
    if ($Status) {
        Show-Status
        return
    }
    
    # 如果没有指定任何操作，显示帮助
    if (-not $Containers -and -not $Volumes -and -not $Images -and -not $All -and -not $System -and -not $DiskSpace) {
        Show-Help
        return
    }
    
    # 执行清理操作
    $cleanupSuccess = $true
    if ($All) {
        $cleanupSuccess = Cleanup-All
    } elseif ($DiskSpace) {
        $cleanupSuccess = Cleanup-DiskSpace
    } elseif ($Volumes) {
        $cleanupSuccess = Cleanup-ContainersAndVolumes
    } elseif ($Containers) {
        $cleanupSuccess = Cleanup-Containers
    } elseif ($Images) {
        $cleanupSuccess = Cleanup-Images
    } elseif ($System) {
        $cleanupSuccess = Cleanup-System
    }
    
    # 重启服务
    if ($Restart -and $cleanupSuccess) {
        if (Test-DockerRunning) {
            Restart-Services
        } else {
            Write-Warning "Cannot restart services: Docker is not running"
        }
    }
    
    # 显示最终状态
    Write-Host ""
    if ($cleanupSuccess) {
        Write-Info "Cleanup completed!"
    } else {
        Write-Warning "Cleanup completed with errors. Please check the messages above."
    }
    Show-Status
}

# 运行主函数
Main

