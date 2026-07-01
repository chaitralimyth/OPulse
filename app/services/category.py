import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import ActivityTypeEnum
from app.repositories.category import category_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.category import CategoryCreate, CategoryUpdate

logger = logging.getLogger("app.services.category")

class CategoryService:
    async def get_by_id(self, db: AsyncSession, *, category_id: int, user_id: int) -> Category:
        """Fetch a category and verify ownership."""
        category = await category_repository.get(db, id=category_id)
        if not category or category.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return category

    async def get_multi(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """Fetch multiple categories belonging to a user."""
        return await category_repository.get_multi_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, category_in: CategoryCreate, user_id: int) -> Category:
        """Create a new category, ensuring unique names per user."""
        existing = await category_repository.get_by_name_and_user(db, name=category_in.name, user_id=user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category_in.name}' already exists."
            )
        
        category_data = category_in.model_dump()
        category_data["user_id"] = user_id
        
        db_category = await category_repository.create(db, obj_in=category_data)
        await db.commit()
        
        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.TASK_EDIT,
            details={"message": f"Created category '{db_category.name}'", "category_id": db_category.id}
        )
        await db.commit()
        
        logger.info("User %s created category: %s", user_id, db_category.name)
        return db_category

    async def update(
        self, db: AsyncSession, *, category_id: int, category_in: CategoryUpdate, user_id: int
    ) -> Category:
        """Update category details."""
        category = await self.get_by_id(db, category_id=category_id, user_id=user_id)
        
        if category_in.name and category_in.name != category.name:
            existing = await category_repository.get_by_name_and_user(db, name=category_in.name, user_id=user_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with name '{category_in.name}' already exists."
                )

        updated_cat = await category_repository.update(db, db_obj=category, obj_in=category_in)
        await db.commit()
        
        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.TASK_EDIT,
            details={"message": f"Updated category ID {category_id}", "category_id": category_id}
        )
        await db.commit()
        
        return updated_cat

    async def remove(self, db: AsyncSession, *, category_id: int, user_id: int) -> Category:
        """Delete a category."""
        category = await self.get_by_id(db, category_id=category_id, user_id=user_id)
        deleted_category = await category_repository.remove(db, id=category_id)
        await db.commit()
        
        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.TASK_EDIT,
            details={"message": f"Deleted category '{category.name}'", "category_id": category_id}
        )
        await db.commit()
        
        return deleted_category

category_service = CategoryService()
