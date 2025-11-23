# 支持的文档类型

本文档列出了 ApeRAGv2 系统支持的所有文档类型和文件格式。

## 📋 文档类型总览

### 📄 文档格式

#### Office 文档

- **Word 文档**

  - `.docx` - Word 2007+ 格式 ✅
  - `.doc` - Word 97-2003 格式 ✅（需要 DocRay 或 LibreOffice）

- **Excel 表格**

  - `.xlsx` - Excel 2007+ 格式 ✅
  - `.xls` - Excel 97-2003 格式 ✅（需要 LibreOffice）

- **PowerPoint 演示文稿**
  - `.pptx` - PowerPoint 2007+ 格式 ✅
  - `.ppt` - PowerPoint 97-2003 格式 ✅（需要 DocRay 或 LibreOffice）

#### PDF 文档

- `.pdf` - PDF 文档 ✅
  - 支持复杂布局、表格、公式
  - 支持 OCR（如果启用）

#### 文本格式

- `.txt` - 纯文本文件 ✅
- `.text` - 纯文本文件 ✅
- `.md` - Markdown 文件 ✅
- `.markdown` - Markdown 文件 ✅
- `.html` - HTML 文件 ✅
- `.htm` - HTML 文件 ✅

#### 电子书

- `.epub` - EPUB 电子书格式 ✅

#### 代码/数据文件

- `.ipynb` - Jupyter Notebook 文件 ✅

### 🖼️ 图像格式

- `.jpg` / `.jpeg` - JPEG 图像 ✅
- `.png` - PNG 图像 ✅
- `.bmp` - BMP 位图 ✅
- `.tiff` / `.tif` - TIFF 图像 ✅

**图像处理功能**：

- OCR 文字识别（支持 SiliconFlow OCR 或 PaddleOCR）
- Vision-to-Text（使用 Vision LLM 生成图像描述）

### 🎵 音频格式

- `.mp3` - MP3 音频 ✅
- `.mp4` - MP4 视频/音频 ✅
- `.mpeg` - MPEG 视频/音频 ✅
- `.mpga` - MPEG 音频 ✅
- `.m4a` - M4A 音频 ✅
- `.wav` - WAV 音频 ✅
- `.webm` - WebM 视频/音频 ✅
- `.ogg` - OGG 音频 ✅
- `.flac` - FLAC 无损音频 ✅

**音频处理功能**：

- 语音转文字（使用 Whisper 服务）

## 🔧 解析器配置

### 默认启用的解析器

1. **DocRay** - 高级文档解析（需要 `DOCRAY_HOST` 配置）

   - 支持：`.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`
   - 特点：高质量解析，支持复杂布局

2. **MarkItDown** - 通用文档解析（默认启用）

   - 支持：`.txt`, `.text`, `.md`, `.markdown`, `.html`, `.htm`, `.ipynb`, `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.ppt`, `.epub`
   - 特点：通用解析器，需要 LibreOffice 处理旧版 Office 格式

3. **ImageParser** - 图像解析（默认启用）

   - 支持：`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`
   - 特点：OCR 和 Vision-to-Text

4. **AudioParser** - 音频解析（默认启用）
   - 支持：`.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm`, `.ogg`, `.flac`
   - 特点：语音转文字

### 可选解析器

5. **MinerU** - 高级 PDF/文档解析（需要配置）
   - 支持：`.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.png`, `.jpg`, `.jpeg`
   - 特点：需要 MinerU API Token
   - 配置：设置 `USE_MINERU_API=True` 和 `MINERU_API_TOKEN`

## 📊 文件类型统计

| 类别        | 数量    | 格式                                                     |
| ----------- | ------- | -------------------------------------------------------- |
| Office 文档 | 6       | .docx, .doc, .xlsx, .xls, .pptx, .ppt                    |
| PDF         | 1       | .pdf                                                     |
| 文本格式    | 7       | .txt, .text, .md, .markdown, .html, .htm, .ipynb         |
| 电子书      | 1       | .epub                                                    |
| 图像        | 6       | .jpg, .jpeg, .png, .bmp, .tiff, .tif                     |
| 音频/视频   | 9       | .mp3, .mp4, .mpeg, .mpga, .m4a, .wav, .webm, .ogg, .flac |
| **总计**    | **30+** |                                                          |

## ⚙️ 配置要求

### DocRay 解析器

- **环境变量**：`DOCRAY_HOST`（例如：`http://aperag-docray:8639`）
- **服务状态**：需要 DocRay 服务运行
- **自动启用**：如果 `DOCRAY_HOST` 已设置，系统会自动启用 DocRay

### LibreOffice（用于旧版 Office 格式）

- **用途**：转换 `.doc` → `.docx`，`.ppt` → `.pptx`，`.xls` → `.xlsx`
- **状态**：已集成到 Dockerfile（如果已重新构建镜像）
- **或**：使用 DocRay 直接解析旧版格式（推荐）

### Whisper 服务（用于音频转文字）

- **环境变量**：`WHISPER_HOST`
- **用途**：语音转文字

### OCR 服务（用于图像文字识别）

- **SiliconFlow OCR**：`SILICONFLOW_OCR_API_KEY`
- **或 PaddleOCR**：自动回退

## 🎯 使用建议

### 推荐配置

1. **启用 DocRay**（推荐）

   - 设置 `DOCRAY_HOST` 环境变量
   - 支持高质量解析，包括旧版 Office 格式

2. **启用 LibreOffice**（可选）

   - 如果已重新构建 Docker 镜像，自动支持
   - 或使用 DocRay 替代

3. **启用 OCR**（图像处理）
   - 配置 `SILICONFLOW_OCR_API_KEY` 或使用 PaddleOCR

### 文件格式选择建议

- **新文档**：优先使用 `.docx`, `.xlsx`, `.pptx`（现代格式）
- **旧文档**：`.doc`, `.xls`, `.ppt` 可通过 DocRay 或 LibreOffice 解析
- **PDF**：推荐使用 DocRay 或 MinerU 获得最佳效果
- **图像**：支持 OCR 和 Vision-to-Text 两种模式
- **音频**：需要配置 Whisper 服务

## 📝 注意事项

1. **文件大小限制**：默认最大 50MB（可通过 `MAX_DOCUMENT_SIZE` 配置）
2. **解析器优先级**：DocRay → MarkItDown → 其他解析器
3. **自动回退**：如果某个解析器失败，系统会自动尝试下一个解析器
4. **服务依赖**：某些格式需要特定服务运行（DocRay、Whisper 等）

## 🔗 相关文档

- [文档解析失败诊断](DOC_DOCUMENT_PARSE_FAILURE_DIAGNOSIS.md)
- [Docker 文档向量化失败诊断](DOCKER_VECTOR_FAILURE_DIAGNOSIS.md)
- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
