from fastapi import APIRouter
from app.routers import auth, user, category, task, reminder, analytics, ai

api_router = APIRouter()

# Group all modules under respective endpoint paths
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(category.router, prefix="/categories", tags=["Categories"])
api_router.include_router(task.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(reminder.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Copilot"])
