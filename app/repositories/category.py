from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.repositories.base import BaseRepository

class CategoryRepository(BaseRepository[Category]):
    def __init__(self) -> None:
        super().__init__(Category)

    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """Fetch categories belonging to a specific user."""
        query = (
            select(Category)
            .filter(Category.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_name_and_user(
        self, db: AsyncSession, *, name: str, user_id: int
    ) -> Optional[Category]:
        """Fetch a category by name for a specific user to verify duplicates."""
        query = select(Category).filter(
            Category.name == name,
            Category.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

# Global singleton repository instance
category_repository = CategoryRepository()
