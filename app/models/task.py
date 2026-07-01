from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.enums import PriorityEnum, TaskStatusEnum, RecurrenceEnum

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    
    # Custom Enums mapped to PG Enums
    status: Mapped[TaskStatusEnum] = mapped_column(
        SQLEnum(TaskStatusEnum, name="task_status_enum", inherit_schema=True),
        default=TaskStatusEnum.TODO,
        nullable=False
    )
    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum, name="priority_enum", inherit_schema=True),
        default=PriorityEnum.MEDIUM,
        nullable=False
    )
    recurrence: Mapped[RecurrenceEnum] = mapped_column(
        SQLEnum(RecurrenceEnum, name="recurrence_enum", inherit_schema=True),
        default=RecurrenceEnum.NONE,
        nullable=False
    )
    
    # Study duration estimation in minutes
    estimated_duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    owner = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")
