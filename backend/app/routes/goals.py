from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user, get_owned_goal
from app.database import get_db
from app.models import Goal, Milestone, Task, utc_now
from app.models import User
from app.schemas import (
    GoalCreate,
    GoalPlanRead,
    GoalRead,
    MilestoneRead,
    PlanGenerateRequest,
    TaskRead,
    GoalUpdate,
)
from app.services.plan_generation import build_scheduled_plan

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Goal:
    normalized_title = payload.title.lower()
    duplicate = db.scalar(
        select(Goal.id)
        .where(
            Goal.user_id == user.id,
            func.lower(func.trim(Goal.title)) == normalized_title,
        )
        .limit(1)
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A goal with this title already exists. Open the existing goal instead.",
        )
    goal = Goal(user_id=user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def read_goal_plan(goal: Goal, db: Session) -> GoalPlanRead:
    milestones = list(
        db.scalars(
            select(Milestone)
            .where(
                Milestone.goal_id == goal.id,
                Milestone.is_archived.is_(False),
            )
            .options(selectinload(Milestone.tasks))
            .order_by(Milestone.sequence)
        ).all()
    )
    tasks = list(
        db.scalars(
            select(Task)
            .where(Task.goal_id == goal.id)
            .where(Task.is_archived.is_(False))
            .options(selectinload(Task.milestone_record))
            .order_by(Task.scheduled_date.nulls_last(), Task.created_at)
        ).all()
    )
    next_action = next((task for task in tasks if not task.completed), None)
    milestone_reads: list[MilestoneRead] = []
    for milestone in milestones:
        active_tasks = [
            TaskRead.model_validate(task)
            for task in milestone.tasks
            if not task.is_archived
        ]
        if active_tasks:
            milestone_reads.append(
                MilestoneRead(
                    id=milestone.id,
                    goal_id=milestone.goal_id,
                    title=milestone.title,
                    description=milestone.description,
                    sequence=milestone.sequence,
                    target_date=milestone.target_date,
                    tasks=active_tasks,
                )
            )
    return GoalPlanRead(
        goal_id=goal.id,
        source=goal.plan_source,
        generated_at=goal.plan_generated_at,
        milestones=milestone_reads,
        unassigned_tasks=[
            TaskRead.model_validate(task)
            for task in tasks
            if task.milestone_id is None
            or (task.milestone_record is not None and task.milestone_record.is_archived)
        ],
        next_action=TaskRead.model_validate(next_action) if next_action else None,
    )


@router.get("/{goal_id}/plan", response_model=GoalPlanRead)
def get_goal_plan(
    goal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalPlanRead:
    goal = get_owned_goal(goal_id, user, db)
    return read_goal_plan(goal, db)


@router.post("/{goal_id}/plan", response_model=GoalPlanRead)
def generate_goal_plan(
    goal_id: str,
    payload: PlanGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalPlanRead:
    goal = get_owned_goal(goal_id, user, db)

    has_existing_tasks = db.scalar(
        select(Task.id).where(Task.goal_id == goal_id).limit(1)
    ) is not None
    has_existing_plan = goal.plan_generated_at is not None or db.scalar(
        select(Milestone.id).where(Milestone.goal_id == goal_id).limit(1)
    ) is not None
    if (has_existing_plan or has_existing_tasks) and not payload.force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This goal already has actions. Confirm replacement before generating a new plan.",
        )

    existing_tasks = list(
        db.scalars(select(Task).where(Task.goal_id == goal_id)).all()
    )
    existing_milestones = list(
        db.scalars(
            select(Milestone).where(
                Milestone.goal_id == goal_id,
                Milestone.is_archived.is_(False),
            )
        ).all()
    )
    active_milestone_ids = {milestone.id for milestone in existing_milestones}
    preserved_tasks = [
        task
        for task in existing_tasks
        if not task.is_archived
        and (
            task.completed
            or task.milestone_id is None
            or task.milestone_id not in active_milestone_ids
        )
    ]
    try:
        source, scheduled_milestones = build_scheduled_plan(
            goal,
            existing_tasks=[
                (task.scheduled_date, task.estimated_minutes)
                for task in preserved_tasks
            ],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    db.rollback()
    db.execute(update(Goal).where(Goal.id == goal_id).values(updated_at=Goal.updated_at))
    db.refresh(goal)
    has_existing_tasks = db.scalar(
        select(Task.id).where(Task.goal_id == goal_id).limit(1)
    ) is not None
    has_existing_plan = goal.plan_generated_at is not None or db.scalar(
        select(Milestone.id).where(Milestone.goal_id == goal_id).limit(1)
    ) is not None
    if (has_existing_plan or has_existing_tasks) and not payload.force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This goal already has actions. Confirm replacement before generating a new plan.",
        )

    existing_task_titles = {
        " ".join(task.title.casefold().split())
        for task in preserved_tasks
    }
    active_milestone_ids = {milestone.id for milestone in existing_milestones}
    if active_milestone_ids:
        db.execute(
            update(Task)
            .where(
                Task.goal_id == goal_id,
                Task.milestone_id.in_(active_milestone_ids),
                Task.is_archived.is_(False),
                Task.completed.is_(False),
            )
            .values(is_archived=True)
        )
        db.execute(
            update(Milestone)
            .where(Milestone.id.in_(active_milestone_ids))
            .values(is_archived=True)
        )

    added_task_count = 0
    for planned_milestone in scheduled_milestones:
        new_tasks = []
        for planned_task in planned_milestone["tasks"]:
            normalized_title = " ".join(planned_task["title"].casefold().split())
            if normalized_title in existing_task_titles:
                continue
            existing_task_titles.add(normalized_title)
            new_tasks.append(planned_task)
        if not new_tasks:
            continue

        milestone = Milestone(
            goal_id=goal.id,
            title=planned_milestone["title"],
            description=planned_milestone["description"],
            sequence=planned_milestone["sequence"],
            target_date=max(task["scheduled_date"] for task in new_tasks),
            is_archived=False,
        )
        db.add(milestone)
        db.flush()
        for planned_task in new_tasks:
            added_task_count += 1
            db.add(
                Task(
                    goal_id=goal.id,
                    title=planned_task["title"],
                    milestone=milestone.title,
                    milestone_id=milestone.id,
                    completed=False,
                    is_archived=False,
                    deadline=planned_task["deadline"],
                    scheduled_date=planned_task["scheduled_date"],
                    estimated_minutes=planned_task["estimated_minutes"],
                    completion_criteria=planned_task["completion_criteria"],
                )
            )

    if added_task_count:
        goal.plan_source = source
        goal.plan_generated_at = utc_now()
    db.commit()
    db.refresh(goal)
    return read_goal_plan(goal, db)
@router.get("", response_model=list[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Goal]:
    return list(
        db.scalars(
            select(Goal)
            .where(Goal.user_id == user.id)
            .order_by(Goal.created_at.desc())
        ).all()
    )


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Goal:
    return get_owned_goal(goal_id, user, db)


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Goal:
    goal = get_owned_goal(goal_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    goal = get_owned_goal(goal_id, user, db)
    db.delete(goal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
