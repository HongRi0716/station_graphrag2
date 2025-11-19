# Google API 连接问题快速修复脚本
# 使用方法: .\scripts\fix-google-api-connection.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Google API 连接问题快速修复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查当前连接状态
Write-Host "[1/5] 检查当前网络连接状态..." -ForegroundColor Yellow
try {
    $testResult = Test-NetConnection -ComputerName generativelanguage.googleapis.com -Port 443 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($testResult) {
        Write-Host "✅ 连接正常！" -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "❌ 无法连接到 Google API 服务器" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/5] 检查系统代理设置..." -ForegroundColor Yellow
$currentProxy = netsh winhttp show proxy
if ($currentProxy -match "Direct access") {
    Write-Host "⚠️  未检测到系统代理配置" -ForegroundColor Yellow
} else {
    Write-Host "✅ 检测到代理配置：" -ForegroundColor Green
    Write-Host $currentProxy
}

Write-Host ""
Write-Host "[3/5] 检查环境变量..." -ForegroundColor Yellow
$envVars = Get-ChildItem Env: | Where-Object { 
    $_.Name -like "*PROXY*" -or 
    $_.Name -like "*GOOGLE*" -or 
    $_.Name -like "*GEMINI*" 
}
if ($envVars) {
    Write-Host "✅ 检测到相关环境变量：" -ForegroundColor Green
    $envVars | ForEach-Object { Write-Host "  $($_.Name) = $($_.Value)" }
} else {
    Write-Host "⚠️  未检测到相关环境变量" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/5] 配置选项" -ForegroundColor Yellow
Write-Host ""
Write-Host "请选择解决方案：" -ForegroundColor Cyan
Write-Host "1. 配置代理（如果有代理服务器）" -ForegroundColor White
Write-Host "2. 设置环境变量代理（临时）" -ForegroundColor White
Write-Host "3. 仅设置 Gemini API Key（推荐使用 ApeRAG Web 界面）" -ForegroundColor White
Write-Host "4. 查看 ApeRAG 配置指南" -ForegroundColor White
Write-Host "5. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "配置系统代理..." -ForegroundColor Yellow
        $proxyHost = Read-Host "请输入代理服务器地址 (例如: 127.0.0.1)"
        $proxyPort = Read-Host "请输入代理端口 (例如: 7890)"
        $proxyUrl = "http://${proxyHost}:${proxyPort}"
        
        Write-Host "正在配置代理: $proxyUrl" -ForegroundColor Yellow
        try {
            netsh winhttp set proxy proxy-server="$proxyUrl" bypass-list="localhost,127.0.0.1"
            Write-Host "✅ 代理配置成功！" -ForegroundColor Green
        } catch {
            Write-Host "❌ 代理配置失败: $_" -ForegroundColor Red
            Write-Host "提示: 可能需要管理员权限" -ForegroundColor Yellow
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "配置环境变量代理（当前会话有效）..." -ForegroundColor Yellow
        $proxyHost = Read-Host "请输入代理服务器地址 (例如: 127.0.0.1)"
        $proxyPort = Read-Host "请输入代理端口 (例如: 7890)"
        $proxyUrl = "http://${proxyHost}:${proxyPort}"
        
        $env:HTTP_PROXY = $proxyUrl
        $env:HTTPS_PROXY = $proxyUrl
        $env:NO_PROXY = "localhost,127.0.0.1"
        
        Write-Host "✅ 环境变量已设置：" -ForegroundColor Green
        Write-Host "  HTTP_PROXY = $env:HTTP_PROXY"
        Write-Host "  HTTPS_PROXY = $env:HTTPS_PROXY"
        Write-Host ""
        Write-Host "⚠️  注意: 这些设置仅在当前 PowerShell 会话中有效" -ForegroundColor Yellow
        Write-Host "   关闭窗口后需要重新设置，或添加到系统环境变量" -ForegroundColor Yellow
    }
    
    "3" {
        Write-Host ""
        Write-Host "设置 Gemini API Key..." -ForegroundColor Yellow
        Write-Host "获取 API Key: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
        $apiKey = Read-Host "请输入 Gemini API Key"
        
        if ($apiKey) {
            $env:GOOGLE_API_KEY = $apiKey
            $env:GEMINI_API_KEY = $apiKey
            Write-Host "✅ API Key 已设置（当前会话）" -ForegroundColor Green
            Write-Host ""
            Write-Host "推荐: 通过 ApeRAG Web 界面配置（永久有效）" -ForegroundColor Cyan
            Write-Host "  1. 访问: http://localhost:3000/web/workspace/providers" -ForegroundColor White
            Write-Host "  2. 找到 'Google Gemini' 提供商" -ForegroundColor White
            Write-Host "  3. 点击'配置'并输入 API Key" -ForegroundColor White
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "ApeRAG 配置指南" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "推荐方案：使用 ApeRAG Web 界面" -ForegroundColor Green
        Write-Host ""
        Write-Host "步骤 1: 启动 ApeRAG 服务" -ForegroundColor Yellow
        Write-Host "  docker-compose up -d" -ForegroundColor White
        Write-Host ""
        Write-Host "步骤 2: 访问 Web 界面" -ForegroundColor Yellow
        Write-Host "  http://localhost:3000/web/workspace/providers" -ForegroundColor White
        Write-Host ""
        Write-Host "步骤 3: 配置 Gemini Provider" -ForegroundColor Yellow
        Write-Host "  - 找到 'Google Gemini'" -ForegroundColor White
        Write-Host "  - 点击'配置'" -ForegroundColor White
        Write-Host "  - 输入 API Key" -ForegroundColor White
        Write-Host "  - 保存" -ForegroundColor White
        Write-Host ""
        Write-Host "步骤 4: 使用 Gemini 模型" -ForegroundColor Yellow
        Write-Host "  - 在聊天界面选择 Gemini 模型" -ForegroundColor White
        Write-Host "  - 开始对话" -ForegroundColor White
        Write-Host ""
        Write-Host "优点：" -ForegroundColor Green
        Write-Host "  ✅ 不需要直接连接 Google API" -ForegroundColor White
        Write-Host "  ✅ 通过 ApeRAG 后端处理，可能已配置代理" -ForegroundColor White
        Write-Host "  ✅ 配置永久有效" -ForegroundColor White
        Write-Host ""
    }
    
    "5" {
        Write-Host "退出..." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[5/5] 验证连接..." -ForegroundColor Yellow
Write-Host "正在测试连接..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

try {
    $testResult = Test-NetConnection -ComputerName generativelanguage.googleapis.com -Port 443 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($testResult) {
        Write-Host ""
        Write-Host "✅✅✅ 连接成功！" -ForegroundColor Green
        Write-Host "现在可以正常使用 Google API 服务了" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  连接仍然失败" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "建议：" -ForegroundColor Cyan
        Write-Host "1. 检查代理服务器是否正在运行" -ForegroundColor White
        Write-Host "2. 确认代理地址和端口正确" -ForegroundColor White
        Write-Host "3. 尝试使用 ApeRAG Web 界面（推荐）" -ForegroundColor White
        Write-Host "4. 查看详细文档: 网络连接问题快速解决指南.md" -ForegroundColor White
    }
} catch {
    Write-Host ""
    Write-Host "❌ 连接测试失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

