
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from aperag.db.database import get_async_session
from aperag.db.models import Collection
from sqlalchemy import select

async def list_collections():
    async for session in get_async_session():
        stmt = select(Collection)
        result = await session.execute(stmt)
        collections = result.scalars().all()
        
        print(f"Total collections found: {len(collections)}")
        for c in collections:
            print(f"ID: {c.id}, Title: {c.title}, User: {c.user}, Type: {c.type}")
        
        if not collections:
            print("No collections found in the database.")
            
        break

if __name__ == "__main__":
    asyncio.run(list_collections())
