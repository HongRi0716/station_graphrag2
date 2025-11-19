# Vision Token 限制修复说明

## 问题描述

Vision-to-Text 生成的内容不完整，可能因为 token 限制导致输出被截断。

## 根本原因

1. **max_tokens 未设置**：

   - Vision LLM 创建时没有传递 `max_tokens` 参数
   - 使用默认值 `None`，可能导致使用模型的最小默认值（通常较小）

2. **提示词中的字数限制**：
   - 提示词中设置了 "Max 4000 words" 限制
   - 可能误导模型提前停止生成

## 已完成的修复

### 1. 添加 max_tokens 配置

修改了 `aperag/index/vision_index.py` 中的 `_get_vision_llm_completion_service` 函数：

- 从模型配置中获取 `max_output_tokens`
- 如果模型配置中有 `max_output_tokens`，使用该值（至少 8192 tokens）
- 如果模型配置中没有设置，使用默认值 **16384 tokens**
- 将 `max_tokens` 传递给 `CompletionService`

**代码逻辑**：

```python
# 从模型配置获取 max_output_tokens
model_config = db_ops.query_llm_provider_model(...)
if model_config and model_config.max_output_tokens:
    max_tokens = max(model_config.max_output_tokens, 8192)  # 至少 8192
else:
    max_tokens = 16384  # 默认 16384 tokens
```

### 2. 移除提示词中的字数限制

修改了提示词规则部分：

**修改前**：

```
- Max 4000 words, prioritize completeness
```

**修改后**：

```
- Prioritize completeness over word count - extract ALL content even if it exceeds typical limits
- **Do not truncate or summarize** - provide complete extraction of all visible content
```

## 当前配置

根据检查，当前 Vision 模型配置：

- **模型**: `Qwen/Qwen3-VL-8B-Instruct`
- **Provider**: `siliconflow`
- **max_output_tokens**: NULL（未配置）
- **实际使用的 max_tokens**: **16384 tokens**（默认值）

## Token 数量说明

16384 tokens 大约相当于：

- 中文：约 8000-12000 字
- 英文：约 12000-16000 词

对于复杂的电气接线图，这应该足够生成完整的内容。

## 验证修复

### 方法 1: 检查日志

重建 Vision 索引后，查看 Celery Worker 日志：

```bash
docker logs aperag-celeryworker --tail 100 | Select-String -Pattern "max_output_tokens|max_tokens|Vision LLM"
```

应该看到：

```
INFO: Using default max_tokens=16384 for Vision LLM Qwen/Qwen3-VL-8B-Instruct
```

### 方法 2: 检查生成的内容长度

重建 Vision 索引后，检查生成的内容：

```bash
# 使用检查脚本
python check_yingzhou_vision_text.py
```

应该看到更长的内容，包含所有线路和设备信息。

## 如果仍然不完整

如果 16384 tokens 仍然不够，可以：

### 方案 1: 在模型配置中设置更大的 max_output_tokens

通过 Web 界面或 API 更新 Vision 模型的配置：

```bash
# 更新模型配置，设置更大的 max_output_tokens
curl -X PUT "http://localhost:8000/api/v1/llm_providers/siliconflow/models/completion/Qwen/Qwen3-VL-8B-Instruct" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "max_output_tokens": 32768
  }'
```

### 方案 2: 检查模型实际支持的最大输出

不同模型有不同的最大输出限制：

- Qwen3-VL-8B-Instruct 可能支持更大的输出
- 检查模型文档或 API 文档确认最大限制

### 方案 3: 分页处理（如果图纸很大）

对于非常大的图纸，可以考虑：

- 将 PDF 分页处理
- 每页单独生成 Vision-to-Text
- 在知识图谱构建时合并所有页面的内容

## 应用修复

修复已应用，重启 Celery Worker 后生效：

```bash
docker-compose restart celeryworker
```

## 下一步

重建 Vision 索引以使用新的 token 限制：

```bash
# 通过 Web 界面或 API 重建 VISION 索引
```

重建后，Vision-to-Text 应该能生成更完整的内容。

## 相关文件

- 修改文件：`aperag/index/vision_index.py`（第 83-119 行，第 307-314 行）
- 诊断文档：`VISION_PROMPT_OPTIMIZATION.md`
