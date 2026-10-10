from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Milestone, Task
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    if db.get(Goal, payload.goal_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if payload.milestone_id is not None:
        milestone = db.get(Milestone, payload.milestone_id)
        if milestone is None or milestone.goal_id != payload.goal_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The milestone must belong to the selected goal",
            )
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    goal_id: str | None = Query(default=None, min_length=1, max_length=36),
    db: Session = Depends(get_db),
) -> list[Task]:
    statement = (
        select(Task)
        .where(Task.is_archived.is_(False))
        .order_by(Task.created_at.desc())
    )
    if goal_id is not None:
        statement = statement.where(Task.goal_id == goal_id)
    return list(db.scalars(statement).all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    changes = payload.model_dump(exclude_unset=True)
    target_goal_id = changes.get("goal_id", task.goal_id)
    if "goal_id" in changes and db.get(Goal, target_goal_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    target_milestone_id = changes.get("milestone_id", task.milestone_id)
    if target_milestone_id is not None:
        milestone = db.get(Milestone, target_milestone_id)
        if milestone is None or milestone.goal_id != target_goal_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The milestone must belong to the selected goal",
            )
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> Response:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
