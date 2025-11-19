# Cleanup Docker data on E drive
# This script helps free up space on E drive where Docker is installed

param(
    [switch]$Help,
    [switch]$Force,
    [switch]$DryRun
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
Docker E Drive Cleanup Script

Usage: .\scripts\cleanup-docker-e-drive.ps1 [options]

Options:
    -Help       Show this help message
    -Force      Force cleanup without confirmation
    -DryRun     Show what would be cleaned without actually cleaning

Examples:
    .\scripts\cleanup-docker-e-drive.ps1 -DryRun    # Preview cleanup
    .\scripts\cleanup-docker-e-drive.ps1             # Clean with confirmation
    .\scripts\cleanup-docker-e-drive.ps1 -Force      # Clean without confirmation

"@
}

# Check E drive space
function Get-EDriveSpace {
    $drive = Get-PSDrive E -ErrorAction SilentlyContinue
    if (-not $drive) {
        Write-Error "E drive not found"
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

# Find Docker directories on E drive
function Find-DockerDirectories {
    $dockerDirs = @()
    $paths = @("E:\Docker", "E:\docker", "E:\DockerData", "E:\docker-data")
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
            $dockerDirs += @{
                Path = $path
                SizeGB = [math]::Round($size, 2)
            }
        }
    }
    
    return $dockerDirs
}

