# Docker Desktop 修复脚本
# 用于解决 containerd bus error 问题

Write-Host "正在修复 Docker Desktop..." -ForegroundColor Yellow

# 1. 停止所有 Docker 相关进程
Write-Host "`n[1/5] 停止 Docker 相关进程..." -ForegroundColor Cyan
Get-Process -Name "*docker*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "*com.docker*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. 停止 Docker Desktop 服务
Write-Host "[2/5] 停止 Docker Desktop 服务..." -ForegroundColor Cyan
Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 3. 清理可能的锁文件（如果存在）
Write-Host "[3/5] 检查锁文件..." -ForegroundColor Cyan
$dockerDataPath = "$env:LOCALAPPDATA\Docker"
if (Test-Path "$dockerDataPath\*.lock") {
    Remove-Item "$dockerDataPath\*.lock" -Force -ErrorAction SilentlyContinue
    Write-Host "  已清理锁文件" -ForegroundColor Green
}

# 4. 启动 Docker Desktop 服务
Write-Host "[4/5] 启动 Docker Desktop 服务..." -ForegroundColor Cyan
try {
    Start-Service -Name "com.docker.service" -ErrorAction Stop
    Write-Host "  服务启动成功" -ForegroundColor Green
} catch {
    Write-Host "  服务启动失败，需要手动启动 Docker Desktop 应用程序" -ForegroundColor Red
    Write-Host "  错误: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 等待并检查 Docker 状态
Write-Host "[5/5] 等待 Docker 就绪..." -ForegroundColor Cyan
$maxWait = 30
$waited = 0
$dockerReady = $false

while ($waited -lt $maxWait) {
    try {
        $result = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            break
        }
    } catch {
        # 继续等待
    }
    Start-Sleep -Seconds 2
    $waited += 2
    Write-Host "  等待中... ($waited/$maxWait 秒)" -ForegroundColor Gray
}

if ($dockerReady) {
    Write-Host "`n✓ Docker Desktop 已成功启动！" -ForegroundColor Green
    docker info --format "{{.ServerVersion}}" | ForEach-Object {
        Write-Host "  Docker 版本: $_" -ForegroundColor Green
    }
} else {
    Write-Host "`n✗ Docker Desktop 未能自动启动" -ForegroundColor Red
    Write-Host "`n请手动执行以下步骤：" -ForegroundColor Yellow
    Write-Host "  1. 打开 Docker Desktop 应用程序" -ForegroundColor White
    Write-Host "  2. 等待 Docker Desktop 完全启动（系统托盘图标不再闪烁）" -ForegroundColor White
    Write-Host "  3. 如果问题持续，尝试：" -ForegroundColor White
    Write-Host "     - 重启计算机" -ForegroundColor White
    Write-Host "     - 在 Docker Desktop 设置中点击 'Troubleshoot' -> 'Reset to factory defaults'" -ForegroundColor White
    Write-Host "     - 检查 Windows 事件查看器中的错误日志" -ForegroundColor White
}

Write-Host "`n修复脚本执行完成。" -ForegroundColor Yellow

