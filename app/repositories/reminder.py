from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reminder import Reminder
from app.models.task import Task
from app.repositories.base import BaseRepository

class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self) -> None:
        super().__init__(Reminder)

    async def get_multi_by_task(
        self, db: AsyncSession, *, task_id: int, skip: int = 0, limit: int = 100
    ) -> List[Reminder]:
        """Fetch all reminders for a specific task."""
        query = (
            select(Reminder)
            .filter(Reminder.task_id == task_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Reminder]:
        """Fetch all reminders for a specific user by joining with tasks."""
        query = (
            select(Reminder)
            .join(Task)
            .filter(Task.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_pending_due_reminders(self, db: AsyncSession) -> List[Reminder]:
        """Fetch reminders that are due to be sent but haven't been sent yet."""
        now = datetime.now(timezone.utc)
        query = select(Reminder).filter(
            and_(
                Reminder.is_sent == False,
                Reminder.reminder_time <= now
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# Global singleton repository instance
reminder_repository = ReminderRepository()
