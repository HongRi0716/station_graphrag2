# Docker 文档向量化失败诊断与修复指南

## 问题现象

文档向量化失败，错误信息显示：

```
Failed to resolve 'aperag-docray' ([Errno -2] Name or service not known)
VECTOR index operation failed for document: Failed to parse document
```

## 根本原因

**DocRay 服务未启动**。DocRay 是用于复杂 PDF 文档解析的微服务。

> **注意**：从配置更新后，DocRay 服务已配置为自动启动。如果您的配置已更新，DocRay 会在 `docker-compose up` 时自动启动。

## 快速诊断步骤

### 1. 检查 DocRay 服务状态

```bash
# 检查docray容器是否运行
docker ps | grep docray

# 或者检查所有服务
docker-compose ps
```

如果看不到`aperag-docray`容器，说明服务未启动。

### 2. 检查 Celery Worker 日志

```bash
# 查看celery worker日志中的错误
docker logs aperag-celeryworker --tail 100 | grep -i "docray\|error\|fail"
```

应该能看到类似错误：

```
Failed to resolve 'aperag-docray' ([Errno -2] Name or service not known)
```

## 解决方案

### 方案一：启动 DocRay 服务（推荐，用于复杂 PDF 解析）

**如果配置已更新（已移除 profiles）**：

```bash
# DocRay会自动启动，只需启动所有服务
docker-compose up -d

# 验证服务已启动
docker ps | grep docray
```

**如果使用旧配置（仍使用 profiles）**：

```bash
# 启动docray服务
docker-compose --profile docray up -d docray

# 验证服务已启动
docker ps | grep docray
```

**注意**：DocRay 服务需要：

- 4+ CPU 核心
- 8GB+ RAM
- 确保有足够资源

### 方案二：使用 GPU 版本的 DocRay（如果可用）

```bash
# 启动GPU版本的docray
docker-compose --profile docray-gpu up -d docray-gpu

# 更新环境变量指向GPU版本
# 在.env或envs/docker.env.overrides中设置：
# DOCRAY_HOST=http://aperag-docray-gpu:8639
```

### 方案三：禁用 DocRay，使用其他解析器（如果不需要复杂 PDF 解析）

如果您的文档主要是简单格式，可以禁用 DocRay：

1. **修改环境变量**，将`DOCRAY_HOST`设置为空或注释掉：

   ```bash
   # 在.env或envs/docker.env.overrides中
   # DOCRAY_HOST=
   ```

2. **重启 celery worker**：
   ```bash
   docker-compose restart celeryworker
   ```

系统会自动回退到其他解析器（如 MarkItDown）。

## 验证修复

### 1. 检查服务连接

```bash
# 在celery worker容器内测试连接
docker exec aperag-celeryworker curl -f http://aperag-docray:8639/health
```

### 2. 重新处理失败的文档

修复后，需要重新处理之前失败的文档：

**方法一：通过 API 重建索引**

```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/{document_id}/rebuild-indexes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "index_types": ["VECTOR"]
  }'
```

**方法二：通过 Web 界面**

1. 进入文档详情页
2. 找到失败的 VECTOR 索引
3. 点击"重建索引"按钮

### 3. 监控日志

```bash
# 实时查看celery worker日志
docker-compose logs -f celeryworker

# 查看文档解析日志
docker logs aperag-celeryworker | grep "parse\|vector\|embedding"
```

## 预防措施

### 1. 使用 Makefile 启动（推荐）

项目提供了 Makefile 来简化启动：

```bash
# 启动完整应用（包括DocRay）
make compose-up WITH_DOCRAY=1

# 启动基础服务（不包括DocRay）
make compose-up
```

### 2. 检查 docker-compose 配置

确保在`docker-compose.yml`中，celery worker 的依赖包含 docray（如果需要）：

```yaml
celeryworker:
  depends_on:
    docray:
      condition: service_healthy
```

### 3. 环境变量配置检查清单

确保以下配置正确：

- [ ] `DOCRAY_HOST` 指向正确的 docray 服务地址
- [ ] DocRay 服务已启动并健康
- [ ] 网络连接正常（容器间可以通信）
- [ ] 有足够的系统资源（CPU 和内存）

## 常见问题

### Q1: 启动 DocRay 后仍然失败？

**检查**：

1. 服务是否真的在运行：`docker ps | grep docray`
2. 网络连接：`docker exec aperag-celeryworker ping aperag-docray`
3. 端口是否正确：检查`8639`端口是否开放
4. 查看 docray 日志：`docker logs aperag-docray`

### Q2: 如何知道是否需要 DocRay？

**需要 DocRay 的情况**：

- 处理复杂的 PDF 文档（包含表格、公式、图表）
- 需要 OCR 功能
- 需要高质量的文档结构提取

**不需要 DocRay 的情况**：

- 简单的文本文档
- Markdown 文件
- 简单的 PDF（纯文本）

### Q3: DocRay 服务启动失败？

**可能原因**：

1. 资源不足（需要 4+ CPU 核心，8GB+ RAM）
2. 端口冲突（8639 端口被占用）
3. 镜像拉取失败

**解决方法**：

```bash
# 检查资源
docker stats aperag-docray

# 检查端口
netstat -an | grep 8639

# 重新拉取镜像
docker-compose pull docray
```

## 相关文档

- [文档索引失败诊断指南](DOCUMENT_INDEX_TROUBLESHOOTING.md)
- [开发指南 - DocRay 配置](docs/development-guide-zh.md#添加高级文档解析服务docray)
- [DocRay 项目](https://github.com/apecloud/doc-ray)
