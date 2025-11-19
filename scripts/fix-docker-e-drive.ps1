# Fix Docker on E drive - Emergency cleanup when disk is full

Write-Host "=== Docker E Drive Emergency Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check E drive space
Write-Host "[1/5] Checking E drive space..." -ForegroundColor Blue
$drive = Get-PSDrive E -ErrorAction SilentlyContinue
if ($drive) {
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    $usedGB = [math]::Round($drive.Used / 1GB, 2)
    Write-Host "  Free: $freeGB GB / Used: $usedGB GB" -ForegroundColor $(if ($freeGB -lt 5) { "Red" } else { "Green" })
} else {
    Write-Host "  E drive not found!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Force stop Docker
Write-Host "[2/5] Stopping Docker processes..." -ForegroundColor Blue
$processes = @("Docker Desktop", "com.docker.backend", "com.docker.proxy", "com.docker.service", "vpnkit")
$stopped = 0
foreach ($procName in $processes) {
    Get-Process -Name $procName -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $stopped++
    }
}
if ($stopped -gt 0) {
    Write-Host "  Stopped $stopped processes" -ForegroundColor Green
} else {
    Write-Host "  No Docker processes running" -ForegroundColor Yellow
}
Start-Sleep -Seconds 3
Write-Host ""

# Step 3: Shutdown WSL2
Write-Host "[3/5] Shutting down WSL2..." -ForegroundColor Blue
wsl --shutdown 2>$null
Start-Sleep -Seconds 3
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# Step 4: Try to start Docker and clean
Write-Host "[4/5] Starting Docker for cleanup..." -ForegroundColor Blue
Write-Host "  Please start Docker Desktop manually, then press Enter to continue..."
Read-Host

# Wait a bit for Docker to start
Start-Sleep -Seconds 10

# Check if Docker is running
$dockerRunning = $false
try {
    $result = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "  Docker is running" -ForegroundColor Green
    }
} catch {
    Write-Host "  Docker is not running yet" -ForegroundColor Yellow
}

if ($dockerRunning) {
    Write-Host ""
    Write-Host "  Cleaning Docker resources..." -ForegroundColor Blue
    
    # Clean build cache
    Write-Host "    - Cleaning build cache..." -ForegroundColor Cyan
    docker builder prune -a -f 2>&1 | Out-Null
    
    # Clean unused images
    Write-Host "    - Cleaning unused images..." -ForegroundColor Cyan
    docker image prune -a -f 2>&1 | Out-Null
    
    # Clean stopped containers
    Write-Host "    - Cleaning stopped containers..." -ForegroundColor Cyan
    docker container prune -f 2>&1 | Out-Null
    
    # Clean unused networks
    Write-Host "    - Cleaning unused networks..." -ForegroundColor Cyan
    docker network prune -f 2>&1 | Out-Null
    
    Write-Host "  Docker cleanup completed" -ForegroundColor Green
} else {
    Write-Host "  Cannot clean Docker resources (Docker not running)" -ForegroundColor Yellow
    Write-Host "  You may need to free up more space first" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Check space after cleanup
Write-Host "[5/5] Checking space after cleanup..." -ForegroundColor Blue
$newDrive = Get-PSDrive E -ErrorAction SilentlyContinue
if ($newDrive) {
    $newFreeGB = [math]::Round($newDrive.Free / 1GB, 2)
    $freed = $newFreeGB - $freeGB
    Write-Host "  New free space: $newFreeGB GB" -ForegroundColor Green
    if ($freed -gt 0) {
        Write-Host "  Freed: $([math]::Round($freed, 2)) GB" -ForegroundColor Green
    }
}
Write-Host ""

Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If Docker still cannot start:" -ForegroundColor Yellow
Write-Host "1. Check E drive has at least 10GB free space"
Write-Host "2. Manually delete large files in E:\Docker if needed"
Write-Host "3. Consider moving Docker data to another drive"
Write-Host ""

