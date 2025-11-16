# OCR 文本与 Vision-to-Text 内容合并与可视化说明

## 一、合并流程

### 1. 文档解析阶段（`aperag/index/document_parser.py`）

#### OCR 文本提取（如果启用）

```python
# 如果 OCR_ENABLED=True 或 SILICONFLOW_OCR_ENABLED=True
if ocr_enabled:
    # 提取OCR文本
    ocr_parts = image_parser.parse_file(filepath_obj, file_metadata)
    ocr_text = ocr_parts[0].content

    # 创建TextPart，标记来源为OCR
    parts.append(TextPart(
        content=ocr_text,
        metadata={"source": "ocr", "ocr_method": ocr_method}
    ))
```

#### 内容合并到 Markdown

在 `save_processed_content_and_assets()` 方法中：

```python
# OCR文本会被添加到content中，格式如下：
content = content + "\n\n------ OCR Text ------\n" + ocr_content
```

**合并后的 content 结构：**

```
[原始Markdown内容（如果有）]

------ OCR Text ------
[OCR提取的文本内容]
```

### 2. Vision 索引创建阶段（`aperag/index/vision_index.py`）

Vision-to-Text 内容被单独存储到向量数据库：

- 存储位置：向量数据库（Qdrant）
- 标识：`index_method: "vision_to_text"`
- 元数据：包含 `asset_id`, `document_id`, `collection_id` 等信息

### 3. 知识图谱构建阶段（`aperag/graph/lightrag_manager.py`）

#### 合并逻辑（`_process_document_async`）

```python
# 1. 获取初始content（包含OCR文本，如果有）
content = "------ OCR Text ------\n[OCR内容]"

# 2. 从Vision索引获取Vision-to-Text内容
vision_content = await _enrich_content_with_vision_analysis(collection, doc_id)

# 3. 合并策略
if vision_content:
    if not content:
        # 如果content为空，直接使用Vision-to-Text
        content = vision_content
    else:
        # 如果content存在（包含OCR），追加Vision-to-Text
        content = content + "\n\n" + vision_content
```

#### Vision 内容提取（`_enrich_content_with_vision_analysis`）

从向量数据库检索 Vision-to-Text 内容：

```python
# 1. 从DocumentIndex获取context_ids
ctx_ids = index_data.get("context_ids", [])

# 2. 从向量数据库检索
points = qdrant_client.retrieve(
    collection_name=collection_name,
    ids=ctx_ids,
    with_payload=True,
)

# 3. 提取并格式化Vision-to-Text内容
for point in points:
    text = payload_data.get("text", "")  # Vision-to-Text生成的文本
    asset_id = metadata.get("asset_id", "")

    # 格式化输出
    section_header = f"\n\n------ Vision Analysis (Asset: {asset_id}) ------\n"
    vision_chunks_text.append(section_header + text.strip())
```

**最终合并后的 content 结构：**

```
------ OCR Text ------
[OCR提取的文本内容]

------ Vision Analysis (Asset: file.png) ------
[Vision-to-Text生成的详细分析内容]
```

## 二、可视化方式

### 1. 通过 API 查看合并内容

#### 获取文档预览（包含所有内容）

```python
GET /api/v1/collections/{collection_id}/documents/{document_id}/preview
```

返回的 `DocumentPreview` 包含：

- `markdown_content`: 包含 OCR 文本的 Markdown 内容
- `chunks`: 向量索引的文本块（包含 OCR 文本）
- `vision_chunks`: Vision-to-Text 的 chunks

#### 获取 Vision Chunks

```python
GET /api/v1/collections/{collection_id}/documents/{document_id}/vision-chunks
```

返回所有 Vision-to-Text 生成的 chunks，每个 chunk 包含：

- `id`: chunk ID
- `text`: Vision-to-Text 生成的文本
- `metadata`: 包含 `asset_id`, `index_method: "vision_to_text"` 等

### 2. 通过检查脚本查看

#### 使用 `check_ocr_vision_graph_status.py`

```bash
python check_ocr_vision_graph_status.py --document-name "主接线.png"
```

输出包括：

- OCR 文本预览（如果启用 OCR）
- Vision-to-Text 内容预览
- 知识图谱数据摘要（实体和关系数量）

#### 使用 `check_vision_content.py`

```bash
python check_vision_content.py --document-id <document_id>
```

显示 Vision 索引的详细内容。

### 3. 在向量数据库中查看

#### OCR 文本（存储在 VECTOR 索引）

