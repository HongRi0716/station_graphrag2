# 查看 Vision-to-Text 文本内容指南

## 方法 1：使用 check_vision_content.py（推荐）

查看指定文档的完整 Vision-to-Text 文本：

```bash
python check_vision_content.py --document-id <document_id>
```

**示例：**

```bash
python check_vision_content.py --document-id abc123-def456-ghi789
```

**输出内容：**

- Vision 索引状态
- Context IDs 数量
- 完整的 Vision-to-Text 文本内容（所有片段）
- 每个片段的元数据（Asset ID、文本长度等）
- 总字符数统计

## 方法 2：使用 check_yingzhou_vision_text.py

按文档名称查找并查看 Vision-to-Text 文本：

```bash
python check_yingzhou_vision_text.py [文档名称]
```

**示例：**

```bash
# 查看"颍州变接线图"的Vision-to-Text
python check_yingzhou_vision_text.py 颍州变接线图

# 查看其他文档（支持模糊匹配）
python check_yingzhou_vision_text.py 主接线
```

**输出内容：**

- 文档信息
- Vision 索引状态
- 完整的 Vision-to-Text 文本内容
- 连接关系关键词分析

## 方法 3：使用 view_merged_content.py

查看 OCR 和 Vision-to-Text 合并后的内容：

```bash
python view_merged_content.py <document_id>
```

## 获取 Document ID

如果需要查找文档的 ID，可以通过以下方式：

1. **通过数据库查询**：

   ```python
   from aperag.config import get_sync_session
   from aperag.db.models import Document
   from sqlalchemy import select

   for session in get_sync_session():
       docs = session.execute(
           select(Document).where(Document.name.like("%文档名称%"))
       ).scalars().all()
       for doc in docs:
           print(f"ID: {doc.id}, Name: {doc.name}")
   ```

2. **通过 API**：
   - 访问 `/api/v1/documents` 端点
   - 查看文档列表获取 ID

## 注意事项

1. **确保环境已激活**：

   - 如果使用虚拟环境，需要先激活
   - 确保所有依赖已安装

2. **确保服务运行**：

   - 数据库连接正常
   - 向量数据库（Qdrant）连接正常

3. **Vision 索引状态**：
   - 确保 Vision 索引已创建（status = "completed"）
   - 如果索引不存在或失败，需要先创建索引

## 输出示例

```
================================================================================
Vision索引内容检查
================================================================================

文档ID: abc123-def456-ghi789

Vision索引状态: completed
Context IDs数量: 2

从向量存储检索到 2 个点
✅ 找到Vision-to-Text #1 (长度: 1234 字符, Asset ID: asset_001)
✅ 找到Vision-to-Text #2 (长度: 2345 字符, Asset ID: asset_002)

================================================================================
Vision-to-Text完整内容 (共 2 个片段)
================================================================================

================================================================================
片段 #1 (Point ID: point_001)
Asset ID: asset_001
文本长度: 1234 字符
--------------------------------------------------------------------------------
## Summary
This is a 500kV substation primary system wiring diagram...

## Equipment & Components
- Transformer 1: 500kV/220kV
- Circuit Breaker 505117: 500kV
...

## Connection Relationships
主变1号连接500kV母线和220kV母线...
汤州5354线通过断路器505117连接到500kV I母...
================================================================================

总计: 2 个Vision-to-Text片段, 总字符数: 3579
```
