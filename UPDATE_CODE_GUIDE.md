# 更新代码指南

## 当前配置情况

根据 Docker 配置，代码是在构建镜像时复制到容器内的（通过 `COPY . /app`），而不是通过 volume 挂载。这意味着：

- ❌ **仅重启容器不会更新代码**
- ✅ **需要重新构建镜像才能更新代码**

## 更新代码的方法

### 方法一：重新构建并重启（推荐）

```bash
# 1. 重新构建镜像（只构建 celeryworker 服务）
docker-compose build celeryworker

# 2. 重启 celeryworker 容器以使用新镜像
docker-compose up -d celeryworker

# 或者一步完成：重新构建并重启
docker-compose up -d --build celeryworker
```

### 方法二：完全重建（如果方法一不行）

```bash
# 停止并删除容器
docker-compose stop celeryworker
docker-compose rm -f celeryworker

# 重新构建并启动
docker-compose build celeryworker
docker-compose up -d celeryworker
```

### 方法三：开发环境配置（可选，用于开发时快速更新）

如果您在开发环境中，可以将代码目录挂载为 volume，这样修改代码后重启容器就能生效。

修改 `docker-compose.yml` 中的 `celeryworker` 服务，添加代码目录挂载：

```yaml
celeryworker:
  # ... 其他配置 ...
  volumes:
    - ~/.cache:/root/.cache
    - ./resources:/data/resources
    - aperag-shared-data:/shared
    - ./aperag:/app/aperag # 添加这行，挂载代码目录
```

然后重启容器：

```bash
docker-compose restart celeryworker
```

**注意**：开发环境配置只适用于开发阶段，生产环境不建议使用。

## 验证代码是否更新

更新后，可以通过以下方式验证：

```bash
# 1. 检查文件修改时间
docker exec aperag-celeryworker ls -la /app/aperag/graph/lightrag_manager.py

# 2. 检查代码内容（查看关键修改）
docker exec aperag-celeryworker grep -A 5 "max_wait_time.*None" /app/aperag/graph/lightrag_manager.py

# 3. 查看 Celery Worker 日志，确认新代码已加载
docker logs aperag-celeryworker --tail 50
```

## 针对当前修改（无限等待 Vision 索引）

修改了 `aperag/graph/lightrag_manager.py` 后，执行：

```bash
# 重新构建并重启
docker-compose up -d --build celeryworker

# 验证修改
docker exec aperag-celeryworker grep "max_wait_time.*None" /app/aperag/graph/lightrag_manager.py
```

应该看到：

```python
max_wait_time: int | None = None,
```

## 注意事项

1. **构建时间**：重新构建镜像可能需要几分钟时间，取决于代码变更量
2. **服务中断**：重启期间，Celery Worker 会短暂停止处理任务
3. **正在运行的任务**：重启会中断正在运行的任务，这些任务会重新排队
4. **缓存问题**：如果修改后仍不生效，可能需要清理 Python 缓存：
   ```bash
   docker exec aperag-celeryworker find /app -name "*.pyc" -delete
   docker exec aperag-celeryworker find /app -name "__pycache__" -type d -exec rm -r {} +
   ```

## 快速更新命令（一键执行）

```bash
# 更新代码并重启
docker-compose up -d --build celeryworker && docker logs aperag-celeryworker --tail 20 -f
```
