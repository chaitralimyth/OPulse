from datetime import datetime, timezone
from typing import Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.enums import PriorityEnum
from app.services.ai.base import BasePriorityEngine

logger = logging.getLogger("app.services.ai.priority_engine")

class PriorityEngine(BasePriorityEngine):
    async def analyze_and_suggest_priority(
        self, db: AsyncSession, *, task: Task
    ) -> Dict[str, Any]:
        """Suggest an optimized priority based on text keywords and deadline urgency."""
        title_lower = task.title.lower()
        desc_lower = (task.description or "").lower()
        text_content = f"{title_lower} {desc_lower}"

        # 1. Keyword Scan
        high_priority_keywords = [
            "exam", "test", "quiz", "midterm", "final", "deadline", "urgent", 
            "project", "grade", "interview", "submit", "critical", "presentation"
        ]
        medium_priority_keywords = [
            "assignment", "homework", "study", "review", "reading", "lecture",
            "practice", "draft", "meeting", "exercise", "write"
        ]
        
        has_high_keyword = any(kw in text_content for kw in high_priority_keywords)
        has_medium_keyword = any(kw in text_content for kw in medium_priority_keywords)

        suggested_priority = task.priority
        reason = "Current user-defined priority is optimal."
        confidence = 0.85

        # 2. Time Urgency Assessment
        hours_to_deadline = None
        if task.due_date:
            now = datetime.now(timezone.utc)
            delta = task.due_date - now
            hours_to_deadline = delta.total_seconds() / 3600

        # Suggestion Logic
        if hours_to_deadline is not None and hours_to_deadline <= 24 and hours_to_deadline > 0:
            suggested_priority = PriorityEnum.HIGH
            reason = "Upgraded to High: Deadline is in less than 24 hours."
            confidence = 0.90
        elif has_high_keyword and task.priority != PriorityEnum.HIGH:
            suggested_priority = PriorityEnum.HIGH
            reason = "Suggested High: Title contains critical educational or deadline keywords."
            confidence = 0.80
        elif has_medium_keyword and task.priority == PriorityEnum.LOW:
            suggested_priority = PriorityEnum.MEDIUM
            reason = "Suggested Medium: Contains study or assignment keywords instead of low-priority tasks."
            confidence = 0.75
        elif not has_high_keyword and not has_medium_keyword and task.priority == PriorityEnum.HIGH:
            if not (hours_to_deadline is not None and hours_to_deadline < 48):
                suggested_priority = PriorityEnum.MEDIUM
                reason = "Suggested Medium: General task characteristics match medium priority (no critical keywords or tight deadlines)."
                confidence = 0.70

        return {
            "suggested_priority": suggested_priority.value,
            "reason": reason,
            "confidence": confidence
        }

# Global singleton engine instance
priority_engine = PriorityEngine()
