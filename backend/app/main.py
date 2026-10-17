from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import create_db_and_tables
from app.routes import auth, challenges, contributions, goals, progress, tasks


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


settings = get_settings()

app = FastAPI(
    title="Skills to Impact API",
    description=(
        "Local development API for persisted goals, generated action plans, tasks, "
        "contributions, and per-account progress with cookie-based authentication."
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

@app.middleware("http")
async def validate_request_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and origin is not None
        and origin not in settings.allowed_origins
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Untrusted request origin"},
        )
    return await call_next(request)


app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(tasks.router)
app.include_router(challenges.router)
app.include_router(contributions.router)
app.include_router(progress.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
