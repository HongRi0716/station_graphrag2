# Vision 索引卡住问题诊断报告

## 问题描述

Vision 索引和 Graph 索引一直处于 CREATING 状态，已超过 6 分钟（甚至超过 8 分钟）。

### 观察到的现象

1. **Vision 索引**：

   - 14:58:38 开始更新 Vision 索引
   - 14:58:42 使用 Vision LLM: `Qwen/Qwen3-VL-8B-Instruct`
   - **之后没有看到 Vision LLM 调用的日志**
   - 状态一直保持 CREATING

2. **Graph 索引**：
   - 正在等待 Vision 索引完成
   - 已等待超过 8 分钟（280+ 秒）
   - 状态一直保持 CREATING

## 根本原因分析

### 代码流程

从 `aperag/index/vision_index.py` 代码来看：

```python
# Path B: Vision-to-Text
if completion_svc and completion_svc.is_vision_model():
    try:
        text_nodes: List[TextNode] = []
        for part in image_parts:
            # ... 准备 prompt 和 data_uri ...

            description = None
            for attempt in range(max_retries):
                try:
                    description = completion_svc.generate(
                        history=[], prompt=prompt, images=[data_uri])
                    break  # Success
                except LLMError as e:
                    # ... 错误处理 ...
```

### 问题定位

1. **日志显示**：

   - ✅ Vision LLM 服务创建成功：`Using VISION_LLM from environment variables: Qwen/Qwen3-VL-8B-Instruct`
   - ❌ **没有看到** `completion_svc.generate()` 调用的日志
   - ❌ **没有看到** 任何错误日志

2. **可能的原因**：
   - `completion_svc.generate()` 调用**卡住**，没有返回也没有抛出异常
   - Vision LLM API 调用**超时**或**网络问题**，导致一直等待
   - **没有超时设置**，导致任务无限期等待

## 已实施的修复

### 1. 添加详细日志

在 `aperag/index/vision_index.py` 中添加了日志：

```python
logger.info(
    f"Starting Vision LLM generation for asset {part.asset_id} of document {document_id} "
    f"(attempt 1/{max_retries})")
for attempt in range(max_retries):
    try:
        logger.info(
            f"Calling Vision LLM generate() for asset {part.asset_id} (attempt {attempt + 1}/{max_retries})")
        description = completion_svc.generate(
            history=[], prompt=prompt, images=[data_uri])
        logger.info(
            f"Vision LLM generate() completed for asset {part.asset_id}, description length: {len(description) if description else 0}")
        break  # Success
```

**作用**：

- 可以确认 `generate()` 是否被调用
- 可以确认调用是否完成
- 可以确认卡住的具体位置

### 2. 重启 Celery Worker

已重启 Celery Worker 以应用新的日志代码。

## 下一步诊断步骤

### 步骤 1: 观察新日志

等待下一次 Vision 索引任务执行，观察新的日志输出：

```bash
docker logs aperag-celeryworker --tail 100 -f | Select-String -Pattern "Vision LLM|vision.*generate|doc943a4031a8c27620"
```

**期望看到**：

- `Starting Vision LLM generation for asset ...`
- `Calling Vision LLM generate() for asset ...`
- `Vision LLM generate() completed for asset ...`

**如果没有看到**：

- `Calling Vision LLM generate() ...` 之后没有 `completed` 日志 → **确认卡在 `generate()` 调用**

### 步骤 2: 检查 Vision LLM API 连接

如果确认卡在 `generate()` 调用，检查 Vision LLM API：

