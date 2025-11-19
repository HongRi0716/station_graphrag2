# Docker 镜像源修复脚本 (简化版)
# 用于修复 dockerproxy.net 502 错误

Write-Host "=== Docker 镜像源修复脚本 ===" -ForegroundColor Green

# 检查 Docker 是否运行
try {
    docker info | Out-Null
} catch {
    Write-Host "错误: Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n推荐的修复方案:" -ForegroundColor Yellow
Write-Host "1. 打开 Docker Desktop" -ForegroundColor Cyan
Write-Host "2. 点击右上角设置图标" -ForegroundColor Cyan
Write-Host "3. 进入 Docker Engine 设置" -ForegroundColor Cyan
Write-Host "4. 添加以下配置到 JSON:" -ForegroundColor Cyan
Write-Host ""
Write-Host '{'
Write-Host '  "registry-mirrors": ['
Write-Host '    "https://docker.mirrors.ustc.edu.cn",'
Write-Host '    "https://hub-mirror.c.163.com",'
Write-Host '    "https://mirror.baidubce.com"'
Write-Host '  ]'
Write-Host '}'
Write-Host ""
Write-Host "5. 点击 Apply & Restart 重启 Docker" -ForegroundColor Cyan

Write-Host "`n配置文件路径:" -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.docker\daemon.json"
Write-Host $configPath -ForegroundColor Cyan

if (Test-Path $configPath) {
    Write-Host "`n当前配置文件已存在" -ForegroundColor Yellow
    Write-Host "请手动编辑配置文件，移除 dockerproxy.net，添加上述镜像源" -ForegroundColor Yellow
} else {
    Write-Host "`n配置文件不存在" -ForegroundColor Yellow
}

Write-Host "`n修复完成后，运行以下命令验证:" -ForegroundColor Yellow
Write-Host "docker pull python:3.11.13-slim" -ForegroundColor Cyan

