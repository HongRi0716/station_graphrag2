# LibreOffice 安装指南

LibreOffice 用于将旧版 Office 格式（`.doc`, `.ppt`, `.xls`）转换为现代格式（`.docx`, `.pptx`, `.xlsx`），以便 MarkItDown 解析器处理。

## 📋 安装方式

### 方式一：通过 Dockerfile 安装（推荐，已配置）

Dockerfile 已经包含了 LibreOffice 的安装配置，位于第 24-31 行：

```dockerfile
# Install minimal system dependencies in one layer and clean up
# Include LibreOffice for .doc/.ppt/.xls file conversion
RUN apt update && \
    apt install --no-install-recommends -y \
        curl \
        libreoffice \
        libreoffice-writer \
        libreoffice-core && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*
```

**安装步骤**：

1. **重新构建 Docker 镜像**：

```bash
# 只构建 celeryworker 服务
docker-compose build celeryworker

# 或重新构建所有服务
docker-compose build
```

2. **重启服务**：

```bash
docker-compose restart celeryworker
```

3. **验证安装**：

```bash
# 检查 soffice 命令是否可用
docker exec aperag-celeryworker which soffice
# 应该输出: /usr/bin/soffice

# 检查 LibreOffice 版本
docker exec aperag-celeryworker soffice --version
```

### 方式二：在运行中的容器中手动安装（临时方案）

如果不想重新构建镜像，可以在运行中的容器中手动安装：

```bash
# 进入容器
docker exec -it aperag-celeryworker bash

# 在容器内安装 LibreOffice
apt update && \
apt install --no-install-recommends -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-core && \
apt clean && \
rm -rf /var/lib/apt/lists/*

# 验证安装
which soffice
soffice --version

# 退出容器
exit
```

**注意**：这种方式安装的 LibreOffice 在容器重启后会丢失，需要重新安装。

### 方式三：使用 Dockerfile 多阶段构建优化（可选）

如果需要最小化镜像大小，可以只安装必要的组件：

```dockerfile
RUN apt update && \
    apt install --no-install-recommends -y \
        curl \
        libreoffice \
        libreoffice-writer \
        libreoffice-core \
        libreoffice-common && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*
```

## ✅ 验证安装

### 1. 检查命令是否可用

```bash
docker exec aperag-celeryworker which soffice
# 应该输出: /usr/bin/soffice
```

### 2. 检查版本信息

```bash
docker exec aperag-celeryworker soffice --version
# 应该输出类似: LibreOffice 7.x.x
```

### 3. 测试文档转换功能

```bash
# 在容器内测试转换功能
docker exec aperag-celeryworker soffice --headless --convert-to docx --outdir /tmp /path/to/test.doc
```

### 4. 查看日志验证

上传一个 `.doc` 文件，查看 Celery Worker 日志：

```bash
docker logs aperag-celeryworker -f | grep -i "parse\|doc\|soffice"
```

应该看到成功解析的日志，而不是 `soffice command not found` 错误。

## 📦 安装的组件说明

- **`libreoffice`** - LibreOffice 核心包
- **`libreoffice-writer`** - Word 文档处理（用于 `.doc` → `.docx`）
- **`libreoffice-core`** - 核心库文件

**可选组件**（如果需要处理 Excel 和 PowerPoint）：

- `libreoffice-calc` - Excel 表格处理（用于 `.xls` → `.xlsx`）
- `libreoffice-impress` - PowerPoint 演示文稿处理（用于 `.ppt` → `.pptx`）

如果需要支持 Excel 和 PowerPoint，可以在 Dockerfile 中添加：

```dockerfile
RUN apt update && \
    apt install --no-install-recommends -y \
        curl \
        libreoffice \
        libreoffice-writer \
        libreoffice-calc \
        libreoffice-impress \
        libreoffice-core && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*
```

## 🔧 配置和使用

### 自动使用

安装 LibreOffice 后，系统会自动使用它来转换旧版 Office 格式：

1. **MarkItDown 解析器**会自动检测 `.doc`、`.ppt`、`.xls` 文件
2. 使用 `soffice` 命令转换为现代格式
3. 然后解析转换后的文件

### 解析器优先级

对于 `.doc` 文件，解析器尝试顺序：

1. **DocRay**（如果 `DOCRAY_HOST` 已设置）- 直接解析，无需转换
2. **MarkItDown + LibreOffice** - 转换为 `.docx` 后解析
3. 如果都失败，会抛出错误

## ⚠️ 注意事项

### 1. 镜像大小

安装 LibreOffice 会增加 Docker 镜像大小约 **200-300MB**。

### 2. 资源消耗

LibreOffice 转换过程会消耗一定的 CPU 和内存资源。

### 3. 无头模式

LibreOffice 在 Docker 容器中以无头模式（headless）运行，不需要图形界面。

### 4. 替代方案

如果不想安装 LibreOffice，可以使用 **DocRay** 来直接解析旧版 Office 格式：

- DocRay 原生支持 `.doc`、`.ppt` 文件
- 不需要转换步骤
- 解析质量通常更好

**推荐**：如果 DocRay 服务可用，优先使用 DocRay，无需安装 LibreOffice。

## 🐛 故障排除

### 问题 1：`soffice command not found`

**原因**：LibreOffice 未安装或未在 PATH 中。

**解决**：

1. 检查是否已重新构建镜像
2. 检查 Dockerfile 中是否包含 LibreOffice 安装
3. 验证安装：`docker exec aperag-celeryworker which soffice`

### 问题 2：转换失败

**可能原因**：

- 文档损坏
- 文档有密码保护
- 内存不足

**解决**：

1. 检查文档是否可以正常打开
2. 查看 Celery Worker 日志获取详细错误信息
3. 尝试使用 DocRay 解析器

### 问题 3：转换速度慢

**原因**：LibreOffice 转换需要时间，特别是大文件。

**解决**：

- 使用 DocRay 解析器（通常更快）
- 或优化文档大小

## 📊 性能对比

| 解析器                       | .doc 支持 | 需要转换 | 速度 | 质量 |
| ---------------------------- | --------- | -------- | ---- | ---- |
| **DocRay**                   | ✅ 原生   | ❌ 否    | 快   | 高   |
| **MarkItDown + LibreOffice** | ✅ 转换后 | ✅ 是    | 中等 | 中等 |

## 🔗 相关文档

- [支持的文档类型](SUPPORTED_DOCUMENT_TYPES.md)
- [文档解析失败诊断](DOC_DOCUMENT_PARSE_FAILURE_DIAGNOSIS.md)
- [Docker 文档向量化失败诊断](DOCKER_VECTOR_FAILURE_DIAGNOSIS.md)