```bash
# 检查 Vision LLM 配置
docker exec aperag-celeryworker env | grep VISION_LLM

# 测试 Vision LLM API 连接（需要 Python 脚本）
docker exec aperag-celeryworker python -c "
import os
import requests
from datetime import datetime

base_url = os.environ.get('VISION_LLM_BASE_URL', '')
api_key = os.environ.get('VISION_LLM_API_KEY', '')
model = os.environ.get('VISION_LLM_MODEL', '')

print(f'Base URL: {base_url}')
print(f'Model: {model}')
print(f'API Key: {api_key[:10]}...' if api_key else 'API Key: Not set')

# 测试连接
if base_url and api_key:
    try:
        response = requests.get(base_url.replace('/v1', ''), timeout=5)
        print(f'Connection test: {response.status_code}')
    except Exception as e:
        print(f'Connection test failed: {e}')
"
```

### 步骤 3: 检查超时设置

检查 `completion_svc.generate()` 是否有超时设置：

```python
# 查看 aperag/llm/completion/completion_service.py
# 检查 _completion_core 方法是否有超时参数
```

## 可能的解决方案

### 方案 1: 添加超时设置

如果 Vision LLM API 调用没有超时设置，添加超时：

```python
# 在 completion_service.py 中添加超时
response = litellm.completion(
    # ... 其他参数 ...
    timeout=300,  # 5 分钟超时
)
```

### 方案 2: 使用异步调用

如果同步调用容易卡住，考虑使用异步调用：

```python
# 使用 async/await
description = await completion_svc.agenerate(
    history=[], prompt=prompt, images=[data_uri])
```

### 方案 3: 添加任务超时

在 Celery 任务级别添加超时：

```python
@celery_app.task(time_limit=600)  # 10 分钟超时
def update_index_task(...):
    # ...
```

### 方案 4: 检查 Vision LLM 服务状态

如果 Vision LLM 服务不可用或响应慢：

- 检查 API 密钥是否有效
- 检查网络连接
- 检查 Vision LLM 服务是否正常运行

## 问题确认

通过诊断日志确认了问题：

```
[15:07:59,237] Starting Vision LLM generation for asset page_0.png of document doc943a4031a8c27620 (attempt 1/3)
[15:07:59,237] Calling Vision LLM generate() for asset page_0.png (attempt 1/3)
```

**之后没有看到** `Vision LLM generate() completed` 日志，说明**确实卡在 `completion_svc.generate()` 调用**。

## 已实施的修复

### 1. 添加诊断日志 ✅

在 `aperag/index/vision_index.py` 中添加了详细日志，可以确认：

- `generate()` 是否被调用
- 调用是否完成
- 卡住的具体位置

### 2. 添加超时设置 ✅

**问题根源**：`litellm.completion()` 调用**没有超时设置**，导致如果 Vision LLM API 响应慢或卡住，任务会无限期等待。

**修复方案**：

1. 在 `CompletionService` 类中添加 `timeout` 参数
2. 默认超时：
   - Vision 模型：**10 分钟**（600 秒）- 复杂图像处理需要更长时间
   - 其他模型：**5 分钟**（300 秒）
3. 在所有 `litellm.completion()` 和 `litellm.acompletion()` 调用中添加 `timeout` 参数
4. Vision LLM 服务创建时显式设置 10 分钟超时

**修改的文件**：

- `aperag/llm/completion/completion_service.py`：
  - 添加 `timeout` 参数到 `__init__` 方法
  - 在所有 `litellm.completion()` 和 `litellm.acompletion()` 调用中添加 `timeout=self.timeout`
- `aperag/index/vision_index.py`：
  - Vision LLM 服务创建时设置 `timeout=600`（10 分钟）

## 当前状态

- ✅ **已添加诊断日志**
- ✅ **已添加超时设置**（Vision 模型 10 分钟，其他模型 5 分钟）
- ✅ **已重启 Celery Worker**
- ⏳ **等待下一次 Vision 索引任务执行以验证修复**

## 相关文档

- `YINGZHOU_INDEX_STATUS.md`: 索引状态报告
- `VISION_TOKEN_LIMIT_FIX.md`: Vision Token 限制修复说明
- `VISION_PROMPT_OPTIMIZATION.md`: Vision 提示词优化说明
