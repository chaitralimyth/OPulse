from enum import Enum

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class RecurrenceEnum(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ActivityTypeEnum(str, Enum):
    TASK_CREATE = "task_create"
    TASK_COMPLETE = "task_complete"
    TASK_EDIT = "task_edit"
    REMINDER_INTERACTION = "reminder_interaction"
