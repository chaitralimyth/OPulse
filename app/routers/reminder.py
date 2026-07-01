from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.reminder import reminder_service

router = APIRouter()

@router.get("/", response_model=List[ReminderResponse])
async def read_reminders(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ReminderResponse]:
    """Retrieve all reminders scheduled for the authenticated user's tasks."""
    return await reminder_service.get_multi(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def read_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ReminderResponse:
    """Retrieve details of a specific reminder."""
    return await reminder_service.get_by_id(db, reminder_id=reminder_id, user_id=current_user.id)

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: ReminderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ReminderResponse:
    """Schedule a new task reminder."""
    return await reminder_service.create(db, reminder_in=reminder_in, user_id=current_user.id)

@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_in: ReminderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ReminderResponse:
    """Update a reminder's scheduling parameters or sent state."""
    return await reminder_service.update(
        db, reminder_id=reminder_id, reminder_in=reminder_in, user_id=current_user.id
    )

@router.delete("/{reminder_id}", response_model=ReminderResponse)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ReminderResponse:
    """Remove a scheduled reminder."""
    return await reminder_service.remove(db, reminder_id=reminder_id, user_id=current_user.id)

@router.post("/{reminder_id}/interact", response_model=ReminderResponse)
async def interact_with_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ReminderResponse:
    """Acknowledge or interact with a reminder notification."""
    return await reminder_service.record_interaction(db, reminder_id=reminder_id, user_id=current_user.id)
