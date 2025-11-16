# Docker 环境图片处理失败诊断指南

## 问题现象

在 Docker 环境中，图片文件（PNG、JPG 等）或包含图片的 PDF 文件处理失败，Vision 索引创建失败。

## 快速诊断步骤

### 方法一：使用诊断脚本（推荐）

```bash
# 在Docker容器内运行诊断脚本
docker exec aperag-celeryworker python diagnose_vision_failure.py --document-id {document_id} --collection-id {collection_id}

# 或者只检查环境配置
docker exec aperag-celeryworker python diagnose_vision_failure.py
```

### 方法二：手动检查

#### 1. 检查环境变量配置

```bash
# 检查Vision LLM环境变量
docker exec aperag-celeryworker env | grep VISION_LLM

# 应该看到：
# VISION_LLM_PROVIDER=siliconflow
# VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
# VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
# VISION_LLM_API_KEY=your_api_key
```

**如果环境变量未设置**，需要在`.env`或`envs/docker.env.overrides`中添加：

```bash
# Vision LLM配置（用于图片分析生成文本）
VISION_LLM_PROVIDER=siliconflow
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
VISION_LLM_API_KEY=your_siliconflow_api_key
```

#### 2. 检查 Celery Worker 日志

```bash
# 查看Vision相关的错误日志
docker logs aperag-celeryworker --tail 500 | grep -i "vision\|image\|multimodal"

# 查看特定文档的处理日志
docker logs aperag-celeryworker --tail 1000 | grep -i "{document_id}"
```

常见错误信息：

- `Neither multimodal embedding nor vision completion model is configured`

  - **原因**: 既没有配置多模态 Embedding，也没有配置 Vision LLM
  - **解决**: 配置 VISION_LLM 环境变量

- `Failed to create pure vision embedding`

  - **原因**: 多模态 Embedding 处理失败
  - **解决**: 检查 Embedding 服务配置和网络连接

- `Failed to create vision-to-text embedding`
  - **原因**: Vision LLM 调用失败
  - **解决**: 检查 VISION_LLM 配置和 API 密钥

#### 3. 检查 Vision 索引状态

```bash
# 通过API查询文档索引状态
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.indexes[] | select(.index_type == "VISION")'
```

或者直接查询数据库：

```sql
-- 查询Vision索引状态
SELECT
    d.name AS document_name,
    di.index_type,
    di.status,
    di.error_message,
    di.gmt_updated
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE d.id = '{document_id}'
  AND di.index_type = 'VISION';
```

#### 4. 检查 Collection 配置

确保 Collection 已启用 Vision 索引：

```bash
# 通过API查询Collection配置
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.config.enable_vision'
```

应该返回`true`。

#### 5. 检查向量存储连接

```bash
# 检查Qdrant服务状态
docker ps | grep qdrant

# 测试网络连接
docker exec aperag-celeryworker ping -c 3 aperag-qdrant

# 检查向量存储配置
docker exec aperag-celeryworker env | grep VECTOR_DB
```

#### 6. 检查 Vision LLM API 连接

```bash
# 测试Vision LLM API连接
VISION_LLM_BASE_URL=$(docker exec aperag-celeryworker env | grep VISION_LLM_BASE_URL | cut -d= -f2)
docker exec aperag-celeryworker curl -f ${VISION_LLM_BASE_URL}/health

# 或者直接测试API
docker exec aperag-celeryworker curl -X POST "${VISION_LLM_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${VISION_LLM_API_KEY}" \
  -d '{"model":"test","messages":[{"role":"user","content":"test"}]}'
```

## 常见失败原因及解决方案

### 原因 1：Vision LLM 未配置（最常见）

**症状**：

- 日志显示：`Neither multimodal embedding nor vision completion model is configured`
- Vision 索引状态为`SKIPPED`

**解决方案**：

1. **配置 VISION_LLM 环境变量**：

在`.env`或`envs/docker.env.overrides`中添加：

```bash
VISION_LLM_PROVIDER=siliconflow
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
VISION_LLM_API_KEY=your_api_key
```

2. **重启 Celery Worker**：

```bash
docker-compose restart celeryworker
```

3. **验证配置**：

```bash
docker exec aperag-celeryworker env | grep VISION_LLM
```

### 原因 2：Vision LLM API 密钥无效

**症状**：

- 日志显示：`Failed to create vision-to-text embedding`
- 错误信息包含：`401 Unauthorized`或`Invalid API key`

**解决方案**：

1. **检查 API 密钥**：

```bash
docker exec aperag-celeryworker env | grep VISION_LLM_API_KEY
```

2. **验证 API 密钥有效性**：

```bash
# 测试API调用
curl -X POST "https://api.siliconflow.cn/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "Pro/Qwen/Qwen2.5-VL-7B-Instruct",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

3. **更新 API 密钥**：

在`.env`文件中更新`VISION_LLM_API_KEY`，然后重启服务。

### 原因 3：网络连接问题

**症状**：

- 日志显示：`Connection timeout`或`Failed to connect`
- Vision LLM API 调用失败

**解决方案**：

1. **检查网络连接**：

```bash
# 从容器内测试连接
docker exec aperag-celeryworker curl -f https://api.siliconflow.cn/v1/health

# 检查DNS解析
docker exec aperag-celeryworker nslookup api.siliconflow.cn
```

2. **检查防火墙和代理设置**：

确保 Docker 容器可以访问外部 API。

3. **使用代理（如果需要）**：

在`docker-compose.yml`中配置代理：

```yaml
celeryworker:
  environment:
    - HTTP_PROXY=http://proxy:port
    - HTTPS_PROXY=http://proxy:port
