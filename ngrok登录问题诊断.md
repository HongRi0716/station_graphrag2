# Ngrok 登录问题深度诊断指南

## 问题现象
通过 ngrok 内网穿透访问时,登录提示 "Invalid credentials",但本地访问正常。

## 可能的原因分析

### 1. 请求路径问题 ⭐ (最可能)
**症状**: 前端通过 ngrok 访问,但 API 请求可能仍然指向 localhost

**检查方法**:
1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签
3. 尝试登录
4. 查看 `/api/v1/login` 请求的 URL

**问题示例**:
```
❌ 错误: Request URL: http://localhost:8000/api/v1/login
✅ 正确: Request URL: https://your-domain.ngrok.io/api/v1/login
```

**解决方案**:
前端需要配置正确的 API 端点。检查前端环境变量配置。

### 2. Cookie Domain 不匹配
**症状**: Cookie 被设置但浏览器不发送

**原因**: Cookie 的 domain 属性与 ngrok 域名不匹配

**当前代码** (`auth.py` 538-545行):
```python
response.set_cookie(
    key="session",
    value=token,
    max_age=COOKIE_MAX_AGE,
    httponly=True,
    samesite=settings.auth_cookie_samesite,
    secure=settings.auth_cookie_secure,
    # 注意:没有设置 domain 参数
)
```

**解决方案**: 添加 domain 配置或使用动态 domain

### 3. 前后端分离部署问题
**症状**: 前端和后端通过不同的 ngrok 隧道访问

**场景**:
- 前端: `https://frontend-abc.ngrok.io`
- 后端: `https://backend-xyz.ngrok.io`

这种情况下,跨域 cookie 会被浏览器阻止。

**解决方案**: 
- 使用同一个 ngrok 隧道
- 或配置反向代理,让前后端在同一域名下

### 4. 数据库查询失败
**症状**: 用户名正确但查询不到用户

**可能原因**:
- 数据库连接问题
- 字符编码问题
- 用户名大小写敏感性

**诊断方法**: 查看后端日志

## 诊断步骤

### 步骤 1: 检查请求是否到达后端

在 `auth.py` 的 `login_view` 函数开头添加日志:

```python
@router.post("/login", tags=["auth"])
async def login_view(
    request: Request,
    response: Response,
    data: view_models.Login,
    session: AsyncSessionDep,
    user_manager: UserManager = Depends(get_user_manager),
) -> view_models.User:
    from sqlalchemy import select
    
    # 添加诊断日志
    logger.info(f"Login attempt - Username: {data.username}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request host: {request.url.hostname}")
    
    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalars().first()
    
    # 添加诊断日志
    if not user:
        logger.warning(f"User not found: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    logger.info(f"User found: {user.username} (ID: {user.id})")
    # ... 其余代码
```

### 步骤 2: 检查前端 API 配置

查看前端的 API 配置文件,通常在:
- `web/.env.local`
- `web/deploy/env.local.template`
- `web/src/lib/api-client.ts` 或类似文件

确保 `API_BASE_URL` 或类似配置指向 ngrok URL:

```bash
# 错误配置
NEXT_PUBLIC_API_URL=http://localhost:8000

# 正确配置 (使用你的 ngrok 域名)
NEXT_PUBLIC_API_URL=https://your-domain.ngrok.io
```

### 步骤 3: 检查浏览器 Cookie

1. 打开开发者工具 (F12)
2. 切换到 Application/Storage 标签
3. 查看 Cookies
4. 检查是否有 `session` cookie
5. 查看 cookie 的属性:
   - Domain
   - Secure
   - SameSite
   - HttpOnly

### 步骤 4: 检查 CORS 预检请求

1. 在 Network 标签中查找 OPTIONS 请求
2. 检查响应头是否包含:
   ```
   Access-Control-Allow-Origin: https://your-ngrok-domain.ngrok.io
   Access-Control-Allow-Credentials: true
   ```

## 快速解决方案

### 方案 A: 单一 ngrok 隧道 (推荐)

