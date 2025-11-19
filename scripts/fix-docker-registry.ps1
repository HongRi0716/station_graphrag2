# Docker 镜像源修复脚本 (Windows PowerShell)
# 用于修复 dockerproxy.net 502 错误

Write-Host "=== Docker 镜像源修复脚本 ===" -ForegroundColor Green

# 检查 Docker 是否运行
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n当前 Docker 配置:" -ForegroundColor Yellow
docker info | Select-String -Pattern "Registry Mirrors" -Context 0,5

Write-Host "`n推荐的修复方案:" -ForegroundColor Yellow
Write-Host "1. 打开 Docker Desktop" -ForegroundColor Cyan
Write-Host "2. 点击右上角设置图标（齿轮）" -ForegroundColor Cyan
Write-Host "3. 进入 'Docker Engine' 设置" -ForegroundColor Cyan
Write-Host "4. 将以下配置添加到 JSON 中:" -ForegroundColor Cyan
Write-Host ""
$jsonExample = @'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
'@
Write-Host $jsonExample -ForegroundColor White
Write-Host ""
Write-Host "5. 点击 'Apply & Restart' 重启 Docker" -ForegroundColor Cyan

Write-Host "`n或者，您可以手动编辑配置文件:" -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.docker\daemon.json"
Write-Host "配置文件路径: $configPath" -ForegroundColor Cyan

# 检查配置文件是否存在
if (Test-Path $configPath) {
    Write-Host "`n当前配置文件内容:" -ForegroundColor Yellow
    Get-Content $configPath | Write-Host -ForegroundColor White
    
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Write-Host "`n创建备份: $backupPath" -ForegroundColor Yellow
    Copy-Item $configPath $backupPath
    
    Write-Host "`n是否要自动修复配置? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        $config = Get-Content $configPath | ConvertFrom-Json
        
        # 移除 dockerproxy.net
        if ($config.'registry-mirrors') {
            $config.'registry-mirrors' = $config.'registry-mirrors' | Where-Object { $_ -notlike '*dockerproxy.net*' }
        } else {
            $config | Add-Member -MemberType NoteProperty -Name 'registry-mirrors' -Value @()
        }
        
        # 添加推荐的镜像源
        $mirrors = @(
            "https://docker.mirrors.ustc.edu.cn",
            "https://hub-mirror.c.163.com",
            "https://mirror.baidubce.com"
        )
        
        foreach ($mirror in $mirrors) {
            if ($config.'registry-mirrors' -notcontains $mirror) {
                $config.'registry-mirrors' += $mirror
            }
        }
        
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
        Write-Host "配置已更新！请重启 Docker Desktop 使配置生效。" -ForegroundColor Green
    }
} else {
    Write-Host "`n配置文件不存在，将创建新配置..." -ForegroundColor Yellow
    $config = @{
        'registry-mirrors' = @(
            "https://docker.mirrors.ustc.edu.cn",
            "https://hub-mirror.c.163.com",
            "https://mirror.baidubce.com"
        )
    }
    
    $configDir = Split-Path $configPath -Parent
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
    Write-Host "配置文件已创建！请重启 Docker Desktop 使配置生效。" -ForegroundColor Green
}

Write-Host "`n修复完成后，请运行以下命令验证:" -ForegroundColor Yellow
Write-Host "docker pull python:3.11.13-slim" -ForegroundColor Cyan

