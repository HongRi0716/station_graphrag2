# 文档索引失败诊断指南

## 问题现象

文档"变电站图纸档案智能化管理技术.docx"建立向量和知识图谱失败。

## 快速诊断步骤

### 方法一:通过Web界面查看

1. 登录系统Web界面
2. 进入对应的Collection(知识库)
3. 找到该文档,查看文档详情页
4. 查看各个索引的状态:
   - ✅ COMPLETED - 索引成功
   - ❌ FAILED - 索引失败
   - 🔄 CREATING - 正在创建
   - ⏳ PENDING - 等待处理

5. 如果状态为FAILED,通常会显示错误信息

### 方法二:通过API查询

```bash
# 获取文档详情
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 方法三:直接查询数据库

使用提供的SQL脚本:

```bash
# 连接到PostgreSQL数据库
psql -h 127.0.0.1 -U postgres -d postgres -f diagnose_doc_failure.sql
```

或者手动执行查询:

```sql
-- 查询文档索引状态
SELECT 
    d.name,
    di.index_type,
    di.status,
    di.error_message,
    di.gmt_updated
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE d.name LIKE '%变电站%'
ORDER BY di.gmt_updated DESC;
```

### 方法四:查看Celery Worker日志

```bash
# 如果使用Docker Compose
docker-compose logs celery-worker --tail=200

# 或者查看系统日志
tail -f /var/log/aperag/celery-worker.log
```

## 常见失败原因及解决方案

### 1. 向量嵌入服务问题

**错误特征:**
- 错误信息包含: "embedding", "OpenAI", "API key", "rate limit"
- VECTOR索引状态为FAILED

**可能原因:**
- ❌ Embedding API密钥无效或过期
- ❌ API配额不足或达到速率限制
- ❌ 网络无法访问Embedding服务
- ❌ Embedding服务配置错误

**解决方案:**

1. 检查环境配置文件 `envs/.env`:
```bash
# 查看当前配置
cat envs/.env | grep -E "EMBEDDING|LLM"
```

2. 验证必需的配置项:
```bash
# 基础LLM配置
LLM_PROVIDER=openai  # 或其他提供商
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxx

# Embedding配置
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_SERVICE_URL=https://api.openai.com/v1
EMBEDDING_SERVICE_API_KEY=sk-xxx
```

3. 测试API连接:
```bash
# 测试OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

4. 常见配置问题:

**问题A: 使用国内API服务(如SiliconFlow)**
```bash
# 正确配置示例
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

EMBEDDING_PROVIDER=openai
EMBEDDING_SERVICE_URL=https://api.siliconflow.cn/v1
EMBEDDING_SERVICE_API_KEY=sk-xxx
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

**问题B: API密钥格式错误**
- 确保密钥没有多余的空格或换行
- 确保密钥格式正确(通常以sk-开头)

### 2. 知识图谱构建失败

**错误特征:**
- 错误信息包含: "graph", "neo4j", "nebula", "entity", "relationship"
- GRAPH索引状态为FAILED

**可能原因:**
- ❌ 图数据库未运行或连接失败
- ❌ LLM服务问题(用于实体和关系提取)
- ❌ 文档内容过长导致处理超时
- ❌ 图数据库存储空间不足

**解决方案:**

1. 检查图数据库连接配置 `envs/.env`:
```bash
# Neo4j配置
NEO4J_HOST=127.0.0.1
NEO4J_PORT=7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# 或 NebulaGraph配置
NEBULA_HOST=127.0.0.1
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
```

2. 验证图数据库是否运行:
```bash
# 检查Neo4j
docker ps | grep neo4j
# 或
curl http://localhost:7474

# 检查NebulaGraph
docker ps | grep nebula
```

3. 测试图数据库连接:
```python
# Neo4j连接测试
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single()[0])
driver.close()
```

4. 检查知识图谱是否启用:

通过API查询Collection配置:
```bash
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}"
```

确认配置中包含:
```json
{
  "config": {
    "enable_knowledge_graph": true
  }
}
```

### 3. 向量数据库连接问题

**错误特征:**
- 错误信息包含: "qdrant", "vector database", "connection"
- VECTOR索引创建时失败

**可能原因:**
- ❌ Qdrant服务未运行
- ❌ Qdrant连接配置错误
- ❌ 向量维度不匹配

**解决方案:**

1. 检查Qdrant配置 `envs/.env`:
```bash
VECTOR_DB_TYPE=qdrant
VECTOR_DB_CONTEXT={"url":"http://127.0.0.1","port":6333,"distance":"Cosine","timeout":1000}
```

2. 验证Qdrant是否运行:
```bash
# 检查服务状态
docker ps | grep qdrant

