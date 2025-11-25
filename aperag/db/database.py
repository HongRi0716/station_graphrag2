"""Database utilities for the ApeRAG project.

This module provides a thin wrapper around the session factories defined in
`aperag.config`. The original code expected a module named
`aperag.db.database` exposing a `get_async_session` function, but the file was
missing, causing `ModuleNotFoundError` during import of the FastAPI routes.

We re-export the async session generator from `aperag.config` so that existing
imports continue to work without modification.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

# Import the actual implementation from the central configuration module.
from aperag.config import get_async_session as _config_get_async_session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` for database operations.

    This function simply forwards to the implementation defined in
    ``aperag.config``. Keeping the wrapper here preserves the original import
    path used throughout the codebase (``aperag.db.database``).
    """
    async for session in _config_get_async_session():
        yield session


__all__ = ["get_async_session"]
