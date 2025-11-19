# Vision Prompt 优化说明（V2 - 简化版）

## 问题描述

Vision-to-Text 生成的内容过长，包含大量重复内容（如重复的 "505117"），导致：

1. 内容超过 embedding 模型的 token 限制（8192 tokens）
2. 向量化失败，错误：`input must have less than 8192 tokens`
3. Vision 索引创建失败，Graph 索引一直等待

## 优化方案

### 1. 简化 Vision Prompt

**优化前**：详细的、多段落的结构化要求

- 要求生成 3 个主要部分（Summary, Detailed Text Extraction, Diagram Analysis）
- 每个部分都有详细的子要求
- 要求生成大量格式化内容

**优化后**：简洁的、聚焦 RAG 需求的要求

- 只要求 3 个核心部分：Summary, Key Text, Key Relationships
- 强调简洁和去重
- 避免过度格式化

**新的 Prompt**：

```
Extract key information from the image for RAG retrieval. Be concise and avoid repetition.

## Requirements
1. **Summary**: One brief paragraph describing the main content
2. **Key Text**: Extract unique text items only (no duplicates)
3. **Key Relationships**: Brief description of main connections

## Rules
- **No duplicates** - each item appears once
- **Be concise** - focus on essential information for retrieval
- Keep original language
- Use simple lists, avoid excessive formatting
```

### 2. 添加内容长度检查和截断机制

在生成 Vision-to-Text 内容后，添加了长度检查和智能截断：

```python
# 检查内容长度
max_chars = 6000  # 保守估计：6000 字符 ≈ 8192 tokens
if len(description) > max_chars:
    # 智能截断：在句子或段落边界截断
    # 添加截断标记
    description = truncated + "\n\n[Content truncated due to length limit]"
```

**特点**：

- 保守的长度限制：6000 字符（约 8192 tokens）
- 智能截断：优先在段落或句子边界截断
- 添加截断标记：告知用户内容被截断

### 3. Token 估算说明

- **中文文本**：约 1.5 字符/ token
- **英文文本**：约 0.75 tokens/词
- **混合文本**：保守估计 6000 字符 ≈ 8192 tokens

## 预期效果

1. **减少内容长度**：

   - 简化 prompt 后，生成的内容更简洁
   - 减少不必要的详细描述和格式化
   - 避免重复内容

2. **防止超长内容**：

   - 即使生成的内容较长，也会被截断
   - 确保不超过 embedding token 限制
   - 避免向量化失败

3. **保持 RAG 效果**：
   - 保留核心信息（Summary, Key Text, Key Relationships）
   - 去重确保信息质量
   - 简洁但完整，满足检索需求

## 修改文件

- `aperag/index/vision_index.py`：
  - 简化 Vision prompt（第 253-279 行）
  - 添加内容长度检查和截断（第 331-353 行）

## 测试建议

1. **测试简化后的 prompt**：

   - 上传图片，检查生成的内容长度
   - 验证内容是否简洁且包含核心信息
   - 确认没有大量重复内容

2. **测试截断机制**：

   - 如果生成的内容超过 6000 字符，验证是否被正确截断
   - 检查截断是否在合理边界（段落/句子）
   - 确认向量化成功

3. **验证 RAG 效果**：
   - 使用简化后的内容进行检索测试
   - 验证检索效果是否满足需求
   - 对比优化前后的检索质量

## 后续优化建议

如果简化后的内容仍然过长或效果不佳，可以考虑：

1. **进一步简化 prompt**：只保留最核心的信息提取要求
2. **分块处理**：将超长内容分成多个块分别向量化
3. **使用更大的 embedding 模型**：如果可用，使用支持更大 token 限制的模型
4. **内容过滤**：在截断前，先过滤掉明显重复或无关的内容

## 相关文档

- `VISION_PROMPT_OPTIMIZATION.md`：之前的 prompt 优化说明
- `VISION_TOKEN_LIMIT_FIX.md`：Token 限制修复说明
- `VISION_INDEX_STUCK_DIAGNOSIS.md`：Vision 索引卡住问题诊断
