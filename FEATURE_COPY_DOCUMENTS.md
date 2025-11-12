# 新功能：创建 Collection 时复制已有文档

## 功能概述

本功能允许用户在创建新的 Collection 时，从一个或多个已有的 Collection（包括共有的 marketplace collections）中复制文档。系统会自动对同名文档进行去重，确保不会重复添加相同名称的文档。

## 主要特性

### 1. 多源复制

- 支持从多个源 Collection 同时复制文档
- 支持复制自己拥有的 Collection
- 支持复制已订阅的共有 Collection（marketplace collections）

### 2. 自动去重

- 按文档名称自动去重
- 跨多个源 Collection 去重
- 如果目标 Collection 中已存在同名文档，会自动跳过

### 3. 后台处理

- 文档复制过程在后台异步执行
- 不阻塞 Collection 创建流程
- 自动触发索引重建

## 技术实现

### 后端改动

#### 1. 数据模型 (`aperag/schema/view_models.py`)

```python
class CollectionCreate(BaseModel):
    title: Optional[str] = None
    config: Optional[CollectionConfig] = None
    type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[CollectionSource] = None
    source_collection_ids: Optional[list[str]] = Field(
        None,
        description='IDs of collections to copy documents from...',
        examples=[['col_id_1', 'col_id_2']]
    )
```

#### 2. 文档服务 (`aperag/service/document_service.py`)

新增方法：`copy_documents_from_collections`

- 参数：
  - `user_id`: 目标 Collection 所有者 ID
  - `target_collection_id`: 目标 Collection ID
  - `source_collection_ids`: 源 Collection ID 列表
  - `deduplicate`: 是否去重（默认 True）
- 功能：
  - 从多个源 Collection 读取所有已完成的文档
  - 检查 marketplace 访问权限
  - 从对象存储读取原始文件
  - 创建新文档并上传到目标 Collection
  - 自动去重（按文档名称）
  - 创建相应的索引

#### 3. Collection 服务 (`aperag/service/collection_service.py`)

修改方法：`create_collection`

- 在 Collection 创建完成后，检查 `source_collection_ids`
- 如果指定了源 Collection，调用 `copy_documents_from_collections`
- 异步复制，不阻塞响应
- 错误不会导致 Collection 创建失败

### 前端改动

#### 1. API 类型定义 (`web/src/api/models/collection-create.ts`)

```typescript
export interface CollectionCreate {
  title?: string;
  config?: CollectionConfig;
  type?: string;
  description?: string;
  source?: CollectionSource;
  source_collection_ids?: Array<string>;
}
```

#### 2. 表单组件 (`web/src/app/workspace/collections/collection-form.tsx`)

- 添加 `source_collection_ids` 字段到表单 schema
- 添加 `loadAvailableCollections` 方法获取可用的 Collection 列表
- 新增 UI 组件：
  - 多选下拉框（使用 Popover + Command 组件）
  - 显示已选择的 Collection 数量
  - 支持搜索过滤
  - 只在创建模式（add）下显示

#### 3. 国际化 (`web/src/i18n/`)

**英文** (`en-US/page_collections.json`):

- `copy_documents`: "Copy Documents from Existing Collections"
- `copy_documents_description`: "Select existing collections..."
- `source_collections`: "Source Collections"
- `source_collections_description`: "Choose one or more collections..."
- `select_collections`: "Select collections..."
- `search_collections`: "Search collections..."
- `collections_selected`: "collections selected"

**中文** (`zh-CN/page_collections.json`):

- `copy_documents`: "从已有知识库复制文档"
- `copy_documents_description`: "选择已有的知识库..."
- `source_collections`: "源知识库"
- `source_collections_description`: "选择一个或多个知识库..."
- `select_collections`: "选择知识库..."
- `search_collections`: "搜索知识库..."
- `collections_selected`: "个知识库已选择"

## 使用场景

### 场景 1：基于现有 Collection 创建新版本

用户想基于现有的 Collection 创建一个新版本，添加新的文档或调整配置：

