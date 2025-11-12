# 🚀 ApeRAG 提供商切换速查卡

## ⚡ 10秒快速切换

### 方法 1：Web 界面（最简单） 👍

```
1. 访问: http://localhost:3000/web/workspace/providers
2. 找到提供商 → 点击"配置"
3. 输入 API 密钥 → 保存
✅ 立即生效，无需重启
```

---

## 📋 常用提供商配置

### 硅基流动 (SiliconFlow) 🆓

**获取密钥**: https://siliconflow.cn/

```bash
# Web 界面配置
提供商: SiliconFlow
API 密钥: sk-your-key

# 推荐模型
Embedding: BAAI/bge-m3 (免费)
Completion: Qwen/Qwen3-8B
Rerank: BAAI/bge-reranker-v2-m3
```

**API 切换**:
```bash
curl -X PUT "http://localhost:8000/api/v1/llm_providers/siliconflow" \
  -H "Authorization: Bearer $APERAG_KEY" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-your-key", "status": "enable"}'
```

---

### OpenRouter 🌐

**获取密钥**: https://openrouter.ai/

```bash
# Web 界面配置
提供商: OpenRouter
API 密钥: sk-or-v1-your-key

# 推荐模型
Completion: google/gemini-2.5-flash
```

---

### OpenAI 🤖

**获取密钥**: https://platform.openai.com/

```bash
# Web 界面配置
提供商: OpenAI
API 密钥: sk-proj-your-key

# 推荐模型
Embedding: text-embedding-3-small
Completion: gpt-4o-mini
```

---

## 🔄 一键切换脚本

### Python 脚本

保存为 `switch_provider.py`:
```python
#!/usr/bin/env python3
import requests
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "your-aperag-api-key"  # 从 Web 界面获取

def switch_to_provider(provider_name, api_key, models):
    """一键切换到指定提供商"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. 启用提供商
    print(f"🔄 正在启用 {provider_name}...")
    response = requests.put(
        f"{BASE_URL}/api/v1/llm_providers/{provider_name}",
        headers=headers,
        json={"api_key": api_key, "status": "enable"}
    )
    
    if response.status_code == 200:
        print(f"✅ {provider_name} 已启用")
    else:
        print(f"❌ 启用失败: {response.text}")
        return False
    
    # 2. 设置默认模型
    print("🔄 正在设置默认模型...")
    defaults = []
    
    if "embedding" in models:
        defaults.append({
            "scenario": "default_for_embedding",
            "provider_name": provider_name,
            "model": models["embedding"]["model"],
            "custom_llm_provider": models["embedding"].get("dialect", "openai")
        })
    
    if "completion" in models:
        defaults.append({
            "scenario": "default_for_collection_completion",
            "provider_name": provider_name,
            "model": models["completion"]["model"],
            "custom_llm_provider": models["completion"].get("dialect", "openai")
        })
    
    if "rerank" in models:
        defaults.append({
            "scenario": "default_for_rerank",
            "provider_name": provider_name,
            "model": models["rerank"]["model"],
            "custom_llm_provider": models["rerank"].get("dialect", "jina_ai")
        })
    
    response = requests.put(
        f"{BASE_URL}/api/v1/default_models",
        headers=headers,
        json={"defaults": defaults}
    )
    
    if response.status_code == 200:
        print(f"✅ 默认模型已设置")
        print(f"\n🎉 成功切换到 {provider_name}!")
        return True
    else:
        print(f"❌ 设置失败: {response.text}")
        return False

# 预设配置
PROVIDERS = {
    "siliconflow": {
        "models": {
            "embedding": {"model": "BAAI/bge-m3", "dialect": "openai"},
            "completion": {"model": "Qwen/Qwen3-8B", "dialect": "openai"},
            "rerank": {"model": "BAAI/bge-reranker-v2-m3", "dialect": "jina_ai"}
        }
    },
    "openrouter": {
        "models": {
            "completion": {"model": "google/gemini-2.5-flash", "dialect": "openrouter"}
        }
    },
    "openai": {
        "models": {
            "embedding": {"model": "text-embedding-3-small", "dialect": "openai"},
            "completion": {"model": "gpt-4o-mini", "dialect": "openai"}
        }
    }
}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python switch_provider.py <provider> <api_key>")
        print("\n支持的提供商:")
        for p in PROVIDERS.keys():
            print(f"  - {p}")
        sys.exit(1)
    
    provider = sys.argv[1]
    api_key = sys.argv[2]
    
    if provider not in PROVIDERS:
        print(f"❌ 不支持的提供商: {provider}")
        sys.exit(1)
    
    switch_to_provider(provider, api_key, PROVIDERS[provider]["models"])
```

**使用方法**:
```bash
# 切换到硅基流动
python switch_provider.py siliconflow sk-your-key

# 切换到 OpenRouter
python switch_provider.py openrouter sk-or-v1-your-key

# 切换到 OpenAI
python switch_provider.py openai sk-proj-your-key
```

---

### Bash 脚本

