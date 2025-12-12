# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from aperag.config import settings
from aperag.docparser.base import BaseParser, FallbackError, Part, TextPart

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
]


class ImageParser(BaseParser):
    name = "image"

    def supported_extensions(self) -> list[str]:
        return SUPPORTED_EXTENSIONS

    @staticmethod
    def _image_to_base64(image_path: str) -> str:
        """
        Convert an image file to base64 encoded JPEG string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image in JPEG format
        """
        with Image.open(image_path) as image:
            # Convert RGBA/P mode to RGB for JPEG compatibility
            if image.mode in ("RGBA", "P"):
                # Create white background for transparent images
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=95)
            img_byte = buffered.getvalue()
            return base64.b64encode(img_byte).decode()

    def parse_file(self, path: Path, metadata: dict[str, Any] = {}, **kwargs) -> list[Part]:
        # Try SiliconFlow OCR first, fallback to PaddleOCR
        if settings.siliconflow_ocr_api_key:
            try:
                content = self.read_image_text_siliconflow(path)
                metadata = metadata.copy()
                metadata["md_source_map"] = [0, content.count("\n") + 1]
                metadata["ocr_method"] = "siliconflow"
                return [TextPart(content=content, metadata=metadata)]
            except Exception as e:
                logger.warning(
                    f"SiliconFlow OCR failed, trying PaddleOCR: {e}")

        # Fallback to PaddleOCR
        if settings.paddleocr_host:
            try:
                content = self.read_image_text_paddleocr(path)
                metadata = metadata.copy()
                metadata["md_source_map"] = [0, content.count("\n") + 1]
                metadata["ocr_method"] = "paddleocr"
                return [TextPart(content=content, metadata=metadata)]
            except Exception as e:
                logger.error(f"PaddleOCR failed: {e}")
                raise FallbackError(
                    f"Both SiliconFlow OCR and PaddleOCR failed: {e}")

        raise FallbackError(
            "Neither SILICONFLOW_OCR_API_KEY nor PADDLEOCR_HOST is set")

    def read_image_text_siliconflow(self, path: Path) -> str:
        """Extract text from image using SiliconFlow OCR API"""
        b64_image = self._image_to_base64(str(path))
        mime_type = "image/jpeg"
        data_uri = f"data:{mime_type};base64,{b64_image}"

        # Use OCR-specific prompt for text extraction
        ocr_prompt = """请提取图像中的所有可见文字，保持原始语言和格式。只返回提取的文字内容，不要添加任何解释或描述。"""

        payload = {
            "model": settings.siliconflow_ocr_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri,
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": ocr_prompt,
                        },
                    ],
                },
            ],
        }

        base_url = settings.siliconflow_ocr_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.siliconflow_ocr_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers,
                                 data=json.dumps(payload), timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get(
            "message", {}).get("content", "")

        if not content:
            raise ValueError("SiliconFlow OCR returned empty content")

        return content.strip()

    def read_image_text_paddleocr(self, path: Path) -> str:
        """Extract text from image using PaddleOCR (legacy method)"""
        b64_image = self._image_to_base64(str(path))

        data = {"images": [b64_image]}
        headers = {"Content-type": "application/json"}
        url = settings.paddleocr_host + "/predict/ocr_system"
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        r.raise_for_status()
        result = json.loads(r.text)

        # TODO: extract image metadata by using exiftool

        texts = [item["text"] for group in result["results"]
                 for item in group if "text" in item]
        return "".join(texts)
