# Quick fix for Docker Desktop stuck on startup
# Run this script to force stop Docker and clean up

Write-Host "=== Docker Desktop Startup Fix ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Force stop Docker processes
Write-Host "[1/4] Stopping Docker processes..." -ForegroundColor Blue
$processes = @("Docker Desktop", "com.docker.backend", "com.docker.proxy", "com.docker.service", "vpnkit")
foreach ($procName in $processes) {
    Get-Process -Name $procName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Write-Host "Done" -ForegroundColor Green
Write-Host ""

# Step 2: Shutdown WSL2
Write-Host "[2/4] Shutting down WSL2..." -ForegroundColor Blue
wsl --shutdown 2>$null
Start-Sleep -Seconds 3
Write-Host "Done" -ForegroundColor Green
Write-Host ""

# Step 3: Check disk space
Write-Host "[3/4] Checking disk space..." -ForegroundColor Blue
$drive = Get-PSDrive C
$freeGB = [math]::Round($drive.Free / 1GB, 2)
Write-Host "Free space: $freeGB GB" -ForegroundColor $(if ($freeGB -lt 5) { "Red" } elseif ($freeGB -lt 10) { "Yellow" } else { "Green" })
Write-Host ""

# Step 4: Clean temp files
Write-Host "[4/4] Cleaning temporary files..." -ForegroundColor Blue
$tempPaths = @("$env:LOCALAPPDATA\Docker\tmp", "$env:TEMP\Docker*")
foreach ($path in $tempPaths) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Done" -ForegroundColor Green
Write-Host ""

Write-Host "=== Fix Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Docker Desktop"
Write-Host "2. Wait for it to fully start (may take a few minutes)"
Write-Host "3. If still stuck, run: .\scripts\cleanup-docker.ps1 -DiskSpace"
Write-Host ""