# Clean Docker build cache
function Clean-DockerBuildCache {
    param([string]$DockerPath)
    
    $buildCachePath = Join-Path $DockerPath "buildkit"
    if (Test-Path $buildCachePath) {
        Write-Info "Cleaning build cache: $buildCachePath"
        if (-not $DryRun) {
            Remove-Item $buildCachePath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "Build cache cleaned"
        } else {
            $size = (Get-ChildItem $buildCachePath -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
            Write-Host "  Would free: $([math]::Round($size, 2)) GB" -ForegroundColor Yellow
        }
    }
}

# Clean Docker images directory
function Clean-DockerImages {
    param([string]$DockerPath)
    
    $imagesPath = Join-Path $DockerPath "images"
    if (Test-Path $imagesPath) {
        Write-Info "Checking Docker images..."
        if (-not $DryRun) {
            # Try to use docker command if available
            try {
                docker image prune -a -f 2>&1 | Out-Null
                Write-Success "Unused images cleaned"
            } catch {
                Write-Warning "Cannot use docker command, skipping image cleanup"
            }
        } else {
            $size = (Get-ChildItem $imagesPath -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
            Write-Host "  Images directory: $([math]::Round($size, 2)) GB" -ForegroundColor Yellow
        }
    }
}

# Clean Docker containers directory
function Clean-DockerContainers {
    param([string]$DockerPath)
    
    $containersPath = Join-Path $DockerPath "containers"
    if (Test-Path $containersPath) {
        Write-Info "Checking stopped containers..."
        if (-not $DryRun) {
            try {
                docker container prune -f 2>&1 | Out-Null
                Write-Success "Stopped containers cleaned"
            } catch {
                Write-Warning "Cannot use docker command, skipping container cleanup"
            }
        }
    }
}

# Clean Docker volumes (be careful!)
function Clean-DockerVolumes {
    param([string]$DockerPath, [switch]$Confirm)
    
    $volumesPath = Join-Path $DockerPath "volumes"
    if (Test-Path $volumesPath) {
        Write-Warning "Docker volumes found at: $volumesPath"
        Write-Warning "WARNING: Cleaning volumes will delete all data!"
        
        if ($DryRun) {
            $size = (Get-ChildItem $volumesPath -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
            Write-Host "  Volumes size: $([math]::Round($size, 2)) GB" -ForegroundColor Yellow
            Write-Host "  WARNING: This would delete all volume data!" -ForegroundColor Red
            return
        }
        
        if (-not $Confirm) {
            $response = Read-Host "Do you want to clean volumes? This will DELETE ALL DATA! [y/N]"
            if ($response -notmatch "^[Yy]$") {
                Write-Info "Skipping volume cleanup"
                return
            }
        }
        
        Write-Info "Cleaning unused volumes..."
        try {
            docker volume prune -f 2>&1 | Out-Null
            Write-Success "Unused volumes cleaned"
        } catch {
            Write-Warning "Cannot use docker command, skipping volume cleanup"
        }
    }
}

# Clean Docker logs
function Clean-DockerLogs {
    param([string]$DockerPath)
    
    $logPaths = @(
        (Join-Path $DockerPath "logs"),
        (Join-Path $DockerPath "*.log")
    )
    
    $cleaned = 0
    foreach ($logPath in $logPaths) {
        if (Test-Path $logPath) {
            Write-Info "Cleaning logs: $logPath"
            if (-not $DryRun) {
                Remove-Item $logPath -Recurse -Force -ErrorAction SilentlyContinue
                $cleaned++
            }
        }
    }
    
    if ($cleaned -gt 0 -and -not $DryRun) {
        Write-Success "Logs cleaned"
    }
}

# Main cleanup function
function Start-Cleanup {
    Write-Host "=== Docker E Drive Cleanup ===" -ForegroundColor Cyan
    Write-Host ""
    
    # Check E drive space
    $space = Get-EDriveSpace
    if (-not $space) {
        return
    }
    
    Write-Info "E Drive Space:"
    Write-Host "  Total: $($space.Total) GB"
    Write-Host "  Used: $($space.Used) GB"
    Write-Host "  Free: $($space.Free) GB" -ForegroundColor $(if ($space.Free -lt 5) { "Red" } else { "Green" })
    Write-Host ""
    
    # Find Docker directories
    $dockerDirs = Find-DockerDirectories
    if ($dockerDirs.Count -eq 0) {
        Write-Warning "No Docker directories found on E drive"
        return
    }
    
    Write-Info "Found Docker directories:"
    foreach ($dir in $dockerDirs) {
        Write-Host "  $($dir.Path): $($dir.SizeGB) GB"
    }
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "=== DRY RUN MODE - No files will be deleted ===" -ForegroundColor Yellow
        Write-Host ""
    }
    
    # Confirm before proceeding
    if (-not $Force -and -not $DryRun) {
        $response = Read-Host "This will clean Docker data on E drive. Continue? [y/N]"
        if ($response -notmatch "^[Yy]$") {
            Write-Info "Operation cancelled"
            return
        }
        Write-Host ""
    }
    
    # Clean each Docker directory
    foreach ($dir in $dockerDirs) {
        Write-Host "Cleaning: $($dir.Path)" -ForegroundColor Cyan
        Write-Host ""
        
        Clean-DockerBuildCache -DockerPath $dir.Path
        Clean-DockerImages -DockerPath $dir.Path
        Clean-DockerContainers -DockerPath $dir.Path
        Clean-DockerLogs -DockerPath $dir.Path
        
        # Volumes require special confirmation
        if (-not $DryRun) {
            Clean-DockerVolumes -DockerPath $dir.Path
        } else {
            Clean-DockerVolumes -DockerPath $dir.Path -Confirm
        }
        
        Write-Host ""
    }
    
    # Check space after cleanup
    if (-not $DryRun) {
        Start-Sleep -Seconds 2
        $newSpace = Get-EDriveSpace
        if ($newSpace) {
            $freed = $newSpace.Free - $space.Free
            Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
            Write-Host "Freed space: $([math]::Round($freed, 2)) GB"
            Write-Host "New free space: $($newSpace.Free) GB"
        }
    } else {
        Write-Host "=== Dry Run Complete ===" -ForegroundColor Yellow
        Write-Host "Run without -DryRun to actually clean"
    }
    Write-Host ""
}

# Main
if ($Help) {
    Show-Help
    exit 0
}

Start-Cleanup

