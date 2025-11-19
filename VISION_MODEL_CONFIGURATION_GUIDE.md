# Vision 模型配置指南 (Vision-to-Text)

本文档说明如何从多个位置配置 Vision 模型（用于 Vision-to-Text 视觉转文本功能）。

## 配置优先级

Vision 模型的配置按以下优先级顺序（从高到低）：

1. **环境变量** (最高优先级)
2. **Collection 配置** (第二优先级)
3. **默认模型配置** (第三优先级，待后端支持)

## 配置方式

### 方式 1: 环境变量配置 (推荐用于全局配置)

**优先级**: ⭐⭐⭐ 最高

**位置**: `.env` 文件或环境变量

**配置项**:

```bash
# Vision-to-Text模型配置
VISION_LLM_PROVIDER=siliconflow          # Provider名称
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct  # 模型名称
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1  # API Base URL
VISION_LLM_API_KEY=your_api_key_here    # API密钥
```

**优点**:

- 全局生效，所有 Collection 共享
- 配置简单，无需在每个 Collection 中单独配置
- 适合生产环境统一管理

**缺点**:

- 需要重启服务才能生效
- 所有 Collection 使用同一个 Vision 模型

**使用场景**:

- 生产环境统一配置
- 所有 Collection 使用相同的 Vision 模型

### 方式 2: Collection 配置 (推荐用于个性化配置)

**优先级**: ⭐⭐ 第二

**位置**: Collection 配置页面 → `config.completion`

**配置步骤**:

1. 在 Provider 模型页面添加 Vision 模型（带`vision`标签）
2. 在 Collection 配置页面：
   - 启用 `enable_vision` 开关
   - 在 `Completion Model` 下拉框中选择 Vision 模型（会显示"Vision"标签）
3. 保存 Collection 配置

**配置示例**:

```json
{
  "enable_vision": true,
  "completion": {
    "model_service_provider": "siliconflow",
    "model": "Pro/Qwen/Qwen2.5-VL-7B-Instruct",
    "custom_llm_provider": "openai"
  }
}
```

**说明**:

- ✅ Collection 表单会自动加载所有 vision 模型（带`vision`标签）
- ✅ Vision 模型会在下拉框中显示"Vision"标签，便于识别
- ✅ 选择 vision 模型后，系统会自动识别并使用该模型进行 Vision-to-Text 转换

**优点**:

- 每个 Collection 可以使用不同的 Vision 模型
- 灵活配置，适合不同场景需求
- 无需重启服务
- 界面友好，vision 模型有明确标识

**缺点**:

- 需要在每个 Collection 中单独配置
- 配置相对复杂

**使用场景**:

- 不同 Collection 需要不同的 Vision 模型
- 个性化配置需求

### 方式 3: Provider 模型配置 (前端界面)

**优先级**: ⭐ 基础配置

**位置**: `http://localhost:3000/workspace/providers/siliconflow/models`

**配置步骤**:

1. 访问 Provider 模型页面
2. 点击"Add Model"按钮
3. 选择"Vision"类型
4. 填写模型信息：
   - Model: `Pro/Qwen/Qwen2.5-VL-7B-Instruct`
   - Custom LLM Provider: `openai`
   - Context Window, Max Input/Output Tokens (可选)

**说明**:

- 此配置将模型添加到 Provider，使其可在 Collection 配置中选择
- 模型会自动添加`vision`标签
- 这是使用 Collection 配置方式的前提

### 方式 4: 默认模型配置 (前端界面，待后端支持)

**优先级**: ⭐ 待实现

**位置**: Default Models Configuration 对话框

**配置步骤**:

1. 在 Provider 页面点击 Settings 按钮
2. 在 Default Models Configuration 对话框中选择"Default For Vision"
3. 选择 Vision 模型

**说明**:

- 当前前端已支持，但后端暂不支持`default_for_vision`场景
- 配置会显示但不会保存到后端
- 等待后端支持后即可生效

## 配置检查清单

### ✅ 环境变量配置检查

```bash
# 检查环境变量是否设置
echo $VISION_LLM_PROVIDER
echo $VISION_LLM_MODEL
echo $VISION_LLM_BASE_URL
echo $VISION_LLM_API_KEY
```

### ✅ Collection 配置检查

1. **检查 Vision 是否启用**:

   ```json
   {
     "enable_vision": true
   }
   ```

2. **检查 Completion 模型是否有 vision 标签**:

   - 在 Provider 模型页面查看模型标签
   - 确保模型有`vision`标签

3. **检查模型是否可用**:
   - 确保 Provider 已配置 API Key
   - 确保模型在 Provider 中已添加

### ✅ Provider 模型配置检查

1. 访问 `http://localhost:3000/workspace/providers/siliconflow/models`
2. 筛选"Vision"类型模型
3. 确认 Vision 模型已添加并可用

