from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide an asynchronous database session."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            # SessionLocal auto-closes on block exit, but we ensure proper release here
            pass
