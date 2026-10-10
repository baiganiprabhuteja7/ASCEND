from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    skill_level: Mapped[str] = mapped_column(String(40), nullable=False)
    weekly_available_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_style: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    learning_constraints: Mapped[str] = mapped_column(Text, nullable=False, default="")
    plan_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plan_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Milestone.sequence",
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    goal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    goal: Mapped[Goal] = relationship(back_populates="milestones")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="milestone_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Task.scheduled_date, Task.created_at",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    goal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    milestone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    milestone_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("milestones.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    goal: Mapped[Goal] = relationship(back_populates="tasks")
    milestone_record: Mapped[Milestone | None] = relationship(back_populates="tasks")


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    contribution_type: Mapped[str] = mapped_column(String(60), nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
