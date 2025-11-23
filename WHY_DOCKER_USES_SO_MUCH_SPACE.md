# 为什么 Docker 会占用这么大空间？

## 📊 当前情况

- **虚拟磁盘文件**: `docker_data.vhdx` 占用 **163.16 GB**
- **E 盘可用空间**: 仅 0.11 GB
- **最后更新时间**: 2025/11/23 16:24:22

## 🔍 Docker 占用空间的主要原因

### 1. WSL2 虚拟磁盘的特性（主要原因）

Docker Desktop 在 Windows 上使用 WSL2（Windows Subsystem for Linux 2），所有 Docker 数据都存储在一个**虚拟磁盘文件**（`.vhdx`）中。

#### 为什么虚拟磁盘文件会这么大？

1. **动态增长，但不会自动缩小**

   - 虚拟磁盘文件会随着使用自动增长
   - 但删除数据后，文件大小**不会自动减小**
   - 即使删除了镜像、容器，虚拟磁盘文件仍然保持最大时的大小

2. **预分配空间**

   - Docker 可能会预分配空间以提高性能
   - 即使没有使用，这些空间也会被占用

3. **文件系统碎片**
   - 频繁创建和删除文件会产生碎片
   - 碎片空间无法被有效利用

### 2. Docker 镜像（Image）

#### 镜像占用空间的原因：

- **基础镜像**: 每个镜像都包含完整的操作系统层

  - Ubuntu 基础镜像: ~70-100 MB
  - Python 镜像: ~100-200 MB
  - 包含完整工具链的镜像: 500 MB - 2 GB+

- **多层叠加**: Docker 使用分层存储

  - 每个 Dockerfile 指令创建一个新层
  - 所有层叠加在一起占用空间

- **多个版本**: 同一个镜像的不同版本（tag）会占用独立空间
  - `python:3.11` 和 `python:3.12` 是两个不同的镜像
  - 即使基础层相同，也会分别存储

#### 示例：ApeRAG 项目的镜像

```yaml
# docker-compose.yml 中的镜像
- aperag:latest # 应用镜像，可能 1-3 GB
- pgvector/pgvector:pg16 # PostgreSQL + pgvector，约 500 MB
- redis:6 # Redis，约 100 MB
- qdrant/qdrant:v1.13.4 # Qdrant向量数据库，约 200 MB
- elasticsearch:8.8.2 # Elasticsearch，约 800 MB
- neo4j:5.26.5 # Neo4j图数据库，约 500 MB
- doc-ray:v0.2.0 # DocRay文档解析，可能 2-5 GB
```

**总计**: 仅镜像就可能占用 **5-10 GB**

### 3. Docker 容器（Container）

#### 容器占用空间的原因：

- **可写层**: 每个运行中的容器都有一个可写层

  - 存储容器运行时的文件修改
  - 日志文件
  - 临时文件

- **日志文件**: 容器产生的日志会不断增长

  - 如果日志没有限制，可能增长到几 GB
  - 特别是应用日志、数据库日志

- **临时文件**: 容器运行过程中产生的临时文件
  - 缓存文件
  - 下载的文件
  - 编译产生的中间文件

#### 示例：ApeRAG 项目的容器

```yaml
# 每个容器都会占用空间
- aperag-api: # API服务，日志可能 100-500 MB
- aperag-celeryworker: # Celery工作进程，日志可能 500 MB - 2 GB
- aperag-frontend: # 前端服务，相对较小
- aperag-postgres: # PostgreSQL数据库，数据文件可能很大
- aperag-qdrant: # 向量数据库，向量数据可能很大
- aperag-es: # Elasticsearch，索引数据可能很大
- aperag-docray: # DocRay服务，可能占用 2-5 GB
```

### 4. Docker 数据卷（Volume）

#### 数据卷占用空间的原因：

数据卷是**持久化存储**，用于保存应用数据，这些数据会一直占用空间：

- **数据库数据**:

  - PostgreSQL 数据文件
  - Elasticsearch 索引
  - Qdrant 向量数据
  - Neo4j 图数据

- **应用数据**:
  - 上传的文件
  - 生成的文档
  - 缓存数据

#### 示例：ApeRAG 项目的数据卷

```yaml
volumes:
  aperag-postgres-data: # PostgreSQL数据，可能 1-10 GB（取决于数据量）
  aperag-qdrant-data: # 向量数据，可能 5-50 GB（取决于向量数量）
  aperag-redis-data: # Redis数据，通常较小
  aperag-es-data: # Elasticsearch索引，可能 1-10 GB
  aperag-neo4j-data: # Neo4j图数据，可能 1-5 GB
  aperag-shared-data: # 共享数据，可能 1-10 GB
```

**总计**: 数据卷可能占用 **10-100 GB**（取决于实际数据量）

### 5. Docker 构建缓存（Build Cache）

#### 构建缓存占用空间的原因：

- **构建层缓存**: Docker 会缓存每个构建步骤

  - 每个`RUN`命令的结果
  - 每个`COPY`命令的文件
  - 即使构建失败，缓存也会保留

- **依赖下载**: 构建过程中下载的依赖包

  - Python 包（pip cache）
  - Node.js 包（npm cache）
  - 系统包（apt cache）

