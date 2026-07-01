from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog
from app.models.enums import ActivityTypeEnum
from app.repositories.base import BaseRepository

class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self) -> None:
        super().__init__(ActivityLog)

    async def get_multi_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        activity_type: Optional[ActivityTypeEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActivityLog]:
        """Fetch activity logs for a user with optional filters, sorted newest first."""
        filters = [ActivityLog.user_id == user_id]
        if activity_type:
            filters.append(ActivityLog.activity_type == activity_type)

        query = (
            select(ActivityLog)
            .filter(*filters)
            .order_by(ActivityLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all_by_user(self, db: AsyncSession, *, user_id: int) -> List[ActivityLog]:
        """Fetch all activity logs for a user (used by AI metrics calculations)."""
        query = (
            select(ActivityLog)
            .filter(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.timestamp.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def log_activity(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        activity_type: ActivityTypeEnum,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Helper to create and save a new activity log entry."""
        log_obj = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            entity_id=entity_id,
            details=details
        )
        db.add(log_obj)
        await db.flush()
        return log_obj

# Global singleton repository instance
activity_log_repository = ActivityLogRepository()
