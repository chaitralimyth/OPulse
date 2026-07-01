import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.task import Task
from app.models.enums import TaskStatusEnum, ActivityTypeEnum, RecurrenceEnum
from app.repositories.task import task_repository
from app.repositories.category import category_repository
from app.repositories.activity_log import activity_log_repository
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.datetime_utils import calculate_next_recurrence

logger = logging.getLogger("app.services.task")

class TaskService:
    async def get_by_id(self, db: AsyncSession, *, task_id: int, user_id: int) -> Task:
        """Fetch a task by ID, eager loading category relationships, and verify ownership."""
        query = (
            select(Task)
            .filter(Task.id == task_id)
            .options(selectinload(Task.category))
        )
        result = await db.execute(query)
        task = result.scalars().first()
        
        if not task or task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        return task

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: Optional[TaskStatusEnum] = None,
        priority: Optional[TaskStatusEnum] = None,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Retrieve filtered list of tasks belonging to user."""
        return await task_repository.get_multi_by_user(
            db,
            user_id=user_id,
            status=status,
            priority=priority,
            category_id=category_id,
            skip=skip,
            limit=limit
        )

    async def create(self, db: AsyncSession, *, task_in: TaskCreate, user_id: int) -> Task:
        """Create a new task after verifying category ownership."""
        if task_in.category_id is not None:
            category = await category_repository.get(db, id=task_in.category_id)
            if not category or category.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID selected"
                )

        task_data = task_in.model_dump()
        task_data["user_id"] = user_id
        
        db_task = await task_repository.create(db, obj_in=task_data)
        await db.commit()

        # Eager load relationships to prevent MissingGreenlet in response serialization
        db_task = await self.get_by_id(db, task_id=db_task.id, user_id=user_id)

        # Log task creation
        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.TASK_CREATE,
            entity_id=db_task.id,
            details={"title": db_task.title}
        )
        await db.commit()

        logger.info("User %s created task: %s", user_id, db_task.title)
        return db_task

    async def update(
        self, db: AsyncSession, *, task_id: int, task_in: TaskUpdate, user_id: int
    ) -> Task:
        """Update a task's details, handling completion timestamps and recurrence rules."""
        db_task = await self.get_by_id(db, task_id=task_id, user_id=user_id)

        if task_in.category_id is not None:
            category = await category_repository.get(db, id=task_in.category_id)
            if not category or category.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID selected"
                )

        update_data = task_in.model_dump(exclude_unset=True)
        status_changed = "status" in update_data and update_data["status"] != db_task.status
        new_status = update_data.get("status")

        # Handle completion timestamps and recurrence logging
        if status_changed:
            if new_status == TaskStatusEnum.COMPLETED:
                db_task.completed_at = datetime.now(timezone.utc)
                # Log completion activity
                await activity_log_repository.log_activity(
                    db,
                    user_id=user_id,
                    activity_type=ActivityTypeEnum.TASK_COMPLETE,
                    entity_id=db_task.id,
                    details={"title": db_task.title}
                )
                
                # Handle recurring task automation
                if db_task.recurrence != RecurrenceEnum.NONE:
                    next_due = calculate_next_recurrence(db_task.due_date, db_task.recurrence)
                    # Spawn next occurrence
                    next_task_in = TaskCreate(
                        title=db_task.title,
                        description=db_task.description,
                        status=TaskStatusEnum.TODO,
                        priority=db_task.priority,
                        recurrence=db_task.recurrence,
                        estimated_duration=db_task.estimated_duration,
                        due_date=next_due,
                        category_id=db_task.category_id
                    )
                    # Use service create to log create action for the future task
                    await self.create(db, task_in=next_task_in, user_id=user_id)
                    logger.info("Auto-spawned recurring task: %s due %s", db_task.title, next_due)
                    
            elif db_task.status == TaskStatusEnum.COMPLETED:
                # Reverting completion
                db_task.completed_at = None

        # Update remaining attributes
        db_task = await task_repository.update(db, db_obj=db_task, obj_in=update_data)
        await db.commit()

        # Refetch with eager loading to prevent MissingGreenlet in response serialization
        db_task = await self.get_by_id(db, task_id=db_task.id, user_id=user_id)

        # Log task edit if not completed just now
        if not (status_changed and new_status == TaskStatusEnum.COMPLETED):
            await activity_log_repository.log_activity(
                db,
                user_id=user_id,
                activity_type=ActivityTypeEnum.TASK_EDIT,
                entity_id=db_task.id,
                details={"title": db_task.title, "updates": list(update_data.keys())}
            )
            await db.commit()

        return db_task

    async def remove(self, db: AsyncSession, *, task_id: int, user_id: int) -> Task:
        """Delete task from database and log deletion."""
        task = await self.get_by_id(db, task_id=task_id, user_id=user_id)
        deleted_task = await task_repository.remove(db, id=task_id)
        await db.commit()

        await activity_log_repository.log_activity(
            db,
            user_id=user_id,
            activity_type=ActivityTypeEnum.TASK_EDIT,
            entity_id=task_id,
            details={"message": f"Deleted task '{task.title}'"}
        )
        await db.commit()

        logger.info("Deleted task ID %s for user %s", task_id, user_id)
        return deleted_task

task_service = TaskService()
