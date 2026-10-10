from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_db_and_tables
from app.routes import challenges, contributions, goals, progress, tasks


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


settings = get_settings()

app = FastAPI(
    title="Skills to Impact API",
    description=(
        "Local development API for persisted goals, generated action plans, tasks, "
        "contributions, and progress. Authentication is not implemented."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(goals.router)
app.include_router(tasks.router)
app.include_router(challenges.router)
app.include_router(contributions.router)
app.include_router(progress.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