## 配置优先级示例

### 场景 1: 环境变量 + Collection 配置

```
环境变量: VISION_LLM_MODEL=Model-A
Collection配置: completion.model=Model-B (vision标签)

结果: 使用 Model-A (环境变量优先级更高)
```

### 场景 2: 仅 Collection 配置

```
环境变量: 未设置
Collection配置: completion.model=Model-B (vision标签)

结果: 使用 Model-B (Collection配置)
```

### 场景 3: 环境变量不完整

```
环境变量: VISION_LLM_PROVIDER=siliconflow (缺少其他配置)
Collection配置: completion.model=Model-B (vision标签)

结果: 使用 Model-B (环境变量不完整，回退到Collection配置)
```

## 常见问题

### Q1: 如何知道当前使用的是哪个 Vision 模型？

**A**: 查看日志，Vision 索引创建时会输出：

```
Using VISION_LLM from environment variables: Model-A
或
Using collection's completion service for vision: Model-B
```

### Q2: 环境变量和 Collection 配置冲突怎么办？

**A**: 环境变量优先级更高。如果环境变量配置完整，会优先使用环境变量；否则回退到 Collection 配置。

### Q3: 如何为不同 Collection 配置不同的 Vision 模型？

**A**:

1. 不使用环境变量配置（或设置为空）
2. 在每个 Collection 的配置中选择不同的 Vision 模型作为 completion 模型
3. 确保模型有`vision`标签

### Q4: Vision 模型配置后不生效？

**A**: 检查清单：

1. ✅ Collection 的`enable_vision=true`
2. ✅ 环境变量配置完整（如果使用环境变量）
3. ✅ Collection 的 completion 模型有`vision`标签（如果使用 Collection 配置）
4. ✅ Provider 已配置 API Key
5. ✅ 模型在 Provider 中已添加

## 推荐配置方案

### 方案 A: 统一配置（推荐用于生产环境）

```bash
# .env文件
VISION_LLM_PROVIDER=siliconflow
VISION_LLM_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct
VISION_LLM_BASE_URL=https://api.siliconflow.cn/v1
VISION_LLM_API_KEY=your_api_key
```

**优点**: 统一管理，所有 Collection 共享配置

### 方案 B: 个性化配置（推荐用于开发/测试）

1. 不设置环境变量（或设置为空）
2. 在 Provider 模型页面添加 Vision 模型
3. 在每个 Collection 配置中选择 Vision 模型

**优点**: 灵活，每个 Collection 可以使用不同模型

## 配置验证

### 验证环境变量配置

```python
# 在vision_index.py中会检查
vision_llm_provider = os.environ.get("VISION_LLM_PROVIDER")
vision_llm_model = os.environ.get("VISION_LLM_MODEL")
vision_llm_base_url = os.environ.get("VISION_LLM_BASE_URL")
vision_llm_api_key = os.environ.get("VISION_LLM_API_KEY")

# 如果所有变量都存在，使用环境变量配置
```

### 验证 Collection 配置

```python
# 在vision_index.py中会检查
completion_svc = get_collection_completion_service_sync(collection)
if completion_svc and completion_svc.is_vision_model():
    # 使用Collection配置的Vision模型
```

## 总结

Vision 模型可以从以下位置配置：

1. ✅ **环境变量** - 全局配置，优先级最高

   - 位置: `.env` 文件
   - 变量: `VISION_LLM_PROVIDER`, `VISION_LLM_MODEL`, `VISION_LLM_BASE_URL`, `VISION_LLM_API_KEY`
   - 状态: ✅ 完全支持

2. ✅ **Collection 配置** - 个性化配置，优先级第二

   - 位置: Collection 配置页面 → Completion Model 选择器
   - 说明: Vision 模型会自动加载并显示"Vision"标签
   - 状态: ✅ 完全支持（已更新，自动包含 vision 模型）

3. ✅ **Provider 模型配置** - 基础配置，使模型可用

   - 位置: `http://localhost:3000/workspace/providers/siliconflow/models`
   - 说明: 添加模型时选择"Vision"类型，会自动添加 vision 标签
   - 状态: ✅ 完全支持

4. ⏳ **默认模型配置** - 前端已支持，等待后端支持
   - 位置: Default Models Configuration 对话框
   - 说明: 前端已实现，但后端暂不支持`default_for_vision`场景
   - 状态: ⏳ 前端支持，等待后端支持

### 配置完整性确认

✅ **所有配置方式都已实现并可以正常工作！**

- ✅ 环境变量配置：完全支持
- ✅ Collection 配置：完全支持（已更新，自动包含 vision 模型）
- ✅ Provider 模型配置：完全支持
- ⏳ 默认模型配置：前端支持，等待后端支持
