# 主接线.png 索引卡住问题诊断和解决方案

## 问题描述

"主接线.png" 文档的向量图谱、Graph 和 Vision 索引一直处于 `CREATING` 状态，无法完成。

## 问题原因分析

### 1. Vision 索引卡住（主要原因）

Vision 索引卡在 `CREATING` 状态，可能的原因包括：

1. **Vision LLM API 调用超时或卡住**

   - Vision LLM 服务响应慢或网络问题
   - API 调用没有返回也没有抛出异常
   - 虽然代码已添加 10 分钟超时，但如果任务在超时前就卡住，可能无法及时检测

2. **Vision LLM 配置问题**

   - API 密钥无效或过期
   - Base URL 配置错误
   - 网络连接问题

3. **任务执行中断**
   - Celery Worker 重启导致任务中断
   - 任务状态没有正确更新

### 2. Graph 索引等待 Vision 索引

Graph 索引依赖于 Vision 索引完成，因为：

- Graph 索引需要 Vision-to-Text 的内容来构建知识图谱
- 如果 Vision 索引一直处于 `CREATING` 状态，Graph 索引会一直等待
- 等待逻辑在 `aperag/graph/lightrag_manager.py` 的 `_enrich_content_with_vision_analysis` 函数中

### 3. 向量索引可能也受影响

如果向量索引也处于 `CREATING` 状态，可能是：

- OCR 处理时间过长
- 向量化任务卡住

## 诊断步骤

### 1. 运行诊断脚本

```bash
# 在 Docker 容器中运行
docker exec aperag-celeryworker python diagnose_main_wiring_status.py
```

这个脚本会：

- 检查文档的所有索引状态
- 显示每个索引的卡住时间
- 提供详细的诊断建议

### 2. 检查 Vision LLM 配置

```bash
# 检查 Vision LLM 环境变量
docker exec aperag-celeryworker env | grep VISION_LLM
```

应该看到：

- `VISION_LLM_PROVIDER`
- `VISION_LLM_MODEL`
- `VISION_LLM_BASE_URL`
- `VISION_LLM_API_KEY`

### 3. 查看 Celery 日志

```bash
# 查看 Vision 相关日志
docker logs aperag-celeryworker --tail 500 | grep -i vision

# 查看是否有 Vision LLM 调用日志
docker logs aperag-celeryworker --tail 500 | grep "Vision LLM generate"

# 查看错误日志
docker logs aperag-celeryworker --tail 500 | grep -i "error\|fail\|exception" | grep -i vision
```

### 4. 检查索引状态持续时间

如果索引处于 `CREATING` 状态超过 10 分钟，很可能已经卡住。

## 解决方案

### 方案 1: 等待超时（推荐）

如果 Vision LLM 调用设置了超时（10 分钟），等待超时后任务会自动失败，状态会变为 `FAILED`。然后可以：

1. 检查错误信息
2. 修复配置问题
3. 重新触发索引创建

### 方案 2: 手动重置卡住的索引

如果确认索引已卡住（超过 10 分钟），可以手动重置：

```bash
# 重置所有卡住的索引
docker exec aperag-celeryworker python reset_stuck_indexes.py --document-name "主接线.png"

# 只重置 Vision 索引
docker exec aperag-celeryworker python reset_stuck_indexes.py --document-name "主接线.png" --index-type VISION

# 只重置 Graph 索引
docker exec aperag-celeryworker python reset_stuck_indexes.py --document-name "主接线.png" --index-type GRAPH

# 设置最小卡住时间（默认5分钟）
docker exec aperag-celeryworker python reset_stuck_indexes.py --document-name "主接线.png" --min-stuck-minutes 10
```

重置后，索引状态会变为 `PENDING`，reconciliation 任务会在 1 分钟内自动重新处理。

### 方案 3: 检查并修复 Vision LLM 配置

如果 Vision LLM 配置有问题：

1. **检查 API 密钥**

   ```bash
   docker exec aperag-celeryworker env | grep VISION_LLM_API_KEY
   ```

2. **检查 Base URL**

   ```bash
   docker exec aperag-celeryworker env | grep VISION_LLM_BASE_URL
   ```

3. **测试 Vision LLM 连接**

   - 检查 Vision LLM 服务是否可访问
   - 验证 API 密钥是否有效

4. **更新配置**
   - 修改环境变量或配置文件
   - 重启 Celery Worker: `docker-compose restart celeryworker`

### 方案 4: 重启 Celery Worker

如果怀疑是任务执行环境问题：

```bash
# 重启 Celery Worker
docker-compose restart celeryworker

# 等待服务启动后，索引会自动重新处理
```

## 预防措施

### 1. 监控索引状态

定期检查长时间处于 `CREATING` 状态的索引：

```sql
-- 查询超过10分钟仍处于CREATING状态的索引
SELECT
    di.document_id,
    d.name as document_name,
    di.index_type,
    di.status,
    di.gmt_updated,
    NOW() - di.gmt_updated as stuck_duration
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE di.status = 'CREATING'
  AND di.gmt_updated < NOW() - INTERVAL '10 minutes'
ORDER BY stuck_duration DESC;
```

### 2. 设置合理的超时时间

确保 Vision LLM 调用有合理的超时设置（当前已设置为 10 分钟）。

### 3. 添加监控告警

可以设置监控告警，当索引处于 `CREATING` 状态超过阈值时发送通知。

## 相关文件

- `diagnose_main_wiring_status.py` - 诊断脚本
- `reset_stuck_indexes.py` - 重置卡住索引的脚本
- `aperag/index/vision_index.py` - Vision 索引实现
- `aperag/graph/lightrag_manager.py` - Graph 索引实现（包含等待 Vision 索引的逻辑）
- `VISION_INDEX_STUCK_DIAGNOSIS.md` - Vision 索引卡住问题详细分析

## 总结

"主接线.png" 索引卡住的主要原因是 **Vision 索引卡在 CREATING 状态**，导致 Graph 索引无法继续。解决步骤：

1. **诊断**：运行 `diagnose_main_wiring_status.py` 确认问题
2. **检查**：查看 Celery 日志和 Vision LLM 配置
3. **解决**：根据情况选择等待超时、手动重置或修复配置
4. **预防**：设置监控和合理的超时时间
