# 颍州变接线图.pdf 索引状态报告

## 检查时间

2025-11-16 15:04

## 文档信息

- **文档 ID**: `doc943a4031a8c27620` (版本 4)
- **文档名称**: 颍州变接线图.pdf

## 索引状态概览

### 版本 4 (最新版本)

| 索引类型   | 状态            | 版本 | 观察版本 | 更新时间            |
| ---------- | --------------- | ---- | -------- | ------------------- |
| FULLTEXT   | ✅ ACTIVE       | 4    | 4        | 2025-11-16 14:58:38 |
| VECTOR     | ✅ ACTIVE       | 4    | 4        | 2025-11-16 14:58:42 |
| **VISION** | ⚠️ **CREATING** | 4    | 3        | 2025-11-16 14:58:16 |
| **GRAPH**  | ⚠️ **CREATING** | 4    | 3        | 2025-11-16 14:58:16 |

### 版本 15 (旧版本)

所有索引均为 ✅ ACTIVE 状态

## 问题分析

### 1. Vision 索引卡住

- **状态**: CREATING（已创建超过 6 分钟）
- **观察版本**: 3（未更新到版本 4）
- **问题**: Vision 索引任务在 14:58:38 开始，但一直没有完成

**日志显示**:

```
[14:58:38] Starting to update VISION index for document doc943a4031a8c27620 (v4)
[14:58:38] Updating VISION index for document doc943a4031a8c27620
[14:58:42] Using VISION_LLM from environment variables: Qwen/Qwen3-VL-8B-Instruct
```

**之后没有看到**:

- Vision LLM 调用的日志
- Vision 索引完成的日志
- 任何错误日志

### 2. Graph 索引等待 Vision

- **状态**: CREATING（等待 Vision 索引完成）
- **观察版本**: 3（未更新到版本 4）
- **问题**: Graph 索引在等待 Vision 索引完成，但 Vision 索引一直卡住

**日志显示**:

```
[14:58:42] Vision index for document doc943a4031a8c27620 is still in progress (CREATING), waited 0s, continuing to wait indefinitely...
[14:58:52] Vision index for document doc943a4031a8c27620 is still in progress (CREATING), waited 10s...
[14:59:22] Vision index for document doc943a4031a8c27620 is still in progress (CREATING), waited 40s...
[14:59:32] Vision index for document doc943a4031a8c27620 is still in progress (CREATING), waited 50s...
```

## 可能的原因

1. **Vision LLM 调用超时或失败**

   - Vision LLM API 调用可能超时
   - 没有错误日志记录
   - 任务可能被卡住

2. **Vision 索引任务被中断**

   - Celery Worker 重启可能导致任务中断
   - 任务状态没有正确更新

3. **Vision LLM 配置问题**
   - API 密钥可能无效
   - 网络连接问题
   - 模型服务不可用

## 建议的解决方案

### 方案 1: 检查 Vision 索引任务状态

```bash
# 检查是否有Vision索引任务正在运行
docker exec aperag-redis redis-cli KEYS "celery-task-meta-*" | grep -i vision
```

### 方案 2: 手动重建 Vision 索引

通过 Web 界面或 API 手动触发 Vision 索引重建：

```bash
# 通过API重建Vision索引
curl -X POST "http://localhost:8000/api/v1/documents/doc943a4031a8c27620/indexes/VISION/rebuild" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 方案 3: 检查 Vision LLM 服务

```bash
# 检查Vision LLM配置
docker exec aperag-celeryworker env | grep VISION_LLM

# 测试Vision LLM连接
docker exec aperag-celeryworker python -c "
from aperag.index.vision_index import _get_vision_llm_completion_service
from aperag.db.models import Collection
from aperag.config import get_sync_session
session = next(get_sync_session())
collection = session.query(Collection).filter(Collection.id == 'colb948520084941356').first()
service = _get_vision_llm_completion_service(collection)
print(f'Vision LLM Service: {service}')
"
```

### 方案 4: 重启 Celery Worker 并重新触发索引

```bash
# 重启Celery Worker
docker-compose restart celeryworker

# 等待服务启动后，通过reconcile触发索引重建
# 系统会自动检测到索引需要重建
```

## 当前状态总结

✅ **已完成**:

- FULLTEXT 索引：ACTIVE
- VECTOR 索引：ACTIVE

⚠️ **进行中**:

- VISION 索引：CREATING（已卡住超过 6 分钟）
- GRAPH 索引：CREATING（等待 Vision 索引完成）

## 下一步行动

1. **立即行动**: 检查 Vision 索引任务是否真的在运行，或者已经失败但没有更新状态
2. **如果任务失败**: 手动重建 Vision 索引
3. **如果任务卡住**: 重启 Celery Worker 并重新触发索引
4. **验证修复**: 确认 Vision 索引完成后，Graph 索引应该会自动完成

## 相关文档

- `VISION_TOKEN_LIMIT_FIX.md`: Vision Token 限制修复说明
- `VISION_PROMPT_OPTIMIZATION.md`: Vision 提示词优化说明
