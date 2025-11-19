# 如何查看 Vision-to-Text 文本内容

## 前提条件

1. **激活虚拟环境**（如果使用 uv）：

   ```bash
   # Windows PowerShell
   .venv\Scripts\Activate.ps1

   # Windows CMD
   .venv\Scripts\activate.bat

   # Linux/Mac
   source .venv/bin/activate
   ```

2. **或者使用 uv 运行**：
   ```bash
   uv run python check_vision_content.py --document-id <document_id>
   ```

## 方法 1：使用文档名称查找（最简单）

```bash
# 查找"颍州变接线图"的Vision-to-Text
python check_yingzhou_vision_text.py 颍州变接线图

# 查找其他文档（支持模糊匹配）
python check_yingzhou_vision_text.py 主接线
python check_yingzhou_vision_text.py 接线图
```

## 方法 2：使用文档 ID（最准确）

首先需要获取文档 ID，然后运行：

```bash
python check_vision_content.py --document-id <document_id>
```

## 方法 3：列出所有有 Vision 索引的文档

```bash
python list_vision_documents.py
```

这会列出所有有 Vision 索引的文档及其 ID，然后你可以使用方法 2 查看具体内容。

## 如果遇到模块导入错误

如果遇到 `ModuleNotFoundError`，请确保：

1. **已安装所有依赖**：

   ```bash
   uv sync --all-groups --all-extras
   ```

2. **或者使用 Docker 环境**：
   ```bash
   docker-compose exec api python check_vision_content.py --document-id <document_id>
   ```

## 输出说明

脚本会显示：

- ✅ Vision 索引状态
- ✅ 完整的 Vision-to-Text 文本内容（所有片段）
- ✅ 每个片段的元数据（Asset ID、文本长度等）
- ✅ 总字符数统计
- ✅ 连接关系关键词分析（如果使用 check_yingzhou_vision_text.py）

## 示例输出

```
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