1. 创建新 Collection
2. 选择原有 Collection 作为源
3. 系统自动复制所有文档
4. 用户可以继续添加新文档

### 场景 2：合并多个 Collection

用户想将多个相关的 Collection 合并为一个：

1. 创建新 Collection
2. 选择多个源 Collection
3. 系统自动复制并去重所有文档

### 场景 3：从共有 Collection 创建私有副本

用户想基于 marketplace 的共有 Collection 创建自己的副本：

1. 创建新 Collection
2. 选择已订阅的共有 Collection
3. 系统复制文档到私有 Collection
4. 用户可以自由修改和扩展

## API 示例

### 创建 Collection 并复制文档

```bash
POST /api/collections
Content-Type: application/json

{
  "title": "我的新知识库",
  "description": "基于已有知识库创建",
  "type": "document",
  "config": {
    "source": "system",
    "enable_vector": true,
    "enable_fulltext": true,
    "enable_knowledge_graph": true,
    "enable_summary": false,
    "enable_vision": false,
    "embedding": {
      "model": "text-embedding-3-small",
      "model_service_provider": "openai"
    },
    "completion": {
      "model": "gpt-4o-mini",
      "model_service_provider": "openai"
    }
  },
  "source_collection_ids": [
    "collection_id_1",
    "collection_id_2"
  ]
}
```

### 响应示例

```json
{
  "id": "new_collection_id",
  "title": "我的新知识库",
  "description": "基于已有知识库创建",
  "type": "document",
  "status": "ACTIVE",
  "config": {...},
  "created": "2025-11-12T10:00:00Z",
  "updated": "2025-11-12T10:00:00Z"
}
```

注意：文档复制在后台异步进行，不影响 Collection 创建的响应。

## 日志示例

```
INFO: Copying documents from 2 source collections to new_collection_id
INFO: Found 50 documents in source collection collection_id_1
INFO: Found 30 documents in source collection collection_id_2
INFO: Skipping duplicate document: document_name.pdf
INFO: Successfully copied document: document_name_2.pdf (ID: doc_123)
INFO: Document copy completed for collection new_collection_id:
      {"copied_count": 75, "skipped_count": 5, "failed_count": 0,
       "message": "Copied 75 documents, skipped 5 duplicates, 0 failed"}
```

## 注意事项

1. **权限检查**：系统会验证用户对源 Collection 的访问权限
2. **配额限制**：复制的文档会计入用户的文档配额
3. **索引类型**：新文档会根据目标 Collection 的配置创建相应的索引
4. **文档状态**：只复制状态为 `COMPLETED` 的文档
5. **对象存储**：文档会从源对象存储读取并上传到新位置
6. **错误处理**：单个文档复制失败不会影响其他文档的复制

## 性能考虑

- 文档复制是异步进行的，不阻塞 API 响应
- 大量文档复制可能需要较长时间
- 建议监控日志以了解复制进度
- 索引构建会在文档复制完成后自动触发

## 未来优化方向

1. 添加复制进度 API 查询
2. 支持选择性复制（按文档类型、日期等筛选）
3. 支持批量操作的任务队列管理
4. 添加 WebSocket 推送复制进度通知
5. 支持文档级别的去重策略（不仅按名称，也可按内容哈希）

## 测试建议

### 单元测试

- 测试 `copy_documents_from_collections` 方法
- 测试去重逻辑
- 测试权限验证
- 测试配额检查

### 集成测试

- 创建 Collection 并复制文档
- 从多个源复制文档
- 从 marketplace Collection 复制文档
- 测试去重效果

### 前端测试

- 测试 UI 组件渲染
- 测试表单提交
- 测试国际化文本
- 测试多选功能

## 总结

本功能实现了前后端统一，提供了完整的文档复制功能，包括：

- ✅ 后端 API 支持
- ✅ 前端 UI 组件
- ✅ 多语言支持
- ✅ 自动去重
- ✅ 权限验证
- ✅ 错误处理
- ✅ 日志记录

用户现在可以轻松地从已有 Collection 复制文档，大大提高了工作效率。

