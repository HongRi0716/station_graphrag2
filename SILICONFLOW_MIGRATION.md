# ApeRAGv2 硅基流动 (SiliconFlow) API 提供商配置迁移

## 概述

本文档记录了将 ApeRAGv2 的默认 API 提供商更改为硅基流动（SiliconFlow）的配置变更。

## 配置分析

### ApeRAG 的 API 提供商配置架构

ApeRAG 使用三层架构来管理 API 提供商：

1. **数据库层**：在 `aperag/migration/sql/model_configs_init.sql` 中定义提供商配置

   - 提供商基本信息（名称、标签、base_url 等）
   - 模型配置（completion、embedding、rerank 模型）

2. **环境变量层**：在 `envs/env.template` 中设置默认提供商

   - 默认的 completion、embedding、rerank 提供商
   - 各提供商的 API 密钥配置

3. **代码生成层**：在 `models/generate_model_configs.py` 中定义配置生成函数
   - `create_siliconflow_config()` 函数生成完整的配置

### 硅基流动配置详情

- **提供商名称**: `siliconflow`
- **显示名称**: `SiliconFlow`
- **API Base URL**: `https://api.siliconflow.cn/v1`
- **Completion Dialect**: `openai`
- **Embedding Dialect**: `openai`
- **Rerank Dialect**: `jina_ai`
- **允许自定义 Base URL**: `False`

### 支持的模型

#### Completion Models

- Pro/Qwen/Qwen2.5-VL-7B-Instruct (vision)
- Qwen/QVQ-72B-Preview (vision)
- Qwen/Qwen2.5-VL-32B-Instruct (vision)
- Qwen/Qwen2.5-VL-72B-Instruct (vision)
- Qwen/Qwen3-8B
- THUDM/GLM-4.1V-9B-Thinking (vision, free)
- deepseek-ai/DeepSeek-R1
- deepseek-ai/DeepSeek-V3
- deepseek-ai/deepseek-vl2 (vision)

#### Embedding Models

- BAAI/bge-m3 (free, enable_for_collection)

#### Rerank Models

- BAAI/bge-reranker-v2-m3 (enable_for_collection)
- netease-youdao/bce-reranker-base_v1 (enable_for_collection)

## 已完成的更改

### 1. 环境配置文件 (envs/env.template)

**状态**: ✅ 已完成

在环境配置模板中添加了硅基流动作为默认提供商：

```bash
# SiliconFlow defaults (override as needed)
COMPLETION_MODEL_PROVIDER=siliconflow
COMPLETION_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
COMPLETION_MODEL_PROVIDER_API_KEY=

EMBEDDING_MODEL_PROVIDER=siliconflow
EMBEDDING_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL_PROVIDER_API_KEY=

RERANK_MODEL_PROVIDER=siliconflow
RERANK_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
RERANK_MODEL_PROVIDER_API_KEY=

VISION_LLM_PROVIDER=siliconflow
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
VISION_LLM_API_KEY=

TEMPLATE_COLLECTION_ID=
```

### 2. 测试配置文件 (tests/e2e_test/config.py)

**状态**: ✅ 已完成

将测试默认提供商从 `alibabacloud` 和 `openrouter` 更改为 `siliconflow`：

**之前**:

- EMBEDDING_MODEL_PROVIDER: `alibabacloud`
- COMPLETION_MODEL_PROVIDER: `openrouter`
- RERANK_MODEL_PROVIDER: `alibabacloud`

**之后**:

- EMBEDDING_MODEL_PROVIDER: `siliconflow`
- COMPLETION_MODEL_PROVIDER: `siliconflow`
- RERANK_MODEL_PROVIDER: `siliconflow`

对应的模型也更新为：

- EMBEDDING_MODEL_NAME: `BAAI/bge-m3`
- COMPLETION_MODEL_NAME: `Qwen/Qwen3-8B`
- RERANK_MODEL_NAME: `BAAI/bge-reranker-v2-m3`

### 3. 数据库初始化脚本