```python
# 查询向量索引的chunks
points = qdrant_client.retrieve(
    collection_name=collection_name,
    ids=vector_ctx_ids,
    with_payload=True,
)

# OCR文本在payload中
text = point.payload.get("_node_content")  # 或 point.payload.get("text")
```

#### Vision-to-Text（存储在 VISION 索引，但也在同一向量数据库）

```python
# 查询Vision索引的chunks
points = qdrant_client.retrieve(
    collection_name=collection_name,
    ids=vision_ctx_ids,
    with_payload=True,
)

# Vision-to-Text在payload中，通过metadata标识
metadata = payload_data.get("metadata", {})
if metadata.get("index_method") == "vision_to_text":
    text = payload_data.get("text", "")  # Vision-to-Text内容
```

### 4. 在知识图谱中查看

合并后的内容用于构建知识图谱：

- **实体提取**：从合并内容中提取实体
- **关系提取**：从合并内容中提取关系
- **可视化**：通过知识图谱可视化界面查看

## 三、内容格式示例

### OCR 文本格式

```
------ OCR Text ------
主接线图
500kV 宜昌变电站
1号主变 2号主变
50117 50118 50119
220kV IA母 IB母
...
```

### Vision-to-Text 格式

```
------ Vision Analysis (Asset: file.png) ------
## Content Type: Pure Diagram

## Overall Summary
This is a 500kV Yichang Substation's primary system wiring diagram...

## Detailed Text Extraction
500kV Yicheng Substation Main Connection Diagram
生产管控中心 二〇二三年六月

## Diagram Regions
### Diagram 1: Main Connection Diagram
**System Overview**: 500kV变电站，包含2台主变压器...
**Key Equipment**:
- Transformers: 1号主变(500kV/220kV), 2号主变(500kV/220kV)
- Circuit breakers: 50117-50119
...
**Connection Relationships**:
1号主变通过断路器50117连接到220kV IB母线，该母线再连接到汤颖5353线...
```

### 合并后的完整内容

```
------ OCR Text ------
[OCR提取的原始文本]

------ Vision Analysis (Asset: file.png) ------
[Vision-to-Text生成的详细分析]
```

## 四、配置控制

### 启用 OCR

```bash
# 在环境变量中设置
OCR_ENABLED=True
# 或
SILICONFLOW_OCR_ENABLED=True
```

### 禁用 OCR（默认）

```bash
# 不设置或设置为False
OCR_ENABLED=False
SILICONFLOW_OCR_ENABLED=False
```

## 五、数据流向图

```
图片文件
    ↓
文档解析 (document_parser.py)
    ├─ OCR提取 (如果OCR_ENABLED=True)
    │   └─ 生成TextPart → 合并到content
    └─ 创建AssetBinPart → 用于Vision索引
    ↓
Vision索引创建 (vision_index.py)
    └─ Vision-to-Text → 存储到向量数据库
    ↓
知识图谱构建 (lightrag_manager.py)
    ├─ 获取content（包含OCR文本）
    ├─ 从Vision索引获取Vision-to-Text
    └─ 合并: content + "\n\n" + vision_content
    ↓
最终内容用于：
    ├─ 向量索引（VECTOR）
    ├─ 全文索引（FULLTEXT）
    └─ 知识图谱索引（GRAPH）
```

## 六、查看合并内容的代码示例

```python
# 1. 查看文档预览（包含所有内容）
from aperag.service.document_service import DocumentService
service = DocumentService()
preview = await service.get_document_preview(
    user_id="user123",
    collection_id="col123",
    document_id="doc123"
)

print("Markdown内容（包含OCR）:")
print(preview.markdown_content)

print("\nVision Chunks:")
for chunk in preview.vision_chunks:
    print(f"Asset: {chunk.metadata.get('asset_id')}")
    print(f"Text: {chunk.text[:200]}...")

# 2. 直接从向量数据库查看
from aperag.config import get_vector_db_connector
from aperag.utils.utils import generate_vector_db_collection_name

collection_name = generate_vector_db_collection_name(collection_id="col123")
vector_store = get_vector_db_connector(collection=collection_name)
qdrant_client = vector_store.connector.client

# 查询Vision索引的chunks
vision_ctx_ids = [...]  # 从DocumentIndex获取
points = qdrant_client.retrieve(
    collection_name=collection_name,
    ids=vision_ctx_ids,
    with_payload=True,
)

for point in points:
    payload_data = json.loads(point.payload.get("_node_content"))
    if payload_data.get("metadata", {}).get("index_method") == "vision_to_text":
        print(f"Vision-to-Text: {payload_data.get('text')[:200]}...")
```
