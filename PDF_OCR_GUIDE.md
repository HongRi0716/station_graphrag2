# PDF 文件 OCR 识别功能指南

## 概述

ApeRAG 项目支持对 PDF 文件进行 OCR（光学字符识别），可以识别扫描版 PDF、图片型 PDF 等包含图像内容的文档。

## OCR 支持方式

项目提供了**多种 OCR 解决方案**，适用于不同的使用场景：

### 1. DocRay OCR（推荐，用于 PDF 文档）

**特点**：

- ✅ **自动 OCR**：DocRay 在处理 PDF 时会自动进行 OCR 识别
- ✅ **表格识别**：支持复杂表格的识别和提取
- ✅ **公式提取**：支持数学公式的识别
- ✅ **布局分析**：保留文档的原始布局结构
- ✅ **多语言支持**：支持中英文等多种语言

**适用场景**：

- 扫描版 PDF 文档
- 包含图片的 PDF
- 复杂布局的 PDF（表格、公式、图表）
- 需要保留文档结构的场景

**配置要求**：

- 已启动 DocRay 服务（已在 docker-compose.yml 中配置为自动启动）
- 环境变量：`DOCRAY_HOST=http://aperag-docray:8639`

**使用方法**：
DocRay 会自动处理 PDF 文件，无需额外配置。上传 PDF 文件后，系统会自动：

1. 使用 DocRay 解析 PDF
2. 对图片页面进行 OCR 识别
3. 提取文本、表格、公式等内容
4. 生成结构化的文档内容

### 2. PaddleOCR（用于图片文件）

**特点**：

- ✅ 专门用于图片文件的 OCR 识别
- ✅ 支持多种图片格式：`.jpg`, `.png`, `.bmp`, `.tiff`, `.tif`
- ✅ 高精度中文识别

**适用场景**：

- 单独的图片文件（非 PDF）
- 需要 OCR 识别的图片

**配置要求**：

- 需要配置 PaddleOCR 服务
- 环境变量：`PADDLEOCR_HOST=http://your-paddleocr-service:port`

**配置示例**：

```bash
# 在.env或envs/docker.env.overrides中
PADDLEOCR_HOST=http://your-paddleocr-service:port
```

### 3. MinerU OCR（云端服务）

**特点**：

- ✅ 云端 OCR 服务
- ✅ 支持 PDF、Word、PPT 等多种格式
- ✅ 自动 OCR 识别（通过`is_ocr: True`配置）

**适用场景**：

- 使用 MinerU 云端服务
- 需要云端处理的场景

**配置要求**：

- 需要 MinerU API Token
- 环境变量：`MINERU_API_TOKEN=your-token`

## 当前配置状态

根据您的 docker-compose.yml 配置：

✅ **DocRay 已配置为自动启动**

- DocRay 服务会在`docker-compose up`时自动启动
- 已配置健康检查和依赖关系
- 默认启用 OCR 功能

## OCR 工作流程

### PDF 文档处理流程

```
上传PDF文件
    ↓
DocRay解析器（自动选择）
    ↓
检测PDF类型
    ├─ 文本型PDF → 直接提取文本
    └─ 图片型PDF → OCR识别
    ↓
提取内容
    ├─ 文本内容
    ├─ 表格数据
    ├─ 公式
    └─ 图片
    ↓
生成结构化内容
    ↓
向量化和索引
```

### 图片文件处理流程

```
上传图片文件
    ↓
ImageParser（如果配置了PADDLEOCR_HOST）
    ↓
PaddleOCR服务OCR识别
    ↓
提取文本内容
    ↓
向量化和索引
```

## 验证 OCR 功能

### 1. 检查 DocRay 服务状态

```bash
# 检查DocRay容器是否运行
docker ps | grep docray

# 查看DocRay日志
docker logs aperag-docray --tail 50
```

### 2. 上传测试 PDF

1. 准备一个扫描版 PDF 或包含图片的 PDF
2. 通过 Web 界面上传 PDF 文件
3. 查看文档解析结果

### 3. 检查 OCR 结果

**通过 API 查询文档内容**：

```bash
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**通过数据库查询**：

```sql
-- 查看文档解析后的内容
SELECT
    d.name,
    di.index_type,
    di.status,
    LEFT(di.index_data::text, 200) as content_preview
FROM document_index di
JOIN document d ON di.document_id = d.id
WHERE d.name LIKE '%your-pdf-name%'
  AND di.index_type = 'VECTOR';
```

## 常见问题

### Q1: PDF 上传后没有 OCR 识别？

**可能原因**：

1. DocRay 服务未启动
2. PDF 是纯文本型，不需要 OCR
3. 文档解析失败

**解决方法**：

```bash
# 检查DocRay服务
docker ps | grep docray

# 查看celery worker日志
docker logs aperag-celeryworker | grep -i "ocr\|docray\|error"

# 重启DocRay服务
docker-compose restart docray
```

### Q2: OCR 识别准确率不高？

**优化建议**：

1. 使用 GPU 版本的 DocRay（如果可用）：
   ```bash
   docker-compose --profile docray-gpu up -d docray-gpu
   ```
2. 确保 PDF 图片质量清晰
3. 对于特定语言，可以配置语言参数

### Q3: 如何禁用 OCR？

如果不需要 OCR 功能，可以：

1. **禁用 DocRay**（不推荐，会失去高级解析功能）：

   ```bash
   # 在.env中注释掉
   # DOCRAY_HOST=
   ```

2. **使用 MarkItDown 解析器**（仅适用于文本型 PDF）：
   - 系统会自动回退到 MarkItDown 解析器
   - 但无法处理扫描版 PDF

### Q4: OCR 处理速度慢？

**优化方案**：

1. 使用 GPU 版本的 DocRay
2. 增加 DocRay 服务资源（CPU 和内存）
3. 对于大文件，考虑分批处理

## 性能优化建议

### 1. 资源配置

DocRay 服务建议配置：

- **CPU 模式**：4+ 核心，8GB+ RAM
- **GPU 模式**：1+ GPU，16GB+ RAM

### 2. 批量处理

对于大量 PDF 文件：

- 使用队列系统（Celery）自动处理
- 避免同时上传过多文件

### 3. 缓存策略

- OCR 结果会被缓存，相同文件不会重复 OCR
- 可以通过`CACHE_ENABLED`和`CACHE_TTL`配置缓存策略

## 相关文档

- [Docker 文档向量化失败诊断](DOCKER_VECTOR_FAILURE_DIAGNOSIS.md)
- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [DocRay 项目文档](https://github.com/apecloud/doc-ray)
- [架构设计文档](docs/design/architecture-zh.md)

## 总结

✅ **您的项目已支持 PDF OCR 识别**

- DocRay 服务已配置为自动启动
- 支持扫描版 PDF 和图片型 PDF 的 OCR 识别
- 自动处理，无需额外配置
- 支持表格、公式等复杂内容的识别

只需上传 PDF 文件，系统会自动进行 OCR 识别并提取文本内容！
