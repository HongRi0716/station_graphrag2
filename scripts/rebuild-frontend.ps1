# Rebuild frontend with latest code
# This script ensures the frontend is rebuilt with the latest code

param(
    [switch]$Help,
    [switch]$NoCache,
    [switch]$Clean
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

function Show-Help {
    Write-Host @"
Frontend Rebuild Script

Usage: .\scripts\rebuild-frontend.ps1 [options]

Options:
    -Help       Show this help message
    -NoCache    Rebuild without using cache (recommended for latest code)
    -Clean      Clean old images before rebuilding

Examples:
    .\scripts\rebuild-frontend.ps1              # Normal rebuild
    .\scripts\rebuild-frontend.ps1 -NoCache     # Rebuild without cache (recommended)
    .\scripts\rebuild-frontend.ps1 -Clean       # Clean and rebuild

"@
}

if ($Help) {
    Show-Help
    exit 0
}

Write-Host "=== Frontend Rebuild ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop frontend container
Write-Info "Step 1/5: Stopping frontend container..."
docker-compose stop frontend 2>&1 | Out-Null
docker-compose rm -f frontend 2>&1 | Out-Null
Write-Success "Frontend container stopped"
Write-Host ""

# Step 2: Remove old frontend image (if Clean)
if ($Clean) {
    Write-Info "Step 2/5: Removing old frontend image..."
    $imageName = "docker.io/apecloud/aperag-frontend:v0.0.0-nightly"
    docker rmi $imageName 2>&1 | Out-Null
    docker image prune -f 2>&1 | Out-Null
    Write-Success "Old images removed"
    Write-Host ""
} else {
    Write-Info "Step 2/5: Skipping image cleanup (use -Clean to remove old images)"
    Write-Host ""
}

# Step 3: Rebuild frontend
Write-Info "Step 3/5: Rebuilding frontend..."
if ($NoCache) {
    Write-Host "  Building without cache (this may take longer)..." -ForegroundColor Yellow
    docker-compose build --no-cache frontend
} else {
    Write-Host "  Building with cache..." -ForegroundColor Yellow
    Write-Warning "  Tip: Use -NoCache to ensure latest code is used"
    docker-compose build frontend
}

if ($LASTEXITCODE -eq 0) {
    Write-Success "Frontend rebuilt successfully"
} else {
    Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Start frontend
Write-Info "Step 4/5: Starting frontend container..."
docker-compose up -d frontend
if ($LASTEXITCODE -eq 0) {
    Write-Success "Frontend started"
} else {
    Write-Host "Failed to start frontend!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 5: Wait and check status
Write-Info "Step 5/5: Checking frontend status..."
Start-Sleep -Seconds 5
$status = docker-compose ps frontend
Write-Host $status
Write-Host ""

Write-Host "=== Rebuild Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Clear browser cache (Ctrl+Shift+Delete or Ctrl+F5)"
Write-Host "2. Access frontend at: http://localhost:3000"
Write-Host "3. If still seeing old interface, try hard refresh: Ctrl+F5"
Write-Host ""