**状态**: ✅ 已存在（无需修改）

`aperag/migration/sql/model_configs_init.sql` 文件中已经包含完整的硅基流动配置（第 117-133 行），包括：

- 提供商基本信息
- 所有支持的模型定义

### 4. 配置生成器

**状态**: ✅ 已存在（无需修改）

`models/generate_model_configs.py` 中已经包含 `create_siliconflow_config()` 函数。

## 使用说明

### 1. 配置 API 密钥

在使用硅基流动之前，需要配置 API 密钥。有两种方式：

#### 方式一：通过环境变量（推荐）

复制 `envs/env.template` 为 `.env` 并填写 API 密钥：

```bash
cp envs/env.template .env
```

编辑 `.env` 文件，填写硅基流动的 API 密钥：

```bash
COMPLETION_MODEL_PROVIDER_API_KEY=your_siliconflow_api_key_here
EMBEDDING_MODEL_PROVIDER_API_KEY=your_siliconflow_api_key_here
RERANK_MODEL_PROVIDER_API_KEY=your_siliconflow_api_key_here
VISION_LLM_API_KEY=your_siliconflow_api_key_here
```

#### 方式二：通过 Web 界面

1. 启动 ApeRAG 服务
2. 访问 http://localhost:3000/web/
3. 进入"设置" -> "模型提供商"
4. 找到"SiliconFlow"提供商
5. 点击配置，输入 API 密钥并保存

### 2. 获取硅基流动 API 密钥

1. 访问 [硅基流动官网](https://siliconflow.cn/)
2. 注册/登录账号
3. 在控制台中创建 API 密钥
4. 复制 API 密钥到配置文件或 Web 界面

### 3. 验证配置

启动服务后，可以通过以下方式验证配置：

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f aperag-backend

# 访问API文档
# http://localhost:8000/docs
```

在 Web 界面中：

1. 创建一个新的 Collection
2. 上传文档
3. 进行对话测试

## 注意事项

1. **API 密钥安全**：不要将 API 密钥提交到版本控制系统中，使用 `.env` 文件（已在 `.gitignore` 中）

2. **免费模型**：硅基流动提供一些免费模型（标记为 `free`），如：

   - BAAI/bge-m3 (embedding)
   - THUDM/GLM-4.1V-9B-Thinking (completion with vision)

3. **模型兼容性**：硅基流动使用 OpenAI 兼容的 API，因此 `completion_dialect` 和 `embedding_dialect` 都设置为 `openai`

4. **Rerank 功能**：Rerank 模型使用 `jina_ai` dialect，确保 litellm 支持

5. **视觉模型**：硅基流动提供多个视觉语言模型（VLM），默认使用 `Pro/Qwen/Qwen2.5-VL-7B-Instruct`

## 与 ApeRAG 的差异

ApeRAGv2 现在与 ApeRAG 在硅基流动配置上保持一致：

| 配置项                 | ApeRAG                | ApeRAGv2 (更新后)        |
| ---------------------- | --------------------- | ------------------------ |
| 默认 Completion 提供商 | siliconflow           | siliconflow ✅           |
| 默认 Embedding 提供商  | siliconflow           | siliconflow ✅           |
| 默认 Rerank 提供商     | siliconflow           | siliconflow ✅           |
| 默认 Vision 提供商     | siliconflow           | siliconflow ✅           |
| SQL 初始化脚本         | 包含 siliconflow      | 包含 siliconflow ✅      |
| 配置生成器             | 包含 siliconflow 函数 | 包含 siliconflow 函数 ✅ |

## 更新日期

2025-11-12

## 相关文件

- `ApeRAGv2/envs/env.template` - 环境变量模板（已更新）
- `ApeRAGv2/tests/e2e_test/config.py` - 测试配置（已更新）
- `ApeRAGv2/aperag/migration/sql/model_configs_init.sql` - 数据库初始化脚本（已存在）
- `ApeRAGv2/models/generate_model_configs.py` - 配置生成器（已存在）
