# 颍州变接线图.pdf 知识图谱未建立问题诊断报告

## 问题概述

文档"颍州变接线图.pdf"（文档 ID: `doc943a4031a8c27620`）的知识图谱索引状态为 ACTIVE，但未提取到任何实体和关系：

- `chunks_created`: 0
- `entities_extracted`: 0
- `relations_extracted`: 0

## 根本原因

从 Celery Worker 日志分析，发现了问题的根本原因：

### 1. 文档内容为空

文档解析后，`content` 字段为空：

```
'content': ''
```

这是因为 PDF 是纯图片型（扫描版），没有文本层。

### 2. Vision 索引处理时间过长

知识图谱构建时，系统尝试等待 Vision 索引完成以获取 Vision-to-Text 内容：

```
[2025-11-16 14:35:30,794] INFO - Processing document doc943a4031a8c27620 for graph indexing, initial content length: 0 characters
[2025-11-16 14:35:30,794] INFO - Attempting to enrich content with vision analysis for document doc943a4031a8c27620...
[2025-11-16 14:35:30,797] INFO - Vision index for document doc943a4031a8c27620 is still in progress (CREATING), waited 0s / 120s, continuing to wait...
```

系统等待了 120 秒，但 Vision 索引需要 **183 秒** 才完成：

```
[2025-11-16 14:37:31,006] WARNING - Timeout waiting for Vision index to complete for document doc943a4031a8c27620 after 120s
[2025-11-16 14:37:31,006] WARNING - No content available for document doc943a4031a8c27620 (neither text nor vision content), skipping graph indexing
```

而 Vision 索引实际完成时间：

```
[2025-11-16 14:38:34,629] INFO - Created 1 vision-to-text vectors for document doc943a4031a8c27620
```

### 3. 超时导致知识图谱跳过

由于 Vision 索引处理时间（183 秒）超过了知识图谱的等待超时时间（120 秒），知识图谱在 Vision 索引完成前就跳过了构建，导致：

- 没有获取到 Vision-to-Text 内容
- 无法从内容中提取实体和关系
- 最终结果：`chunks_created: 0, entities_extracted: 0, relations_extracted: 0`

## 解决方案

### 方案一：重建知识图谱索引（推荐，最简单）

由于 Vision 索引已经成功创建并生成了 vision-to-text 向量，现在可以直接重建知识图谱索引：

**方法 A：通过 Web 界面**

1. 登录 ApeRAG Web 界面
2. 进入对应的 Collection
3. 找到"颍州变接线图.pdf"文档
4. 进入文档详情页
5. 找到 GRAPH 索引
6. 点击"重建索引"按钮

**方法 B：通过 API**

```bash
curl -X POST "http://localhost:8000/api/v1/collections/colb948520084941356/documents/doc943a4031a8c27620/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["GRAPH"]
  }'
```

重建后，系统会：

1. 从已完成的 Vision 索引中获取 vision-to-text 内容
2. 使用这些内容构建知识图谱
3. 提取实体和关系

### 方案二：代码已修复（无需超时等待）

**✅ 已修复**：代码已修改为无限等待 Vision 索引完成，不再有超时限制。

修改内容：

- `aperag/graph/lightrag_manager.py` 中的 `_enrich_content_with_vision_analysis` 函数
- `max_wait_time` 参数默认值改为 `None`，表示无限等待
- 移除了超时检查，知识图谱构建会一直等待直到 Vision 索引完成

**应用修复**：

重启 Celery Worker 以应用修复：

```bash
docker-compose restart celeryworker
```

修复后，知识图谱构建会：

- 无限等待 Vision 索引完成（不再有 120 秒超时限制）
- 每 10 秒记录一次等待日志
- 一旦 Vision 索引完成，立即获取内容并构建知识图谱

## 验证修复效果

重建知识图谱索引后，检查日志应该看到：

```
INFO: Enriched content for document doc943a4031a8c27620 with X vision analysis sections
INFO: Processing document doc943a4031a8c27620 for graph indexing, initial content length: XXXX characters
```

并且知识图谱数据应该包含：

- `chunks_created > 0`
- `entities_extracted > 0`（应该有很多实体，特别是设备编号、线路名称等）
- `relations_extracted > 0`（应该有很多关系，特别是连接关系）

## 预期结果

重建索引后，对于变电站接线图，应该提取到：

### 实体类型：

- 电压等级实体（如"500kV"、"220kV"）
- 母线实体（如"500kV I 母"、"220kV IA 母"）
- 主变压器实体（如"1 号主变"、"2 号主变"）
- 线路实体（如"汤州 5354 线"、"颍稻 4736 线"）
- 设备实体（开关、刀闸、CT、低抗、站用变等）

### 关系类型：

- 连接关系（如"线路 A 连接到母线 B"）
- 包含关系（如"主变包含多个绕组"）
- 位置关系（如"设备位于某个电压等级"）

## 相关文档

- [颍州变接线图\_知识图谱诊断报告.md](颍州变接线图_知识图谱诊断报告.md)
- [DOCUMENT_INDEX_TROUBLESHOOTING.md](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [KNOWLEDGE_GRAPH_DIAGNOSIS.md](KNOWLEDGE_GRAPH_DIAGNOSIS.md)
