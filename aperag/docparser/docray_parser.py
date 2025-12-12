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
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from aperag.config import settings
from aperag.docparser.base import (
    BaseParser,
    FallbackError,
    Part,
    PdfPart,
)
from aperag.docparser.mineru_common import middle_json_to_parts, to_md_part

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
]


class DocRayParser(BaseParser):
    name = "docray"
    
    # Configuration constants
    INITIAL_POLL_INTERVAL = 2      # Initial polling interval in seconds
    MAX_POLL_INTERVAL = 30         # Maximum polling interval in seconds
    POLL_BACKOFF_FACTOR = 1.5      # Exponential backoff factor
    MAX_PROCESSING_TIME = 1800     # Maximum total processing time (30 minutes)
    HTTP_TIMEOUT = 60              # HTTP request timeout in seconds
    SUBMIT_TIMEOUT = 120           # File submission timeout (larger files need more time)

    def supported_extensions(self) -> list[str]:
        return SUPPORTED_EXTENSIONS

    def parse_file(self, path: Path, metadata: dict[str, Any], **kwargs) -> list[Part]:
        if not settings.docray_host:
            raise FallbackError("DOCRAY_HOST is not set")

        job_id = None
        temp_dir_obj = None
        try:
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir_path = Path(temp_dir_obj.name)

            # Submit file to doc-ray
            with open(path, "rb") as f:
                files = {"file": (path.name, f)}
                response = requests.post(
                    f"{settings.docray_host}/submit",
                    files=files,
                    timeout=self.SUBMIT_TIMEOUT
                )
                response.raise_for_status()
                submit_response = response.json()
                job_id = submit_response["job_id"]
                logger.info(f"Submitted file {path.name} to DocRay, job_id: {job_id}")

            # Polling the processing status with exponential backoff
            start_time = time.time()
            poll_interval = self.INITIAL_POLL_INTERVAL
            poll_count = 0
            
            while True:
                elapsed_time = time.time() - start_time
                
                # Check for timeout
                if elapsed_time > self.MAX_PROCESSING_TIME:
                    raise TimeoutError(
                        f"DocRay job {job_id} exceeded maximum processing time "
                        f"({self.MAX_PROCESSING_TIME}s). File: {path.name}"
                    )
                
                time.sleep(poll_interval)
                poll_count += 1
                
                try:
                    status_response: dict = requests.get(
                        f"{settings.docray_host}/status/{job_id}",
                        timeout=self.HTTP_TIMEOUT
                    ).json()
                except requests.exceptions.Timeout:
                    logger.warning(f"DocRay status check timed out for job {job_id}, retrying...")
                    continue
                
                status = status_response["status"]
                logger.info(
                    f"DocRay job {job_id} status: {status} "
                    f"(poll #{poll_count}, elapsed: {elapsed_time:.1f}s)"
                )

                if status == "completed":
                    break
                elif status == "failed":
                    error_message = status_response.get("error", "Unknown error")
                    raise RuntimeError(f"DocRay parsing failed for job {job_id}: {error_message}")
                elif status not in ["processing", "pending", "queued"]:
                    raise RuntimeError(f"Unexpected DocRay job status for {job_id}: {status}")
                
                # Exponential backoff: increase poll interval up to max
                poll_interval = min(poll_interval * self.POLL_BACKOFF_FACTOR, self.MAX_POLL_INTERVAL)

            # Get the result
            result_response = requests.get(
                f"{settings.docray_host}/result/{job_id}",
                timeout=self.HTTP_TIMEOUT
            ).json()
            result = result_response["result"]
            middle_json = result["middle_json"]
            images_data = result.get("images", {})

            # Dump image files into temp dir
            for img_name, img_base64 in images_data.items():
                img_file_path = temp_dir_path / str(img_name)

                # Ensure the resolved path is within the temporary directory.
                resolved_img_file_path = img_file_path.resolve()
                resolved_temp_dir_path = temp_dir_path.resolve()
                if not resolved_img_file_path.is_relative_to(resolved_temp_dir_path):
                    logger.error(
                        f"Security: Prevented writing image to an unintended path. "
                        f"File name: '{img_name}' "
                        f"Attempted path: '{resolved_img_file_path}', "
                        f"Temp dir: '{resolved_temp_dir_path}'"
                    )
                    continue

                img_file_path.parent.mkdir(parents=True, exist_ok=True)
                img_data = base64.b64decode(img_base64)
                with open(img_file_path, "wb") as f_img:
                    f_img.write(img_data)

            if metadata is None:
                metadata = {}
            parts = middle_json_to_parts(temp_dir_path / "images", middle_json, metadata)
            if not parts:
                return []

            pdf_data = result.get("pdf_data", None)
            if pdf_data:
                pdf_part = PdfPart(data=base64.b64decode(pdf_data), metadata=metadata.copy())
                parts.append(pdf_part)

            md_part = to_md_part(parts, metadata.copy())
            
            logger.info(
                f"DocRay job {job_id} completed successfully. "
                f"Parsed {len(parts)} parts in {time.time() - start_time:.1f}s"
            )
            return [md_part] + parts

        except requests.exceptions.RequestException:
            logger.exception("DocRay API request failed")
            raise
        except TimeoutError:
            logger.exception("DocRay processing timed out")
            raise
        except Exception:
            logger.exception("DocRay parsing failed")
            raise
        finally:
            # Delete the job in doc-ray to release resources
            if job_id:
                try:
                    requests.delete(
                        f"{settings.docray_host}/result/{job_id}",
                        timeout=self.HTTP_TIMEOUT
                    )
                    logger.info(f"Deleted DocRay job {job_id}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to delete DocRay job {job_id}: {e}")
            if temp_dir_obj:
                temp_dir_obj.cleanup()

