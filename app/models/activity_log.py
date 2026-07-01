from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Integer, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.enums import ActivityTypeEnum

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    activity_type: Mapped[ActivityTypeEnum] = mapped_column(
        SQLEnum(ActivityTypeEnum, name="activity_type_enum", inherit_schema=True),
        nullable=False
    )
    
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Store event metadata (e.g. before/after states or descriptive notes)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="activity_logs")
