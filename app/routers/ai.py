from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.task import task_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.ai import RecommendationItem, DailyPlanResponse
from app.services.ai.recommendation_engine import recommendation_engine
from app.services.ai.productivity_engine import productivity_engine

router = APIRouter()

@router.get("/recommendations", response_model=List[RecommendationItem])
async def get_task_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[RecommendationItem]:
    """Retrieve scored and sorted task recommendations for the current user."""
    tasks = await task_repository.get_all_by_user(db, user_id=current_user.id)
    logs = await activity_log_repository.get_all_by_user(db, user_id=current_user.id)
    
    # Get recommendations from the injected/resolved recommendation engine
    recs = await recommendation_engine.get_recommendations(db, user_id=current_user.id, tasks=tasks, logs=logs)
    return recs

@router.get("/daily-plan", response_model=DailyPlanResponse)
async def get_daily_study_plan(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> DailyPlanResponse:
    """Generate a prioritized daily study plan with custom study ordering and productivity insights."""
    tasks = await task_repository.get_all_by_user(db, user_id=current_user.id)
    logs = await activity_log_repository.get_all_by_user(db, user_id=current_user.id)
    
    recs = await recommendation_engine.get_recommendations(db, user_id=current_user.id, tasks=tasks, logs=logs)
    metrics = await productivity_engine.calculate_metrics(db, user_id=current_user.id, tasks=tasks, logs=logs)
    
    if not recs:
        return DailyPlanResponse(
            highest_priority_task=None,
            suggested_study_order=[],
            estimated_completion_time=0,
            productivity_insights=metrics.get("insights", []),
            ai_explanation="You have no active tasks. Great job keeping your workspace clean!"
        )

    # Calculate total duration of recommended tasks
    rec_task_ids = {r["task_id"] for r in recs}
    total_duration = sum(t.estimated_duration for t in tasks if t.id in rec_task_ids)

    highest_rec = recs[0]
    
    # Find matching task title for explanation
    highest_task = next((t for t in tasks if t.id == highest_rec["task_id"]), None)
    highest_title = highest_task.title if highest_task else "top task"

    ai_explanation = (
        f"For your daily study plan, you have {len(recs)} active tasks requiring approximately "
        f"{total_duration} minutes of focus. We recommend tackling '{highest_title}' first due to its "
        f"high recommendation score ({highest_rec['priority_score']})."
    )

    return DailyPlanResponse(
        highest_priority_task=RecommendationItem(**highest_rec),
        suggested_study_order=[RecommendationItem(**r) for r in recs],
        estimated_completion_time=total_duration,
        productivity_insights=metrics.get("insights", []),
        ai_explanation=ai_explanation
    )
