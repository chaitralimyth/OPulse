from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import PriorityEnum, TaskStatusEnum, RecurrenceEnum
from app.schemas.category import CategoryResponse

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatusEnum = TaskStatusEnum.TODO
    priority: PriorityEnum = PriorityEnum.MEDIUM
    recurrence: RecurrenceEnum = RecurrenceEnum.NONE
    estimated_duration: int = Field(default=30, ge=5, le=1440)  # minutes, 5min to 24h
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    category_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    recurrence: Optional[RecurrenceEnum] = None
    estimated_duration: Optional[int] = Field(default=None, ge=5, le=1440)
    due_date: Optional[datetime] = None
    category_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    completed_at: Optional[datetime] = None
    user_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
