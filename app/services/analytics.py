from datetime import datetime, timezone, timedelta
from typing import Dict, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.enums import TaskStatusEnum
from app.repositories.task import task_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.analytics import ProductivityMetricsResponse

logger = logging.getLogger("app.services.analytics")

class AnalyticsService:
    async def get_productivity_metrics(
        self, db: AsyncSession, *, user_id: int
    ) -> ProductivityMetricsResponse:
        """Calculate productivity metrics for the specified user."""
        all_tasks = await task_repository.get_all_by_user(db, user_id=user_id)
        completed_tasks = [t for t in all_tasks if t.status == TaskStatusEnum.COMPLETED]
        
        # 1. Completion Rate
        total_count = len(all_tasks)
        completed_count = len(completed_tasks)
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0.0

        # 2. Weekly Productivity (completions in last 7 days)
        now = datetime.now(timezone.utc)
        today = now.date()
        past_week_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        # Initialize day distribution: {"Mon": 0, "Tue": 0, ...}
        weekly_productivity: Dict[str, int] = {}
        for d in past_week_dates:
            day_name = d.strftime("%a")  # e.g. "Mon", "Tue"
            weekly_productivity[day_name] = 0

        for task in completed_tasks:
            if task.completed_at:
                completed_date = task.completed_at.date()
                if completed_date in past_week_dates:
                    day_name = completed_date.strftime("%a")
                    weekly_productivity[day_name] += 1

        # 3. Longest Study Streak (consecutive days of completed tasks)
        completion_dates = sorted({t.completed_at.date() for t in completed_tasks if t.completed_at})
        longest_streak = 0
        if completion_dates:
            longest_streak = 1
            current_streak = 1
            for i in range(len(completion_dates) - 1):
                diff = (completion_dates[i + 1] - completion_dates[i]).days
                if diff == 1:
                    current_streak += 1
                elif diff > 1:
                    longest_streak = max(longest_streak, current_streak)
                    current_streak = 1
            longest_streak = max(longest_streak, current_streak)

        # 4. Most Productive Day of Week
        day_counts: Dict[str, int] = {}
        for task in completed_tasks:
            if task.completed_at:
                day_name = task.completed_at.strftime("%A")  # Full day name, e.g. "Monday"
                day_counts[day_name] = day_counts.get(day_name, 0) + 1

        most_productive_day = max(day_counts, key=day_counts.get) if day_counts else "None"

        # 5. Focus Score Calculation
        # Focus Score = 40% Completion Rate + 30% Streak Factor + 30% On-Time Completion Rate
        streak_factor = min(longest_streak * 10, 100)  # Maxes out at a 10-day streak
        
        on_time_count = 0
        tasks_with_due_date = 0
        for task in completed_tasks:
            if task.due_date and task.completed_at:
                tasks_with_due_date += 1
                completed_at = task.completed_at
                due_date = task.due_date
                if completed_at.tzinfo is not None:
                    completed_at = completed_at.astimezone(timezone.utc).replace(tzinfo=None)
                if due_date.tzinfo is not None:
                    due_date = due_date.astimezone(timezone.utc).replace(tzinfo=None)
                if completed_at <= due_date:
                    on_time_count += 1
                    
        on_time_rate = (on_time_count / tasks_with_due_date * 100) if tasks_with_due_date > 0 else 100.0
        
        focus_score = (0.4 * completion_rate) + (0.3 * streak_factor) + (0.3 * on_time_rate)
        focus_score = round(min(focus_score, 100.0), 2)

        return ProductivityMetricsResponse(
            completion_rate=round(completion_rate, 2),
            weekly_productivity=weekly_productivity,
            longest_study_streak=longest_streak,
            most_productive_day=most_productive_day,
            focus_score=focus_score
        )

# Global singleton repository instance
analytics_service = AnalyticsService()
