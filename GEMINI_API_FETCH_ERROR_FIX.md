# Gemini API Fetch 错误解决方案

## 问题描述

使用 Gemini CLI 工具时出现以下错误：

```
✖Error when talking to Gemini API
exception TypeError: fetch failed sending request
```

错误报告文件位置：

```
C:\Users\Admin\AppData\Local\Temp\gemini-client-error-*.json
```

## 原因分析

1. **网络连接问题**：无法连接到 Google 的 API 服务器 (`generativelanguage.googleapis.com`)
2. **防火墙/代理限制**：网络环境可能阻止了对 Google 服务的访问
3. **DNS 解析问题**：无法解析 Google API 域名
4. **地理位置限制**：在某些地区，Google 服务可能无法直接访问

## 解决方案

### 方案 1：配置代理（如果有可用的代理服务器）✅

如果你有可用的代理服务器，可以配置 Node.js 使用代理：

#### Windows PowerShell

```powershell
# 设置代理环境变量
$env:HTTP_PROXY="http://proxy.example.com:8080"
$env:HTTPS_PROXY="http://proxy.example.com:8080"
$env:NO_PROXY="localhost,127.0.0.1"

# 或者使用系统代理设置
$env:HTTP_PROXY="http://127.0.0.1:7890"  # 示例：本地代理端口
$env:HTTPS_PROXY="http://127.0.0.1:7890"
```

#### 配置 npm 代理（如果使用 npm 安装的工具）

```powershell
npm config set proxy http://proxy.example.com:8080
npm config set https-proxy http://proxy.example.com:8080
```

### 方案 2：检查网络连接

#### 测试 Google API 服务器连接

```powershell
# 测试 DNS 解析
nslookup generativelanguage.googleapis.com

# 测试 HTTPS 连接
Test-NetConnection -ComputerName generativelanguage.googleapis.com -Port 443
```

#### 检查防火墙设置

1. 打开 Windows 防火墙设置
2. 检查是否阻止了 Node.js 或相关应用的网络访问
3. 如果需要，添加例外规则

### 方案 3：使用 API Key 直接配置（推荐）

如果 Gemini CLI 支持直接使用 API Key，可以避免网络认证问题：

#### 设置环境变量

```powershell
# 设置 Gemini API Key
$env:GOOGLE_API_KEY="your-gemini-api-key"
$env:GEMINI_API_KEY="your-gemini-api-key"

# 获取 API Key：https://aistudio.google.com/app/apikey
```

#### 在 ApeRAG 项目中配置

如果是在 ApeRAG 项目中使用 Gemini：

1. 访问 Web 界面：`http://localhost:3000/web/workspace/providers`
2. 找到 "Google Gemini" 提供商
3. 点击"配置"
4. 输入你的 Gemini API Key
5. 保存

### 方案 4：使用 ApeRAG 的 Gemini 集成（替代 CLI）

如果 Gemini CLI 无法正常工作，可以考虑：

1. **使用 ApeRAG Web 界面**：

   - 通过 Web UI 与 Gemini 模型交互
   - 不需要 CLI 工具

2. **使用 ApeRAG API**：
   ```bash
   curl -X POST "http://localhost:8000/api/v1/agent/chat" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{
       "query": "你的问题",
       "completion": {
         "model": "gemini/gemini-2.5-flash",
         "model_service_provider": "gemini"
       }
     }'
   ```

### 方案 5：检查 Node.js 和 npm 配置

#### 更新 Node.js 和 npm

```powershell
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version

# 更新 npm
npm install -g npm@latest
```

#### 清理 npm 缓存

```powershell
npm cache clean --force
```

### 方案 6：使用 VPN 或网络代理工具

如果网络环境限制了对 Google 服务的访问：

1. **使用 VPN**：连接到可以访问 Google 服务的网络
2. **使用代理工具**：配置系统级代理
3. **使用镜像服务**：如果有可用的 Google API 镜像

## 诊断步骤

### 1. 检查错误报告文件

```powershell
# 查看最新的错误报告
Get-ChildItem "$env:LOCALAPPDATA\Temp\gemini-client-error*.json" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 |
  Get-Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 2. 测试 API 连接

```powershell
# 使用 curl 测试（如果已安装）
curl -v https://generativelanguage.googleapis.com

# 或使用 PowerShell
Invoke-WebRequest -Uri "https://generativelanguage.googleapis.com" -Method GET
```

### 3. 检查环境变量

```powershell
# 检查所有相关环境变量
Get-ChildItem Env: | Where-Object { $_.Name -like "*GOOGLE*" -or $_.Name -like "*GEMINI*" -or $_.Name -like "*PROXY*" }
```

## 推荐配置

### 完整的环境变量配置示例

```powershell
# Gemini API Key
$env:GOOGLE_API_KEY="your-api-key-here"
$env:GEMINI_API_KEY="your-api-key-here"

# 代理配置（如果需要）
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"

# Node.js 配置
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"  # 仅用于开发环境，生产环境不推荐
```

### 永久配置（系统环境变量）

1. 打开"系统属性" → "高级" → "环境变量"
2. 添加以下变量：
   - `GOOGLE_API_KEY` = `your-api-key`
   - `HTTP_PROXY` = `http://proxy:port`（如果需要）
   - `HTTPS_PROXY` = `http://proxy:port`（如果需要）

## 相关资源

- Gemini API Key 获取：https://aistudio.google.com/app/apikey
- ApeRAG Provider 配置：`QUICK_PROVIDER_SWITCH.md`
- Google OAuth 问题：`GOOGLE_OAUTH_TIMEOUT_FIX.md`

## 注意事项

1. **API Key 安全**：不要将 API Key 提交到代码仓库或公开分享
2. **网络要求**：即使使用 API Key，仍需要能够访问 `generativelanguage.googleapis.com`
3. **配额限制**：注意 API 使用配额和费用
4. **代理安全**：使用代理时注意数据安全
