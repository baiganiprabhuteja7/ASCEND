from fastapi import APIRouter, Depends
from sqlalchemy import Integer, and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Task
from app.schemas import GoalProgress, ProgressRead

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressRead)
def get_progress(db: Session = Depends(get_db)) -> ProgressRead:
    total_goals = db.scalar(select(func.count()).select_from(Goal)) or 0
    total_tasks = db.scalar(
        select(func.count()).select_from(Task).where(Task.is_archived.is_(False))
    ) or 0
    completed_tasks = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.completed.is_(True), Task.is_archived.is_(False))
    ) or 0

    goal_rows = db.execute(
        select(
            Goal.id,
            Goal.title,
            func.count(Task.id),
            func.sum(func.cast(Task.completed, Integer)),
        )
        .outerjoin(
            Task,
            and_(Task.goal_id == Goal.id, Task.is_archived.is_(False)),
        )
        .group_by(Goal.id, Goal.title)
        .order_by(Goal.created_at.desc())
    ).all()

    goals = []
    for goal_id, title, goal_task_count, goal_completed_count in goal_rows:
        completed_count = int(goal_completed_count or 0)
        goals.append(
            GoalProgress(
                goal_id=goal_id,
                title=title,
                total_tasks=goal_task_count,
                completed_tasks=completed_count,
                completion_percentage=(
                    round(completed_count / goal_task_count * 100) if goal_task_count else 0
                ),
            )
        )

    return ProgressRead(
        total_goals=total_goals,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=total_tasks - completed_tasks,
        completion_percentage=round(completed_tasks / total_tasks * 100) if total_tasks else 0,
        goals=goals,
    )
