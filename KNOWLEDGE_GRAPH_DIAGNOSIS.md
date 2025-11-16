# 知识图谱未生成问题诊断指南

## 问题现象

文档"B5391S-T0102-土建总平面布置图.pdf"没有形成知识图谱。

## 快速诊断步骤

### 方法一：通过 Web 界面检查

1. 登录系统 Web 界面
2. 进入该文档所属的 Collection（知识库）
3. 查看 Collection 设置：
   - 进入 Collection 设置页面
   - 检查"知识图谱"选项是否已启用
4. 查看文档详情：
   - 进入文档详情页
   - 查看 GRAPH 索引的状态：
     - ✅ COMPLETED - 索引成功
     - ❌ FAILED - 索引失败
     - 🔄 CREATING - 正在创建
     - ⏳ PENDING - 等待处理
     - ⏭️ SKIPPED - 已跳过

### 方法二：通过 API 查询

```bash
# 1. 获取文档详情（需要替换collection_id和document_id）
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 获取Collection配置
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

检查返回的 JSON 中：

- `config.enable_knowledge_graph` 应该为 `true`
- `indexes` 数组中应该有 `GRAPH` 类型的索引记录

### 方法三：直接查询数据库

```sql
-- 1. 查找文档
SELECT id, name, collection_id, status
FROM document
WHERE name LIKE '%B5391S-T0102%' OR name LIKE '%土建总平面布置图%';

-- 2. 查看文档的索引状态
SELECT
    d.name AS document_name,
    di.index_type,
    di.status,
    di.error_message,
    di.gmt_updated
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE d.name LIKE '%B5391S-T0102%' OR d.name LIKE '%土建总平面布置图%'
ORDER BY di.index_type;

-- 3. 检查Collection配置
SELECT
    c.id,
    c.name,
    c.config
FROM collection c
JOIN document d ON c.id = d.collection_id
WHERE d.name LIKE '%B5391S-T0102%' OR d.name LIKE '%土建总平面布置图%';
```

### 方法四：查看 Celery Worker 日志

```bash
# 查看知识图谱相关的日志
docker logs aperag-celeryworker --tail 500 | grep -i "graph\|lightrag\|知识图谱"

# 查看特定文档的处理日志
docker logs aperag-celeryworker --tail 1000 | grep -i "B5391S\|土建"
```

## 常见原因及解决方案

### 原因 1：知识图谱未启用（最常见）

**症状**：

- GRAPH 索引状态为 SKIPPED 或不存在
- Collection 配置中`enable_knowledge_graph`为`false`

**解决方案**：

1. **通过 Web 界面启用**：

   - 进入 Collection 设置
   - 勾选"知识图谱"选项
   - 保存设置
   - 重建文档索引

2. **通过 API 启用**：

```bash
# 更新Collection配置
curl -X PUT "http://localhost:8000/api/v1/collections/{collection_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "config": {
      "enable_knowledge_graph": true,
      "knowledge_graph_config": {
        "language": "Chinese",
        "entity_types": ["organization", "person", "geo", "event", "product", "technology", "date", "category"]
      }
    }
  }'
```

3. **重建索引**：

```bash
# 重建GRAPH索引
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["GRAPH"]
  }'
```

### 原因 2：知识图谱索引创建失败

**症状**：

- GRAPH 索引状态为 FAILED
- 有错误信息

**可能原因**：

#### 2.1 LLM 服务问题

知识图谱构建需要 LLM 服务来提取实体和关系。

**检查 LLM 配置**：

```bash
# 查看环境变量
docker exec aperag-celeryworker env | grep -E "LLM_|COMPLETION_"
```

**验证 LLM 服务**：

```bash
# 测试LLM API
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**解决方案**：

1. 检查`LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY`等配置
2. 确保 LLM API 密钥有效且有足够配额
3. 检查网络连接

#### 2.2 图数据库连接问题

**检查图数据库配置**：

项目默认使用 PostgreSQL 存储知识图谱，但也可以使用 Neo4j 或 NebulaGraph。

```bash
# 检查Neo4j（如果使用）
docker ps | grep neo4j

# 检查NebulaGraph（如果使用）
docker ps | grep nebula

# 检查PostgreSQL（默认）
docker ps | grep postgres
```

**解决方案**：

