from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReminderBase(BaseModel):
    task_id: int
    reminder_time: datetime

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    reminder_time: Optional[datetime] = None
    is_sent: Optional[bool] = None

class ReminderResponse(ReminderBase):
    id: int
    is_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
