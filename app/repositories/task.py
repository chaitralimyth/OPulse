from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.enums import TaskStatusEnum, PriorityEnum
from app.repositories.base import BaseRepository

class TaskRepository(BaseRepository[Task]):
    def __init__(self) -> None:
        super().__init__(Task)

    async def get_multi_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: Optional[TaskStatusEnum] = None,
        priority: Optional[PriorityEnum] = None,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Fetch tasks belonging to a specific user with optional filters."""
        filters = [Task.user_id == user_id]
        
        if status:
            filters.append(Task.status == status)
        if priority:
            filters.append(Task.priority == priority)
        if category_id:
            filters.append(Task.category_id == category_id)

        query = (
            select(Task)
            .filter(and_(*filters))
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all_by_user(self, db: AsyncSession, *, user_id: int) -> List[Task]:
        """Fetch all tasks for a specific user. (Primarily used for AI recommendations & Analytics)"""
        query = select(Task).filter(Task.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_tasks_by_user(self, db: AsyncSession, *, user_id: int) -> List[Task]:
        """Fetch incomplete tasks that have passed their due date."""
        now = datetime.now(timezone.utc)
        query = select(Task).filter(
            Task.user_id == user_id,
            Task.status != TaskStatusEnum.COMPLETED,
            Task.due_date < now
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# Global singleton repository instance
task_repository = TaskRepository()
