# 如何添加模型

本指南介绍如何在 ApeRAG 系统中添加新的模型。

## 概述

在 ApeRAG 中，模型是挂载在**提供商（Provider）**下的。因此，添加模型需要：

1. 确保已有一个可用的提供商（Provider）
2. 在该提供商下添加模型（Model）

## 方法一：通过 Web UI 添加（推荐）

### 步骤 1: 进入模型管理页面

1. 登录 ApeRAG Web 界面
2. 导航到 **设置 > 模型**（Settings > Models）
3. 找到您要添加模型的提供商
4. 点击提供商右侧的 **三个点（...）** 菜单
5. 选择 **"Models"** 进入模型管理页面

### 步骤 2: 添加新模型

1. 在模型管理页面，点击 **"添加模型"（Add Model）** 按钮
2. 填写模型配置信息：

#### 必填字段

- **模型名称（Model Name）**: 输入模型的标识符
  - 例如：`gpt-4o-mini`、`claude-3-5-sonnet-20241022`、`gemini-1.5-pro`
- **模型类型（API Type）**: 选择模型的 API 类型

  - **Completion**: 用于文本生成和对话
  - **Vision**: 用于视觉理解（实际上是 completion API，但带有 vision 标签）
  - **Embedding**: 用于文本向量化
  - **Rerank**: 用于文档重排序

- **LLM 提供商（Custom LLM Provider）**: 选择模型使用的提供商实现
  - 可选值：`openai`、`anthropic`、`gemini`、`deepseek`、`alibabacloud`、`siliconflow`、`openrouter`、`jina`、`xai` 等
  - 这个字段决定了系统使用哪个 API 客户端来调用模型

#### 可选字段

- **Context Window**: 上下文窗口大小（总 token 数）
  - 例如：`128000`、`200000`
- **Max Input Tokens**: 最大输入 token 数
  - 例如：`120000`
- **Max Output Tokens**: 最大输出 token 数
  - 例如：`8000`

3. 点击 **"保存"（Save）** 完成添加

### 步骤 3: 启用模型（可选）

添加模型后，您可以在模型列表中看到两个切换开关：

- **Agent**: 启用后，模型可用于 Agent 回答问题
- **Collection**: 启用后，模型可用于构建 Collection 索引

根据您的需求启用相应的开关。

## 方法二：通过 API 添加

### API 端点

```
POST /llm_providers/{provider_name}/models
```

### 请求示例

```bash
curl -X POST "http://your-aperag-host/llm_providers/openai/models" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "openai",
    "api": "completion",
    "model": "gpt-4o-mini",
    "custom_llm_provider": "openai",
    "context_window": 128000,
    "max_input_tokens": 120000,
    "max_output_tokens": 8000,
    "tags": ["enable_for_agent", "enable_for_collection"]
  }'
```

### 请求体字段说明

| 字段                  | 类型    | 必填 | 说明                                                                                                                               |
| --------------------- | ------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `provider_name`       | string  | 是   | 提供商名称                                                                                                                         |
| `api`                 | string  | 是   | API 类型：`completion`、`embedding` 或 `rerank`                                                                                    |
| `model`               | string  | 是   | 模型名称/标识符                                                                                                                    |
| `custom_llm_provider` | string  | 是   | 自定义 LLM 提供商实现                                                                                                              |
| `context_window`      | integer | 否   | 上下文窗口大小                                                                                                                     |
| `max_input_tokens`    | integer | 否   | 最大输入 token 数                                                                                                                  |
| `max_output_tokens`   | integer | 否   | 最大输出 token 数                                                                                                                  |
| `tags`                | array   | 否   | 标签数组，常用标签：<br>- `enable_for_agent`: 可用于 Agent<br>- `enable_for_collection`: 可用于 Collection<br>- `vision`: 视觉模型 |

## 常见场景示例

### 示例 1: 添加 OpenAI 模型

```json
{
  "provider_name": "openai",
  "api": "completion",
  "model": "gpt-4o-mini",
  "custom_llm_provider": "openai",
  "context_window": 128000,
  "max_input_tokens": 120000,
  "max_output_tokens": 8000,
  "tags": ["enable_for_agent", "enable_for_collection"]
}
```

### 示例 2: 添加视觉模型

```json
{
  "provider_name": "openai",
  "api": "completion",
  "model": "gpt-4o",
  "custom_llm_provider": "openai",
  "context_window": 128000,
  "tags": ["vision", "enable_for_agent"]
}
```

注意：视觉模型使用 `completion` API，但需要添加 `vision` 标签。

### 示例 3: 添加 Embedding 模型

```json
{
  "provider_name": "openai",
  "api": "embedding",
  "model": "text-embedding-3-large",
  "custom_llm_provider": "openai",
  "context_window": 8191,
  "max_input_tokens": 8191,
  "tags": ["enable_for_collection"]
}
```

### 示例 4: 添加 Rerank 模型

```json
{
  "provider_name": "jina",
  "api": "rerank",
  "model": "jina-reranker-v1-base-en",
  "custom_llm_provider": "jina",
  "tags": ["enable_for_collection"]
}
```

## 注意事项

1. **提供商必须存在**: 在添加模型之前，确保对应的提供商已经创建并启用

2. **模型名称唯一性**: 同一提供商下，相同 API 类型的模型名称不能重复

3. **API 类型选择**:

   - `completion`: 用于文本生成、对话、视觉理解
   - `embedding`: 用于文本向量化
   - `rerank`: 用于文档重排序

4. **标签使用**:

   - `enable_for_agent`: 模型可用于 Agent 功能
   - `enable_for_collection`: 模型可用于 Collection 索引构建
   - `vision`: 标记视觉模型（仅用于 completion API）

5. **自定义提供商**: `custom_llm_provider` 字段决定了系统使用哪个 API 客户端，必须与提供商的实际 API 兼容

## 验证模型

添加模型后，您可以通过以下方式验证：

1. **在模型列表中查看**: 返回模型管理页面，确认新模型已出现在列表中
2. **在 Collection 中使用**: 创建或编辑 Collection 时，在 LLM 设置中应该能看到新模型
3. **在 Agent 中使用**: 在聊天界面中，应该能看到并选择新模型

## 故障排除

### 问题：模型添加后无法使用

**可能原因**:

- 提供商未启用
- 模型标签未正确设置（如未启用 `enable_for_agent` 或 `enable_for_collection`）
- API 密钥未配置

**解决方法**:

1. 检查提供商状态，确保已启用
2. 检查模型的标签设置
3. 确认提供商已配置有效的 API 密钥

### 问题：模型名称已存在

**解决方法**:

- 使用不同的模型名称
- 或者编辑现有模型而不是创建新模型

## 相关文档

- [如何配置本地 Ollama](how-to-configure-ollama-zh.md)
- [提供商切换指南](../PROVIDER_SWITCHING_GUIDE.md)
- [视觉模型配置指南](../../VISION_MODEL_CONFIGURATION_GUIDE.md)