1. 如果使用 Neo4j，确保服务运行并配置正确
2. 如果使用 NebulaGraph，确保服务运行并配置正确
3. 默认使用 PostgreSQL，通常不需要额外配置

#### 2.3 文档内容问题

**可能原因**：

- 文档内容为空或无法解析
- 文档内容不包含可提取的实体和关系
- 文档是纯图片（需要 OCR）

**解决方案**：

1. 检查文档是否成功解析（查看 VECTOR 索引是否成功）
2. 如果是图片型 PDF，确保 OCR 功能正常工作
3. 检查文档内容是否包含有意义的文本

### 原因 3：索引任务尚未执行

**症状**：

- GRAPH 索引状态为 PENDING
- 没有错误信息

**解决方案**：

1. 等待 celery worker 处理（通常 30 秒内）
2. 检查 celery worker 是否正常运行：
   ```bash
   docker ps | grep celeryworker
   docker logs aperag-celeryworker --tail 50
   ```
3. 手动触发索引创建：
   ```bash
   # 重建索引
   curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"index_types": ["GRAPH"]}'
   ```

### 原因 4：索引正在创建中

**症状**：

- GRAPH 索引状态为 CREATING
- 日志显示正在处理

**说明**：

- 知识图谱构建需要较长时间，特别是大文档
- 需要 LLM 多次调用来提取实体和关系
- 请耐心等待

**查看进度**：

```bash
# 实时查看处理日志
docker logs -f aperag-celeryworker | grep -i "graph\|lightrag"
```

## 完整诊断流程

### 步骤 1：检查 Collection 配置

```bash
# 通过API获取Collection信息
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.config.enable_knowledge_graph'
```

如果返回`false`，需要启用知识图谱。

### 步骤 2：检查文档索引状态

```bash
# 通过API获取文档信息
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.indexes[] | select(.index_type == "GRAPH")'
```

### 步骤 3：检查错误信息

如果 GRAPH 索引状态为 FAILED，查看错误信息：

```bash
# 从API响应中查看error_message字段
# 或查看celery worker日志
docker logs aperag-celeryworker --tail 500 | grep -A 10 -B 10 "GRAPH\|graph\|LightRAG"
```

### 步骤 4：检查服务状态

```bash
# 检查所有相关服务
docker ps | grep -E "celeryworker|postgres|neo4j|nebula"

# 检查celery worker健康状态
docker exec aperag-celeryworker celery -A config.celery inspect active
```

## 修复失败的索引

### 方法一：通过 Web 界面重建

1. 进入文档详情页
2. 找到失败的 GRAPH 索引
3. 点击"重建索引"按钮
4. 选择 GRAPH 索引类型

### 方法二：通过 API 重建

```bash
# 重建GRAPH索引
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["GRAPH"]
  }'
```

### 方法三：重建 Collection 中所有失败的索引

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/rebuild-failed-indexes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 预防措施

### 1. 创建 Collection 时启用知识图谱

在创建 Collection 时，确保配置中包含：

```json
{
  "config": {
    "enable_knowledge_graph": true,
    "knowledge_graph_config": {
      "language": "Chinese",
      "entity_types": [
        "organization",
        "person",
        "geo",
        "event",
        "product",
        "technology",
        "date",
        "category"
      ]
    }
  }
}
```

### 2. 配置检查清单

- [ ] Collection 配置中`enable_knowledge_graph`为`true`
- [ ] LLM 服务配置正确且可访问
- [ ] 图数据库（如果使用 Neo4j/NebulaGraph）运行正常
- [ ] Celery worker 正常运行
- [ ] 文档内容已成功解析（VECTOR 索引成功）

### 3. 监控知识图谱创建

```bash
# 实时监控celery worker日志
docker-compose logs -f celeryworker | grep -i "graph\|lightrag"

# 定期检查失败的索引
# 通过API或数据库查询
```

## 相关文档

- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [知识图谱创建流程](docs/design/graph_index_creation_zh.md)
- [架构设计文档](docs/design/architecture-zh.md)

## 获取帮助

如果问题仍未解决，请收集以下信息：

1. Collection 配置（特别是`enable_knowledge_graph`）
2. 文档的 GRAPH 索引状态和错误信息
3. Celery worker 日志（包含 GRAPH 相关部分）
4. LLM 服务配置（隐藏敏感信息）
5. 图数据库状态（如果使用）

然后提交 Issue 或联系技术支持。
