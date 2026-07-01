from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.activity_log import ActivityLog

class BaseRecommendationEngine(ABC):
    @abstractmethod
    async def get_recommendations(
        self, db: AsyncSession, *, user_id: int, tasks: List[Task], logs: List[ActivityLog]
    ) -> List[Dict[str, Any]]:
        """Evaluate uncompleted tasks using a scoring algorithm to rank the top recommendations."""
        pass

class BasePriorityEngine(ABC):
    @abstractmethod
    async def analyze_and_suggest_priority(
        self, db: AsyncSession, *, task: Task
    ) -> Dict[str, Any]:
        """Examine task metadata to suggest appropriate priority revisions."""
        pass

class BaseProductivityEngine(ABC):
    @abstractmethod
    async def calculate_metrics(
        self, db: AsyncSession, *, user_id: int, tasks: List[Task], logs: List[ActivityLog]
    ) -> Dict[str, Any]:
        """Aggregate completion logs to generate productivity metrics (streaks, score)."""
        pass
