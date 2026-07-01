from typing import Dict
from pydantic import BaseModel, ConfigDict

class ProductivityMetricsResponse(BaseModel):
    completion_rate: float            # Percentage, e.g. 85.5
    weekly_productivity: Dict[str, int] # Completed tasks per day of the current week (e.g. {"Mon": 3, "Tue": 4})
    longest_study_streak: int         # Consecutive active days
    most_productive_day: str          # Day name (e.g. "Wednesday")
    focus_score: float                # Focus score, scale 0-100

    model_config = ConfigDict(from_attributes=True)
