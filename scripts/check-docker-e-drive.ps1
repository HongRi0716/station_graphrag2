# Check Docker files and space usage on E drive

Write-Host "=== Checking Docker on E Drive ===" -ForegroundColor Cyan
Write-Host ""

# Check E drive space
Write-Host "[1] E Drive Space:" -ForegroundColor Blue
$drive = Get-PSDrive E -ErrorAction SilentlyContinue
if ($drive) {
    $usedGB = [math]::Round($drive.Used / 1GB, 2)
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    $totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
    Write-Host "  Total: $totalGB GB"
    Write-Host "  Used: $usedGB GB"
    Write-Host "  Free: $freeGB GB" -ForegroundColor $(if ($freeGB -lt 5) { "Red" } elseif ($freeGB -lt 10) { "Yellow" } else { "Green" })
} else {
    Write-Host "  E drive not found" -ForegroundColor Red
}
Write-Host ""

# Check for Docker directories on E drive
Write-Host "[2] Docker Directories on E Drive:" -ForegroundColor Blue
$dockerDirs = @(
    "E:\Docker",
    "E:\docker",
    "E:\DockerData",
    "E:\docker-data",
    "E:\\.docker"
)

$found = $false
foreach ($dir in $dockerDirs) {
    if (Test-Path $dir) {
        $found = $true
        $size = (Get-ChildItem $dir -Recurse -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Host "  Found: $dir ($([math]::Round($size, 2)) GB)" -ForegroundColor Green
    }
}

if (-not $found) {
    Write-Host "  No Docker directories found in common locations" -ForegroundColor Yellow
}
Write-Host ""

# Check Docker Desktop WSL2 vhdx file location
Write-Host "[3] Docker WSL2 Disk Files:" -ForegroundColor Blue
$vhdxPaths = @(
    "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx",
    "E:\Docker\wsl\data\ext4.vhdx",
    "E:\\.docker\wsl\data\ext4.vhdx"
)

$foundVhdx = $false
foreach ($vhdxPath in $vhdxPaths) {
    if (Test-Path $vhdxPath) {
        $foundVhdx = $true
        $size = (Get-Item $vhdxPath).Length / 1GB
        Write-Host "  Found: $vhdxPath" -ForegroundColor Green
        Write-Host "    Size: $([math]::Round($size, 2)) GB"
    }
}

if (-not $foundVhdx) {
    Write-Host "  No WSL2 vhdx files found" -ForegroundColor Yellow
}
Write-Host ""

# Check Docker volumes location
Write-Host "[4] Docker Volumes:" -ForegroundColor Blue
try {
    $volumes = docker volume ls --format "{{.Name}}" 2>$null
    if ($volumes) {
        Write-Host "  Found $($volumes.Count) volumes"
        $volumes | Select-Object -First 5 | ForEach-Object {
            Write-Host "    - $_"
        }
        if ($volumes.Count -gt 5) {
            Write-Host "    ... and $($volumes.Count - 5) more"
        }
    } else {
        Write-Host "  No volumes found or Docker not running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Cannot check volumes (Docker may not be running)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
if ($drive) {
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeGB -lt 5) {
        Write-Host "WARNING: E drive has less than 5GB free space!" -ForegroundColor Red
        Write-Host "Recommendation: Run cleanup script" -ForegroundColor Yellow
    } elseif ($freeGB -lt 10) {
        Write-Host "WARNING: E drive has less than 10GB free space" -ForegroundColor Yellow
        Write-Host "Recommendation: Consider running cleanup script" -ForegroundColor Yellow
    } else {
        Write-Host "E drive has sufficient space" -ForegroundColor Green
    }
}
Write-Host ""

