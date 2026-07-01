from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token, TokenRefreshRequest
from app.services.auth import auth_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new user account."""
    return await auth_service.register(db, user_in=user_in)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """OAuth2 password flow token login. Use 'username' as email and 'password'."""
    user = await auth_service.authenticate(db, email=form_data.username, password=form_data.password)
    return auth_service.generate_tokens(user_id=user.id)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_req: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Acquire a new access token using a refresh token."""
    return await auth_service.refresh_access_token(db, refresh_token=refresh_req.refresh_token)
