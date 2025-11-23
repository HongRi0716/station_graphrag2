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

"""
OpenAI-compatible API endpoints for compatibility with OpenAI SDK.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openai", tags=["openai-compatible"])


@router.get("/models")
async def list_models():
    """
    List available models (OpenAI-compatible endpoint).
    """
    # TODO: Implement OpenAI-compatible model listing
    return {"data": [], "object": "list"}


@router.post("/chat/completions")
async def create_chat_completion():
    """
    Create chat completion (OpenAI-compatible endpoint).
    """
    # TODO: Implement OpenAI-compatible chat completion
    return {"error": "Not implemented yet"}
