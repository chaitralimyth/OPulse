import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.reminder_job import check_due_reminders

logger = logging.getLogger("app.jobs.scheduler")

# Instantiate async scheduler
scheduler = AsyncIOScheduler()

def start_scheduler() -> None:
    """Initialize jobs and start the background scheduler."""
    logger.info("Starting background scheduler...")
    
    # Schedule the reminder scanner to run every minute
    scheduler.add_job(
        check_due_reminders,
        trigger="interval",
        minutes=1,
        id="due_reminder_scanner",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started successfully.")

def shutdown_scheduler() -> None:
    """Shut down the background scheduler cleanly on app close."""
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()
    logger.info("Background scheduler stopped successfully.")