如果前后端都在本地运行,使用一个 ngrok 隧道指向前端,前端再代理 API 请求到后端。

**前端 Next.js 配置** (`web/next.config.js`):
```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}
```

然后只需要一个 ngrok 隧道:
```bash
ngrok http 3000
```

### 方案 B: 双 ngrok 隧道 + 环境变量

如果需要分别暴露前后端:

1. **后端 ngrok**:
```bash
ngrok http 8000
# 假设得到: https://backend-abc.ngrok.io
```

2. **前端环境变量** (`web/.env.local`):
```bash
NEXT_PUBLIC_API_URL=https://backend-abc.ngrok.io
```

3. **后端 CORS 配置** (`.env`):
```bash
CORS_ALLOW_ORIGINS=https://frontend-xyz.ngrok.io
AUTH_COOKIE_SAMESITE=none
AUTH_COOKIE_SECURE=true
```

4. **重启服务**:
```bash
docker-compose restart api
cd web && npm run dev
```

### 方案 C: 添加 Cookie Domain 配置

修改 `aperag/config.py`,添加 cookie domain 配置:

```python
class Config(BaseSettings):
    # ... 现有配置 ...
    
    # Cookie domain (留空则自动使用请求域名)
    auth_cookie_domain: Optional[str] = Field(None, alias="AUTH_COOKIE_DOMAIN")
```

修改 `aperag/views/auth.py` 的 `login_view`:

```python
# Set cookie using configured security attributes
cookie_params = {
    "key": "session",
    "value": token,
    "max_age": COOKIE_MAX_AGE,
    "httponly": True,
    "samesite": settings.auth_cookie_samesite,
    "secure": settings.auth_cookie_secure,
}

# 添加 domain 配置
if settings.auth_cookie_domain:
    cookie_params["domain"] = settings.auth_cookie_domain

response.set_cookie(**cookie_params)
```

然后在 `.env` 中配置:
```bash
# 留空则自动使用当前域名
AUTH_COOKIE_DOMAIN=

# 或指定具体域名 (包括子域名)
# AUTH_COOKIE_DOMAIN=.ngrok.io
```

## 验证清单

- [ ] 前端 API URL 配置正确指向 ngrok 后端
- [ ] CORS 配置包含 ngrok 前端域名
- [ ] Cookie 配置: `SECURE=true`, `SAMESITE=none`
- [ ] 浏览器能看到 `session` cookie
- [ ] Network 标签中 `/api/v1/login` 请求成功返回 200
- [ ] 后端日志显示收到登录请求
- [ ] 数据库中存在测试用户

## 常见错误信息对照

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| Invalid credentials | 用户不存在或密码错误 | 检查数据库,确认用户存在 |
| CORS error | 跨域配置问题 | 更新 CORS_ALLOW_ORIGINS |
| 401 Unauthorized | Cookie 未发送 | 检查 cookie 配置和浏览器 |
| Network error | API URL 错误 | 检查前端 API 配置 |
| 500 Internal Server Error | 后端异常 | 查看后端日志 |

## 调试命令

### 查看 Docker 日志
```bash
# 查看 API 日志
docker logs aperag-api -f --tail=100

# 查看所有服务日志
docker-compose logs -f
```

### 测试 API 连通性
```bash
# 从本地测试
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  -v

# 从 ngrok 测试
curl -X POST https://your-domain.ngrok.io/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  -v
```

### 检查数据库用户
```bash
# 进入 Postgres 容器
docker exec -it aperag-postgres psql -U postgres -d aperag

# 查询用户
SELECT id, username, email, is_active FROM users;
```

## 下一步行动

1. **立即检查**: 打开浏览器开发者工具,查看 `/api/v1/login` 请求的完整 URL
2. **确认前端配置**: 检查前端的 API 端点配置
3. **查看日志**: 运行 `docker logs aperag-api -f` 查看登录尝试日志
4. **测试 curl**: 使用上面的 curl 命令直接测试 API

根据检查结果,选择对应的解决方案。
