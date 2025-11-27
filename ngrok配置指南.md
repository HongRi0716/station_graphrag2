# Ngrok 内网穿透登录问题解决指南

## 问题描述
通过 ngrok 内网穿透后,登录时出现 "Invalid credentials" 错误。

## 根本原因
1. **Cookie 安全策略不匹配**: ngrok 使用 HTTPS,但应用的 cookie 配置为非安全模式
2. **SameSite 策略限制**: 跨域请求时 cookie 被浏览器阻止
3. **CORS 配置未包含 ngrok 域名**

## 解决方案

### 步骤 1: 修改环境配置

编辑 `envs/docker.env.overrides` 文件,添加或修改以下配置:

```bash
# ============================================
# Ngrok 内网穿透配置
# ============================================

# Cookie 安全设置 - 适配 HTTPS
# 注意: ngrok 使用 HTTPS,因此需要启用 secure cookie
AUTH_COOKIE_SECURE=true

# SameSite 策略 - 允许跨站点请求携带 cookie
# 选项: strict | lax | none
# ngrok 场景下必须使用 'none' 以支持跨域认证
AUTH_COOKIE_SAMESITE=none

# CORS 配置 - 允许 ngrok 域名
# 格式: 多个域名用逗号分隔
# 示例: CORS_ALLOW_ORIGINS=https://abc123.ngrok.io,http://localhost:3000
CORS_ALLOW_ORIGINS=https://YOUR_NGROK_DOMAIN.ngrok.io,http://localhost:3000

# OAuth 重定向 URL (如果使用 OAuth 登录)
OAUTH_REDIRECT_URL=https://YOUR_NGROK_DOMAIN.ngrok.io/auth/callback
```

**重要**: 将 `YOUR_NGROK_DOMAIN` 替换为你的实际 ngrok 域名!

### 步骤 2: 获取 ngrok 域名

运行 ngrok 后,从输出中获取域名:

```bash
ngrok http 3000
```

输出示例:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:3000
```

使用 `https://abc123.ngrok.io` 作为你的 ngrok 域名。

### 步骤 3: 重启 Docker 容器

修改配置后,需要重启容器使配置生效:

```bash
# 停止容器
docker-compose down

# 重新启动
docker-compose up -d
```

### 步骤 4: 验证配置

1. 通过 ngrok URL 访问应用
2. 打开浏览器开发者工具 (F12)
3. 切换到 "Network" 标签
4. 尝试登录
5. 检查 `/api/v1/login` 请求的响应头,确认 `Set-Cookie` 包含:
   - `Secure` 属性
   - `SameSite=None` 属性

## 配置选项说明

### AUTH_COOKIE_SECURE
- `true`: Cookie 仅在 HTTPS 连接中传输 (ngrok 必须设置为 true)
- `false`: Cookie 可在 HTTP 和 HTTPS 中传输 (仅本地开发)

### AUTH_COOKIE_SAMESITE
- `strict`: 最严格,完全禁止跨站点请求携带 cookie
- `lax`: 部分允许跨站点请求 (默认值,但 ngrok 场景下不够)
- `none`: 允许所有跨站点请求携带 cookie (ngrok 必须使用,且必须配合 Secure=true)

### CORS_ALLOW_ORIGINS
- `*`: 允许所有域名 (不安全,仅测试使用)
- 具体域名列表: 推荐生产环境使用,逗号分隔

## 常见问题排查

### 问题 1: 仍然显示 "Invalid credentials"

**检查项**:
1. 确认 ngrok 域名配置正确
2. 确认 Docker 容器已重启
3. 清除浏览器 cookie 和缓存
4. 检查浏览器控制台是否有 CORS 错误

### 问题 2: Cookie 未被设置

**解决方法**:
1. 检查 `AUTH_COOKIE_SAMESITE=none` 时,`AUTH_COOKIE_SECURE` 必须为 `true`
2. 确认通过 HTTPS (ngrok URL) 访问,而非 HTTP

### 问题 3: CORS 错误

**错误信息**: 
```
Access to fetch at 'https://xxx.ngrok.io/api/v1/login' from origin 'https://yyy.ngrok.io' 
has been blocked by CORS policy
```

**解决方法**:
确保 `CORS_ALLOW_ORIGINS` 包含前端的 ngrok 域名。

## 本地开发 vs Ngrok 配置对比

| 配置项 | 本地开发 | Ngrok 穿透 |
|--------|---------|-----------|
| AUTH_COOKIE_SECURE | false | **true** |
| AUTH_COOKIE_SAMESITE | lax | **none** |
| CORS_ALLOW_ORIGINS | * 或 localhost | **ngrok 域名** |

## 安全建议

1. **生产环境**: 
   - 使用具体的域名列表,避免使用 `*`
   - 启用 `AUTH_COOKIE_SECURE=true`
   - 使用 `AUTH_COOKIE_SAMESITE=lax` 或 `strict`

2. **开发/测试环境**:
   - 可以使用 `CORS_ALLOW_ORIGINS=*`
   - ngrok 场景必须使用 `SameSite=none`

## 快速配置模板

### 仅用于 Ngrok 测试 (宽松配置)

```bash
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
CORS_ALLOW_ORIGINS=*
```

### 生产级 Ngrok 配置 (推荐)

```bash
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
CORS_ALLOW_ORIGINS=https://your-domain.ngrok.io
OAUTH_REDIRECT_URL=https://your-domain.ngrok.io/auth/callback
```

## 参考资料

- [MDN - SameSite cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
- [FastAPI CORS 配置](https://fastapi.tiangolo.com/tutorial/cors/)
- [Ngrok 文档](https://ngrok.com/docs)