```

### 原因 4：图片数据编码问题

**症状**：

- 日志显示：`Failed to encode image`或`Invalid image data`
- Base64 编码失败

**解决方案**：

1. **检查图片文件大小**：

```bash
# 查看文档大小
docker exec aperag-celeryworker python -c "
from aperag.db.models import Document
from aperag.config import get_sync_session
for session in get_sync_session():
    doc = session.query(Document).filter_by(id='{document_id}').first()
    if doc:
        print(f'Document size: {doc.size} bytes')
        print(f'Max size: {10 * 1024 * 1024} bytes (10MB)')
"
```

2. **检查图片格式**：

确保图片格式受支持（PNG、JPG、JPEG 等）。

### 原因 5：向量存储连接失败

**症状**：

- 日志显示：`Failed to store vectors`或`Vector store connection failed`
- Vision 索引创建失败

**解决方案**：

1. **检查 Qdrant 服务**：

```bash
docker ps | grep qdrant
docker logs aperag-qdrant --tail 50
```

2. **检查向量存储配置**：

```bash
docker exec aperag-celeryworker env | grep VECTOR_DB
```

3. **测试连接**：

```bash
docker exec aperag-celeryworker python -c "
from aperag.config import get_vector_db_connector
from aperag.utils.utils import generate_vector_db_collection_name
try:
    connector = get_vector_db_connector(collection=generate_vector_db_collection_name(collection_id='test'))
    print('Vector store connection OK')
except Exception as e:
    print(f'Vector store connection failed: {e}')
"
```

### 原因 6：Collection 未启用 Vision 索引

**症状**：

- Vision 索引状态为`SKIPPED`
- 日志显示：`Vision index is disabled`

**解决方案**：

1. **通过 Web 界面启用**：

   - 进入 Collection 设置
   - 勾选"Vision 索引"选项
   - 保存设置

2. **通过 API 启用**：

```bash
curl -X PUT "http://localhost:8000/api/v1/collections/{collection_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "config": {
      "enable_vision": true
    }
  }'
```

3. **重建 Vision 索引**：

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VISION"]
  }'
```

## 完整诊断流程

### 步骤 1：检查环境变量

```bash
docker exec aperag-celeryworker env | grep -E "VISION_LLM|EMBEDDING|VECTOR_DB"
```

### 步骤 2：检查服务状态

```bash
# 检查所有相关服务
docker ps | grep -E "celeryworker|qdrant|docray"

# 检查服务健康状态
docker exec aperag-celeryworker celery -A config.celery inspect active
```

### 步骤 3：查看错误日志

```bash
# 实时查看日志
docker-compose logs -f celeryworker | grep -i "vision\|image\|error"

# 查看最近的错误
docker logs aperag-celeryworker --tail 500 | grep -i "error\|fail\|vision"
```

### 步骤 4：测试 Vision LLM 连接

```bash
# 获取环境变量
VISION_LLM_BASE_URL=$(docker exec aperag-celeryworker env | grep VISION_LLM_BASE_URL | cut -d= -f2)
VISION_LLM_API_KEY=$(docker exec aperag-celeryworker env | grep VISION_LLM_API_KEY | cut -d= -f2)

# 测试API调用
docker exec aperag-celeryworker curl -X POST "${VISION_LLM_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${VISION_LLM_API_KEY}" \
  -d '{
    "model": "Pro/Qwen/Qwen2.5-VL-7B-Instruct",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

## 修复失败的索引

### 方法一：通过 Web 界面重建

1. 进入文档详情页
2. 找到失败的 VISION 索引
3. 点击"重建索引"按钮

### 方法二：通过 API 重建

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VISION"]
  }'
```

### 方法三：重建 Collection 中所有失败的索引

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/rebuild-failed-indexes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 预防措施

### 1. 配置检查清单

- [ ] `VISION_LLM_PROVIDER`已配置
- [ ] `VISION_LLM_MODEL`已配置
- [ ] `VISION_LLM_BASE_URL`已配置
- [ ] `VISION_LLM_API_KEY`已配置且有效
- [ ] Collection 配置中`enable_vision`为`true`
- [ ] 向量存储服务正常运行
- [ ] 网络连接正常（可以访问 Vision LLM API）

### 2. 监控 Vision 索引创建

```bash
# 实时监控celery worker日志
docker-compose logs -f celeryworker | grep -i "vision"

# 定期检查失败的索引
# 通过API或数据库查询
```

### 3. 资源要求

Vision 索引创建需要：

- **CPU**: 2+ 核心（用于图片编码和 API 调用）
- **内存**: 4GB+ RAM（用于处理大图片）
- **网络**: 稳定的网络连接（访问 Vision LLM API）
- **存储**: 足够的磁盘空间（存储向量数据）

## 相关文档

- [知识图谱诊断指南](KNOWLEDGE_GRAPH_DIAGNOSIS.md)
- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [Vision 索引创建流程](docs/design/vision_index_creation_zh.md)

## 获取帮助

如果问题仍未解决，请收集以下信息：

1. Celery Worker 日志（包含 Vision 相关部分）
2. 环境变量配置（隐藏敏感信息）
3. Vision 索引状态和错误信息
4. Vision LLM API 测试结果
5. 向量存储连接状态

然后提交 Issue 或联系技术支持。
