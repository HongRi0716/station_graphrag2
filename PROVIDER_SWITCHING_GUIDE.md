# ApeRAG 提供商灵活切换完全指南

## 概述

ApeRAG 提供了多种灵活的方式来管理和切换 API 提供商，无需重启服务即可动态更换。本文档详细介绍所有切换方法。

## 目录

1. [提供商管理架构](#提供商管理架构)
2. [方法一：Web 界面切换（推荐）](#方法一web-界面切换推荐)
3. [方法二：REST API 切换](#方法二rest-api-切换)
4. [方法三：环境变量配置](#方法三环境变量配置)
5. [方法四：数据库直接管理](#方法四数据库直接管理)
6. [实际应用场景](#实际应用场景)
7. [最佳实践](#最佳实践)

---

## 提供商管理架构

ApeRAG 使用三层分离的架构来管理提供商：

### 1. 提供商配置层（LLM Provider）
存储在 `llm_provider` 表中，包含：
- 提供商名称、标签、Base URL
- API 方言配置（completion/embedding/rerank）
- 是否允许自定义 Base URL

### 2. 模型配置层（LLM Provider Models）
存储在 `llm_provider_models` 表中，包含：
- 每个提供商支持的具体模型
- 模型的上下文窗口、最大 token 等参数
- 模型标签（如 free、recommend、vision）

### 3. API 密钥层（Model Service Provider）
存储在 `model_service_provider` 表中：
- 用户或系统级别的 API 密钥
- 支持一个提供商配置多个 API 密钥（按用户隔离）

**关键特性**：三层解耦设计允许在运行时动态切换，无需重启服务。

---

## 方法一：Web 界面切换（推荐）

### 适用场景
- 日常使用
- 非技术用户
- 可视化管理多个提供商

### 操作步骤

#### 1. 访问提供商管理页面
```
http://localhost:3000/web/workspace/providers
```

#### 2. 查看所有提供商
系统会显示所有可用的提供商列表，包括：
- ✅ 已启用（已配置 API 密钥）
- ⚪ 未启用（未配置 API 密钥）

#### 3. 启用新提供商

**方式 A：配置现有提供商**
1. 找到要启用的提供商（如 `SiliconFlow`）
2. 点击提供商卡片上的"配置"按钮
3. 输入 API 密钥
4. 点击"保存"

**方式 B：创建自定义提供商**
1. 点击"添加提供商"按钮
2. 填写信息：
   ```
   名称: my-custom-provider
   标签: My Custom Provider
   Base URL: https://api.example.com/v1
   Completion Dialect: openai
   Embedding Dialect: openai
   Rerank Dialect: jina_ai
   API Key: your-api-key
   ```
3. 点击"创建"

#### 4. 设置为默认提供商

**Collection 级别**：
1. 进入"Collections"页面
2. 编辑或创建 Collection
3. 在"模型配置"部分选择：
   - Completion Model: 选择新提供商和模型
   - Embedding Model: 选择新提供商和模型
   - Rerank Model: 选择新提供商和模型

**系统级别**：
1. 进入"设置" -> "默认模型"
2. 为不同场景设置默认提供商：
   - Collection Completion: 用于文档对话
   - Agent Completion: 用于智能代理
   - Embedding: 用于文档索引
   - Rerank: 用于结果重排
   - Background Task: 用于后台任务

#### 5. 禁用提供商
1. 找到要禁用的提供商
2. 点击"禁用"按钮
3. 系统会删除该提供商的 API 密钥（但保留配置）

### Web 界面功能
- ✅ 实时生效，无需重启
- ✅ 可视化管理
- ✅ API 密钥加密存储
- ✅ 支持批量切换
- ✅ 显示提供商状态

---

## 方法二：REST API 切换

### 适用场景
- 自动化部署
- 批量管理
- CI/CD 集成
- 脚本化操作

### API 端点

#### 1. 获取所有提供商配置
```bash
GET /api/v1/llm_configuration
```

**示例请求**：
```bash
curl -X GET "http://localhost:8000/api/v1/llm_configuration" \
  -H "Authorization: Bearer your-api-key"
```

**响应示例**：
```json
{
  "providers": [
    {
      "name": "siliconflow",
      "label": "SiliconFlow",
      "base_url": "https://api.siliconflow.cn/v1",
      "completion_dialect": "openai",
      "embedding_dialect": "openai",
      "rerank_dialect": "jina_ai",
      "api_key": "sk-****abc"
    }
  ],
  "models": [...]
}
```

#### 2. 创建新提供商
```bash
POST /api/v1/llm_providers
```

**示例请求**：
```bash
curl -X POST "http://localhost:8000/api/v1/llm_providers" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-provider",
    "label": "My Provider",
    "base_url": "https://api.example.com/v1",
    "completion_dialect": "openai",
    "embedding_dialect": "openai",
    "rerank_dialect": "jina_ai",
    "api_key": "your-api-key-here",
    "status": "enable"
  }'
```

#### 3. 更新提供商（切换 API 密钥）
```bash
PUT /api/v1/llm_providers/{provider_name}
```

**示例：启用硅基流动**：
```bash
curl -X PUT "http://localhost:8000/api/v1/llm_providers/siliconflow" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-your-siliconflow-key",
    "status": "enable"
  }'
```

**示例：禁用提供商**：
```bash
curl -X PUT "http://localhost:8000/api/v1/llm_providers/openai" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "disable"
  }'
```

#### 4. 获取特定提供商
```bash
GET /api/v1/llm_providers/{provider_name}
```

**示例**：
```bash
curl -X GET "http://localhost:8000/api/v1/llm_providers/siliconflow" \
  -H "Authorization: Bearer your-api-key"
```

#### 5. 获取提供商的模型列表
```bash
GET /api/v1/llm_providers/{provider_name}/models
```

**示例**：
```bash
curl -X GET "http://localhost:8000/api/v1/llm_providers/siliconflow/models" \
  -H "Authorization: Bearer your-api-key"
```

#### 6. 添加模型到提供商
```bash
POST /api/v1/llm_providers/{provider_name}/models
```

**示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/llm_providers/siliconflow/models" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "api": "completion",
    "model": "Qwen/Qwen3-8B",
    "custom_llm_provider": "openai",
    "tags": ["recommend"]
  }'
```

#### 7. 更新默认模型
```bash
PUT /api/v1/default_models
```

**示例：切换到硅基流动**：
```bash
curl -X PUT "http://localhost:8000/api/v1/default_models" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "defaults": [
      {
        "scenario": "default_for_embedding",
        "provider_name": "siliconflow",
        "model": "BAAI/bge-m3",
        "custom_llm_provider": "openai"
      },
      {
        "scenario": "default_for_collection_completion",
        "provider_name": "siliconflow",
        "model": "Qwen/Qwen3-8B",
        "custom_llm_provider": "openai"
      },
      {
        "scenario": "default_for_rerank",
        "provider_name": "siliconflow",
        "model": "BAAI/bge-reranker-v2-m3",
        "custom_llm_provider": "jina_ai"
      }
    ]
  }'
```

### Python 脚本示例

**一键切换到硅基流动**：
```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your-aperag-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 1. 启用硅基流动
response = requests.put(
    f"{BASE_URL}/api/v1/llm_providers/siliconflow",
    headers=headers,
    json={
        "api_key": "sk-your-siliconflow-key",
        "status": "enable"
    }
)
print(f"Enable SiliconFlow: {response.status_code}")

# 2. 设置为默认
response = requests.put(
    f"{BASE_URL}/api/v1/default_models",
    headers=headers,
    json={
        "defaults": [
            {
                "scenario": "default_for_embedding",
                "provider_name": "siliconflow",
                "model": "BAAI/bge-m3",
                "custom_llm_provider": "openai"
            },
            {
                "scenario": "default_for_collection_completion",
                "provider_name": "siliconflow",
                "model": "Qwen/Qwen3-8B",
                "custom_llm_provider": "openai"
            },
            {
                "scenario": "default_for_rerank",
                "provider_name": "siliconflow",
                "model": "BAAI/bge-reranker-v2-m3",
                "custom_llm_provider": "jina_ai"
            }
        ]
    }
)
print(f"Set Default Models: {response.status_code}")

# 3. 禁用其他提供商（可选）
for provider in ["openai", "anthropic", "openrouter"]:
    response = requests.put(
        f"{BASE_URL}/api/v1/llm_providers/{provider}",
        headers=headers,
        json={"status": "disable"}
    )
    print(f"Disable {provider}: {response.status_code}")
```

---

## 方法三：环境变量配置

### 适用场景
- 初始部署
- Docker 容器配置
- 环境隔离（开发/测试/生产）

### 配置步骤

#### 1. 编辑 `.env` 文件
```bash
cp envs/env.template .env
nano .env
```

#### 2. 设置默认提供商
```bash
# 切换到硅基流动
COMPLETION_MODEL_PROVIDER=siliconflow
COMPLETION_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
COMPLETION_MODEL_PROVIDER_API_KEY=sk-your-key

EMBEDDING_MODEL_PROVIDER=siliconflow
EMBEDDING_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL_PROVIDER_API_KEY=sk-your-key

RERANK_MODEL_PROVIDER=siliconflow
RERANK_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
RERANK_MODEL_PROVIDER_API_KEY=sk-your-key

VISION_LLM_PROVIDER=siliconflow
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
VISION_LLM_API_KEY=sk-your-key
```

#### 3. 重启服务（仅首次配置需要）
```bash
docker-compose restart aperag-backend
```

### Docker Compose 配置
```yaml
services:
  aperag-backend:
    environment:
      - COMPLETION_MODEL_PROVIDER=siliconflow
      - COMPLETION_MODEL_PROVIDER_API_KEY=${SILICONFLOW_API_KEY}
      - EMBEDDING_MODEL_PROVIDER=siliconflow
      - EMBEDDING_MODEL_PROVIDER_API_KEY=${SILICONFLOW_API_KEY}
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aperag-config
data:
  COMPLETION_MODEL_PROVIDER: "siliconflow"
  EMBEDDING_MODEL_PROVIDER: "siliconflow"
  RERANK_MODEL_PROVIDER: "siliconflow"
---
apiVersion: v1
kind: Secret
metadata:
  name: aperag-secrets
type: Opaque
stringData:
  COMPLETION_MODEL_PROVIDER_API_KEY: "sk-your-key"
  EMBEDDING_MODEL_PROVIDER_API_KEY: "sk-your-key"
  RERANK_MODEL_PROVIDER_API_KEY: "sk-your-key"
```

---

## 方法四：数据库直接管理

### 适用场景
- 批量迁移
- 数据备份/恢复
- 高级调试

### SQL 操作

#### 1. 查看所有提供商
```sql
SELECT name, label, base_url, user_id 
FROM llm_provider 
WHERE gmt_deleted IS NULL;
```

#### 2. 启用提供商（添加 API 密钥）
```sql
INSERT INTO model_service_provider (name, api_key, gmt_created, gmt_updated)
VALUES ('siliconflow', 'sk-your-key', NOW(), NOW())
ON CONFLICT (name) 
DO UPDATE SET api_key = EXCLUDED.api_key, gmt_updated = NOW();
```

#### 3. 禁用提供商（删除 API 密钥）
```sql
UPDATE model_service_provider 
SET gmt_deleted = NOW() 
WHERE name = 'openai';
```

#### 4. 查看提供商的模型
```sql
SELECT provider_name, api, model, tags 
FROM llm_provider_models 
WHERE provider_name = 'siliconflow' 
  AND gmt_deleted IS NULL;
```

#### 5. 添加自定义模型
```sql
INSERT INTO llm_provider_models 
  (provider_name, api, model, custom_llm_provider, tags, gmt_created, gmt_updated)
VALUES 
  ('siliconflow', 'completion', 'Qwen/Qwen3-70B', 'openai', 
   '["recommend"]'::jsonb, NOW(), NOW())
ON CONFLICT (provider_name, api, model) DO NOTHING;
```

---

## 实际应用场景

### 场景 1：从 OpenRouter 切换到硅基流动

**需求**：降低成本，使用免费模型

**步骤**（Web 界面）：
1. 访问"提供商"页面
2. 找到"SiliconFlow"，点击"配置"
3. 输入硅基流动 API 密钥，点击保存
4. 访问"设置" -> "默认模型"
5. 将所有场景的提供商改为"siliconflow"
6. 选择对应模型：
   - Embedding: BAAI/bge-m3（免费）
   - Completion: Qwen/Qwen3-8B
   - Rerank: BAAI/bge-reranker-v2-m3
7. 保存设置

**验证**：创建新对话，检查是否使用新提供商

---

### 场景 2：多环境配置（开发/生产）

**需求**：开发环境用免费模型，生产环境用高性能模型

**开发环境 `.env`**：
```bash
COMPLETION_MODEL_PROVIDER=siliconflow
COMPLETION_MODEL_PROVIDER_API_KEY=sk-dev-key
EMBEDDING_MODEL_PROVIDER=siliconflow
```

**生产环境 `.env`**：
```bash
COMPLETION_MODEL_PROVIDER=openrouter
COMPLETION_MODEL_PROVIDER_API_KEY=sk-prod-key
EMBEDDING_MODEL_PROVIDER=openai
```

---

### 场景 3：AB 测试不同提供商

**需求**：对比不同提供商的效果

**方法**：
1. 为不同 Collection 配置不同提供商
2. Collection A: 使用 SiliconFlow
3. Collection B: 使用 OpenRouter
4. Collection C: 使用 OpenAI
5. 通过评估工具对比效果

---

### 场景 4：提供商故障切换

**需求**：主提供商不可用时自动切换到备用

**方法**（API 脚本）：
```python
def switch_provider_on_failure():
    providers = ["openrouter", "siliconflow", "openai"]
    
    for provider in providers:
        try:
            # 测试提供商
            response = test_provider(provider)
            if response.ok:
                # 切换到可用提供商
                enable_provider(provider)
                set_as_default(provider)
                print(f"Switched to {provider}")
                break
        except Exception as e:
            print(f"{provider} failed: {e}")
            continue
```

---

### 场景 5：按用户隔离提供商

**需求**：不同用户使用不同的 API 密钥

**实现**：ApeRAG 原生支持用户级 API 密钥隔离

1. 用户 A 登录，配置自己的 OpenAI API 密钥
2. 用户 B 登录，配置自己的 SiliconFlow API 密钥
3. 系统自动使用各自的密钥，互不影响

---

## 最佳实践

### 1. 提供商选择原则

**成本优先**：
- 主：SiliconFlow（免费模型）
- 备：OpenRouter（按需付费）

**性能优先**：
- 主：OpenAI（高质量）
- 备：Anthropic（Claude 系列）

**平衡方案**：
- Embedding: SiliconFlow（BAAI/bge-m3，免费且效果好）
- Completion: OpenRouter（灵活选择模型）
- Rerank: SiliconFlow（免费）

### 2. API 密钥管理

**安全建议**：
- ✅ 使用环境变量存储密钥
- ✅ 定期轮换 API 密钥
- ✅ 使用只读权限的密钥（如支持）
- ✅ 监控 API 使用量和成本
- ❌ 不要在代码中硬编码密钥
- ❌ 不要提交 `.env` 到版本控制

### 3. 切换时机

**建议立即切换**：
- 发现更便宜的提供商
- 现有提供商频繁超时
- 需要特定模型（如视觉模型）

**建议延后切换**：
- 正在处理重要任务
- 需要先进行 AB 测试
- 还有大量 API 余额未用完

### 4. 监控和日志

**配置监控**：
```bash
# 查看提供商使用情况
docker-compose logs -f aperag-backend | grep "provider"

# 监控 API 调用
docker-compose logs -f aperag-backend | grep "api_key"
```

**Jaeger 追踪**（可选）：
```bash
# 启用分布式追踪
JAEGER_ENABLED=True
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

### 5. 测试流程

**切换前测试**：
1. 在测试环境先验证新提供商
2. 创建测试 Collection
3. 上传小文档进行测试
4. 验证 Embedding、Completion、Rerank 功能
5. 检查响应速度和质量
6. 确认无问题后在生产环境切换

### 6. 回滚计划

**出现问题时快速回滚**：
```bash
# Web 界面：1 分钟回滚
# 1. 访问"提供商"页面
# 2. 禁用新提供商
# 3. 启用旧提供商
# 4. 在"默认模型"中切换回去

# API 方式：30 秒回滚
curl -X PUT "http://localhost:8000/api/v1/llm_providers/openai" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"status": "enable"}'
```

### 7. 成本优化

**策略**：
1. **分级使用**：
   - 开发/测试：免费提供商
   - 生产：付费提供商
   
2. **按任务分配**：
   - 简单任务：使用小模型
   - 复杂任务：使用大模型
   
3. **缓存策略**：
   ```bash
   CACHE_ENABLED=True
   CACHE_TTL=86400  # 24小时
   ```

---

## 常见问题

### Q1: 切换提供商后旧的对话历史会丢失吗？
**A**: 不会。对话历史存储在数据库中，与提供商无关。

### Q2: 可以同时使用多个提供商吗？
**A**: 可以。不同 Collection 可以配置不同的提供商，系统会自动调用对应的 API。

### Q3: 切换提供商需要重启服务吗？
**A**: 不需要。通过 Web 界面或 API 切换后立即生效。

### Q4: API 密钥如何安全存储？
**A**: API 密钥加密存储在数据库的 `model_service_provider` 表中。

### Q5: 如何验证切换是否成功？
**A**: 
1. 查看"提供商"页面的状态指示
2. 创建新对话并检查模型信息
3. 查看日志：`docker-compose logs aperag-backend`

### Q6: 提供商不可用时系统会怎样？
**A**: 系统会返回错误信息，但不会崩溃。建议配置多个备用提供商。

### Q7: 可以自定义添加新提供商吗？
**A**: 可以，只要该提供商兼容 OpenAI 或其他支持的 API 格式。

---

## 总结

ApeRAG 提供了四种灵活的提供商切换方式：

| 方式 | 实时性 | 难度 | 适用场景 |
|------|--------|------|----------|
| **Web 界面** | ✅ 实时 | ⭐ 简单 | 日常使用 |
| **REST API** | ✅ 实时 | ⭐⭐ 中等 | 自动化 |
| **环境变量** | ❌ 需重启 | ⭐ 简单 | 初始配置 |
| **数据库** | ✅ 实时 | ⭐⭐⭐ 高级 | 批量操作 |

**推荐方案**：
- 普通用户：使用 **Web 界面**
- 开发运维：使用 **REST API** + 脚本自动化
- 初始部署：使用 **环境变量**

**核心优势**：
- ✅ 无需重启即可切换
- ✅ 支持多提供商并存
- ✅ 用户级密钥隔离
- ✅ 完整的 API 支持
- ✅ 可视化管理界面

---

## 相关资源

- [ApeRAG 官方文档](https://github.com/apecloud/ApeRAG)
- [硅基流动官网](https://siliconflow.cn/)
- [OpenRouter 文档](https://openrouter.ai/)
- [API 参考](http://localhost:8000/docs)

**更新日期**: 2025-11-12


