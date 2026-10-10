from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Boolean, Date, DateTime, Engine, Integer, String, Text, create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> Engine:
    connect_args: dict[str, object] = {}
    engine_options: dict[str, object] = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if database_url.endswith(":memory:"):
            engine_options["poolclass"] = StaticPool
        else:
            database_path = database_url.split("///", maxsplit=1)[-1].split("?", maxsplit=1)[0]
            if database_path and database_path != ":memory:":
                Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        **engine_options,
    )

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_db_and_tables() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_existing_schema(engine)


def migrate_existing_schema(target_engine: Engine) -> None:
    additions = {
        "goals": {
            "learning_style": (String(120), " NOT NULL DEFAULT ''"),
            "learning_constraints": (Text(), " NOT NULL DEFAULT ''"),
            "plan_source": (String(20), ""),
            "plan_generated_at": (DateTime(timezone=True), ""),
        },
        "tasks": {
            "milestone_id": (
                String(36),
                " REFERENCES milestones(id) ON DELETE SET NULL",
            ),
            "scheduled_date": (Date(), ""),
            "estimated_minutes": (Integer(), ""),
            "completion_criteria": (Text(), ""),
            "is_archived": (Boolean(), " NOT NULL DEFAULT FALSE"),
        },
        "milestones": {
            "is_archived": (Boolean(), " NOT NULL DEFAULT FALSE"),
        },
    }
    inspector = inspect(target_engine)
    with target_engine.begin() as connection:
        for table_name, table_additions in additions.items():
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, (column_type, column_suffix) in table_additions.items():
                if column_name not in existing_columns:
                    type_sql = target_engine.dialect.type_compiler.process(column_type)
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN "
                            f"{column_name} {type_sql}{column_suffix}"
                        )
                    )


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
