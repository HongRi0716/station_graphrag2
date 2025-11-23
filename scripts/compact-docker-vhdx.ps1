# Compact Docker WSL2 virtual disk to free up space
# This script compresses the docker_data.vhdx file on E drive

param(
    [switch]$Help
)

function Show-Help {
    Write-Host @"
Compress Docker WSL2 Virtual Disk

Usage: .\scripts\compact-docker-vhdx.ps1

This script will compress the docker_data.vhdx file to free up space.
Requires administrator privileges.

"@
}

if ($Help) {
    Show-Help
    exit 0
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

$vhdxPath = "E:\docker\DockerDesktopWSL\disk\docker_data.vhdx"

if (-not (Test-Path $vhdxPath)) {
    Write-Host "ERROR: Virtual disk file not found: $vhdxPath" -ForegroundColor Red
    exit 1
}

Write-Host "=== Docker WSL2 Virtual Disk Compression ===" -ForegroundColor Cyan
Write-Host ""

# Get current size
$fileSize = (Get-Item $vhdxPath).Length / 1GB
Write-Host "Virtual disk file: $vhdxPath" -ForegroundColor Blue
Write-Host "Current size: $([math]::Round($fileSize, 2)) GB" -ForegroundColor Yellow
Write-Host ""

# Ensure WSL2 is shut down
Write-Host "Ensuring WSL2 is shut down..." -ForegroundColor Blue
wsl --shutdown 2>&1 | Out-Null
Start-Sleep -Seconds 5
Write-Host "WSL2 shutdown complete" -ForegroundColor Green
Write-Host ""

# Compress the virtual disk
Write-Host "Starting compression (this may take 10-30 minutes)..." -ForegroundColor Yellow
Write-Host "Please wait..." -ForegroundColor Yellow
Write-Host ""

$diskpartScript = @"
select vdisk file="$vhdxPath"
compact vdisk
exit
"@

try {
    $diskpartScript | diskpart | Out-Null
    
    # Get new size
    $newSize = (Get-Item $vhdxPath).Length / 1GB
    $saved = $fileSize - $newSize
    
    Write-Host ""
    Write-Host "=== Compression Complete ===" -ForegroundColor Green
    Write-Host "New size: $([math]::Round($newSize, 2)) GB" -ForegroundColor Green
    Write-Host "Space freed: $([math]::Round($saved, 2)) GB" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Compression failed: $_" -ForegroundColor Red
    exit 1
}


