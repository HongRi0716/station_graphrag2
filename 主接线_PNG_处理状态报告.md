# "主接线.png" 处理状态报告

## 📋 文档信息

- **文档名称**: 主接线.png
- **文档 ID**: `docb53472da4581b6c0`
- **文档状态**: PENDING
- **文档大小**: 525,105 bytes
- **创建时间**: 2025-11-17 03:16:36
- **处理时长**: 已持续 6.6 分钟

## 📊 索引状态

所有索引均处于 **CREATING** 状态：

| 索引类型 | 状态        | 持续时间 | 问题               |
| -------- | ----------- | -------- | ------------------ |
| VECTOR   | 🔄 CREATING | 6.6 分钟 | 等待中             |
| VISION   | 🔄 CREATING | 6.6 分钟 | **失败（重试中）** |
| GRAPH    | 🔄 CREATING | 6.6 分钟 | 等待 VISION 完成   |

## ❌ 失败原因

### 核心错误

```
Error code: 413 - {'code': 20042, 'message': 'input must have less than 8192 tokens'}
```

### 问题分析

1. **Vision LLM 生成成功**: Vision LLM 成功生成了图片的文本描述
2. **文本过长**: 生成的文本描述超过了 8192 tokens 的限制
3. **Embedding 失败**: 当尝试对长文本进行 embedding 时，API 返回 413 错误（请求实体过大）
4. **索引创建失败**: 由于 embedding 失败，Vision 索引创建失败
5. **自动重试**: Celery 任务正在自动重试（每 60 秒重试一次）

### 错误时间线

- **03:17:36**: 开始 Vision LLM 生成
- **03:21:36**: 第一次失败 - `input must have less than 8192 tokens`
- **03:22:36**: 第一次重试
- **03:23:24**: 第二次失败 - 同样的错误

## 🔍 详细错误日志

```
[2025-11-17 03:21:36,348: ERROR] Batch embedding API call failed:
litellm.APIError: APIError: OpenAIException - Error code: 413 -
{'code': 20042, 'message': 'input must have less than 8192 tokens', 'data': None}

[2025-11-17 03:21:36,348: ERROR] Failed to create vision-to-text embedding
for document docb53472da4581b6c0: Batch processing error
```

## 💡 解决方案

### 方案 1: 对 Vision 文本进行分块处理（推荐）

修改 `aperag/index/vision_index.py`，在创建 embedding 之前对文本进行分块：

```python
# 在 line 365 附近，embed_documents 之前添加文本分块逻辑
from aperag.utils.text_splitter import TextSplitter

# 对每个 text_node 的内容进行分块
chunked_nodes = []
for node in text_nodes:
    # 如果文本超过 8000 tokens，进行分块
    if len(node.get_content()) > 8000:  # 估算 token 数
        splitter = TextSplitter(chunk_size=8000, chunk_overlap=200)
        chunks = splitter.split_text(node.get_content())
        for i, chunk in enumerate(chunks):
            chunk_node = TextNode(
                text=chunk,
                metadata={**node.metadata, "chunk_index": i}
            )
            chunked_nodes.append(chunk_node)
    else:
        chunked_nodes.append(node)

# 使用分块后的节点
vectors = embedding_svc.embed_documents(
    [node.get_content() for node in chunked_nodes])
```

### 方案 2: 限制 Vision LLM 输出长度

在 Vision LLM 调用时设置更严格的 `max_tokens` 限制：

```python
# 在 vision_index.py 中，Vision LLM 调用时
max_tokens = min(max_tokens, 6000)  # 确保不超过 embedding 限制
```

### 方案 3: 使用支持更长文本的 Embedding 模型

检查并切换到支持更长输入（>8192 tokens）的 embedding 模型。

### 方案 4: 临时解决方案 - 截断文本

在创建 embedding 之前截断过长的文本：

```python
# 在 line 365 之前
MAX_EMBEDDING_TOKENS = 8000
for node in text_nodes:
    content = node.get_content()
    # 简单截断（更好的方法是使用 tokenizer）
    if len(content) > MAX_EMBEDDING_TOKENS * 4:  # 粗略估算：1 token ≈ 4 chars
        node.text = content[:MAX_EMBEDDING_TOKENS * 4]
        logger.warning(f"Truncated vision text for {node.metadata.get('asset_id')}")
```

## 🚀 立即操作建议

1. **检查当前 Vision 文本长度**:

   ```bash
   docker exec aperag-celeryworker python -c "
   from aperag.db.models import Document
   from aperag.config import get_sync_session
   from sqlalchemy import select
   for session in get_sync_session():
       doc = session.execute(select(Document).where(Document.id == 'docb53472da4581b6c0')).scalar_one_or_none()
       print(f'Document: {doc.name if doc else \"Not found\"}')
   "
   ```

2. **查看 Vision LLM 生成的文本长度**:

   - 检查日志中 Vision LLM 的输出
   - 估算 token 数量

3. **实施修复**:

   - 选择上述方案之一进行修复
   - 重新部署代码
   - 重置索引状态以重新处理

4. **重置索引状态**（修复后）:
   ```bash
   docker exec aperag-celeryworker python reset_stuck_indexes.py \
     --document-id docb53472da4581b6c0 \
     --index-type VISION
   ```

## 📝 相关文件

- `aperag/index/vision_index.py` - Vision 索引实现（line 365-370）
- `aperag/llm/embed/embedding_service.py` - Embedding 服务（line 107）
- `config/celery_tasks.py` - Celery 任务定义

## ⚠️ 注意事项

1. 当前任务会持续重试，直到达到最大重试次数（3 次）
2. 如果所有重试都失败，索引状态会变为 `FAILED`
3. Graph 索引会一直等待 VISION 索引完成
4. 建议尽快修复，避免任务队列堆积

## ✅ 验证修复

修复后，可以通过以下方式验证：

```bash
# 1. 查看新的处理日志
docker logs aperag-celeryworker --tail 100 -f | grep docb53472da4581b6c0

# 2. 检查索引状态
docker exec aperag-celeryworker python diagnose_main_wiring_status.py

# 3. 确认 Vision 索引成功创建
# 检查数据库中的 document_index 表
```