- **中间镜像**: 构建过程中产生的中间镜像
  - 每个构建步骤都会创建一个中间镜像
  - 这些镜像会一直保留直到被清理

#### 示例：ApeRAG 项目的构建缓存

```dockerfile
# Dockerfile 中的每个步骤都会产生缓存
FROM python:3.11.13-slim          # 基础镜像层
RUN apt update && apt install...  # 系统包缓存
COPY pyproject.toml uv.lock* ./    # 依赖文件层
RUN uv sync --active              # Python依赖缓存
COPY . /app                       # 应用代码层
```

**构建缓存可能占用**: **5-20 GB**

### 6. 未使用的资源

#### 未使用的资源占用空间：

- **停止的容器**: 已停止但未删除的容器
- **悬空镜像**: 没有标签的镜像（`<none>`）
- **未使用的卷**: 已创建但未使用的数据卷
- **未使用的网络**: 已创建但未使用的网络

## 📈 空间占用增长模式

### 正常使用情况下的空间增长：

```
初始安装:          ~5-10 GB
+ 基础镜像:        +5-10 GB
+ 应用镜像:        +2-5 GB
+ 数据卷（初始）:   +1-5 GB
─────────────────────────────
小规模使用:        ~15-30 GB

+ 运行日志:        +1-5 GB
+ 构建缓存:        +5-20 GB
+ 数据增长:        +10-50 GB
─────────────────────────────
中等规模使用:      ~30-100 GB

+ 大量数据:        +50-200 GB
+ 多个项目:        +20-50 GB
+ 未清理资源:      +10-30 GB
─────────────────────────────
大规模使用:        ~100-400 GB
```

### 为什么你的 Docker 占用了 163 GB？

可能的原因：

1. **长期使用未清理**

   - 积累了大量的构建缓存
   - 多个版本的镜像
   - 未删除的停止容器

2. **大量数据存储**

   - 向量数据库存储了大量向量数据
   - 文档数据库存储了大量文档
   - 日志文件不断增长

3. **虚拟磁盘未压缩**

   - 即使删除了数据，虚拟磁盘文件不会自动缩小
   - 需要手动压缩才能释放空间

4. **多个项目共享**
   - 如果 E 盘上还有其他 Docker 项目
   - 所有项目共享同一个虚拟磁盘

## 🛠️ 如何减少 Docker 占用空间

### 1. 定期清理（推荐）

```powershell
# 每周运行一次
docker system prune -a --volumes -f
docker builder prune -a -f
```

### 2. 限制日志大小

在`docker-compose.yml`中配置日志限制：

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. 使用多阶段构建

减少最终镜像大小：

```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder
# ... 构建步骤

# 运行阶段（只包含运行时需要的文件）
FROM python:3.11-slim
COPY --from=builder /app /app
```

### 4. 定期压缩虚拟磁盘

```powershell
# 每月运行一次
.\scripts\compact-docker-vhdx.ps1
```

### 5. 监控空间使用

```powershell
# 定期检查
docker system df
Get-PSDrive E | Select-Object Free, Used
```

### 6. 删除不需要的数据卷

```powershell
# 查看数据卷大小
docker system df -v

# 删除未使用的数据卷（⚠️ 会删除数据）
docker volume prune -f
```

## 📊 空间占用分析工具

### 查看详细空间使用：

```powershell
# Docker资源使用情况
docker system df -v

# 查看各个镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 查看各个容器大小
docker ps -a --format "table {{.Names}}\t{{.Size}}"

# 查看各个数据卷大小
docker system df -v | Select-String "VOLUME"
```

### 查找大文件：

```powershell
# 在WSL2中查找大文件（需要进入WSL2）
wsl -d docker-desktop
du -sh /var/lib/docker/* | sort -h
```

## 🎯 最佳实践

### 1. 定期维护计划

- **每天**: 检查运行中的容器
- **每周**: 清理未使用的资源
- **每月**: 压缩虚拟磁盘
- **每季度**: 审查和清理数据卷

### 2. 设置自动清理

在 Docker Desktop 中启用：

- Settings → Resources → Advanced
- 启用 "Automatically clean up unused data"

### 3. 监控和告警

设置空间使用阈值：

- 当 E 盘可用空间 < 10GB 时，执行清理
- 当虚拟磁盘 > 100GB 时，考虑压缩

### 4. 数据管理策略

- **重要数据**: 定期备份到其他位置
- **临时数据**: 使用临时卷，容器停止后自动删除
- **日志数据**: 设置日志轮转和大小限制

## 🔗 相关文档

- [E 盘空间紧急修复指南](E_DRIVE_SPACE_EMERGENCY_FIX.md)
- [Docker 清理指南](DOCKER_CLEANUP_GUIDE.md)
- [Docker 磁盘空间修复](DOCKER_DISK_SPACE_FIX.md)

## 💡 总结

Docker 占用大量空间的主要原因：

1. ✅ **WSL2 虚拟磁盘不会自动缩小** - 需要手动压缩
2. ✅ **镜像、容器、数据卷累积** - 需要定期清理
3. ✅ **构建缓存不断增长** - 需要定期清理
4. ✅ **日志文件不断增长** - 需要限制大小
5. ✅ **数据不断积累** - 需要管理策略

**解决方案**: 定期清理 + 压缩虚拟磁盘 + 监控空间使用