保存为 `switch_provider.sh`:
```bash
#!/bin/bash

# 配置
BASE_URL="http://localhost:8000"
APERAG_KEY="your-aperag-api-key"

# 函数：切换到硅基流动
switch_to_siliconflow() {
    local API_KEY=$1
    
    echo "🔄 切换到硅基流动..."
    
    # 启用提供商
    curl -s -X PUT "${BASE_URL}/api/v1/llm_providers/siliconflow" \
      -H "Authorization: Bearer ${APERAG_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"api_key\": \"${API_KEY}\", \"status\": \"enable\"}" > /dev/null
    
    # 设置默认模型
    curl -s -X PUT "${BASE_URL}/api/v1/default_models" \
      -H "Authorization: Bearer ${APERAG_KEY}" \
      -H "Content-Type: application/json" \
      -d '{
        "defaults": [
          {
            "scenario": "default_for_embedding",
            "provider_name": "siliconflow",
            "model": "BAAI/bge-m3",
            "custom_llm_provider": "openai"
          },
          {
            "scenario": "default_for_collection_completion",
            "provider_name": "siliconflow",
            "model": "Qwen/Qwen3-8B",
            "custom_llm_provider": "openai"
          },
          {
            "scenario": "default_for_rerank",
            "provider_name": "siliconflow",
            "model": "BAAI/bge-reranker-v2-m3",
            "custom_llm_provider": "jina_ai"
          }
        ]
      }' > /dev/null
    
    echo "✅ 已切换到硅基流动"
}

# 函数：切换到 OpenRouter
switch_to_openrouter() {
    local API_KEY=$1
    
    echo "🔄 切换到 OpenRouter..."
    
    curl -s -X PUT "${BASE_URL}/api/v1/llm_providers/openrouter" \
      -H "Authorization: Bearer ${APERAG_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"api_key\": \"${API_KEY}\", \"status\": \"enable\"}" > /dev/null
    
    curl -s -X PUT "${BASE_URL}/api/v1/default_models" \
      -H "Authorization: Bearer ${APERAG_KEY}" \
      -H "Content-Type: application/json" \
      -d '{
        "defaults": [
          {
            "scenario": "default_for_collection_completion",
            "provider_name": "openrouter",
            "model": "google/gemini-2.5-flash",
            "custom_llm_provider": "openrouter"
          }
        ]
      }' > /dev/null
    
    echo "✅ 已切换到 OpenRouter"
}

# 主程序
case "$1" in
    siliconflow)
        switch_to_siliconflow "$2"
        ;;
    openrouter)
        switch_to_openrouter "$2"
        ;;
    *)
        echo "用法: $0 {siliconflow|openrouter} <api_key>"
        exit 1
        ;;
esac
```

**使用方法**:
```bash
chmod +x switch_provider.sh

# 切换到硅基流动
./switch_provider.sh siliconflow sk-your-key

# 切换到 OpenRouter
./switch_provider.sh openrouter sk-or-v1-your-key
```

---

## 🔍 验证切换

### 方法 1：Web 界面
```
访问: http://localhost:3000/web/workspace/providers
查看提供商状态（已启用/未启用）
```

### 方法 2：API 查询
```bash
curl -X GET "http://localhost:8000/api/v1/llm_configuration" \
  -H "Authorization: Bearer $APERAG_KEY"
```

### 方法 3：日志查看
```bash
docker-compose logs -f aperag-backend | grep "provider"
```

---

## 📊 提供商对比

| 提供商 | 免费模型 | 速度 | 成本 | 推荐场景 |
|--------|----------|------|------|----------|
| **SiliconFlow** | ✅ 有 | ⚡⚡⚡ 快 | 💰 低 | 开发测试、预算有限 |
| **OpenRouter** | ❌ 无 | ⚡⚡ 中 | 💰💰 中 | 灵活选择模型 |
| **OpenAI** | ❌ 无 | ⚡⚡⚡ 快 | 💰💰💰 高 | 追求最佳质量 |
| **Anthropic** | ❌ 无 | ⚡⚡ 中 | 💰💰💰 高 | Claude 系列粉丝 |
| **AlibabaCloud** | ❌ 无 | ⚡⚡⚡ 快 | 💰💰 中 | 国内用户 |

---

## 💡 最佳实践

### 成本优化方案
```
Embedding: SiliconFlow (BAAI/bge-m3) - 免费
Completion: OpenRouter (按需) - 灵活
Rerank: SiliconFlow (BAAI/bge-reranker-v2-m3) - 免费
```

### 性能优先方案
```
Embedding: OpenAI (text-embedding-3-large)
Completion: OpenAI (gpt-4o)
Rerank: SiliconFlow (BAAI/bge-reranker-v2-m3)
```

### 平衡方案
```
Embedding: SiliconFlow (BAAI/bge-m3) - 免费且效果好
Completion: OpenRouter (google/gemini-2.5-flash) - 性价比高
Rerank: SiliconFlow (BAAI/bge-reranker-v2-m3) - 免费
```

---

## ⚠️ 注意事项

1. **API 密钥安全**: 不要在公开代码中硬编码密钥
2. **切换时机**: 建议在非高峰期切换
3. **测试验证**: 切换后创建测试对话验证功能
4. **回滚准备**: 保留旧提供商配置以便快速回滚
5. **监控使用**: 定期检查 API 调用量和成本

---

## 📚 相关文档

- **详细指南**: [PROVIDER_SWITCHING_GUIDE.md](PROVIDER_SWITCHING_GUIDE.md)
- **迁移文档**: [SILICONFLOW_MIGRATION.md](SILICONFLOW_MIGRATION.md)
- **API 文档**: http://localhost:8000/docs

---

## 🆘 常见问题

**Q: 切换后旧对话还能访问吗？**  
A: 可以，对话历史与提供商无关。

**Q: 可以同时用多个提供商吗？**  
A: 可以，不同 Collection 可配置不同提供商。

**Q: 切换需要重启吗？**  
A: 不需要，立即生效。

**Q: 如何快速回滚？**  
A: Web 界面 → 禁用新提供商 → 启用旧提供商（1分钟内完成）

---

**更新**: 2025-11-12  
**版本**: ApeRAG v0.1.0