# 测试连接
curl http://localhost:6333/collections
```

3. 重启Qdrant服务(如果需要):
```bash
docker-compose restart qdrant
```

### 4. 文档解析问题

**错误特征:**
- 错误信息包含: "parse", "docx", "format", "corrupted"
- 所有索引都失败

**可能原因:**
- ❌ 文档格式损坏
- ❌ 文档包含不支持的特殊格式
- ❌ 文档过大
- ❌ 文档编码问题

**解决方案:**

1. 检查文档大小限制 `envs/.env`:
```bash
# 默认最大文档大小(字节)
MAX_DOCUMENT_SIZE=52428800  # 50MB
```

2. 验证文档是否可以正常打开:
- 使用Word打开文档
- 检查文档是否有密码保护
- 尝试另存为新文件

3. 查看文档解析日志:
```bash
docker-compose logs celery-worker | grep "parse"
```

4. 尝试重新上传:
- 如果文档下载自网络,尝试重新下载
- 如果是转换的文档,使用原始格式

### 5. LLM API调用失败

**错误特征:**
- 错误信息包含: "LLM", "API", "timeout", "rate limit", "quota"
- GRAPH或SUMMARY索引失败

**可能原因:**
- ❌ LLM API密钥问题
- ❌ API配额耗尽
- ❌ 网络超时
- ❌ 模型不支持

**解决方案:**

1. 检查LLM配置:
```bash
cat envs/.env | grep LLM
```

2. 验证API密钥:
```bash
# 测试OpenAI API
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

3. 检查API配额和余额

4. 调整超时设置(如果需要):
```bash
# 在envs/.env中
LLM_TIMEOUT=120  # 增加超时时间
```

## 修复失败的索引

### 方法一:通过Web界面重建

1. 进入文档详情页
2. 找到失败的索引
3. 点击"重建索引"按钮
4. 选择要重建的索引类型

### 方法二:通过API重建

```bash
# 重建单个文档的失败索引
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VECTOR", "GRAPH"]
  }'

# 重建Collection中所有失败的索引
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/rebuild-failed-indexes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 方法三:删除并重新上传

如果重建仍然失败:

1. 删除文档
2. 修复配置问题
3. 重新上传文档

## 预防措施

### 1. 配置检查清单

在上传文档之前,确保以下配置正确:

- [ ] LLM服务配置正确且可访问
- [ ] Embedding服务配置正确且可访问
- [ ] 向量数据库(Qdrant)运行正常
- [ ] 图数据库(Neo4j/NebulaGraph)运行正常(如果启用知识图谱)
- [ ] API密钥有效且配额充足
- [ ] 网络连接正常

### 2. 监控Celery Worker

```bash
# 实时查看worker日志
docker-compose logs -f celery-worker

# 查看worker状态
docker-compose exec celery-worker celery -A config.celery inspect active
```

### 3. 定期检查失败的任务

```sql
-- 查询最近失败的索引
SELECT COUNT(*), index_type, 
       LEFT(error_message, 100) as error_sample
FROM document_index
WHERE status = 'FAILED' 
  AND gmt_updated > NOW() - INTERVAL '24 hours'
GROUP BY index_type, LEFT(error_message, 100)
ORDER BY COUNT(*) DESC;
```

## 日志位置

根据部署方式,日志可能位于:

### Docker Compose部署
```bash
# Celery Worker日志
docker-compose logs celery-worker

# API服务日志
docker-compose logs api

# 所有服务日志
docker-compose logs
```

### 本地开发部署
```bash
# 查看Python日志
tail -f logs/aperag.log

# Celery日志
tail -f logs/celery.log
```

## 获取帮助

如果问题仍未解决:

1. 收集以下信息:
   - 完整的错误信息
   - 文档名称和大小
   - Collection配置
   - 环境配置(隐藏敏感信息)
   - Celery Worker日志

2. 提交Issue或联系技术支持

## 相关文档

- [Provider配置切换指南](PROVIDER_SWITCHING_GUIDE.md)
- [SiliconFlow迁移指南](SILICONFLOW_MIGRATION.md)
- [文档复制功能说明](FEATURE_COPY_DOCUMENTS.md)

