# ApeRAGv2 非 Docker 迁移部署指南

本指南详细说明如何在**不使用 Docker** 的情况下部署 ApeRAGv2 系统。适用于以下场景：
- 离线环境部署
- 服务器资源有限无法运行 Docker
- 需要更精细的进程管理
- 开发测试环境

---

## 📋 目录

1. [系统要求](#系统要求)
2. [依赖服务安装](#依赖服务安装)
3. [后端部署](#后端部署)
4. [前端部署](#前端部署)
5. [启动服务](#启动服务)
6. [进程管理（生产环境）](#进程管理生产环境)
7. [常见问题](#常见问题)

---

## 🖥️ 系统要求

### 硬件要求
| 组件 | 最小配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8+ 核 |
| 内存 | 8 GB | 16+ GB |
| 磁盘 | 50 GB SSD | 200+ GB SSD |

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows 10/11
- **Python**: 3.11.12 ~ 3.12 (推荐 3.11.12)
- **Node.js**: 18+ (推荐 20.x)
- **包管理器**: uv (Python) / yarn (Node.js)

---

## 🗄️ 依赖服务安装

ApeRAGv2 需要以下数据库和服务，您需要在目标机器上单独安装：

### 1. PostgreSQL (必需)
主数据库，存储元数据、用户、文档等。

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE USER aperag WITH PASSWORD 'your_password';
CREATE DATABASE aperag OWNER aperag;
GRANT ALL PRIVILEGES ON DATABASE aperag TO aperag;
\q
```

**Windows:**
1. 下载安装包: https://www.postgresql.org/download/windows/
2. 运行安装程序，设置密码
3. 使用 pgAdmin 创建数据库

### 2. Redis (必需)
用于 Celery 任务队列、缓存、会话管理。

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Windows:**
1. 下载 Redis for Windows: https://github.com/microsoftarchive/redis/releases
2. 或使用 Memurai (Redis 兼容): https://www.memurai.com/

### 3. Qdrant (必需)
向量数据库，用于语义搜索。

**所有平台:**
```bash
# 下载并运行
curl -L https://github.com/qdrant/qdrant/releases/download/v1.9.1/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz
./qdrant --config-path config/config.yaml

# 或使用官方安装脚本
curl -sSL https://get.qdrant.io | sh
```

**默认端口**: 6333 (HTTP) / 6334 (gRPC)

### 4. Elasticsearch (必需)
全文搜索引擎。

**Ubuntu/Debian:**
```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.12.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.12.0-linux-x86_64.tar.gz
cd elasticsearch-8.12.0
./bin/elasticsearch
```

**禁用安全认证 (开发环境):**
编辑 `config/elasticsearch.yml`:
```yaml
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
```

### 5. NebulaGraph (可选，用于知识图谱)
如果使用 NebulaGraph 作为图数据库：

```bash
# 下载 Nebula Graph
wget https://github.com/vesoft-inc/nebula/releases/download/v3.6.0/nebula-graph-3.6.0.ubuntu2004.amd64.deb
sudo dpkg -i nebula-graph-3.6.0.ubuntu2004.amd64.deb
sudo systemctl start nebula-graphd nebula-storaged nebula-metad
```

### 6. Neo4j (可选，用于知识图谱)
如果使用 Neo4j 作为图数据库：

```bash
# Ubuntu
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
sudo systemctl enable neo4j
sudo systemctl start neo4j
```

**默认端口**: 7474 (HTTP) / 7687 (Bolt)

---

## 🐍 后端部署

### 步骤 1: 克隆项目
```bash
git clone https://github.com/apecloud/ApeRAG.git
cd ApeRAG
```

### 步骤 2: 安装 Python 环境

**安装 uv (推荐的包管理器):**
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

**创建虚拟环境并安装依赖:**
```bash
# 创建 Python 3.11 虚拟环境
uv venv -p 3.11.12

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\activate

# 安装所有依赖
uv sync --all-groups --all-extras
```

### 步骤 3: 配置环境变量

复制环境变量模板：
```bash
cp envs/env.template .env
```

编辑 `.env` 文件，配置以下关键项：

```bash
# ===== 数据库配置 =====
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=aperag
POSTGRES_USER=aperag
POSTGRES_PASSWORD=your_password

# ===== Redis 配置 =====
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# ===== 向量数据库 =====
VECTOR_DB_TYPE=qdrant
VECTOR_DB_CONTEXT={"url":"http://127.0.0.1","port":6333,"distance":"Cosine","timeout":1000}

# ===== Elasticsearch =====
ES_HOST_NAME=127.0.0.1
ES_PORT=9200
ES_USER=
ES_PASSWORD=
ES_PROTOCOL=http

# ===== 图数据库 (选择一个) =====
# Neo4j
NEO4J_HOST=127.0.0.1
NEO4J_PORT=7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# 或 NebulaGraph
NEBULA_HOST=127.0.0.1
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula

# ===== LLM 模型配置 =====
COMPLETION_MODEL_PROVIDER=siliconflow
COMPLETION_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
COMPLETION_MODEL_PROVIDER_API_KEY=your_api_key

EMBEDDING_MODEL_PROVIDER=siliconflow
EMBEDDING_MODEL_PROVIDER_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL_PROVIDER_API_KEY=your_api_key

# ===== 认证配置 =====
AUTH_TYPE=cookie

# ===== 对象存储（本地文件）=====
OBJECT_STORE_TYPE=local
OBJECT_STORE_LOCAL_ROOT_DIR=.objects
```

### 步骤 4: 初始化数据库

运行数据库迁移：
```bash
# 确保虚拟环境已激活
uv run alembic -c aperag/alembic.ini upgrade head
```

---

## 🌐 前端部署

### 步骤 1: 安装 Node.js 依赖
```bash
cd web
yarn install
```

### 步骤 2: 开发模式运行
```bash
yarn dev
```

### 步骤 3: 生产构建
```bash
yarn build
```

### 步骤 4: 生产环境运行
```bash
yarn start
```

或使用静态文件服务器：
```bash
# 使用 serve
npm install -g serve
serve -s build -l 3000
```

---

## 🚀 启动服务

ApeRAGv2 需要同时运行多个服务：

### 开发环境（命令行启动）

**终端 1 - 后端 API:**
```bash
cd ApeRAG
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
uvicorn aperag.app:app --host 0.0.0.0 --port 8000 --log-config scripts/uvicorn-log-config.yaml
```

**终端 2 - Celery Worker (异步任务):**
```bash
cd ApeRAG
source .venv/bin/activate
celery -A config.celery worker -B -l INFO --pool=threads --concurrency=16
```

**终端 3 - 前端:**
```bash
cd ApeRAG/web
yarn dev
# 或生产环境: yarn start
```

### 服务访问地址
- **Web 界面**: http://localhost:3000/web/
- **API 文档**: http://localhost:8000/docs
- **Celery Flower (任务监控)**: http://localhost:5555/

---

## 🏭 进程管理（生产环境）

### 使用 Systemd (Linux)

创建服务文件：

**/etc/systemd/system/aperag-api.service**
```ini
[Unit]
Description=ApeRAG API Server
After=network.target postgresql.service redis.service

[Service]
User=aperag
Group=aperag
WorkingDirectory=/opt/ApeRAG
Environment="PATH=/opt/ApeRAG/.venv/bin"
ExecStart=/opt/ApeRAG/.venv/bin/uvicorn aperag.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/aperag-celery.service**
```ini
[Unit]
Description=ApeRAG Celery Worker
After=network.target redis.service

[Service]
User=aperag
Group=aperag
WorkingDirectory=/opt/ApeRAG
Environment="PATH=/opt/ApeRAG/.venv/bin"
ExecStart=/opt/ApeRAG/.venv/bin/celery -A config.celery worker -B -l INFO --pool=threads --concurrency=16
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable aperag-api aperag-celery
sudo systemctl start aperag-api aperag-celery
```

### 使用 PM2 (跨平台)

安装 PM2：
```bash
npm install -g pm2
```

创建 **ecosystem.config.js**:
```javascript
module.exports = {
  apps: [
    {
      name: 'aperag-api',
      cwd: '/opt/ApeRAG',
      interpreter: '.venv/bin/python',
      script: '-m',
      args: 'uvicorn aperag.app:app --host 0.0.0.0 --port 8000',
      env: {
        PATH: '/opt/ApeRAG/.venv/bin:' + process.env.PATH,
      },
    },
    {
      name: 'aperag-celery',
      cwd: '/opt/ApeRAG',
      interpreter: '.venv/bin/celery',
      args: '-A config.celery worker -B -l INFO --pool=threads --concurrency=16',
    },
    {
      name: 'aperag-frontend',
      cwd: '/opt/ApeRAG/web',
      script: 'yarn',
      args: 'start',
    },
  ],
};
```

启动：
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 使用 Supervisor

安装：
```bash
sudo apt install supervisor
```

配置 **/etc/supervisor/conf.d/aperag.conf**:
```ini
[program:aperag-api]
command=/opt/ApeRAG/.venv/bin/uvicorn aperag.app:app --host 0.0.0.0 --port 8000
directory=/opt/ApeRAG
user=aperag
autostart=true
autorestart=true
stderr_logfile=/var/log/aperag/api.err.log
stdout_logfile=/var/log/aperag/api.out.log

[program:aperag-celery]
command=/opt/ApeRAG/.venv/bin/celery -A config.celery worker -B -l INFO --pool=threads --concurrency=16
directory=/opt/ApeRAG
user=aperag
autostart=true
autorestart=true
stderr_logfile=/var/log/aperag/celery.err.log
stdout_logfile=/var/log/aperag/celery.out.log
```

启动：
```bash
sudo mkdir -p /var/log/aperag
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

---

## 🔧 Nginx 反向代理配置

```nginx
upstream aperag_api {
    server 127.0.0.1:8000;
}

upstream aperag_frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://aperag_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://aperag_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # MCP
    location /mcp/ {
        proxy_pass http://aperag_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

---

## ❓ 常见问题

### 1. 数据库连接失败
检查 PostgreSQL 是否运行：
```bash
sudo systemctl status postgresql
psql -h localhost -U aperag -d aperag
```

### 2. Celery 任务不执行
检查 Redis 连接：
```bash
redis-cli ping
# 应该返回 PONG
```

### 3. 向量搜索失败
确保 Qdrant 正在运行：
```bash
curl http://localhost:6333/collections
```

### 4. 图谱功能不可用
检查 NebulaGraph/Neo4j 状态：
```bash
# Neo4j
curl http://localhost:7474
# NebulaGraph
nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula
```

### 5. 前端无法连接后端
检查 CORS 配置，在 `.env` 中添加：
```bash
CORS_ALLOW_ORIGINS=http://localhost:3000,http://your-domain.com
```

---

## 📦 迁移清单

将项目迁移到新服务器时，需要复制以下内容：

| 内容 | 路径 | 说明 |
|------|------|------|
| 代码 | `/opt/ApeRAG/` | 整个项目目录 |
| 环境变量 | `.env` | 包含所有配置 |
| 对象存储 | `.objects/` | 上传的文件 |
| PostgreSQL | - | 导出 SQL dump |
| Qdrant | - | 备份 collections |
| Redis | - | 通常不需要迁移 |

**PostgreSQL 导出/导入:**
```bash
# 导出
pg_dump -h localhost -U aperag aperag > aperag_backup.sql

# 导入
psql -h localhost -U aperag aperag < aperag_backup.sql
```

---

## 🎉 完成

按照以上步骤，您应该已经成功在没有 Docker 的环境中部署了 ApeRAGv2。如有问题，请检查各服务的日志输出。
