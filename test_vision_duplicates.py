#!/usr/bin/env python3
"""快速测试 Vision LLM 响应中的重复内容"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aperag.llm.completion.completion_service import CompletionService
import base64
from pathlib import Path

# 读取优化后的 prompt
with open("vision_prompt_test.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

# 读取图片
image_path = Path("主接线.png")
with image_path.open("rb") as f:
    image_data = f.read()
    base64_data = base64.b64encode(image_data).decode("utf-8")
    data_uri = f"data:image/png;base64,{base64_data}"

# 创建服务
provider = os.getenv("VISION_LLM_PROVIDER", "siliconflow")
model = os.getenv("VISION_LLM_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
base_url = os.getenv("VISION_LLM_BASE_URL", "https://api.siliconflow.cn/v1")
api_key = os.getenv("VISION_LLM_API_KEY")

if not api_key:
    print("❌ 错误: 未设置 VISION_LLM_API_KEY")
    sys.exit(1)

# 获取 completion_dialect
try:
    from aperag.db.ops import db_ops
    llm_provider = db_ops.query_llm_provider_by_name(provider)
    if llm_provider and llm_provider.completion_dialect:
        provider = llm_provider.completion_dialect
except:
    pass

service = CompletionService(
    provider=provider,
    model=model,
    base_url=base_url,
    api_key=api_key,
    temperature=0.1,
    vision=True,
    caching=False,
)

print("开始调用 Vision LLM...")
print(f"Prompt 长度: {len(prompt)} 字符")
print(f"图片大小: {len(image_data)} 字节\n")

response = service.generate(history=[], prompt=prompt, images=[data_uri])

print(f"\n✅ 调用成功!")
print(f"响应长度: {len(response)} 字符\n")

# 检查重复内容
print("=" * 80)
print("重复内容分析")
print("=" * 80)

# 检查母线名称重复
import re
busbar_pattern = r'35kV\s+[A-Z]+\d*母'
busbars = re.findall(busbar_pattern, response)
unique_busbars = set(busbars)
print(f"\n母线名称:")
print(f"  总出现次数: {len(busbars)}")
print(f"  唯一数量: {len(unique_busbars)}")
if len(busbars) > len(unique_busbars):
    print(f"  ⚠️  发现重复: {len(busbars) - len(unique_busbars)} 次")
    # 找出重复的
    from collections import Counter
    duplicates = {k: v for k, v in Counter(busbars).items() if v > 1}
    if duplicates:
        print(f"  重复的母线名称:")
        for name, count in list(duplicates.items())[:10]:  # 只显示前10个
            print(f"    - {name}: {count} 次")
else:
    print(f"  ✅ 无重复")

# 检查行重复
print(f"\n响应内容预览 (前1000字符):")
print("-" * 80)
print(response[:1000])
print("-" * 80)

# 保存完整响应
with open("vision_response_optimized.txt", "w", encoding="utf-8") as f:
    f.write(response)
print(f"\n完整响应已保存到: vision_response_optimized.txt")


