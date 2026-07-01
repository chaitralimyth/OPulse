from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.analytics import ProductivityMetricsResponse
from app.services.analytics import analytics_service

router = APIRouter()

@router.get("/stats", response_model=ProductivityMetricsResponse)
async def get_productivity_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductivityMetricsResponse:
    """Retrieve detailed user productivity metrics, study streaks, and focus score."""
    return await analytics_service.get_productivity_metrics(db, user_id=current_user.id)
