from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.activity_log import ActivityLog
from app.models.enums import TaskStatusEnum, PriorityEnum, RecurrenceEnum, ActivityTypeEnum
from app.services.ai.base import BaseRecommendationEngine

logger = logging.getLogger("app.services.ai.recommendation_engine")

class RecommendationEngine(BaseRecommendationEngine):
    async def get_recommendations(
        self, db: AsyncSession, *, user_id: int, tasks: List[Task], logs: List[ActivityLog]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate tasks using a deterministic weighted scoring model:
        Score = 40% Urgency + 30% User Priority + 15% Duration Fit + 10% Pattern Alignment + 5% Recurrence Type
        """
        now = datetime.now(timezone.utc)
        recommendations = []
        
        # Analyze completion logs to determine category + daily time patterns
        # Group historical completions by category_id and hour of completion
        completions = [log for log in logs if log.activity_type == ActivityTypeEnum.TASK_COMPLETE]
        category_completion_counts: Dict[int, int] = {}
        hour_completion_counts: Dict[int, int] = {}
        
        for comp in completions:
            # Check details if category is logged
            details = comp.details or {}
            cat_id = details.get("category_id")
            if cat_id is not None:
                category_completion_counts[cat_id] = category_completion_counts.get(cat_id, 0) + 1
            
            # Count the hour pattern
            comp_hour = comp.timestamp.hour
            hour_completion_counts[comp_hour] = hour_completion_counts.get(comp_hour, 0) + 1

        total_completions = len(completions)

        # Process only uncompleted tasks
        active_tasks = [t for t in tasks if t.status != TaskStatusEnum.COMPLETED]

        for task in active_tasks:
            # 1. Deadline Urgency (0 to 10 points)
            urgency_score = 0.0
            urgency_level = "LOW"
            time_explanation = ""
            is_overdue = False

            if task.due_date:
                task_due = task.due_date
                # Normalize both to naive UTC datetimes to prevent offset-naive/aware subtraction errors
                if task_due.tzinfo is not None:
                    task_due = task_due.astimezone(timezone.utc).replace(tzinfo=None)
                now_naive = now.astimezone(timezone.utc).replace(tzinfo=None)
                
                time_delta = task_due - now_naive
                hours_left = time_delta.total_seconds() / 3600

                if hours_left < 0:
                    # Overdue
                    urgency_score = 10.0
                    urgency_level = "CRITICAL"
                    is_overdue = True
                    time_explanation = "is already overdue"
                elif hours_left <= 12:
                    urgency_score = 9.5
                    urgency_level = "CRITICAL"
                    time_explanation = f"is due in {round(hours_left, 1)} hours"
                elif hours_left <= 24:
                    urgency_score = 8.5
                    urgency_level = "HIGH"
                    time_explanation = f"is due in {round(hours_left, 1)} hours"
                elif hours_left <= 72:
                    urgency_score = 6.0
                    urgency_level = "MEDIUM"
                    time_explanation = f"is due within 3 days"
                else:
                    urgency_score = 3.0
                    urgency_level = "LOW"
                    time_explanation = "has an extended deadline"
            else:
                # No due date
                urgency_score = 2.0
                urgency_level = "LOW"
                time_explanation = "has no assigned deadline"

            # 2. Priority weight (0 to 10 points)
            priority_score = 0.0
            if task.priority == PriorityEnum.HIGH:
                priority_score = 10.0
            elif task.priority == PriorityEnum.MEDIUM:
                priority_score = 6.0
            else:
                priority_score = 2.0

            # 3. Focus duration alignment (0 to 10 points)
            # Pomodoro sweet spot is between 25 and 50 minutes
            duration_score = 0.0
            if 25 <= task.estimated_duration <= 50:
                duration_score = 10.0
            elif task.estimated_duration < 25:
                duration_score = 7.0  # Quick task
            else:
                duration_score = 4.0  # Heavy task (long)

            # 4. Pattern Alignment (0 to 10 points)
            pattern_score = 0.0
            pattern_match = False
            current_hour = now.hour

            # Boost if task matches typical times user completes tasks (±2 hours range)
            matching_hours_count = 0
            for h in range(current_hour - 2, current_hour + 3):
                matching_hours_count += hour_completion_counts.get(h % 24, 0)
            
            if total_completions > 0 and matching_hours_count > 0:
                pattern_score = min((matching_hours_count / total_completions) * 20.0, 10.0)
                if pattern_score > 3.0:
                    pattern_match = True

            # Boost based on category popularity
            category_boost = 0.0
            if task.category_id and total_completions > 0:
                cat_count = category_completion_counts.get(task.category_id, 0)
                category_boost = min((cat_count / total_completions) * 10.0, 10.0)
            
            pattern_score = min(pattern_score + category_boost, 10.0)

            # 5. Recurrence Score (0 to 10 points)
            recurrence_score = 0.0
            if task.recurrence == RecurrenceEnum.DAILY:
                recurrence_score = 10.0
            elif task.recurrence == RecurrenceEnum.WEEKLY:
                recurrence_score = 6.0
            elif task.recurrence == RecurrenceEnum.MONTHLY:
                recurrence_score = 3.0

            # Weighted sum calculation
            # Weights: Urgency (0.40), Priority (0.30), Duration (0.15), Pattern (0.10), Recurrence (0.05)
            final_weighted_score = (
                (urgency_score * 0.40) +
                (priority_score * 0.30) +
                (duration_score * 0.15) +
                (pattern_score * 0.10) +
                (recurrence_score * 0.05)
            ) * 10.0  # Scale to 0-100 range

            # Add heavy penalty/bonus for overdue items to pull them to the top
            if is_overdue:
                final_weighted_score += 15.0
            
            # Bound score to [0, 100]
            final_weighted_score = round(min(max(final_weighted_score, 0.0), 100.0), 2)

            # Calculate confidence score (representing consistency of data and patterns)
            # Higher completions history = higher prediction confidence
            base_confidence = 0.60
            if total_completions > 5:
                base_confidence += 0.15
            if pattern_match:
                base_confidence += 0.15
            if task.priority == PriorityEnum.HIGH:
                base_confidence += 0.05
            
            confidence = round(min(base_confidence, 0.99), 2)

            # Formulate detailed explanation
            explanations = []
            if is_overdue:
                explanations.append("This task is overdue and requires immediate focus.")
            elif task.due_date and urgency_score >= 8.5:
                explanations.append(f"It is high priority due to its impending deadline ({time_explanation}).")
            
            if task.priority == PriorityEnum.HIGH:
                explanations.append("It is marked as High Priority.")
            
            if pattern_match:
                explanations.append("The time aligns perfectly with your historical high-productivity hours.")
            
            if task.recurrence != RecurrenceEnum.NONE:
                explanations.append(f"This is a recurring {task.recurrence.value} task to keep your streak going.")

            if not explanations:
                explanations.append("Fits well into your standard queue of active study items.")

            explanation_str = " ".join(explanations)

            recommendations.append({
                "task_id": task.id,
                "priority_score": final_weighted_score,
                "confidence": confidence,
                "explanation": explanation_str,
                "urgency_level": urgency_level
            })

        # Sort recommendations descending by score
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        return recommendations

# Global singleton engine instance
recommendation_engine = RecommendationEngine()
