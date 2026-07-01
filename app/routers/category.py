from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category import category_service

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[CategoryResponse]:
    """Retrieve all categories for the authenticated user."""
    return await category_service.get_multi(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=CategoryResponse)
async def read_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    """Retrieve details of a specific category."""
    return await category_service.get_by_id(db, category_id=category_id, user_id=current_user.id)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    """Create a new task category."""
    return await category_service.create(db, category_in=category_in, user_id=current_user.id)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    """Update a category's properties."""
    return await category_service.update(
        db, category_id=category_id, category_in=category_in, user_id=current_user.id
    )

@router.delete("/{category_id}", response_model=CategoryResponse)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    """Delete a category."""
    return await category_service.remove(db, category_id=category_id, user_id=current_user.id)
