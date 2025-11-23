# .doc 文件解析失败诊断报告

## 问题现象

文档 `2-国家电网公司变电运维管理规定（试行）.doc` 解析失败，所有索引（VECTOR、FULLTEXT、GRAPH、VISION）都失败。

## 错误信息

```
Exception: Document parsing failed for /tmp/2-国家电网公司变电运维管理规定（试行）orljyjk4.doc:
No parser can handle file with extension ".doc"

根本原因：
aperag.docparser.base.FallbackError: soffice command not found
```

## 问题分析

### 1. 核心问题

- **`.doc` 文件（旧版 Word 格式）无法被解析**
- **MarkItDown 解析器需要 LibreOffice 的 `soffice` 命令来转换 `.doc` 文件**
- **Docker 容器中未安装 LibreOffice**

### 2. 解析器支持情况

| 解析器         | 支持 .doc   | 状态      | 说明                               |
| -------------- | ----------- | --------- | ---------------------------------- |
| **MarkItDown** | ✅ 需要转换 | ❌ 失败   | 需要 `soffice` 命令（LibreOffice） |
| **DocRay**     | ✅ 原生支持 | ✅ 可用   | 服务已运行，但需要配置启用         |
| **MinerU**     | ✅ 原生支持 | ⚠️ 需配置 | 需要 MinerU API Token              |

### 3. 当前解析器配置

根据代码分析：

- **MarkItDown** 是默认解析器，优先级较高
- **DocRay** 需要 `use_doc_ray=True` 配置才会启用
- 解析器按顺序尝试，如果 MarkItDown 失败且没有 `soffice`，会抛出 `FallbackError`，但最终所有解析器都失败

## 解决方案

### 方案一：安装 LibreOffice（推荐，兼容性最好）

在 Dockerfile 中添加 LibreOffice 安装：

```dockerfile
# 在 Final stage 的 RUN 命令中添加
RUN apt update && \
    apt install --no-install-recommends -y \
        curl \
        libreoffice \
        libreoffice-writer \
        libreoffice-core && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*
```

**优点**：

- 支持所有旧版 Office 格式（.doc, .ppt, .xls）
- 与现有解析器兼容
- 不需要修改代码

**缺点**：

- 增加镜像大小（约 200-300MB）
- 需要重新构建镜像

### 方案二：使用 DocRay 解析 .doc 文件（✅ 已实现）

**已自动修复**：代码已修改，当 `DOCRAY_HOST` 环境变量设置时，DocRay 会自动启用来处理 `.doc` 文件，即使 `use_doc_ray=False`。

**优点**：

- ✅ 不需要重新构建镜像
- ✅ DocRay 服务已运行
- ✅ 自动启用，无需手动配置
- ✅ DocRay 在 MarkItDown 之前尝试，优先处理 `.doc` 文件

**说明**：

- 如果 DocRay 服务可用（`DOCRAY_HOST` 已设置），系统会自动使用 DocRay 解析 `.doc` 文件
- 无需在 Collection 配置中设置 `use_doc_ray=True`
- 解析器顺序：DocRay → MarkItDown，确保 DocRay 优先处理

### 方案三：将 .doc 文件转换为 .docx（临时方案）

在本地将 `.doc` 文件转换为 `.docx` 后重新上传。

**优点**：

- 立即可用，无需修改系统

**缺点**：

- 需要手动转换每个文件
- 不适用于批量处理

## 推荐修复步骤

### 方案二（推荐，无需重建镜像）

由于 DocRay 服务已运行，代码已自动修复，系统会自动使用 DocRay 解析 `.doc` 文件。

**只需重启 Celery Worker**：

```bash
docker-compose restart celeryworker
```

然后重新处理失败的文档（在 Web 界面中点击"重建索引"）。

### 方案一（如果需要 LibreOffice 支持其他格式）

### 1. 修改 Dockerfile

在 `Dockerfile` 的第 23-26 行，修改为：

```dockerfile
# Install minimal system dependencies in one layer and clean up
RUN apt update && \
    apt install --no-install-recommends -y \
        curl \
        libreoffice \
        libreoffice-writer \
        libreoffice-core && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*
```

### 2. 重新构建镜像

```bash
docker-compose build celeryworker
# 或者重新构建所有服务
docker-compose build
```

### 3. 重启服务

```bash
docker-compose restart celeryworker
```

### 4. 重新处理失败的文档

在 Web 界面中：

1. 进入文档详情页
2. 点击"重建索引"按钮

或使用 API：

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"index_types": ["VECTOR", "FULLTEXT", "GRAPH", "VISION"]}'
```

## 验证修复

### 1. 检查 LibreOffice 是否安装

```bash
docker exec aperag-celeryworker which soffice
# 应该输出: /usr/bin/soffice
```

### 2. 测试 .doc 文件解析

上传一个 `.doc` 文件，观察日志：

```bash
docker logs aperag-celeryworker -f | grep -i "parse\|doc"
```

应该看到成功解析的日志，而不是 `soffice command not found` 错误。

## 其他相关文档

- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [Docker 文档向量化失败诊断](DOCKER_VECTOR_FAILURE_DIAGNOSIS.md)
