# B5391S-T0102-土建总平面布置图.pdf 知识图谱分析

## 日志分析结果

### 文档信息

- **文档 ID**: `doc7cd4efa65cdfbaf7`
- **文档名称**: `B5391S-T0102-土建总平面布置图.pdf`
- **Collection ID**: `col1fd8b3b8e2a4002a`

### 索引创建状态

从日志中可以看到，GRAPH 索引**已成功创建**，但结果如下：

```
'status': 'success',
'index_type': 'GRAPH',
'document_id': 'doc7cd4efa65cdfbaf7',
'data': {
    'status': 'success',
    'doc_id': 'doc7cd4efa65cdfbaf7',
    'chunks_created': 0,      # ⚠️ 0个文本块
    'entities_extracted': 0,  # ⚠️ 0个实体
    'relations_extracted': 0  # ⚠️ 0个关系
}
```

### 根本原因

**文档解析后没有文本内容**：

从日志可以看到：

```
'content': '',  # 内容为空
'doc_parts': [
    {
        'content': None,  # 文本内容为None
        'asset_id': 'page_0.png',  # 只有图片资源
        'data': b'89504e470d0a1a0a...'  # PNG图片数据
    }
]
```

**问题分析**：

1. ✅ 文档解析成功（DocRay 处理完成）
2. ✅ 图片提取成功（生成了`page_0.png`）
3. ❌ **文本提取失败**：DocRay 没有从 PDF 中提取到任何文本内容
4. ❌ 知识图谱构建失败：因为没有文本内容，无法提取实体和关系

### 为什么没有文本内容？

可能的原因：

1. **纯图片型 PDF**：PDF 是扫描版或图片型，没有嵌入的文本层
2. **OCR 未执行或失败**：虽然 DocRay 支持 OCR，但可能：
   - OCR 功能未启用
   - OCR 识别失败
   - 图片质量不佳导致 OCR 无法识别

### 解决方案

#### 方案一：检查 DocRay OCR 功能（推荐）

DocRay 应该自动进行 OCR 识别，但需要确认：

1. **检查 DocRay 日志**：

```bash
docker logs aperag-docray --tail 100
```

2. **检查文档解析结果**：

   - 查看 DocRay 是否执行了 OCR
   - 检查 OCR 识别结果

3. **手动触发 OCR**：
   如果 DocRay 没有自动 OCR，可能需要：
   - 检查 DocRay 配置
   - 确保 OCR 功能已启用

#### 方案二：使用 PaddleOCR 进行图片 OCR

如果 DocRay 的 OCR 未工作，可以使用 PaddleOCR：

1. **配置 PaddleOCR 服务**：

```bash
# 在.env中配置
PADDLEOCR_HOST=http://your-paddleocr-service:port
```

2. **重新处理文档**：
   - 系统会自动使用 PaddleOCR 对图片进行 OCR 识别
   - 提取文本后重新构建知识图谱

#### 方案三：检查文档内容

1. **验证 PDF 类型**：

   - 使用 PDF 阅读器打开 PDF
   - 尝试复制文本，如果能复制说明有文本层
   - 如果不能复制，说明是纯图片型 PDF

2. **检查图片质量**：
   - 图片是否清晰
   - 文字是否可读
   - 是否有模糊、倾斜等问题

### 对比：成功的知识图谱案例

从日志中可以看到另一个文档成功创建了知识图谱：

**文档**: `doc34931d4919ef47aa` (国家电网公司变电运维管理规定.doc)

```
'chunks_created': 53,
'entities_extracted': 551,    # ✅ 成功提取551个实体
'relations_extracted': 261    # ✅ 成功提取261个关系
```

这个文档有文本内容，所以成功构建了知识图谱。

### 诊断步骤

1. **检查文档解析结果**：

```bash
# 查看文档详情
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/doc7cd4efa65cdfbaf7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **检查 DocRay OCR 日志**：

```bash
docker logs aperag-docray --tail 200 | grep -i "ocr\|text\|extract"
```

3. **检查文档内容**：
   - 查看`parsed.md`文件是否有内容
   - 检查图片资源是否正确提取

### 预期结果

如果 OCR 正常工作，应该能看到：

- `content`字段包含 OCR 识别的文本
- `chunks_created > 0`
- `entities_extracted > 0`
- `relations_extracted > 0`

### 下一步操作

1. **检查 DocRay OCR 配置和日志**
2. **如果 OCR 未工作，配置 PaddleOCR**
3. **重新处理文档**（重建索引）
4. **验证文本内容是否提取成功**
