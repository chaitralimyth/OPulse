from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Get profile information for the authenticated user."""
    return current_user
