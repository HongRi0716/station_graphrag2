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
Admin API endpoints for preset collections management
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from aperag.db.models import User
from aperag.service.collection_service import collection_service
from aperag.views.auth import required_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/preset-collections", tags=["admin", "preset-collections"])


class PresetCollectionsConfigResponse(BaseModel):
    """Response model for preset collections configuration"""
    enabled: bool
    auto_create_for_new_users: bool
    collections: List[Dict]
    categories: Dict


class PresetCollectionsConfigUpdate(BaseModel):
    """Request model for updating preset collections configuration"""
    enabled: bool
    auto_create_for_new_users: bool
    collections: List[Dict]
    categories: Dict


class CreatePresetCollectionsRequest(BaseModel):
    """Request model for creating preset collections for a user"""
    locale: str = "zh"


@router.get("/config", response_model=PresetCollectionsConfigResponse)
async def get_preset_collections_config(
    user: User = Depends(required_user),
):
    """
    Get preset collections configuration
    
    Requires admin privileges
    """
    # TODO: Add admin role check
    # if not is_admin(current_user):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config = await collection_service.get_preset_collections_config()
        return PresetCollectionsConfigResponse(**config)
    except Exception as e:
        logger.error(f"Failed to get preset collections config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get configuration")


@router.put("/config")
async def update_preset_collections_config(
    config: PresetCollectionsConfigUpdate,
    user: User = Depends(required_user),
):
    """
    Update preset collections configuration
    
    Requires admin privileges
    """
    # TODO: Add admin role check
    # if not is_admin(user):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        success = await collection_service.update_preset_collections_config(config.model_dump())
        if success:
            return {"message": "Configuration updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    except Exception as e:
        logger.error(f"Failed to update preset collections config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-for-user")
async def create_preset_collections_for_user(
    request: CreatePresetCollectionsRequest,
    user: User = Depends(required_user),
):
    """
    Create all enabled preset collections for the current user
    """
    try:
        created_collections = await collection_service.create_preset_collections_for_user(
            user=str(user.id),
            locale=request.locale
        )
        return {
            "message": f"Created {len(created_collections)} preset collections",
            "collections": [
                {"id": c.id, "title": c.title} for c in created_collections
            ]
        }
    except Exception as e:
        logger.error(f"Failed to create preset collections for user {user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
