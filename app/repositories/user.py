from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        query = select(User).filter(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

# Global singleton repository instance
user_repository = UserRepository()
