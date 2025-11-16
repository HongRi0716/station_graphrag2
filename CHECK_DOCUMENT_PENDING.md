# 文档 Pending 状态诊断指南

## 快速使用

### 在 Docker 容器中运行诊断脚本

```bash
# 检查特定文档（通过文件名）
docker exec aperag-celeryworker python check_document_pending.py --document-name "颍州变接线图"

# 检查特定文档（通过文档ID）
docker exec aperag-celeryworker python check_document_pending.py --document-id "doc7cd4efa65cdfbaf7"
```

## 脚本功能

该诊断脚本会检查以下内容：

1. **查找文档**: 通过文件名或 ID 查找文档
2. **检查索引状态**: 查看所有索引（VECTOR, FULLTEXT, GRAPH, VISION, SUMMARY）的状态
3. **检查 Reconciler 检测**: 验证 reconciler 是否能检测到需要处理的操作
4. **检查 Collection 配置**: 查看 Collection 的索引配置
5. **检查 Celery 状态**: 提供检查 Celery 服务的命令
6. **提供解决方案**: 根据检查结果提供修复建议

## 常见问题诊断

### 问题 1: 索引一直处于 PENDING 状态

**可能原因**:

- Celery Beat 未运行或未正确调度`reconcile_indexes_task`
- Celery Worker 未运行或资源不足
- 任务执行失败但未正确更新状态

**解决方案**:

1. 检查 Celery Beat 是否运行:

   ```bash
   docker ps | grep celerybeat
   ```

2. 检查 Celery Worker 是否运行:

   ```bash
   docker ps | grep celeryworker
   ```

3. 手动触发 reconciliation:

   ```bash
   docker exec aperag-celeryworker python -c "from config.celery_tasks import reconcile_indexes_task; reconcile_indexes_task()"
   ```

4. 查看 Celery 日志:
   ```bash
   docker logs aperag-celeryworker --tail 200 | grep -i "reconcile\|parse\|index"
   ```

### 问题 2: Reconciler 未检测到需要处理的操作

**可能原因**:

- 索引状态不是 PENDING
- version 和 observed_version 已同步
- 索引记录不存在

**解决方案**:

1. 检查索引状态和版本:

   ```sql
   SELECT document_id, index_type, status, version, observed_version
   FROM document_index
   WHERE document_id = 'your_document_id';
   ```

2. 如果 version > observed_version 但状态不是 PENDING，可能需要手动更新状态:
   ```sql
   UPDATE document_index
   SET status = 'PENDING'
   WHERE document_id = 'your_document_id' AND version > observed_version;
   ```

### 问题 3: 索引处于 CREATING 状态但长时间未完成

**可能原因**:

- 任务执行失败但未正确更新状态
- Worker 资源不足
- 网络或 API 连接问题

**解决方案**:

1. 查看 Celery Worker 日志查找错误
2. 检查 Worker 资源使用情况
3. 检查相关服务（向量数据库、LLM API 等）是否正常

### 问题 4: 索引处于 FAILED 状态

**解决方案**:

1. 查看错误信息:

   ```sql
   SELECT error_message FROM document_index
   WHERE document_id = 'your_document_id' AND status = 'FAILED';
   ```

2. 修复错误后重建索引（通过 API 或 Web 界面）

## 手动检查步骤

如果脚本无法运行，可以手动执行以下检查:

### 1. 查询文档状态

```sql
SELECT id, name, status, size, gmt_created, gmt_updated
FROM document
WHERE name LIKE '%颍州变接线图%';
```

### 2. 查询索引状态

```sql
SELECT
    di.document_id,
    di.index_type,
    di.status,
    di.version,
    di.observed_version,
    di.error_message,
    di.gmt_created,
    di.gmt_updated,
    di.gmt_last_reconciled
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE d.name LIKE '%颍州变接线图%';
```

### 3. 检查需要协调的索引

```sql
-- 检查CREATE操作
SELECT * FROM document_index
WHERE status = 'PENDING'
  AND observed_version < version
  AND version = 1;

-- 检查UPDATE操作
SELECT * FROM document_index
WHERE status = 'PENDING'
  AND observed_version < version
  AND version > 1;
```

### 4. 检查 Celery 任务

```bash
# 检查活跃任务
docker exec aperag-celeryworker celery -A config.celery inspect active

# 检查保留任务
docker exec aperag-celeryworker celery -A config.celery inspect reserved

# 查看任务统计
docker exec aperag-celeryworker celery -A config.celery inspect stats
```

## 修复 Pending 状态的索引

### 方法 1: 手动触发 Reconciliation

```bash
docker exec aperag-celeryworker python -c "
from config.celery_tasks import reconcile_indexes_task
reconcile_indexes_task()
"
```

### 方法 2: 通过 API 重建索引

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VECTOR", "FULLTEXT", "GRAPH", "VISION"]
  }'
```

### 方法 3: 手动更新状态（谨慎使用）

```sql
-- 将FAILED状态的索引重置为PENDING（需要确保问题已修复）
UPDATE document_index
SET status = 'PENDING',
    error_message = NULL,
    gmt_updated = NOW()
WHERE document_id = 'your_document_id'
  AND status = 'FAILED';
```

## 相关文档

- [Vision 索引失败诊断指南](DOCKER_VISION_FAILURE_DIAGNOSIS.md)
- [知识图谱诊断指南](KNOWLEDGE_GRAPH_DIAGNOSIS.md)
- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
