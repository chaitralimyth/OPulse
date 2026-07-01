import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.reminder import Reminder
from app.repositories.reminder import reminder_repository

logger = logging.getLogger("app.jobs.reminder_job")

async def check_due_reminders() -> None:
    """Scheduled task to check for due reminders and dispatch them."""
    logger.debug("Background scan: Checking for due task reminders...")
    
    async with SessionLocal() as db:
        try:
            # Fetch pending due reminders, loading corresponding tasks eager
            due_reminders = await reminder_repository.get_pending_due_reminders(db)
            
            if not due_reminders:
                return

            logger.info("Found %s due reminders to dispatch.", len(due_reminders))
            
            for reminder in due_reminders:
                # Eagerly load the task title to print a pretty console message
                query = select(Reminder).filter(Reminder.id == reminder.id).options(selectinload(Reminder.task))
                res = await db.execute(query)
                full_reminder = res.scalars().first()
                
                if full_reminder and full_reminder.task:
                    # Simulated notification dispatch (e.g. push notification, email)
                    logger.info(
                        "*** ALERT DISPATCHED *** Reminder ID %s: Task '%s' is due! (Scheduled: %s)",
                        full_reminder.id,
                        full_reminder.task.title,
                        full_reminder.reminder_time
                    )
                
                # Mark reminder sent
                reminder.is_sent = True
                db.add(reminder)
                
            await db.commit()
            
        except Exception as e:
            logger.exception("Error executing check_due_reminders background job:")
            await db.rollback()
