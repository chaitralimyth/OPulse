import logging
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.enums import ActivityTypeEnum
from app.repositories.user import user_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.user import UserCreate
from app.schemas.token import Token

logger = logging.getLogger("app.services.auth")

class AuthService:
    async def register(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """Register a new user and hash their password."""
        existing_user = await user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists in the system."
            )
        
        user_data = user_in.model_dump()
        password = user_data.pop("password")
        user_data["hashed_password"] = get_password_hash(password)
        
        db_user = await user_repository.create(db, obj_in=user_data)
        await db.commit()
        
        # Log user creation activity
        await activity_log_repository.log_activity(
            db,
            user_id=db_user.id,
            activity_type=ActivityTypeEnum.TASK_EDIT,  # Using edit/create action general
            details={"message": f"User {db_user.email} registered successfully."}
        )
        await db.commit()
        
        logger.info("Registered new user: %s", db_user.email)
        return db_user

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> User:
        """Authenticate a user with email and password, returning User if successful."""
        user = await user_repository.get_by_email(db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        logger.info("Authenticated user: %s", email)
        return user

    def generate_tokens(self, user_id: int) -> Token:
        """Generate JWT access and refresh tokens for a user ID."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_access_token(self, db: AsyncSession, *, refresh_token: str) -> Token:
        """Issue new access and refresh tokens using a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
            user_id_str: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if not user_id_str or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
            user_id = int(user_id_str)
        except (jwt.InvalidTokenError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = await user_repository.get(db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return self.generate_tokens(user_id=user.id)

auth_service = AuthService()
