from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.activity_log import ActivityLog
from app.models.enums import TaskStatusEnum
from app.services.ai.base import BaseProductivityEngine

logger = logging.getLogger("app.services.ai.productivity_engine")

class ProductivityEngine(BaseProductivityEngine):
    async def calculate_metrics(
        self, db: AsyncSession, *, user_id: int, tasks: List[Task], logs: List[ActivityLog]
    ) -> Dict[str, Any]:
        """Aggregate user history data, compute metrics, and generate AI productivity insights."""
        completed_tasks = [t for t in tasks if t.status == TaskStatusEnum.COMPLETED]
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        
        # 1. Completion Rate
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0

        # 2. Weekly completion distribution
        now = datetime.now(timezone.utc)
        today = now.date()
        past_week_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        weekly_productivity: Dict[str, int] = {}
        for d in past_week_dates:
            day_name = d.strftime("%a")
            weekly_productivity[day_name] = 0

        for task in completed_tasks:
            if task.completed_at:
                c_date = task.completed_at.date()
                if c_date in past_week_dates:
                    weekly_productivity[c_date.strftime("%a")] += 1

        # 3. Longest Streak
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

        # 4. Most Productive Day
        day_counts: Dict[str, int] = {}
        for task in completed_tasks:
            if task.completed_at:
                day_name = task.completed_at.strftime("%A")
                day_counts[day_name] = day_counts.get(day_name, 0) + 1
        most_productive_day = max(day_counts, key=day_counts.get) if day_counts else "None"

        # 5. Focus Score Calculation
        streak_factor = min(longest_streak * 10, 100)
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

        # 6. Generate Productivity Insights
        insights = []
        if focus_score >= 80.0:
            insights.append("Outstanding work! Your focus score is exceptional. You are managing your time very efficiently.")
        elif focus_score >= 50.0:
            insights.append("Good consistency. Keep organizing tasks with clear due dates to lift your on-time score.")
        else:
            insights.append("Set smaller daily goals to build momentum and improve your overall completion rates.")

        if longest_streak >= 3:
            insights.append(f"Strong momentum! You have maintained a consecutive study streak of {longest_streak} days.")
        else:
            insights.append("Try completing at least one task daily to start a study streak.")

        if most_productive_day != "None":
            insights.append(f"Your highest output day is typically {most_productive_day}. Plan your complex assignments then.")

        now_naive = now.astimezone(timezone.utc).replace(tzinfo=None)
        overdue_count = 0
        for t in tasks:
            if t.status != TaskStatusEnum.COMPLETED and t.due_date:
                t_due = t.due_date
                if t_due.tzinfo is not None:
                    t_due = t_due.astimezone(timezone.utc).replace(tzinfo=None)
                if t_due < now_naive:
                    overdue_count += 1

        if overdue_count > 0:
            insights.append(f"You have {overdue_count} overdue tasks. Clearing these out will regain schedule stability.")

        return {
            "completion_rate": round(completion_rate, 2),
            "weekly_productivity": weekly_productivity,
            "longest_study_streak": longest_streak,
            "most_productive_day": most_productive_day,
            "focus_score": focus_score,
            "insights": insights
        }

# Global singleton engine instance
productivity_engine = ProductivityEngine()
