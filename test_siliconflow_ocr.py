import base64
import json
import os
import sys
from pathlib import Path

import requests

API_KEY = os.getenv(
    "SILICONFLOW_OCR_API_KEY") or "sk-efhlwqukxzpwrvddduayuuzqoziksmgutiumqmwlvguuvowo"
MODEL = os.getenv("SILICONFLOW_OCR_MODEL") or "Pro/Qwen/Qwen2.5-VL-7B-Instruct"
BASE_URL = os.getenv(
    "SILICONFLOW_OCR_BASE_URL") or "https://api.siliconflow.cn/v1"
IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else "test.png"

if not API_KEY or API_KEY.startswith("sk-your-key"):
    raise SystemExit("请先配置有效的 SiliconFlow API Key")

img_path = Path(IMAGE_PATH)
if not img_path.exists():
    raise SystemExit(f"找不到图片文件: {img_path}")

with img_path.open("rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are an OCR assistant. Transcribe text and describe the image."},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": "请描述图像并提取所有可见文字。",
                },
            ],
        },
    ],
}

resp = requests.post(
    BASE_URL.rstrip("/") + "/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}",
             "Content-Type": "application/json"},
    data=json.dumps(payload),
    timeout=60,
)

print("Status:", resp.status_code)
print("Response:")
print(resp.text)
