# Google OAuth 连接超时问题解决方案

## 问题描述

在尝试使用 Google OAuth 认证时出现连接超时错误：

```
Failed to login. Message: Failed to exchange authorization code for tokens:
request to https://oauth2.googleapis.com/token failed, reason: connect ETIMEDOUT 142.250.157.95:443
```

## 原因分析

- 网络无法访问 Google OAuth 服务器 (`oauth2.googleapis.com`)
- 可能是防火墙、代理或网络限制导致
- 在中国大陆地区，Google 服务可能无法直接访问

## 解决方案

### 方案 1：使用 API Key 认证（推荐）✅

**在认证提示中选择选项 2：Use Gemini API Key**

1. 获取 Gemini API Key：

   - 访问：https://aistudio.google.com/app/apikey
   - 创建新的 API Key
   - 复制 API Key

2. 在认证提示中选择：

   ```
   2. Use Gemini API Key
   ```

3. 输入你的 API Key

**优点**：

- 不需要 OAuth 流程
- 不依赖网络访问 Google OAuth 服务器
- 配置简单，立即生效

### 方案 2：配置代理（如果可用）

如果你有可用的代理服务器，可以配置环境变量：

```bash
# Windows PowerShell
$env:HTTP_PROXY="http://proxy.example.com:8080"
$env:HTTPS_PROXY="http://proxy.example.com:8080"

# Linux/macOS
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

### 方案 3：使用 Vertex AI（如果可用）

在认证提示中选择选项 3：Vertex AI

这需要：

- Google Cloud 项目配置
- 适当的权限和网络访问

### 方案 4：在 ApeRAG 中配置 Gemini Provider

如果这是在 ApeRAG 项目中使用 Gemini，可以通过 Web 界面配置：

1. 访问：`http://localhost:3000/web/workspace/providers`
2. 找到 "Google Gemini" 提供商
3. 点击"配置"
4. 输入你的 Gemini API Key
5. 保存

这样就不需要通过 OAuth 认证了。

## 推荐做法

**对于 ApeRAG 项目**：

- 使用 Web 界面配置 Gemini API Key（方案 4）
- 或者通过环境变量设置：`GEMINI_API_KEY=your-api-key`

**对于 Google SDK 工具**：

- 选择选项 2（Use Gemini API Key）
- 或设置环境变量：`GOOGLE_API_KEY=your-api-key`

## 环境变量配置

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your-gemini-api-key"
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux/macOS
export GOOGLE_API_KEY="your-gemini-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

## 验证配置

配置完成后，可以通过以下方式验证：

```python
import google.generativeai as genai

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello")
print(response.text)
```

## 注意事项

1. **API Key 安全**：不要将 API Key 提交到代码仓库
2. **配额限制**：注意 API 使用配额和费用
3. **网络要求**：即使使用 API Key，仍需要能够访问 `generativelanguage.googleapis.com`

## 相关链接

- Gemini API Key 获取：https://aistudio.google.com/app/apikey
- ApeRAG Provider 配置文档：`QUICK_PROVIDER_SWITCH.md`
