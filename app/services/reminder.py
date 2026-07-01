import logging
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.reminder import Reminder
from app.models.enums import ActivityTypeEnum
from app.repositories.reminder import reminder_repository
from app.repositories.task import task_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.reminder import ReminderCreate, ReminderUpdate

logger = logging.getLogger("app.services.reminder")

class ReminderService:
    async def get_by_id(self, db: AsyncSession, *, reminder_id: int, user_id: int) -> Reminder:
        """Fetch a reminder and verify that the user owns the corresponding task."""
        query = (
            select(Reminder)
            .filter(Reminder.id == reminder_id)
            .options(selectinload(Reminder.task))
        )
        result = await db.execute(query)
        reminder = result.scalars().first()
        
        if not reminder or reminder.task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        return reminder

    async def get_multi(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Reminder]:
        """Fetch all reminders for a user's tasks."""
        return await reminder_repository.get_multi_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, *, reminder_in: ReminderCreate, user_id: int) -> Reminder:
        """Create a new reminder for a task after verifying task ownership and scheduling parameters."""
        task = await task_repository.get(db, id=reminder_in.task_id)
        if not task or task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found or unauthorized access"
            )

        if reminder_in.reminder_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reminder time must be set in the future."
            )

        reminder_data = reminder_in.model_dump()
        db_reminder = await reminder_repository.create(db, obj_in=reminder_data)
        await db.commit()

        logger.info("Created reminder ID %s for Task %s (User %s)", db_reminder.id, task.id, user_id)
        return db_reminder

    async def update(
        self, db: AsyncSession, *, reminder_id: int, reminder_in: ReminderUpdate, user_id: int
    ) -> Reminder:
        """Update a reminder's details."""
        reminder = await self.get_by_id(db, reminder_id=reminder_id, user_id=user_id)
        
        if reminder_in.reminder_time and reminder_in.reminder_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reminder time must be in the future."
            )

        updated_rem = await reminder_repository.update(db, db_obj=reminder, obj_in=reminder_in)
        await db.commit()
        return updated_rem

    async def remove(self, db: AsyncSession, *, reminder_id: int, user_id: int) -> Reminder:
        """Remove a reminder."""
        reminder = await self.get_by_id(db, reminder_id=reminder_id, user_id=user_id)
        deleted_rem = await reminder_repository.remove(db, id=reminder_id)
        await db.commit()
        return deleted_rem

    async def record_interaction(self, db: AsyncSession, *, reminder_id: int, user_id: int) -> Reminder:
        """Track user interaction with a reminder (snooze, click, dismiss)."""
        reminder = await self.get_by_id(db, reminder_id=reminder_id, user_id=user_id)
        
        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.REMINDER_INTERACTION,
            entity_id=reminder_id,
            details={"task_id": reminder.task_id, "action": "acknowledged"}
        )
        await db.commit()
        
        logger.info("Recorded reminder interaction for user %s on reminder %s", user_id, reminder_id)
        return reminder

# Global singleton repository instance
reminder_service = ReminderService()
