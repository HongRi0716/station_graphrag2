# Docker 镜像拉取问题修复指南

## 问题描述

构建 Docker 镜像时出现以下错误：

```
failed to solve: python:3.11.13-slim: failed to resolve source metadata for docker.io/library/python:3.11.13-slim: unexpected status from HEAD request to https://dockerproxy.net/v2/library/python/manifests/3.11.13-slim?ns=docker.io: 502 Bad Gateway
```

## 原因分析

Docker 配置了 `dockerproxy.net` 作为镜像代理，但该代理服务器当前不可用（502 Bad Gateway）。

## 解决方案

### 方案 1：使用国内镜像源（推荐）

#### Windows (Docker Desktop)

1. 打开 Docker Desktop
2. 点击右上角设置图标（齿轮）
3. 进入 **Docker Engine** 设置
4. 修改或添加以下配置：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

5. 点击 **Apply & Restart** 重启 Docker

#### Linux / macOS

编辑 Docker daemon 配置文件：

```bash
# Linux
sudo nano /etc/docker/daemon.json

# macOS (Docker Desktop)
# 通过 Docker Desktop 设置界面修改，或编辑：
# ~/.docker/daemon.json
```

添加或修改为：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

重启 Docker：

```bash
# Linux
sudo systemctl restart docker

# macOS/Windows
# 通过 Docker Desktop 重启
```

### 方案 2：移除代理配置，使用官方源

如果不需要代理，可以移除 `dockerproxy.net` 配置：

1. 打开 Docker Desktop 设置
2. 进入 **Docker Engine**
3. 删除或注释掉包含 `dockerproxy.net` 的配置
4. 重启 Docker

### 方案 3：临时使用环境变量（仅限当前构建）

在构建时指定镜像源：

```bash
# Windows PowerShell
$env:DOCKER_BUILDKIT=1
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t aperag:latest .

# 或者使用国内镜像源
docker pull python:3.11.13-slim
```

### 方案 4：修改 Dockerfile 使用国内镜像源

如果上述方案都不行，可以临时修改 Dockerfile：

```dockerfile
# 使用阿里云镜像源
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.11.13-slim AS builder
```

或使用中科大镜像：

```dockerfile
FROM docker.mirrors.ustc.edu.cn/library/python:3.11.13-slim AS builder
```

## 验证修复

修复后，验证镜像拉取是否正常：

```bash
docker pull python:3.11.13-slim
```

如果成功，应该能看到：

```
3.11.13-slim: Pulling from library/python
...
Status: Downloaded newer image for python:3.11.13-slim
```

## 推荐的国内镜像源

1. **中科大镜像**：`https://docker.mirrors.ustc.edu.cn`
2. **网易镜像**：`https://hub-mirror.c.163.com`
3. **百度云镜像**：`https://mirror.baidubce.com`
4. **阿里云镜像**：`https://registry.cn-hangzhou.aliyuncs.com`（需要登录）

## 注意事项

- 修改 Docker daemon.json 后必须重启 Docker 服务
- 如果使用多个镜像源，Docker 会按顺序尝试
- 某些镜像源可能需要登录或限制访问频率
