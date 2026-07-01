from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.models.enums import TaskStatusEnum, PriorityEnum
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task import task_service

router = APIRouter()

@router.get("/", response_model=List[TaskResponse])
async def read_tasks(
    status: Optional[TaskStatusEnum] = None,
    priority: Optional[PriorityEnum] = None,
    category_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[TaskResponse]:
    """Retrieve all tasks for the current user, optionally filtered by status, priority, and category."""
    return await task_service.get_multi(
        db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        category_id=category_id,
        skip=skip,
        limit=limit
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Retrieve details of a specific task."""
    return await task_service.get_by_id(db, task_id=task_id, user_id=current_user.id)

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Create a new task."""
    return await task_service.create(db, task_in=task_in, user_id=current_user.id)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Update a task's details."""
    return await task_service.update(db, task_id=task_id, task_in=task_in, user_id=current_user.id)

@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Delete a task."""
    return await task_service.remove(db, task_id=task_id, user_id=current_user.id)
