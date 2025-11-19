# Vision 提示词优化说明

## 问题描述

"颍州变接线图.pdf" 的 Vision-to-Text 生成结果不够准确和详细，例如：

- 线路名称提取不完整（如只提取了"颍州 5354 线"的部分，缺少完整名称）
- 设备编号可能遗漏
- 连接关系描述不够详细

## 已完成的优化

### 1. 增强文本提取要求（重点：线路名称前缀识别）

在提示词中添加了更严格的文本提取规则，**特别强调线路名称前缀的准确识别**：

```
**CRITICAL for Text Extraction**:
- Read EVERY visible text character, number, and symbol in the image
- Do NOT summarize or abbreviate - extract exactly as shown
- For Chinese text, preserve the exact characters (e.g., "颍州" not "Yingzhou", "汤州" not "Tangzhou")
- **CRITICAL for Line Names**: Each line has a UNIQUE location prefix. Do NOT assume all lines start with the same prefix.
  - Example: If you see "汤州5354线", extract it as "汤州5354线" (NOT "颍州5354线")
  - Example: If you see "颍稻4736线", extract it as "颍稻4736线" (NOT "颍州4736线")
  - Example: If you see "颍州5354线", extract it as "颍州5354线"
  - **Read the ACTUAL prefix shown for EACH line** - different lines may have different prefixes (汤州, 颍州, 颍稻, etc.)
  - The substation name (e.g., "颍州变") does NOT mean all lines start with "颍州"
- For line names, include the full name with all parts (location prefix + number + "线")
- For equipment IDs, extract every single number visible (circuit breakers, disconnectors, transformers, etc.)
- If text is partially obscured, extract what is visible and note uncertainty
```

**关键改进**：
- ✅ 明确说明每个线路都有唯一的位置前缀
- ✅ 强调不要假设所有线路都有相同的前缀
- ✅ 明确指出变电站名称不代表所有线路都以相同前缀开头
- ✅ 提供具体示例说明如何正确提取不同前缀的线路名称

### 2. 细化电压等级提取要求

对每个电压等级（500kV、220kV、35kV）的提取要求进行了详细说明：

- **500kV**: 要求提取所有母线完整名称、所有线路完整名称（包括位置前缀）、所有断路器完整 ID 等
- **220kV**: 同样要求完整提取所有组件
- **35kV**: 包括站用变、低抗等所有组件的完整信息

### 3. 增强规则部分

更新了规则部分，强调：

```
- Max 4000 words (prioritize completeness over brevity for complex diagrams)
- **CRITICAL**: Read every text label, number, and identifier visible in the image
- **CRITICAL**: For line names, extract the COMPLETE name as shown
- **CRITICAL**: For equipment IDs, extract ALL numbers exactly as shown
- **Language Preservation**: Keep original Chinese text exactly as shown, do not translate equipment names or line names
- **Detail Level**: For electrical diagrams, provide exhaustive detail - every line, every breaker, every connection matters
```

## 应用优化

### 步骤 1: 重启 Celery Worker

```bash
docker-compose restart celeryworker
```

### 步骤 2: 重建 Vision 索引

优化后的提示词只会在重建 Vision 索引时生效。

**方法 A：通过 Web 界面**

1. 进入文档详情页
2. 找到 VISION 索引
3. 点击"重建索引"按钮

**方法 B：通过 API**

```bash
curl -X POST "http://localhost:8000/api/v1/collections/colb948520084941356/documents/doc943a4031a8c27620/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VISION"]
  }'
```

### 步骤 3: 验证优化效果

重建 Vision 索引后，检查生成的文本应该：

1. **线路名称完整**：

   - ✅ "颍州 5354 线"（完整名称）
   - ✅ "汤州 5354 线"（完整名称）
   - ✅ "颍稻 4736 线"（完整名称）
   - ❌ 不再是 "5354 线" 或 "汤州线"（不完整）

2. **设备编号完整**：

   - ✅ 列出所有断路器 ID（如 5013, 50132, 50117, 50118, 50119 等）
   - ✅ 列出所有隔离开关 ID
   - ✅ 不遗漏任何可见的设备编号

3. **连接关系详细**：
   - ✅ 明确说明每个线路通过哪些断路器连接到哪些母线
   - ✅ 说明主变的连接路径
   - ✅ 说明功率流向

## 预期改进

优化后的 Vision-to-Text 输出应该：

1. **线路名称前缀准确**（最重要）：
   - ✅ 正确识别每个线路的实际前缀（汤州、颍州、颍稻等）
   - ✅ 不再将所有线路都误识别为"颍州"开头
   - ✅ 区分不同线路的不同前缀

2. **更准确**：提取的文本与 PDF 中的实际内容一致
3. **更完整**：不遗漏可见的文本标签、编号和标识符
4. **更详细**：连接关系和设备关联描述更清晰
5. **语言保持**：保留原始中文文本，不进行翻译

## 注意事项

1. **Vision LLM 模型能力**：提示词优化可以提高提取质量，但最终效果还取决于 Vision LLM 模型的能力
2. **图片质量**：如果 PDF 转图片后分辨率较低或文字模糊，可能影响提取效果
3. **处理时间**：更详细的提取可能需要更长的处理时间
4. **Token 限制**：如果内容过多，可能需要调整 max_tokens 参数

## 进一步优化建议

如果优化后效果仍不理想，可以考虑：

1. **更换 Vision LLM 模型**：

   - 当前使用：`Qwen/Qwen3-VL-8B-Instruct`
   - 可尝试：`Qwen/Qwen2.5-VL-72B-Instruct`（更大模型，可能更准确）

2. **调整图片分辨率**：

   - 检查 PDF 转图片时的分辨率设置
   - 确保文字清晰可读

3. **分区域处理**：
   - 对于大型图纸，可以考虑分区域提取后合并

## 相关文件

- 修改文件：`aperag/index/vision_index.py`（第 220-321 行）
- 诊断脚本：`check_yingzhou_vision_text.py`
- 诊断报告：`YINGZHOU_GRAPH_DIAGNOSIS.md`
