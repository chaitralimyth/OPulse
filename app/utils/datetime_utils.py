from datetime import datetime, timedelta, timezone
from app.models.enums import RecurrenceEnum

def calculate_next_recurrence(base_date: datetime, recurrence: RecurrenceEnum) -> datetime:
    """Calculate the next occurrence date based on RecurrenceEnum."""
    if not base_date:
        base_date = datetime.now(timezone.utc)
        
    if recurrence == RecurrenceEnum.DAILY:
        return base_date + timedelta(days=1)
    elif recurrence == RecurrenceEnum.WEEKLY:
        return base_date + timedelta(days=7)
    elif recurrence == RecurrenceEnum.MONTHLY:
        # Standardize monthly recurrence as 30 days out for robust cross-month interval handling
        return base_date + timedelta(days=30)
    return base_date
