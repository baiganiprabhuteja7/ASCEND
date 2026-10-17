from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Full name must contain at least two non-space characters")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not (
            any("a" <= character <= "z" for character in value)
            and any("A" <= character <= "Z" for character in value)
            and any("0" <= character <= "9" for character in value)
            and any(character.isascii() and not character.isalnum() for character in value)
        ):
            raise ValueError(
                "Use at least one uppercase letter, lowercase letter, number, and symbol"
            )
        return value

    @model_validator(mode="after")
    def passwords_must_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class UserRead(ORMModel):
    id: str
    full_name: str
    email: EmailStr = Field(max_length=320)
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserRead


class GoalCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    status: Literal["not_started", "in_progress", "completed"] = "not_started"
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
    status: Literal["not_started", "in_progress", "completed"] | None = None
    deadline: date | None = None
    skill_level: str | None = Field(default=None, min_length=1, max_length=40)
    weekly_available_hours: int | None = Field(default=None, ge=1, le=168)
    learning_style: str | None = Field(default=None, max_length=120)
    learning_constraints: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> Self:
        required_fields = {
            "title", "description", "skill_level", "weekly_available_hours",
            "learning_style", "learning_constraints", "status",
        }
        if any(field in self.model_fields_set and getattr(self, field) is None for field in required_fields):
            raise ValueError(
                "title, status, skill_level, and weekly_available_hours cannot be null"
            )
        return self


class GoalRead(ORMModel):
    id: str
    title: str
    description: str
    status: Literal["not_started", "in_progress", "completed"]
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
    status: Literal["not_started", "in_progress", "completed"]
    total_tasks: int
    completed_tasks: int
    completion_percentage: int


class ProgressRead(BaseModel):
    total_goals: int
    completed_goals: int
    in_progress_goals: int
    pending_goals: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completion_percentage: int
    goals: list[GoalProgress]
