from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GoalCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    deadline: date | None = None
    skill_level: str = Field(min_length=1, max_length=40)
    weekly_available_hours: int = Field(ge=1, le=168)
    learning_style: str = Field(default="", max_length=120)
    learning_constraints: str = Field(default="", max_length=2000)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Title must contain at least three non-space characters")
        return normalized


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    deadline: date | None = None
    skill_level: str | None = Field(default=None, min_length=1, max_length=40)
    weekly_available_hours: int | None = Field(default=None, ge=1, le=168)
    learning_style: str | None = Field(default=None, max_length=120)
    learning_constraints: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> Self:
        required_fields = {
            "title", "description", "skill_level", "weekly_available_hours",
            "learning_style", "learning_constraints",
        }
        if any(field in self.model_fields_set and getattr(self, field) is None for field in required_fields):
            raise ValueError("title, skill_level, and weekly_available_hours cannot be null")
        return self


class GoalRead(ORMModel):
    id: str
    title: str
    description: str
    deadline: date | None
    skill_level: str
    weekly_available_hours: int
    learning_style: str
    learning_constraints: str
    plan_source: Literal["ai", "fallback"] | None
    plan_generated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    goal_id: str = Field(min_length=1, max_length=36)
    title: str = Field(min_length=3, max_length=160)
    milestone: str | None = Field(default=None, max_length=120)
    milestone_id: str | None = Field(default=None, min_length=1, max_length=36)
    completed: bool = False
    deadline: date | None = None
    scheduled_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=1440)
    completion_criteria: str | None = Field(default=None, max_length=2000)


class TaskUpdate(BaseModel):
    goal_id: str | None = Field(default=None, min_length=1, max_length=36)
    title: str | None = Field(default=None, min_length=3, max_length=160)
    milestone: str | None = Field(default=None, max_length=120)
    milestone_id: str | None = Field(default=None, min_length=1, max_length=36)
    completed: bool | None = None
    deadline: date | None = None
    scheduled_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=1440)
    completion_criteria: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> Self:
        required_fields = {"goal_id", "title", "completed"}
        if any(field in self.model_fields_set and getattr(self, field) is None for field in required_fields):
            raise ValueError("goal_id, title, and completed cannot be null")
        return self


class TaskRead(ORMModel):
    id: str
    goal_id: str
    title: str
    milestone: str | None
    milestone_id: str | None
    completed: bool
    deadline: date | None
    scheduled_date: date | None
    estimated_minutes: int | None
    completion_criteria: str | None
    created_at: datetime
    updated_at: datetime


class PlanGenerateRequest(BaseModel):
    force: bool = False


class DraftTask(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    estimated_minutes: int = Field(ge=15, le=1440)
    completion_criteria: str = Field(min_length=8, max_length=2000)


class DraftMilestone(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=2000)
    tasks: list[DraftTask] = Field(min_length=1, max_length=12)


class PlanDraft(BaseModel):
    milestones: list[DraftMilestone] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def require_multiple_tasks(self) -> Self:
        if sum(len(milestone.tasks) for milestone in self.milestones) < 2:
            raise ValueError("A plan must include at least two actionable tasks")
        return self


class MilestoneRead(ORMModel):
    id: str
    goal_id: str
    title: str
    description: str
    sequence: int
    target_date: date
    tasks: list[TaskRead]


class GoalPlanRead(BaseModel):
    goal_id: str
    source: Literal["ai", "fallback"] | None
    generated_at: datetime | None
    milestones: list[MilestoneRead]
    unassigned_tasks: list[TaskRead]
    next_action: TaskRead | None


class ChallengeRead(BaseModel):
    id: str
    category: str
    title: str
    description: str
    duration: str
    level: str
    demo: bool = True


class ContributionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=2000)
    contribution_type: str = Field(min_length=1, max_length=60)
    evidence_url: HttpUrl | None = None


class ContributionRead(ORMModel):
    id: str
    title: str
    description: str
    contribution_type: str
    evidence_url: str | None
    created_at: datetime


class GoalProgress(BaseModel):
    goal_id: str
    title: str
    total_tasks: int
    completed_tasks: int
    completion_percentage: int


class ProgressRead(BaseModel):
    total_goals: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completion_percentage: int
    goals: list[GoalProgress]
