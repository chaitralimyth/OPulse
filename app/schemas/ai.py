from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class RecommendationItem(BaseModel):
    task_id: int
    priority_score: float
    confidence: float
    explanation: str
    urgency_level: str  # E.g. "LOW", "MEDIUM", "HIGH", "CRITICAL"

    model_config = ConfigDict(from_attributes=True)

class DailyPlanResponse(BaseModel):
    highest_priority_task: Optional[RecommendationItem] = None
    suggested_study_order: List[RecommendationItem]
    estimated_completion_time: int  # Total estimated study duration in minutes
    productivity_insights: List[str]
    ai_explanation: str

    model_config = ConfigDict(from_attributes=True)
